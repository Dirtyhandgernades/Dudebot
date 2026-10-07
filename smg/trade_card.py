"""Compact signal cards and bounded paper sizing; scores are not probabilities."""
import math
from datetime import datetime,timedelta
from urllib.parse import urlsplit
from .shortability import executable_short

VERSION='simple-signal-v1'


def clean(value):
    return str(value).replace('@','＠').replace('`','').replace('<','').replace('>','')


def number(value,default=0):
    return value if isinstance(value,(int,float)) and math.isfinite(value) else default


def strength(e,now):
    """Fixed 100-point rubric. Missing evidence receives no points.

    Firm35, chart25, prior trained rank15, pump/volume10, live checks10,
    fresh news/FINRA context5. This has never been calibrated as a win rate.
    """
    firm=0
    if e.matches:
        firm=5
        roles={}
        for m in e.matches:
            role='underwriter' if m['role']=='placement_agent' else m['role']
            multiplier=1 if number(m.get('priority'),99)<=1 else .7 if number(m.get('priority'),99)==2 else .4
            roles[role]=max(roles.get(role,0),multiplier)
        firm+=15*roles.get('auditor',0)+10*roles.get('underwriter',0)+5*roles.get('counsel',0)
    ranked=e.ranking_evidence.get('ranked_firm',{});event=ranked.get('event',{})
    chart=0
    if 'RANKED_FIRM_EXHAUSTION_SHORT' in e.reasons:chart=15
    elif any('PUMP_FAILURE' in r for r in e.reasons):chart=15
    elif any('BREAKDOWN_SHORT' in r for r in e.reasons):chart=10
    chart=max(chart,25*max(0,min(100,number(event.get('dump_structure_score'))))/100)
    rank=15*max(0,min(1,number(ranked.get('rank_score'))))
    m=e.snapshot;market=checks=0
    if m:
        market=6*max(0,min(1,number(m.monthly_return)/60))+4*max(0,min(1,number(m.rvol)/3))
        effective=now-timedelta(minutes=m.declared_delay_minutes)
        if 0<=(effective-m.price_time).total_seconds()<=300:checks+=2.5
        if m.market_cap is not None and m.market_cap>=25_000_000 and m.market_cap_observed_at and 0<=(now-m.market_cap_observed_at).total_seconds()<=26*3600:checks+=2.5
    if e.halt and e.halt.status=='CLEAR' and 0<=(now-e.halt.checked_at).total_seconds()<=300:checks+=2.5
    if executable_short(e.shortability):checks+=2.5
    news=0;news_status='unavailable'
    context=e.ranking_evidence.get('sentiment',{})
    try:
        observed=datetime.fromisoformat(context['observed_at']);age=(now-observed).total_seconds()
        value=context['value'];sources=value.get('providers',{})
        item=sources.get('news',{});published=datetime.fromisoformat(item['latest_source_timestamp'])
        if 0<=age<=86400 and item.get('status')=='AVAILABLE' and 0<=(now-published).total_seconds()<=86400:
            news_status='fresh headline context'
            news=min(2.5,max(0,-number(item.get('headline_score'))))
    except (KeyError,ValueError,TypeError):pass
    finra=0
    try:
        row=e.ranking_evidence['finra_short_volume'];observed=datetime.fromisoformat(row['observed_at'])
        value=row['value'];ratio=value['short_volume_ratio']
        if 0<=(now-observed).total_seconds()<=86400 and value.get('status')=='AVAILABLE' and 0<=ratio<=1:
            finra=2.5*ratio
    except (KeyError,ValueError,TypeError):pass
    parts={'firm':round(firm,2),'chart':round(chart,2),'trained_rank':round(rank,2),
           'pump_volume':round(market,2),'current_checks':round(checks,2),'news':round(news,2),'finra_context':round(finra,2)}
    return {'score':min(99,max(0,int(round(sum(parts.values()))))),'components':parts,
            'is_probability':False,'news_status':news_status,'version':VERSION}


def position_guide(price,score,firm,qualified,equity=100000,available_bp=150000,probability=None,observed_range=None,reserved=0):
    """Exact integer count at a delayed quote; closing fill remains unknown.

    Evidence strength cannot override the shared exposure envelope.
    $5 order fee, 30bps modeled entry friction and a20% pre-order reserve apply.
    Account balances are explicit assumptions, not a connected SMG account.
    """
    if not qualified or price is None or not math.isfinite(price) or price<=3:
        return {'shares':0,'capital':0,'target':0,'tier':'Watch only','status':'NO_QUALIFIED_ENTRY'}
    if any(not math.isfinite(v) or v<0 for v in (equity,available_bp)):raise ValueError('Invalid paper account assumptions')
    evidence=probability or {};drop=evidence.get('targets',{}).get('day_3',{})
    severe=evidence.get('targets',{}).get('severe_50pct_day_3',{})
    high=(firm and score>=80 and evidence.get('status')=='ESTIMATED_HISTORICAL_REFERENCE'
          and evidence.get('samples',0)>=30 and drop.get('estimate',0)>=.35
          and drop.get('wilson_95',[0,1])[0]>=.20 and severe.get('estimate',0)>=.10)
    target=50000 if high else 20000 if score>=65 else 10000
    from .exposure import budget
    risk=budget(equity,available_bp,target,observed_range,reserved)
    ceiling=risk['ceiling']
    shares=max(0,math.floor((ceiling-5)/(price*1.2*1.003)))
    if shares<10:shares=0
    capital=round(shares*price,2)
    return {'shares':shares,'capital':capital,'target':target,'tier':'Strong firm setup' if high else 'Standard' if score>=65 else 'Small',
            'status':'PAPER_REFERENCE_ONLY' if shares else 'MINIMUM_10_SHARES_EXCEEDS_CAP',
            'equity_assumption':equity,'available_bp_assumption':available_bp,'reserve_pct':20,
            'exposure':risk,'reserved_capital':shares*price*1.2*1.003+5 if shares else 0}


