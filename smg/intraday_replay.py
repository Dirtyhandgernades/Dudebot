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


def run(packet,cfg,client,years,out,max_seconds=600):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);summary=[]
    started=time.monotonic()
    for year in years:
        events={};audit=[];gaps=Counter()
        days=[d for d in packet['sessions'] if f'{year}-09-08'<=d<f'{year}-12-05']
        for day in days:
            if time.monotonic()-started>max_seconds:
                gaps['TIME_BUDGET']+=len(days)-days.index(day);break
            names=candidates(packet,day);opened,closed,decision,cutoff=decision_window(day)
            try:
                adjusted=client.get(names,opened,cutoff,'split')
                preliminary={}
                for ticker in names:
                    partial=partial_bar(adjusted.get(ticker,[]),opened,cutoff)
                    if not partial:gaps['MISSING_OR_STALE_SPLIT_WINDOW']+=1;continue
                    # Fetch raw quotes only after a chart match. There is no
                    # guessed raw price or trade event at this stage.
                    history,_,_=projected_history(packet,ticker,day,partial)
                    if firm_exhaustion_trigger(history,cfg):preliminary[ticker]=partial
                raw=client.get(list(preliminary),opened,cutoff,'raw')
                selected=[]
                for ticker,partial in preliminary.items():
                    raw_partial=partial_bar(raw.get(ticker,[]),opened,cutoff)
                    if not raw_partial:gaps['MISSING_OR_STALE_RAW_WINDOW']+=1;continue
                    event=signal_event(packet,ticker,day,partial,raw_partial,cfg)
                    if event:selected.append(event)
                events[day]=selected
                audit.append({'day':day,'candidates':len(names),'chart_matches':len(preliminary),
                              'signals':len(selected),'decision_at':decision.isoformat(),'data_cutoff':cutoff.isoformat()})
            except (ProviderError,RuntimeError) as exc:
                gaps['PROVIDER_OR_BUDGET_FAILURE']+=1
                audit.append({'day':day,'status':'UNAVAILABLE','error_type':type(exc).__name__,
                              'http_status':getattr(exc,'status',None)})
                if getattr(exc,'status',None) in {401,403,429} or str(exc)=='REQUEST_BUDGET':
                    gaps['UNREVIEWED_SESSIONS']+=len(days)-days.index(day)-1;break
        write_json(out/f'{year}-intraday-signals.json',events)
        write_json(out/f'{year}-intraday-audit.json',{'sessions':audit,'gaps':dict(gaps)})
        for bps,borrow,label in [(30,.1,'base'),(100,1.,'stress')]:
            result=simulate(packet['raw'],packet['split'],packet['cohorts'][f'{year}-09-08']['short'],packet['sessions'],
                            start=f'{year}-09-08',end=f'{year}-12-05',hold=3,strategy=STRATEGY,
                            cost_bps=bps,borrow_rate=borrow,position_target=30000,buying_power=150000,
                            firm_dates=packet['firm_dates'],firm_cfg=cfg,risk_controls=True,signal_share_sizing=True,
                            intraday_signals=events)
            write_json(out/(f'{year}-{STRATEGY}.json' if label=='base' else f'{year}-{STRATEGY}-stress.json'),result)
            if label=='base':write_json(out/f'{year}-lead.json',lead_metrics(result,packet['raw'],packet['split'],packet['sessions'],f'{year}-09-08',f'{year}-12-05'))
            summary.append({'year':year,'cost_case':label,**{k:result[k] for k in ['net_profit','ending_balance','closed_trades','max_observed_drawdown_pct','signals','account_insolvent']},'data_gaps':dict(gaps),
                            'scan_complete':not any(gaps[k] for k in ['TIME_BUDGET','UNREVIEWED_SESSIONS','PROVIDER_OR_BUDGET_FAILURE'])})
        print(json.dumps(summary[-2:]),flush=True)
    write_json(out/'summary.json',{'strategy':STRATEGY,'results':summary,'market_requests':client.requests,
               'live_enabled':False,'universe_uses_reference_inputs':False,
               'limitations':['Previously inspected 2025 is not a fresh holdout','Firm corpus is partial; prior-close price >$3 and nonnegative prior 21-session return restrict minute requests',
                              'Five-minute aggregates and uniform-time volume projection are research proxies',
                              'Historical borrow/cap/halts/SMG availability/fees/margin unknown','Market-data gaps are not zero-return outcomes; result is conditional on reviewed sessions']})


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--years',default='2023,2024,2025')
    p.add_argument('--out',default='reports/intraday-replay');p.add_argument('--max-requests',type=int,default=400)
    args=p.parse_args();packet=json.loads(gzip.decompress(Path(args.packet).read_bytes()))
    cfg,_=settings(Path.cwd())
    run(packet,cfg,Bars('backtest/runtime/intraday-bars',args.max_requests),[int(y) for y in args.years.split(',')],args.out)


if __name__=='__main__':main()
