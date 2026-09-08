import argparse,os,json,time,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
import yaml
from .models import Config,Candidate,Evaluation
from .rules import EntityList
from .transport import Http
from .storage import Store,GitHubState
from .providers import Alpaca,Sec,NasdaqHalts
from .extraction import LocalParser
from .discovery import Discovery
from .runner import Scanner
from .notify import digest,DiscordSender,local_time,send_allowed
UTC=timezone.utc

def settings(root):
    cfg=Config.model_validate(yaml.safe_load((root/'config/strategy.yaml').read_text()))
    overrides={}
    if os.environ.get('SURGE_RETURN_MIN_PCT','').strip():
        overrides['surge_return_min_pct']=os.environ['SURGE_RETURN_MIN_PCT']
    if overrides:
        cfg=Config.model_validate(dict(cfg.model_dump(),**overrides))
    entries=yaml.safe_load((root/'config/entities.yaml').read_text())
    if cfg.rvol_min_sessions>cfg.rvol_target_sessions:raise ValueError('Invalid RVOL window')
    if cfg.market_feed=='sip' and cfg.market_data_delay_minutes<16:raise ValueError('Free SIP mode requires at least 16 minutes of delay')
    return cfg,entries

def report(root,results,now,cfg,issues=()):
    folder=root/'reports';folder.mkdir(exist_ok=True)
    raw={'asof':now.isoformat(),'config':cfg.model_dump(),'issues':list(issues),'results':[r.model_dump(mode='json') for r in results]}
    (folder/'latest.json').write_text(json.dumps(raw,indent=2,allow_nan=False))
    chunks=digest(results,now,cfg)
    (folder/'discord-preview.txt').write_text('\n\n--- NEXT MESSAGE ---\n\n'.join(p['content']+'\n'+json.dumps(p.get('embeds',[]),indent=2) for p in chunks) or 'No qualified alerts. See latest.json for review and configuration reasons.')
    (folder/'discord-payloads.json').write_text(json.dumps(chunks,indent=2))
    counts={}
    for r in results:counts[r.status]=counts.get(r.status,0)+1
    print(json.dumps({'evaluations':counts,'issues':len(issues),'report':'reports/latest.json'}))

def required_env(name):
    value=os.environ.get(name,'')
    if not value:raise ValueError('Missing '+name+'; configure it as a GitHub Actions secret')
    return value

