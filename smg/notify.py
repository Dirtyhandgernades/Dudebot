from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import hashlib,json,re
from urllib.parse import urlsplit
from .market import snapshot_window
from .game_rules import eligibility
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
    if c.pipeline=='VOLATILITY_WATCH':
        setup='pump failure' if 'PUMP_FAILURE_SHORT' in e.reasons else 'high-volatility breakdown'
        firm='; '.join(f"{x['name']} ({x['role']}; {x['category']})" for x in e.matches) or 'no listed high-priority firm match'
        lines=[f'**VOLATILITY SHORT | {clean(c.ticker)} | {clean(c.name)}**',
            f'Setup: {setup}; listed-firm context: {clean(firm)}.',
            f'Price ${m.price:,.2f} | 21-session return {metric(m.monthly_return,"%")} | one-session {metric(m.one_day_return,"%")}.',
            f'RVOL {metric(m.rvol,"×")} | drawdown from recent high {m.drawdown_pct:.2f}%.',
            'Broad lane requires stronger market confirmation when no priority firm is present.',
            f'Data: {m.feed}, delayed {m.declared_delay_minutes} minutes; price {m.price_time.isoformat()}.',
            f'Halt check: {e.halt.checked_at.isoformat()}.','Sources:']
        lines += [f'<{v.url}>' for v in c.evidence.values() if urlsplit(v.url).scheme=='https']
        return '\n'.join(lines)
    if 'VERIFIED_LISTED_FIRM_RELATIONSHIP' in e.reasons:
        entity='; '.join(f"{x['name']} ({x['role']}; {x['category']})" for x in e.matches)
        phase='monthly history unavailable' if m.monthly_return is None else 'below preferred surge' if 'NOT_YET_PUMPED_OR_BELOW_PREFERRED_SURGE' in e.reasons else 'lower-priority surge' if 'LOW_PRIORITY_MONTHLY_SURGE' in e.reasons else 'pumped'
        if m.drawdown_pct<=-20:phase+='; below recent high'
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
        title='VOLATILITY SHORT' if c.pipeline=='VOLATILITY_WATCH' else 'FIRM-FIRST WATCH' if firm_first else 'IPO SURGE MATCH' if c.pipeline=='RECENT_IPO' else 'DIRECT OFFERING REVIEW'
        super_priority=any(x.get('category','').startswith('SUPER ') for x in e.matches)
        firms='\n'.join(f"**{clean(x['name'])}** · {clean(x['role'])} · {clean(x['category'])}" for x in e.matches)
        urls=list(dict.fromkeys(x['evidence']['url'] for x in e.matches))
        sources='\n'.join(f'[Filing {n+1}]({u})' for n,u in enumerate(urls) if urlsplit(u).scheme=='https' and '@' not in urlsplit(u).netloc and not any(x in u for x in '()<>\n\r'))
        details=rationale(e).split('\n')[2:]
        # One card per stock stays below Discord's 6,000-character aggregate embed limit.
        description='\n'.join(x for x in details if x!='Sources:' and not x.startswith('<https://'))[:2500]
        borrow=e.shortability or {};finra=(e.ranking_evidence.get('finra_short_volume') or {}).get('value',{})
        sentiment=(e.ranking_evidence.get('sentiment') or {}).get('value',{})
        context=f"Alpaca borrow: {borrow.get('borrow_status','unavailable')} · tradable {borrow.get('tradable','?')} · shortable {borrow.get('shortable','?')}\n"
        context+=f"FINRA prior-day short-volume ratio: {metric((finra.get('short_volume_ratio')*100) if finra.get('short_volume_ratio') is not None else None,'%')}\n"
        context+=f"Sentiment score: {metric(sentiment.get('score'))} (ranking context only)"
        embed={'title':f'{clean(c.ticker)} · {title}'[:256], 'description':clean(c.name)[:250]+'\n\n'+description,
               'color':0xE7AF38 if super_priority else 0x39B9A8,
               'fields':[{'name':'Matched firms','value':firms[:1000] or 'No listed high-priority firm match; stronger volatility confirmation required','inline':False},
                         {'name':'Price','value':'$'+metric(m.price),'inline':True},
                         {'name':'21-session change','value':metric(m.monthly_return,'%'),'inline':True},
                         {'name':'Relative volume','value':metric(m.rvol,'×'),'inline':True},
                         {'name':'DECA eligibility','value':f'Reported market cap: ${metric(m.market_cap)}\nNasdaq/NYSE · price > $3 · cap ≥ $25M\nMinimum opening order: 10 shares (~${metric(m.price*10)} before fees)','inline':False},
                         {'name':'4–7 session short evidence','value':context[:1024],'inline':False},
                         {'name':'Source filings','value':sources[:1000] or 'See research report','inline':False}],
               'footer':{'text':f'Dudebot · {m.feed.upper()} delayed {m.declared_delay_minutes} min · Research watchlist'},
               'timestamp':m.price_time.isoformat()}
        payloads.append({'username':'Dudebot','content':('@everyone\n' if i==0 else '')+'**New qualified trade** · '+local_time(now,cfg).strftime('%b %d, %Y · %H:%M %Z'),
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
            if eligibility(e.snapshot,cfg,now)[0]:continue
            from .shortability import executable_short
            if cfg.short_alerts_require_borrow and (e.signal_side!='SHORT' or not executable_short(e.shortability)):continue
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

    def _valid_trade(self,e,cfg,now):
        if e.status!='QUALIFIED' or not e.halt or e.halt.status!='CLEAR' or not e.snapshot:return False
        if eligibility(e.snapshot,cfg,now)[0]:return False
        from .shortability import executable_short
        if cfg.short_alerts_require_borrow and (e.signal_side!='SHORT' or not executable_short(e.shortability)):return False
        effective=now-timedelta(minutes=e.snapshot.declared_delay_minutes)
        if not snapshot_window(effective):return False
        feed_ok=e.snapshot.feed=='synthetic' or (e.snapshot.feed==cfg.market_feed and e.snapshot.declared_delay_minutes==cfg.market_data_delay_minutes)
        return bool(feed_ok and 0<=(now-e.halt.checked_at).total_seconds()<=cfg.max_snapshot_age_seconds and
            all(0<=(effective-t).total_seconds()<=cfg.max_snapshot_age_seconds for t in [e.snapshot.price_time,e.snapshot.asof]))

    @staticmethod
    def _phase(e,cfg):
        m=e.snapshot
        if m.drawdown_pct<=-20:return 'FALLEN_20'
        if m.monthly_return is None:return 'HISTORY_UNKNOWN'
        if m.monthly_return<(cfg.surge_return_min_pct or 0):return 'PRE_PUMP'
        if cfg.ipo_low_priority_surge_max_pct is not None and m.monthly_return<=cfg.ipo_low_priority_surge_max_pct:return 'LOW_SURGE'
        return 'PUMPED'

    def send_new(self,evaluations,cfg):
        """Send only newly qualified trade phases; no wall-clock delivery gate.

        Claims are checkpointed before Discord. An uncertain request is never
        retried, and a continuing signal does not ping again every 15 minutes.
        """
        from .transport import ProviderError
        now=self.clock();new=[];claims=[]
        for e in sorted(evaluations,key=lambda x:(not bool(x.matches),x.rank,x.candidate.ticker)):
            # A ticker/side/phase is one trade even when both discovery lanes
            # found it. This prevents duplicate firm and volatility alerts.
            identity=e.candidate.ticker+':'+str(e.signal_side or cfg.live_signal_side)
            state_key='trade_alert_state:'+hashlib.sha256(identity.encode()).hexdigest()
            if not self._valid_trade(e,cfg,now):
                definitive=e.status in {'EXCLUDED','MARKET_NOT_CONFIRMED'} or ('CURRENT_BORROW_NOT_EXECUTABLE' in e.reasons and (e.shortability or {}).get('status')=='CURRENT')
                if definitive:self.store.delete(state_key)
                continue
            phase=self._phase(e,cfg);prior=self.store.get(state_key)
            if prior and prior.get('phase')==phase:continue
            claim={'status':'CLAIMED','claimed_at':now.isoformat(),'phase':phase,'candidate_key':e.candidate.key,'ticker':e.candidate.ticker,'side':e.signal_side}
            self.store.put(state_key,claim);claims.append((state_key,claim));new.append(e)
        if not new:return 'NO_NEW_TRADES'
        self.checkpoint(self.store)
        payloads=digest(new,now,cfg)
        for (key,claim),payload in zip(claims,payloads):
            try:
                data=self.http.json(self.webhook,method='POST',params={'wait':'true'},body=payload,timeout=8)
                claim.update(status='SENT',message_id=data['id'],sent_at=self.clock().isoformat())
            except (ProviderError,KeyError):claim['status']='DELIVERY_UNCERTAIN'
            self.store.put(key,claim);self.checkpoint(self.store)
        return {'status':'SENT' if all(c['status']=='SENT' for _,c in claims) else 'DELIVERY_UNCERTAIN',
            'new_trades':len(new),'tickers':[e.candidate.ticker for e in new]}

    def send_daily_no_trade(self,evaluations,cfg):
        """Send one mention-free close-of-day summary when no trade was sent.

        This is deliberately separate from trade qualification: near misses are
        useful review context, but are never promoted into actionable alerts.
        """
        from .transport import ProviderError
        now=self.clock();local=local_time(now,cfg);day=str(local.date())
        if local.weekday()>=5 or local.hour<13:return 'BEFORE_DAILY_SUMMARY'
        for _,value in self.store.items('trade_alert_state:'):
            sent=value.get('sent_at')
            if sent and str(local_time(datetime.fromisoformat(sent),cfg).date())==day:
                return 'TRADE_SENT_TODAY'
        key='daily_no_trade:'+day
        if self.store.get(key):return 'ALREADY_CLAIMED'
        ranked=sorted(evaluations,key=lambda e:(e.snapshot is None,e.status in {'EXCLUDED','REVIEW_REQUIRED'},not bool(e.matches),e.rank,e.candidate.ticker))[:5]
        lines=[]
        for e in ranked:
            m=e.snapshot
            market='' if not m else f' · ${m.price:.2f} · 21d {metric(m.monthly_return,"%")} · RVOL {metric(m.rvol,"×")}'
            reasons=', '.join(e.reasons[:3]) or e.status
            lines.append(f'**{clean(e.candidate.ticker)}** · {clean(e.status)}{market}\n{clean(reasons)[:300]}')
        embed={'title':'Daily scan complete · no qualified trade',
            'description':'Dudebot completed today’s scans. No setup passed every live execution rule. The strongest reviewed names are shown as near-misses only.',
            'color':0x6B7280,
            'fields':[{'name':'Strongest near-misses','value':'\n\n'.join(lines)[:1024] if lines else 'No eligible candidates had complete market data.','inline':False},
                      {'name':'Rules kept active','value':'Nasdaq/NYSE · price > $3 · market cap ≥ $25M · exclusions · current halt check · current Alpaca borrow for shorts','inline':False}],
            'footer':{'text':'Dudebot · no trade was forced · research watchlist'},'timestamp':now.isoformat()}
        payload={'username':'Dudebot','content':'**Daily Dudebot status** · '+local.strftime('%b %d, %Y'),
            'embeds':[embed],'allowed_mentions':{'parse':[]}}
        claim={'status':'CLAIMED','claimed_at':now.isoformat(),'candidate_count':len(evaluations)}
        self.store.put(key,claim);self.checkpoint(self.store)
        try:
            data=self.http.json(self.webhook,method='POST',params={'wait':'true'},body=payload,timeout=8)
            claim.update(status='SENT',message_id=data['id'],sent_at=self.clock().isoformat())
        except (ProviderError,KeyError):claim['status']='DELIVERY_UNCERTAIN'
        self.store.put(key,claim);self.checkpoint(self.store)
        return claim
