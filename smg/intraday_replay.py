"""Fixed pre-close firm experiment; reference labels never select its universe.

Five-minute price proxies are truncated before the delayed observation cutoff.
Volume uses a disclosed uniform-time projection, not a claimed matched-time
RVOL. No percentage confidence or executable historical return is certified.
"""
import argparse
import gzip
import hashlib
import json
import os
import time
from collections import Counter
from datetime import date,datetime,timedelta
from pathlib import Path
from .backtest import write_json
from .cli import settings
from .game_firm_replay import lead_metrics
from .market import session_bounds
from .swing_backtest import simulate,firm_exhaustion_trigger,dump_structure_score
from .transport import Http,ProviderError

STRATEGY='FIRM_INTRADAY_EXHAUSTION_RESEARCH'
HYBRID='FIRM_HYBRID_EXHAUSTION_RESEARCH'


def decision_window(day,delay=16):
    opened,closed=session_bounds(date.fromisoformat(day))
    decision=closed-timedelta(minutes=20)
    return opened,closed,decision,decision-timedelta(minutes=delay)


def partial_bar(bars,opened,cutoff):
    valid={}
    for bar in bars:
        stamp=datetime.fromisoformat(bar['t'].replace('Z','+00:00'))
        if stamp.tzinfo is None:raise ValueError('Naive provider bar timestamp')
        if opened<=stamp and stamp+timedelta(minutes=5)<=cutoff:
            valid[stamp]=bar
    if not valid:return None
    stamps=sorted(valid)
    if cutoff-(stamps[-1]+timedelta(minutes=5))>timedelta(minutes=5):return None
    rows=[valid[s] for s in stamps]
    return {'o':rows[0]['o'],'h':max(r['h'] for r in rows),
            'l':min(r['l'] for r in rows),'c':rows[-1]['c'],
            'v':sum(r['v'] for r in rows),'last_complete_at':(stamps[-1]+timedelta(minutes=5)).isoformat(),
            'bars':len(rows)}


def candidates(packet,day):
    sessions=packet['sessions'];i=sessions.index(day)
    if i<22:return []
    previous=sessions[i-22:i];chosen=[]
    for ticker,first in sorted(packet['firm_dates'].items()):
        if first>day or ticker not in packet['raw']:continue
        raw=packet['raw'][ticker].get(previous[-1])
        history=[packet['split'].get(ticker,{}).get(d) for d in previous]
        # Cheap selection uses prior information, never today's final close.
        if not raw or raw['c']<=3 or not all(history):continue
        if history[-1]['c']/history[0]['c']-1<0:continue
        chosen.append(ticker)
    return chosen


class Bars:
    def __init__(self,cache,max_requests=400):
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.http=Http();self.requests=0;self.max_requests=max_requests
        self.headers={'APCA-API-KEY-ID':os.environ['ALPACA_API_KEY'],
                      'APCA-API-SECRET-KEY':os.environ['ALPACA_SECRET_KEY']}
    def get(self,symbols,opened,cutoff,adjustment):
        result={};seen=set()
        if not symbols:return result
        query={'symbols':','.join(sorted(symbols)),'timeframe':'5Min',
               'start':opened.isoformat(),'end':cutoff.isoformat(),
               'feed':'sip','adjustment':adjustment,'asof':'-','limit':10000}
        while True:
            path=self.cache/(hashlib.sha256(json.dumps(query,sort_keys=True).encode()).hexdigest()+'.json')
            if path.exists():data=json.loads(path.read_text())
            else:
                if self.requests>=self.max_requests:raise RuntimeError('REQUEST_BUDGET')
                data=self.http.json('https://data.alpaca.markets/v2/stocks/bars',params=query,headers=self.headers)
                self.requests+=1;write_json(path,data)
            for ticker,rows in (data.get('bars') or {}).items():result.setdefault(ticker,[]).extend(rows)
            token=data.get('next_page_token')
            if not token:return result
            if token in seen:raise ValueError('Repeated provider pagination token')
            seen.add(token);query['page_token']=token


