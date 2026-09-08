from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import hashlib,json,re
from urllib.parse import urlsplit
from .market import snapshot_window
UTC=timezone.utc

def local_time(now,cfg):
    zone=timezone(timedelta(hours=-8),'PST') if cfg.notification_timezone=='fixed_UTC_minus_08' else ZoneInfo('America/Los_Angeles')
    return now.astimezone(zone)

def send_allowed(now,cfg):
    local=local_time(now,cfg)
    return local.hour==12 and local.minute==0 and local.second<cfg.send_window_seconds and snapshot_window(now)

def clean(text):
    # Untrusted filings cannot produce mentions, Markdown link labels, or code fences.
    return str(text).replace('@','＠').replace('`','').replace('<','').replace('>','')

def metric(value,suffix=''):
    return 'unavailable' if value is None else f'{value:,.2f}{suffix}'

def rationale(e):
    c=e.candidate;m=e.snapshot
    entity='; '.join(f"{x['name']} ({x['role']}; {x['category']})" for x in e.matches)
    title='IPO SURGE MATCH' if c.pipeline=='RECENT_IPO' else 'DIRECT OFFERING REVIEW'
    age=f'IPO {c.ipo_date}; {(m.asof.date()-c.ipo_date).days} days old' if c.pipeline=='RECENT_IPO' else f'Offering {c.event_date}; {c.status}'
    lines=[f'**{title} | {clean(c.ticker)} | {clean(c.name)}**',
        f'{age} | operations: {clean(c.operations_country)}',
        f'Offering: ${c.offer_gross:,.0f} at ${c.offer_price:,.2f} per share/ADS.',
        f'User-list match: {clean(entity)}.',
        f'Price ${m.price:,.2f} | 21-session return {metric(m.monthly_return,"%")} | 5-session {metric(m.five_day_return,"%")}.',
        f'RVOL {metric(m.rvol,"×")} vs {m.baseline_sessions} prior sessions at the same minute; 20-session RVOL {metric(m.rvol20,"×")}.',
        f'Volume {m.cumulative_volume:,.0f} / baseline {metric(m.baseline_volume)}; recent-high drawdown {m.drawdown_pct:.2f}%.',
        'Rationale: offering terms and a verified listed-firm relationship passed; '+('configured surge and RVOL floor passed.' if c.pipeline=='RECENT_IPO' else 'RVOL floor passed; transaction is for case-by-case team review.'),
        f'Data feed: {m.feed}; declared delay {m.declared_delay_minutes} minutes.',
        f'Price as of {m.price_time.isoformat()}; halt checked {e.halt.checked_at.isoformat()}.']
    age_priority_index=1 if c.pipeline=='RECENT_IPO' and len(e.rank)==6 else 0
    if e.rank and e.rank[age_priority_index]==0:
        lines.append('Priority: '+('30–100-day IPO focus.' if c.pipeline=='RECENT_IPO' else 'operations outside the U.S./Canada.'))
    if 'LOW_PRIORITY_MONTHLY_SURGE' in e.reasons:
        lines.append('Low priority: monthly gain is within the configured lower surge band; all screening rules still apply.')
    if m.flags:lines.append('Data notes: '+clean(', '.join(m.flags)))
    if c.notes:lines.append('Filing notes: '+clean('; '.join(c.notes))[:500])
    urls=list(dict.fromkeys([x['evidence']['url'] for x in e.matches]+[v.url for v in c.evidence.values()]+[m.source_url,e.halt.source_url]))
    urls=[u for u in urls if urlsplit(u).scheme=='https' and '@' not in urlsplit(u).netloc]
    lines+=['Sources:']+[f'<{u}>' for u in urls]
    return '\n'.join(lines)

def digest(evaluations,now,cfg):
    groups=[]
    for pipeline,label in [('RECENT_IPO','RECENT IPOs'),('DIRECT_OFFERING','DIRECT OFFERINGS')]:
        items=sorted([e for e in evaluations if e.status=='QUALIFIED' and e.candidate.pipeline==pipeline],key=lambda e:e.rank)
        if items:groups.append('**'+label+'**\n\n'+'\n\n'.join(rationale(e) for e in items))
    if not groups:return []
    text='SMG screening digest | '+local_time(now,cfg).strftime('%Y-%m-%d %H:%M %Z')+'\n\n'+'\n\n'.join(groups)
    chunks=[];current=''
    for line in text.splitlines(keepends=True):
        while len(line)>1850:
            if current:chunks.append(current);current=''
            chunks.append(line[:1850]);line=line[1850:]
        if len(current)+len(line)>1850:chunks.append(current);current=''
        current+=line
    if current:chunks.append(current)
    return [{'content':('@everyone\n' if i==0 else '')+part,'allowed_mentions':{'parse':['everyone'] if i==0 else []}} for i,part in enumerate(chunks)]

class DiscordSender:
    def __init__(self,http,webhook,store,checkpoint,clock=None):
        parsed=urlsplit(webhook)
        if parsed.scheme!='https' or parsed.hostname not in {'discord.com','discordapp.com'} or not re.fullmatch(r'/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_.-]+',parsed.path):
            raise ValueError('Invalid Discord webhook URL')
        if parsed.query or parsed.fragment:raise ValueError('Webhook URL must not include query/fragment')
        self.http=http;self.webhook=webhook;self.store=store;self.checkpoint=checkpoint
        self.clock=clock or (lambda:datetime.now(UTC))
    def send(self,evaluations,cfg):
        from .transport import ProviderError
        now=self.clock()
        if not send_allowed(now,cfg):return 'OUTSIDE_SEND_WINDOW'
        # Hard revalidation of timestamps and halt results before creating any payload.
        good=[]
        for e in evaluations:
            if e.status!='QUALIFIED' or not e.halt or e.halt.status!='CLEAR' or not e.snapshot:continue
            effective_now=now-timedelta(minutes=e.snapshot.declared_delay_minutes)
            feed_ok=e.snapshot.feed=='synthetic' or (e.snapshot.feed==cfg.market_feed and e.snapshot.declared_delay_minutes==cfg.market_data_delay_minutes)
            if feed_ok and 0<=(now-e.halt.checked_at).total_seconds()<=cfg.max_snapshot_age_seconds and all(0<=(effective_now-t).total_seconds()<=cfg.max_snapshot_age_seconds for t in [e.snapshot.price_time,e.snapshot.asof]):good.append(e)
        payloads=digest(good,now,cfg)
        if not payloads:return 'NO_QUALIFIED_MATCHES'
        key='delivery:'+str(local_time(now,cfg).date())
        if self.store.get(key):return 'ALREADY_CLAIMED'
        claim={'status':'CLAIMED','claimed_at':now.isoformat(),'hash':hashlib.sha256(json.dumps(payloads).encode()).hexdigest(),'messages':[]}
        self.store.put(key,claim)
        # Persist the claim remotely BEFORE the first network send. Failure aborts delivery.
        self.checkpoint(self.store)
        for payload in payloads:
            now=self.clock()
            if not send_allowed(now,cfg):
                claim['status']='MISSED_WINDOW';break
            try:
                data=self.http.json(self.webhook,method='POST',params={'wait':'true'},body=payload,timeout=8)
                claim['messages'].append(data['id']);claim['status']='SENT' if len(claim['messages'])==len(payloads) else 'PARTIAL'
            except (ProviderError,KeyError):
                # Ambiguous network results cannot safely be resent as another @everyone ping.
                claim['status']='DELIVERY_UNCERTAIN';break
            finally:
                self.store.put(key,claim);self.checkpoint(self.store)
        self.store.put(key,claim);self.checkpoint(self.store)
        return claim['status']
