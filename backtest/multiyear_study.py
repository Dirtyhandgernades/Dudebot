"""Frozen eight-season research, prior-only holding/size choices, no live writes."""
import argparse,csv,gzip,json,hashlib,math
from collections import defaultdict,Counter
from datetime import date,datetime,timedelta
from pathlib import Path
import numpy as np
import yaml
from smg.market import calendar,session_bounds
from smg.cli import settings
from smg.game_firm_replay import discover,research_entries
from smg.risk_model import matured_before
from smg.action_learning import fit_policy,policy_scores,policy_outcome
from smg.entry_features import features
from smg.rules import EntityList
from smg.exposure import POLICY
from smg.swing_backtest import download,simulate
from smg.history_identity import repair_legacy_volume
from backtest.balanced_packet import merge_records
from backtest.extend_training_inputs import align_early_history
from backtest.balanced_checkpoints import SymbolBars
from backtest.intraday_checkpoint_study import run as checkpoints
from backtest.entry_quality import prepare
from backtest.repair_study import independent_rows

YEARS=tuple(range(2018,2026))
ALLOCATIONS=('BOUNDED_EQUAL','BOUNDED_PRIOR_EDGE','AGGRESSIVE_PRIOR_EDGE')
AGGRESSIVE={**POLICY,'id':'research-aggressive-prior-edge-v1','max_position_fraction':.30,
            'max_gross_fraction':1.,'shock_loss_fraction':.08,'target_ceiling':50000}


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')


def full_sessions(first=2016,last=2025):
    return [str(d.date()) for year in range(first,last+1)
            for d in calendar(year).sessions_in_range(f'{year}-01-01',f'{year}-12-31')]


def collect(packet,out,budget):
    cfg,entries=settings(Path.cwd())
    records,source=discover(Path.cwd(),cfg,entries,max_documents=budget,max_seconds=300,
                            priority_period='earlier_years',start_year=2016,end_year=2025)
    added,earlier,conflicts=merge_records(packet,records);packet['sessions']=full_sessions()
    missing=[]
    for t,first in packet['first_dates'].items():
        warm=max('2016-01-04',str(date.fromisoformat(first)-timedelta(days=90)))
        if not packet['raw'].get(t) or min(packet['raw'][t])>warm:missing.append(t)
    cache=Path('backtest/runtime/multiyear-daily');cache.mkdir(parents=True,exist_ok=True)
    extra,requests=download(missing,'2016-01-04','2025-12-31',cache)
    alignment=align_early_history(packet,extra)
    report={'source_discovery':source,'added_records':len(added),'earlier_dates':earlier,
            'identity_conflicts':conflicts,'daily_requests':requests,'price_alignment':alignment,
            'source_year_counts':dict(sorted(Counter(r['decision_at'][:4] for r in packet['records']).items())),
            'universe_complete':False,'live_changed':False}
    write(out/'collection.json',report)
    with gzip.open(out/'inputs.json.gz','wt',encoding='utf-8') as stream:json.dump(packet,stream)
    print(json.dumps({'stage':'collection','requests':requests,'added_records':len(added),'source_years':report['source_year_counts']}),flush=True)
    return packet


def hold_outcome(row,packet,hold):
    if hold==3:return policy_outcome(row,packet['split'],packet['raw'])
    # Preserve the existing outcome availability and three-session label end.
    base=policy_outcome(row,packet['split'],packet['raw'])
    if base.get('policy_net_return') is None:return base
    entry=row['entry_date'];t=row['ticker'];days=[str(d.date()) for d in calendar(int(entry[:4])).sessions_in_range(entry,str(date.fromisoformat(entry)+timedelta(days=15)))][:4]
    series=packet['split'][t];price=series[entry]['c'];exit_day=days[hold];reason=f'{hold}_SESSION_LIMIT'
    for i in range(1,hold):
        r=1-series[days[i]]['c']/price
        if r<=-.12+1e-10 or r>=.20-1e-10:exit_day=days[i+1];reason='PRIOR_CLOSE_STOP_OR_TARGET';break
    ratio=series[exit_day]['c']/price;elapsed=(date.fromisoformat(exit_day)-date.fromisoformat(entry)).days
    net=1-ratio-.003*(1+ratio)-10/25000-.1*elapsed/365
    return {**base,'exit_date':exit_day,'exit_reason':reason,'policy_net_return':net,
            'policy_profitable':int(net>0),'tail_loss':int(net<=-.30)}