def projected_history(packet,ticker,day,partial):
    sessions=packet['sessions'];i=sessions.index(day);opened,closed,decision,cutoff=decision_window(day)
    history=[packet['split'][ticker][d] for d in sessions[i-21:i]]
    observed=datetime.fromisoformat(partial['last_complete_at'])
    fraction=(observed-opened)/(closed-opened)
    return history+[{**partial,'v':partial['v']/fraction}],fraction,observed


def signal_event(packet,ticker,day,adjusted_partial,raw_partial,cfg):
    if not adjusted_partial or not raw_partial or raw_partial['c']<=3:return None
    if raw_partial['last_complete_at']!=adjusted_partial['last_complete_at']:return None
    opened,closed,decision,cutoff=decision_window(day)
    history,fraction,observed=projected_history(packet,ticker,day,adjusted_partial)
    trigger=firm_exhaustion_trigger(history,cfg)
    if not trigger:return None
    return {'ticker':ticker,'signal_date':day,'decision_at':decision.isoformat(),
            'data_cutoff':cutoff.isoformat(),'last_complete_at':observed.isoformat(),
            'decision_price':raw_partial['c'],'timing_trigger':STRATEGY,
            'dump_structure_score':dump_structure_score(history),
            'volume_method':'UNIFORM_TIME_PROJECTION_RESEARCH_ONLY',
            'observed_volume':adjusted_partial['v'],'session_fraction':fraction}


def hybrid_event(packet,ticker,day,partial,raw_partial,cfg):
    """Prefer a current chart; otherwise revalidate a prior-close pattern.

    The fixed price band rejects a >10% already-fallen move or >20% resumed
    squeeze. It is an experimental invalidation rule, not a loss guarantee.
    """
    event=signal_event(packet,ticker,day,partial,raw_partial,cfg)
    if event:return {**event,'timing_trigger':HYBRID,'pattern_date':day,'source_policy':STRATEGY}
    if not partial or not raw_partial or raw_partial['c']<=3:return None
    if partial['last_complete_at']!=raw_partial['last_complete_at']:return None
    i=packet['sessions'].index(day);prior=packet['sessions'][i-22:i]
    history=[packet['split'][ticker][d] for d in prior]
    if not firm_exhaustion_trigger(history,cfg):return None
    change=partial['c']/history[-1]['c']-1
    if not -.10<change<=.20:return None
    _,_,decision,cutoff=decision_window(day)
    return {'ticker':ticker,'signal_date':day,'pattern_date':prior[-1],
            'source_policy':'PRIOR_CLOSE_EXHAUSTION_REVALIDATED_PRICE',
            'decision_at':decision.isoformat(),'data_cutoff':cutoff.isoformat(),
            'last_complete_at':partial['last_complete_at'],'decision_price':raw_partial['c'],
            'timing_trigger':HYBRID,'dump_structure_score':dump_structure_score(history),
            'observed_change_from_prior_close':change}


def confirmed_hybrid_events(packet,events,max_observed_gain=.02):
    """Research filter: avoid entering a short during a continuing up move.

    Uses only the decision quote and prior raw close. It never reads the
    entry-day final close or future outcomes. Raw price changes remain subject
    to the same unresolved corporate-action coverage as the source replay.
    """
    index={d:i for i,d in enumerate(packet['sessions'])}
    result={};audit=Counter()
    for day,rows in events.items():
        result[day]=[]
        i=index.get(day,0)
        for event in rows:
            prior=packet['raw'].get(event['ticker'],{}).get(packet['sessions'][i-1]) if i else None
            if not prior or prior['c']<=0:
                audit['UNKNOWN_PRIOR_RAW_PRICE']+=1;continue
            change=event['decision_price']/prior['c']-1
            if change>max_observed_gain:
                audit['CONTINUING_UP_MOVE']+=1;continue
            result[day].append({**event,'entry_filter':'OBSERVED_GAIN_AT_MOST_2_PERCENT',
                                'observed_gain_from_prior_raw_close':change})
            audit['RETAINED']+=1
    return result,dict(audit)