def main():
    parser=argparse.ArgumentParser(description='DECA SMG notifier (no order execution)')
    parser.add_argument('command',choices=['doctor','discover','scan','noon','demo','activate','practice'])
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--send',action='store_true',help='Only noon mode can send, and only during the configured noon minute')
    args=parser.parse_args();root=args.root.resolve();cfg,entries=settings(root)
    if args.send and args.command!='noon':parser.error('--send is available only for noon mode')
    if args.command=='demo':
        from .demo import run_demo
        results,now=run_demo(cfg,EntityList(entries));report(root,results,now,cfg,['SYNTHETIC FIXTURES: demo uses an explicit 100% threshold for demonstration only']);return
    if args.command=='doctor':
        checks={key:bool(os.environ.get(key)) for key in ['ALPACA_API_KEY','ALPACA_SECRET_KEY','SEC_USER_AGENT','DISCORD_WEBHOOK_URL']}
        print(json.dumps({'secrets_present':checks,'hosted_ai_required':False,'market_feed':cfg.market_feed,'market_data_delay_minutes':cfg.market_data_delay_minutes,'surge_threshold_configured':cfg.surge_return_min_pct is not None,'time':cfg.notification_timezone+' 12:00','sending_enabled':os.environ.get('DISCORD_ENABLED')=='true'},indent=2));return
    http=Http();backend=None;path=root/'runtime/state.sqlite'
    if os.environ.get('GITHUB_ACTIONS')=='true':
        backend=GitHubState(http,required_env('GITHUB_REPOSITORY'),required_env('GITHUB_TOKEN'),cfg.state_branch)
        backend.restore(path)
    store=Store(path)
    checkpoint=backend.checkpoint if backend else lambda state:None
    entities=EntityList(entries)
    now=datetime.now(UTC)
    try:
        if args.command=='practice':
            if os.environ.get('DISCORD_ENABLED')!='true':raise ValueError('Discord delivery is disabled')
            from .practice import practice_payload,practice_embed
            payload,audit=practice_payload(store,root,now,cfg,entities)
            sender=DiscordSender(http,required_env('DISCORD_WEBHOOK_URL'),store,checkpoint)
            payload=practice_embed(payload,audit,now)
            receipt=sender.activation('practice-reference-check-2026-09-08',payload,format_version='embed-v1')
            folder=root/'reports';folder.mkdir(exist_ok=True)
            (folder/'practice.json').write_text(json.dumps(dict(receipt=receipt,audit=audit),indent=2))
            (folder/'practice-embed.json').write_text(json.dumps(payload,indent=2))
            print(json.dumps({'practice_receipt':receipt,'overlap':audit['overlap_tickers']}));return
        if args.command=='discover':
            sec=Sec(http,required_env('SEC_USER_AGENT'),store)
            if cfg.screening_profile=='firm_first':
                from .live_firms import LiveFirmDiscovery
                discovery=LiveFirmDiscovery(sec,LocalParser(entries),store,cfg)
            else:discovery=Discovery(sec,LocalParser(entries),store,cfg)
            candidates=discovery.run(now)
            print(json.dumps({'stored_candidates':len(candidates),'issues':discovery.issues,'filing_downloads':discovery.downloads}));return
        if args.command=='activate':
            if os.environ.get('DISCORD_ENABLED')!='true':raise ValueError('Discord delivery is disabled')
            from .backtest import probe_market
            health=probe_market(cfg)
            if health.get('status')!='ACCESS_VERIFIED':raise ValueError('Alpaca health probe failed')
            discovery=store.get('live_discovery')
            if not discovery:raise ValueError('Run live discovery before activation')
            sender=DiscordSender(http,required_env('DISCORD_WEBHOOK_URL'),store,checkpoint)
            release=json.loads((root/'config/deployment.json').read_text())['release_id']
            content=('Dudebot is deployed with the firm-first screen. Underwriters, auditors and counsel lead the watchlist; stocks can qualify before a pump.\n'
                'Hard exclusions: halted/suspended stocks, SPACs/acquisition corporations, and exactly-five-letter tickers. Unknown checks suppress stock alerts.\n'
                'Stock alerts: weekdays at 12:00 Pacific / 2:00 Central, following daylight saving time, using free Alpaca SIP delayed 16 minutes. GitHub scheduling can run late.\n'
                f'Initial discovery reviewed {discovery["reviewed"]} source records; further work resumes on schedule. Coverage remains partial.\n'
                'Historical screening replay is incomplete; no detection rate is established. This is an activation receipt, not a stock alert.')
            receipt=sender.activation(release,content)
            folder=root/'reports';folder.mkdir(exist_ok=True)
            (folder/'activation.json').write_text(json.dumps(dict(receipt,provider_health=health,discovery=discovery),indent=2))
            print(json.dumps({'activation':receipt}));return
        market=Alpaca(http,required_env('ALPACA_API_KEY'),require…1312 tokens truncated…     if m.drawdown_pct<=-20:phase+='; below recent high'
        lines=[f'**FIRM-FIRST WATCH | {clean(c.ticker)} | {clean(c.name)}**',
               'Listed-firm relationship: '+clean(entity)+'.',
               f'Price ${m.price:,.2f} | 21-session return {metric(m.monthly_return,"%")} | RVOL {metric(m.rvol,"×")}.',
               f'State: {phase}; drawdown from recent high {m.drawdown_pct:.2f}%.',
               f'IPO date: {c.ipo_date or "unverified"} | offering price {metric(c.offer_price)}; proceeds {metric(c.offer_gross)}.',
               'Offering size, price, age, geography and pump/volume are preferences; firm association is a research signal.',
               f'Data: {m.feed}, delayed {m.declared_delay_minutes} minutes; price {m.price_time.isoformat()}.',
               f'Halt check: {e.halt.checked_at.isoformat()}.']
        gaps=[r.removeprefix('PREFERENCE_GAP:') for r in e.reasons if r.startswith('PREFERENCE_GAP:')]
        if gaps:lines.append('Preference/data gaps: '+clean(', '.join(gaps))[:450])
        urls=list(dict.fromkeys(x['evidence']['url'] for x in e.matches))
        lines+=['Sources:']+[f'<{u}>' for u in urls if urlsplit(u).scheme=='https' and '@' not in urlsplit(u).netloc]
        return '\n'.join(lines)
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
    items=sorted([e for e in evaluations if e.status=='QUALIFIED'],key=lambda e:e.rank)
    payloads=[]
    for i,e in enumerate(items):
        c=e.candidate;m=e.snapshot
        firm_first='VERIFIED_LISTED_FIRM_RELATIONSHIP' in e.reasons
        title='FIRM-FIRST WATCH' if firm_first else 'IPO SURGE MATCH' if c.pipeline=='RECENT_IPO' else 'DIRECT OFFERING REVIEW'
        super_priority=any(x.get('category','').startswith('SUPER ') for x in e.matches)
        firms='\n'.join(f"**{clean(x['name'])}** · {clean(x['role'])} · {clean(x['category'])}" for x in e.matches)
        urls=list(dict.fromkeys(x['evidence']['url'] for x in e.matches))
        sources='\n'.join(f'[Filing {n+1}]({u})' for n,u in enumerate(urls) if urlsplit(u).scheme=='https' and '@' not in urlsplit(u).netloc and not any(x in u for x in '()<>\n\r'))
        details=rationale(e).split('\n')[2:]
        # One card per stock stays below Discord's 6,000-character aggregate embed limit.
        description='\n'.join(x for x in details if x!='Sources:' and not x.startswith('<https://'))[:2500]
        embed={'title':f'{clean(c.ticker)} · {title}'[:256], 'description':clean(c.name)[:250]+'\n\n'+description,
               'color':0xE7AF38 if super_priority else 0x39B9A8,
               'fields':[{'name':'Matched firms','value':firms[:1000] or 'Unavailable','inline':False},
                         {'name':'Price','value':'$'+metric(m.price),'inline':True},
                         {'name':'21-session change','value':metric(m.monthly_return,'%'),'inline':True},
                         {'name':'Relative volume','value':metric(m.rvol,'×'),'inline':True},
                         {'name':'Source filings','value':sources[:1000] or 'See research report','inline':False}],
               'footer':{'text':f'Dudebot · {m.feed.upper()} delayed {m.declared_delay_minutes} min · Research watchlist'},
               'timestamp':m.price_time.isoformat()}
        payloads.append({'username':'Dudebot','content':('@everyone\n' if i==0 else '')+'**Daily research watchlist** · '+local_time(now,cfg).strftime('%b %d, %Y · %H:%M %Z'),
                         'embeds':[embed],'allowed_mentions':{'parse':['everyone'] if i==0 else []}})
    return payloads

class DiscordSender:
    def __init__(self,http,webhook,store,checkpoint,clock=None):
        parsed=urlsplit(webhook)
        if parsed.scheme!='https' or parsed.hostname not in {'discord.com','discordapp.com'} or not re.fullmatch(r'/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_.-]+',parsed.path):
            raise ValueError('Invalid Discord webhook URL')
        if parsed.query or parsed.fragment:raise ValueError('Webhook URL must not include query/fragment')
        self.http=http;self.webhook=webhook;self.store=store;self.checkpoint=checkpoint
        self.clock=clock or (lambda:datetime.now(UTC))
    def activation(self,release_id,content,format_version=None):
        """User-authorized deployment receipt, without mentions or stock alerts."""
        from .transport import ProviderError
        key='activation:'+release_id
        existing=self.store.get(key)
        body=dict(content) if isinstance(content,dict) else {'content':content}
        body['allowed_mentions']={'parse':[]}
        if existing:
            # Reformat the already-authorized practice message, never create another ping.
            if format_version and existing.get('status')=='SENT' and existing.get('format_version')!=format_version:
                message_id=str(existing.get('message_id',''))
                if not message_id.isdigit():raise ValueError('Invalid stored Discord message ID')
                try:
                    self.http.json(self.webhook+'/messages/'+message_id,method='PATCH',body=body,timeout=8)
                    existing.update(format_version=format_version,format_status='UPDATED')
                except ProviderError:existing['format_status']='UPDATE_UNCERTAIN'
                self.store.put(key,existing);self.checkpoint(self.store)
            return existing
        claim={'status':'CLAIMED','claimed_at':self.clock().isoformat()}
        self.store.put(key,claim);self.checkpoint(self.store)
        try:
            data=self.http.json(self.webhook,method='POST',params={'wait':'true'},
                body=body,timeout=8)
            claim.update(status='SENT',message_id=data['id'],channel_id=data.get('channel_id'))
            if format_version:claim['format_version']=format_version
        except (ProviderError,KeyError):claim['status']='DELIVERY_UNCERTAIN'
        self.store.put(key,claim);self.checkpoint(self.store)
        return claim
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