def embed(e,now,practice=False):
    c=e.candidate;m=e.snapshot;score=strength(e,now)
    firm=bool(e.matches);qualified=e.status=='QUALIFIED' and not practice
    probability=e.ranking_evidence.get('drop_probability',{})
    risk=e.ranking_evidence.get('exposure',{})
    plan=e.ranking_evidence.get('paper_position_plan') if qualified else None
    if plan is None:plan=position_guide(m.price if m else None,score['score'],firm,qualified,probability=probability,
                                      observed_range=risk.get('observed_range'),reserved=risk.get('reserved',0))
    if 'RANKED_FIRM_EXHAUSTION_SHORT' in e.reasons:setup='Pump exhaustion / failed follow-through'
    elif any('PUMP_FAILURE' in r for r in e.reasons):setup='Pump failure'
    elif any('BREAKDOWN' in r for r in e.reasons):setup='Price breakdown'
    else:setup='Firm association; waiting for price confirmation' if firm else 'Volatility watch; confirmation pending'
    parties='; '.join(f"{clean(x['name'])} ({clean(x['role'])})" for x in e.matches[:3])
    why=(parties+'\n' if parties else 'No verified listed-firm match.\n')+setup
    if m:why+=f" · price ${m.price:.2f}"+(f" · RVOL {m.rvol:.1f}×" if m.rvol is not None else '')
    horizon='Estimated drop window: next 1–3 trading sessions.\nReassess each close; maximum planned hold: 3 sessions.' if qualified else 'No entry confirmed. Monitor for a 1–3-session setup; hold 0 shares until qualified.'
    sizing=(f"**{plan['shares']:,} shares · ${plan['capital']:,.2f} at the quoted price**\n{plan['tier']} · 20% price reserve. 10% per-position / 60% total advisory exposure limits.\nPaper account: $100k equity. Closing fill and actual holdings are unknown; losses can exceed the modeled risk budget."
            if plan['shares'] else '**0 shares · $0 allocated**\n'+('Practice/watch only; no qualified entry.' if not qualified else '10-share minimum exceeds the paper position cap.'))
    urls=list(dict.fromkeys(x['evidence']['url'] for x in e.matches))
    safe=[u for u in urls if urlsplit(u).scheme=='https' and '@' not in urlsplit(u).netloc and not any(t in u for t in '()<>\r\n')]
    source=' · '.join(f'[Filing {i+1}]({u})' for i,u in enumerate(safe[:2])) or 'See scan report for source evidence.'
    lane='FIRM WATCH' if firm else 'VOLATILITY SHORT' if c.pipeline=='VOLATILITY_WATCH' else 'NON-FIRM WATCH'
    title=f"{clean(c.ticker)} · {lane}"+(' · PRACTICE' if practice else ' · SHORT' if qualified else ' · WATCH')
    chance='Insufficient comparable data / entry not confirmed.'
    if qualified and probability.get('status')=='ESTIMATED_HISTORICAL_REFERENCE':
        targets=probability['targets'];third=targets['day_3'];interval=third['wilson_95']
        chance='20%+ closing-price drop: '+ ' · '.join(f"{h}d {100*targets[f'day_{h}']['estimate']:.1f}%" for h in (1,2,3))
        chance+=f"\n3-day range: {100*interval[0]:.0f}–{100*interval[1]:.0f}% · {probability['samples']} past episodes"
        chance+=f"\n50%+ drop within 3d: {100*targets['severe_50pct_day_3']['estimate']:.1f}% · conditional historical estimate"
    fields=[{'name':'Why picked · Firm watch: '+('Yes' if firm else 'No'),'value':why[:900]},
            {'name':'Strength score','value':f"**{score['score']}/100** · heuristic evidence strength, not a probability. News: {score['news_status']}."},
            {'name':'Estimated drop probability','value':chance},
            {'name':'Drop window / hold','value':horizon},
            {'name':'Suggested paper position','value':sizing},
            {'name':'Source','value':source[:950]}]
    return {'title':title[:256],'description':clean(c.name)[:200],
            'color':0x39B9A8 if qualified else 0xE7AF38,'fields':fields,
            'footer':{'text':('PRACTICE ONLY · ' if practice else '')+'Historical estimates, not live-calibrated guarantees · firm association is not a fraud finding'+(f' · SIP delayed {m.declared_delay_minutes} min' if m else '')},'timestamp':now.isoformat()}