def scaled_hybrid_events(packet,events):
    """Fixed research sizing: half target while the observed pump continues.

    Retains higher-risk firm signals so a strict confirmation filter cannot
    remove all such rug candidates. This multiplier is not confidence.
    """
    confirmed,audit=confirmed_hybrid_events(packet,events)
    allowed={(day,e['ticker']) for day,rows in confirmed.items() for e in rows}
    index={d:i for i,d in enumerate(packet['sessions'])};result={}
    for day,rows in events.items():
        result[day]=[];i=index.get(day,0)
        for event in rows:
            prior=packet['raw'].get(event['ticker'],{}).get(packet['sessions'][i-1]) if i else None
            if not prior or prior['c']<=0:continue
            result[day].append({**event,'position_scale':1.0 if (day,event['ticker']) in allowed else .5,
                'observed_gain_from_prior_raw_close':event['decision_price']/prior['c']-1,
                'entry_filter':'FIXED_HALF_TARGET_DURING_CONTINUING_UP_MOVE'})
    return result,audit


def run(packet,cfg,client,years,out,max_seconds=600):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);summary=[]
    started=time.monotonic()
    for year in years:
        events={};hybrid={};audit=[];gaps=Counter()
        days=[d for d in packet['sessions'] if f'{year}-09-08'<=d<f'{year}-12-05']
        for day in days:
            if time.monotonic()-started>max_seconds:
                gaps['TIME_BUDGET']+=len(days)-days.index(day);break
            names=candidates(packet,day);opened,closed,decision,cutoff=decision_window(day)
            try:
                adjusted=client.get(names,opened,cutoff,'split')
                preliminary={};partials={}
                for ticker in names:
                    partial=partial_bar(adjusted.get(ticker,[]),opened,cutoff)
                    if not partial:gaps['MISSING_OR_STALE_SPLIT_WINDOW']+=1;continue
                    partials[ticker]=partial
                    # Fetch raw quotes only after a chart match. There is no
                    # guessed raw price or trade event at this stage.
                    history,_,_=projected_history(packet,ticker,day,partial)
                    if firm_exhaustion_trigger(history,cfg):preliminary[ticker]=partial
                prior_names=[]
                i=packet['sessions'].index(day)
                for ticker in partials:
                    prior=[packet['split'][ticker][d] for d in packet['sessions'][i-22:i]]
                    if firm_exhaustion_trigger(prior,cfg):prior_names.append(ticker)
                raw=client.get(sorted(set(preliminary)|set(prior_names)),opened,cutoff,'raw')
                selected=[];combined=[]
                raw_missing=set()
                for ticker in sorted(set(preliminary)|set(prior_names)):
                    partial=partials[ticker]
                    raw_partial=partial_bar(raw.get(ticker,[]),opened,cutoff)
                    if not raw_partial:
                        gaps['MISSING_OR_STALE_RAW_WINDOW']+=1;raw_missing.add(ticker);continue
                    event=signal_event(packet,ticker,day,partial,raw_partial,cfg)
                    if event:selected.append(event)
                    event=hybrid_event(packet,ticker,day,partial,raw_partial,cfg)
                    if event:combined.append(event)
                events[day]=selected
                hybrid[day]=combined
                audit.append({'day':day,'candidates':len(names),'chart_matches':len(preliminary),
                              'signals':len(selected),'hybrid_signals':len(combined),'decision_at':decision.isoformat(),'data_cutoff':cutoff.isoformat(),
                              'candidate_audit':[{'ticker':t,'status':'SPLIT_WINDOW_UNAVAILABLE' if t not in partials else
                                  'RAW_WINDOW_UNAVAILABLE' if t in raw_missing else 'HYBRID_SETUP_FOUND' if any(e['ticker']==t for e in combined) else
                                  'SETUP_PRICE_OR_CONFIRMATION_REJECTED' if t in set(preliminary)|set(prior_names) else 'NO_TIMING_PATTERN'} for t in names]})
            except (ProviderError,RuntimeError) as exc:
                gaps['PROVIDER_OR_BUDGET_FAILURE']+=1
                audit.append({'day':day,'status':'UNAVAILABLE','error_type':type(exc).__name__,
                              'http_status':getattr(exc,'status',None)})
                if getattr(exc,'status',None) in {401,403,429} or str(exc)=='REQUEST_BUDGET':
                    gaps['UNREVIEWED_SESSIONS']+=len(days)-days.index(day)-1;break
        write_json(out/f'{year}-intraday-signals.json',events)
        write_json(out/f'{year}-hybrid-signals.json',hybrid)
        write_json(out/f'{year}-intraday-audit.json',{'sessions':audit,'gaps':dict(gaps)})
        confirmed,confirmation_audit=confirmed_hybrid_events(packet,hybrid)
        write_json(out/f'{year}-confirmed-hybrid-signals.json',confirmed)
        write_json(out/f'{year}-confirmation-audit.json',confirmation_audit)
        policies=[(STRATEGY,events,'baseline'),(HYBRID,hybrid,'baseline'),(HYBRID,confirmed,'confirmed')]
        for strategy,event_set,policy,bps,borrow,label in [(st,es,p,b,bw,l) for st,es,p in policies for b,bw,l in [(30,.1,'base'),(100,1.,'stress')]]:
            result=simulate(packet['raw'],packet['split'],packet['cohorts'][f'{year}-09-08']['short'],packet['sessions'],
                            start=f'{year}-09-08',end=f'{year}-12-05',hold=3,strategy=strategy,
                            cost_bps=bps,borrow_rate=borrow,position_target=30000,buying_power=150000,
                            firm_dates=packet['firm_dates'],firm_cfg=cfg,risk_controls=True,signal_share_sizing=True,
                            intraday_signals=event_set,smg_cash_interest=True)
            suffix='-confirmed' if policy=='confirmed' else ''
            prefix=f'{year}-{strategy}{suffix}'
            write_json(out/(f'{prefix}.json' if label=='base' else f'{prefix}-stress.json'),result)
            if label=='base':write_json(out/f'{prefix}-lead.json',lead_metrics(result,packet['raw'],packet['split'],packet['sessions'],f'{year}-09-08',f'{year}-12-05'))
            summary.append({'year':year,'strategy':strategy,'entry_policy':policy,'cost_case':label,**{k:result[k] for k in ['net_profit','ending_balance','closed_trades','max_observed_drawdown_pct','signals','account_insolvent']},'data_gaps':dict(gaps),
                            'scan_complete':not any(gaps[k] for k in ['TIME_BUDGET','UNREVIEWED_SESSIONS','PROVIDER_OR_BUDGET_FAILURE'])})
        print(json.dumps(summary[-6:]),flush=True)
    write_json(out/'summary.json',{'strategies':[STRATEGY,HYBRID],'results':summary,'market_requests':client.requests,
               'live_enabled':False,'universe_uses_reference_inputs':False,
               'limitations':['All years have been inspected; confirmation was motivated by prior losses and needs fresh validation','Firm corpus is partial; prior-close price >$3 and nonnegative prior 21-session return restrict minute requests',
                              'Five-minute aggregates and uniform-time volume projection are research proxies',
                              'Historical borrow/cap/halts/SMG availability/fees/margin unknown','Market-data gaps are not zero-return outcomes; result is conditional on reviewed sessions']})


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--years',default='2023,2024,2025')
    p.add_argument('--out',default='reports/intraday-replay');p.add_argument('--max-requests',type=int,default=400)
    args=p.parse_args();packet=json.loads(gzip.decompress(Path(args.packet).read_bytes()))
    cfg,_=settings(Path.cwd())
    run(packet,cfg,Bars('backtest/runtime/intraday-bars',args.max_requests),[int(y) for y in args.years.split(',')],args.out)


if __name__=='__main__':main()