def training_heads(rows,packet,year):
    earlier=[r for r in matured_before(rows,f'{year}-01-01',f'{year-2}-01-01') if not r['held_issuer']]
    heads={};thresholds={};counts={}
    for hold in (1,2,3):
        train=independent_rows([{**r,**hold_outcome(r,packet,hold)} for r in earlier]);model=fit_policy(train)
        if model:
            values=[s['return_rank'] for s in policy_scores(model,train)]
            thresholds[hold]=[float(np.quantile(values,q)) for q in (.5,.8)]
        heads[hold]=model;counts[hold]=len(train)
    return heads,thresholds,counts


def allocation(score,bands):
    """Ranks are not probabilities; no test-year label participates."""
    if score is None:return None
    value=score['return_rank']
    if not all(math.isfinite(score[k]) for k in ('return_rank','profitability_rank','tail_loss_rank')):return None
    if value<=0 or score['profitability_rank']<.5 or score['tail_loss_rank']>.25:return None
    return 1. if value>=bands[1] else .6 if value>=bands[0] else .2


def timing_audit(result,packet):
    sessions=packet['sessions'];index={d:i for i,d in enumerate(sessions)};events={(e['planned_entry_date'],e['ticker']):e for e in result['signal_events']};rows=[]
    for trade in result['trades']:
        day=trade['entry_date'];ticker=trade['ticker'];i=index[day];future=sessions[i+1:i+4];series=packet['split'].get(ticker,{})
        event=events.get((day,ticker),{});known=len(future)==3 and all(d in series for d in future)
        first=next((d for d in future if series[d]['c']/series[day]['c']-1<=-.20+1e-10),None) if known else None
        rows.append({**trade,'decision_at':event.get('decision_at'),'data_cutoff':event.get('data_cutoff'),
            'holding_sessions':index[trade['exit_date']]-i,'first_20pct_lower_close':first,
            'holding_policy_overrun':index[trade['exit_date']]-i>3,
            'sessions_until_20pct_lower_close':index[first]-i if first else None,
            'drop_outcome_status':'OBSERVED' if known else 'UNKNOWN','drop_time_basis':'FOLLOWING_CLOSING_PRICES_NOT_INTRADAY_DUMP_TIME',
            'historical_borrow':'UNKNOWN','historical_cap_halt_game_membership':'UNKNOWN'})
    return rows


def consistency(results):
    checks={}
    for name in sorted({r['variant'] for r in results}):
        rows=[r for r in results if r['variant']==name];failures=[]
        for year in YEARS:
            r=next((v for v in rows if v['year']==year),None)
            if not r or r['status']!='EVALUATED':failures.append(f'{year}:DATA_OR_TRAINING_UNAVAILABLE');continue
            for case in ('base','stress'):
                p=r[case]
                if p['net_profit'] is None or p['net_profit']-p['interest_pnl']<=0:failures.append(f'{year}:{case}:NO_POSITIVE_TRADING_PROFIT')
                if p['closed_trades']<10:failures.append(f'{year}:{case}:SPARSE_TRADES')
                if p['max_observed_drawdown_pct']>25:failures.append(f'{year}:{case}:DRAWDOWN_OVER_25')
                if p['account_insolvent']:failures.append(f'{year}:{case}:INSOLVENT')
        checks[name]={'passed_all_years':not failures,'failures':failures,'live_promotion':False,
                      'season_target_achieved_all_years':len(rows)==len(YEARS) and all(isinstance(r.get('base',{}).get('net_profit'),(int,float)) and r['base']['net_profit']>=70000 for r in rows)}
    return checks


def replay(packet,folder,out):
    entities=EntityList(research_entries(yaml.safe_load(Path('config/entities.yaml').read_text(encoding='utf-8')))).entries
    by,index,rows=prepare(packet,entities);results=[];ledgers=[];coverage=[]
    for year in YEARS:
        path=folder/f'{year}-PRECLOSE_ONLY-signals.json';heads,bands,counts=training_heads(rows,packet,year)
        events=json.loads(path.read_text()) if path.exists() else None
        models={'models':heads,'prior_training_counts':counts,'prior_training_cutoff':f'{year}-01-01','prior_return_bands':bands,'scores_are_calibrated_probabilities':False}
        write(out/f'{year}-prior-models.json',models)
        variants=[(f'{a}_H{h}',a,h) for a in ALLOCATIONS for h in (1,2,3)]+[(f'{a}_ADAPTIVE_1_3',a,None) for a in ALLOCATIONS[1:]]
        for name,alloc,hold in variants:
            if events is None or (alloc!='BOUNDED_EQUAL' and not all(heads.values())):
                results.append({'year':year,'variant':name,'status':'DATA_OR_TRAINING_UNAVAILABLE','prior_training_counts':counts});continue
            chosen=defaultdict(list);holds={};scores=[]
            for day,group in events.items():
                for event in group:
                    t=event['ticker'];at=datetime.fromisoformat(event['decision_at']);j=index[day]
                    x=features([packet['split'][t][d] for d in packet['sessions'][j-22:j]],by[t],[],at,entities)
                    if alloc=='BOUNDED_EQUAL':selected=hold;scale=1.;score=None
                    else:
                        predicted={h:policy_scores(m,[{'x':x[:14]}])[0] for h,m in heads.items()} if x else {}
                        eligible={h:s for h,s in predicted.items() if allocation(s,bands[h]) is not None}
                        if hold is None:
                            if not eligible:continue
                            selected=max(eligible,key=lambda h:(eligible[h]['return_rank']-.25*eligible[h]['tail_loss_rank'],-h))
                        else:selected=hold
                        score=eligible.get(selected);scale=allocation(score,bands[selected])
                        if scale is None:continue
                    chosen[day].append({**event,'position_scale':scale});holds[day+':'+t]=selected
                    scores.append({'ticker':t,'decision_at':event['decision_at'],'hold_sessions':selected,'allocation_scale':scale,'prior_research_scores':score})
            symbols=sorted({e['ticker'] for es in chosen.values() for e in es})
            row={'year':year,'variant':name,'status':'EVALUATED','signal_count':len(scores),'live_enabled':False,'prior_training_counts':counts}
            exposure=AGGRESSIVE if alloc=='AGGRESSIVE_PRIOR_EDGE' else POLICY
            for case,bps,rate in [('base',30,.1),('stress',100,1.)]:
                p=simulate(packet['raw'],packet['split'],symbols,packet['sessions'],start=f'{year}-09-08',end=f'{year}-12-05',hold=hold or 3,
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',firm_dates=packet['first_dates'],intraday_signals=chosen,
                    signal_share_sizing=True,risk_controls=True,position_target=10000 if alloc=='BOUNDED_PRIOR_EDGE' else 50000,
                    buying_power=150000,max_position_equity_fraction=exposure['max_position_fraction'],decision_price_buffer=1.2,
                    smg_cash_interest=True,cost_bps=bps,borrow_rate=rate,exposure_policy=exposure,research_hold_by_entry=holds)
                write(out/f'{year}-{name}-{case}.json',p)
                row[case]={k:p[k] for k in ('net_profit','ending_balance','interest_pnl','closed_trades','max_observed_drawdown_pct','account_insolvent','borrow_execution','gaps')}
                ledgers.extend({**r,'year':year,'variant':name,'cost_case':case} for r in timing_audit(p,packet))
            write(out/f'{year}-{name}-decisions.json',scores);results.append(row)
            print(json.dumps({'year':year,'variant':name,'net':row['base']['net_profit'],'stress_net':row['stress']['net_profit'],'trades':row['base']['closed_trades']}),flush=True)
        eligible=[t for t,d in packet['first_dates'].items() if d<=f'{year}-12-05']
        coverage.append({'year':year,'dated_firm_symbols':len(eligible),'symbols_with_season_raw_prices':sum(any(f'{year}-09-08'<=d<=f'{year}-12-05' for d in packet['raw'].get(t,{})) for t in eligible),
                         'prior_training_counts':counts,'preclose_data_status':'AVAILABLE' if events is not None else 'UNKNOWN'})
    write(out/'trade-timing-and-sizing.json',ledgers)
    if ledgers:
        fields=['year','variant','cost_case','ticker','decision_at','data_cutoff','entry_date','exit_date','holding_sessions','shares','notional','pnl','first_20pct_lower_close','sessions_until_20pct_lower_close','drop_outcome_status']
        with (out/'trades.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(ledgers)
    report={'status':'EIGHT_SEASON_PRIOR_ONLY_RESEARCH','years':list(YEARS),'results':results,'consistency':consistency(results),'coverage':coverage,
            'live_changed':False,'automatic_promotion':False,'season_profit_target':70000,
            'limits':['Partial independently discovered universe, not full-market recall','Historical borrow/cap/halts/game membership remain unknown',
                      'Drop timestamps are closing-session intervals; actual intraday dump times unknown','Prior return/tail scores are not calibrated probabilities',
                      'Aggressive allocations are research-only; losses and closing overshoots are retained','Previously inspected years are not fresh holdouts; prospective validation still required']}
    write(out/'summary.json',report);return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--out',default='reports/multiyear');p.add_argument('--collect',action='store_true');p.add_argument('--max-documents',type=int,default=400);p.add_argument('--cached-signals');a=p.parse_args()
    if not 0<=a.max_documents<=1000:raise ValueError('Source budget must be within0–1000')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);packet=repair_legacy_volume(json.loads(gzip.decompress(Path(a.packet).read_bytes())))
    write(out/'experiment.json',{'years':list(YEARS),'allocations':list(ALLOCATIONS),'holds':[1,2,3,'PRIOR_ONLY_ADAPTIVE'],
        'training_years':2,'initial':100000,'buying_power_assumption':150000,'source_budget':a.max_documents,
        'base_input_sha256':hashlib.sha256(Path(a.packet).read_bytes()).hexdigest(),'automatic_promotion':False,'live_enabled':False})
    original=repair_legacy_volume(json.loads(gzip.decompress(Path(a.packet).read_bytes())))
    if a.collect:packet=collect(packet,out,a.max_documents)
    folder=Path(a.cached_signals) if a.cached_signals else out/'checkpoints'
    if not a.cached_signals:
        client=SymbolBars('backtest/runtime/multiyear-minutes',max_requests=500)
        client.provider.max_requests=0
        try:checkpoints(original,client,out/'legacy-cache-prime',train_window_years=2,policies=[])
        except RuntimeError as exc:
            if str(exc)!='REQUEST_BUDGET':raise
        client.provider.max_requests=500
        controls=[];reports=[]
        for offset in (20,15,10,5):
            directory=folder/str(offset)
            check=checkpoints(packet,client,directory,train_window_years=2,years=YEARS,policies=['PRECLOSE_ONLY'],preclose_offset_minutes=offset)
            write(out/f'checkpoint-coverage-{offset}.json',check)
            report=replay(packet,directory,out/f'portfolios-{offset}')
            reports.append(report)
            controls.extend({**r,'variant':r['variant']+f'_PRECLOSE_{offset}','preclose_offset_minutes':offset} for r in report['results'])
        write(out/'summary.json',{'status':'EIGHT_SEASON_TIMING_CONTROLS','results':controls,'consistency':consistency(controls),
              'source_and_price_requests':client.requests,'live_changed':False,'automatic_promotion':False,
              'limits':reports[0]['limits'],'timing_offsets_before_close':[20,15,10,5]})
    else:replay(packet,folder,out/'portfolios')


if __name__=='__main__':main()
