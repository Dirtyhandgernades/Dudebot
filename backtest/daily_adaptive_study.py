"""Daily cached, past-only annual comparisons of one preregistered filter.

The timestamped corpus is already restricted by the incumbent historical rank.
It can evaluate an EXTRA filter, not a broader replacement universe/model.
"""
import gzip
import json
import hashlib
from pathlib import Path
import numpy as np
from smg.action_learning import add_outcomes
from smg.risk_model import samples,fit,predict,feature_row,matured_before
from smg.swing_backtest import simulate
from smg.history_identity import repair_legacy_volume
from backtest.repair_study import fixed_trade_cost_sensitivity


def gate(results):
    failures=[]
    if {r['year'] for r in results}!={2023,2024,2025}:failures.append('THREE_SEASONS_REQUIRED')
    improvement=0
    for r in results:
        for case in ('base','stress','same_trade_stress'):
            base=r['incumbent'][case];new=r['challenger'][case]
            if new.get('net_profit') is None or new['net_profit']<=0:failures.append(f"{r['year']}_{case}_NOT_PROFITABLE")
            if new.get('max_observed_drawdown_pct',0)>25:failures.append(f"{r['year']}_{case}_DRAWDOWN_ABOVE_25")
            if new.get('net_profit') is None or base.get('net_profit') is None or new['net_profit']<base['net_profit']*.90:
                failures.append(f"{r['year']}_{case}_REGRESSES_MORE_THAN_10_PERCENT")
        if r['challenger']['base']['closed_trades']<2:failures.append(f"{r['year']}_SPARSE_TRADES")
        improvement+=r['challenger']['stress']['net_profit'] or 0
        improvement-=r['incumbent']['stress']['net_profit'] or 0
    if improvement<500:failures.append('AGGREGATE_STRESSED_IMPROVEMENT_BELOW_500')
    return {'passed':not failures,'failures':failures,'aggregate_stressed_profit_improvement':improvement,
            'fresh_prospective_validation_also_required':True}


def compare(packet,rows,signals_folder,out,penalty):
    index={d:i for i,d in enumerate(packet['sessions'])};results=[];out.mkdir(parents=True,exist_ok=True)
    for year in (2023,2024,2025):
        train=[{**r,'label':r['policy_profitable']} for r in matured_before(rows,f'{year}-01-01') if r['policy_net_return'] is not None]
        model=fit(train,l2=penalty)
        if model is None:continue
        threshold=float(np.quantile(predict(model,train),.5))
        base_events=json.loads((signals_folder/f'{year}-PRECLOSE_ONLY-signals.json').read_text())
        filtered={};gaps=0
        for day,events in base_events.items():
            prior=packet['sessions'][index[day]-22:index[day]];filtered[day]=[]
            for e in events:
                history=[packet['split'].get(e['ticker'],{}).get(d) for d in prior]
                x=feature_row(history) if len(history)==22 and all(history) else None
                if x is None:gaps+=1;continue
                if predict(model,[{'x':x}])[0]>=threshold:filtered[day].append(e)
        row={'year':year,'training_latest_label':max(r['label_end'] for r in train),'training_samples':len(train),
             'threshold_from_training_only':threshold,'feature_gaps':gaps,'incumbent':{},'challenger':{}}
        for name,events in [('incumbent',base_events),('challenger',filtered)]:
            symbols=sorted({e['ticker'] for es in events.values() for e in es})
            for case,bps,rate in [('base',30,.1),('stress',100,1.)]:
                portfolio=simulate(packet['raw'],packet['split'],symbols,packet['sessions'],start=f'{year}-09-08',end=f'{year}-12-05',
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',hold=3,firm_dates=packet['first_dates'],
                    intraday_signals=events,signal_share_sizing=True,risk_controls=True,position_target=50000,
                    buying_power=150000,max_position_equity_fraction=.30,decision_price_buffer=1.2,
                    smg_cash_interest=True,cost_bps=bps,borrow_rate=rate)
                (out/f'{year}-{name}-{case}.json').write_text(json.dumps(portfolio,indent=2))
                row[name][case]={k:portfolio[k] for k in ('net_profit','ending_balance','closed_trades','max_observed_drawdown_pct')}
                if case=='base':base=portfolio
            row[name]['same_trade_stress']=fixed_trade_cost_sensitivity({**base,'open_positions':base.get('unresolved_positions',{})},packet['split'])
        results.append(row)
    report={'status':'DAILY_THREE_YEAR_FILTER_REPLAY','l2':penalty,'years':[2023,2024,2025],'results':results,
            'provider_requests':0,'promotion_gate':gate(results),
            'limits':['Repeatedly inspected seasons are reused diagnostics, not untouched holdouts',
                      'Timestamped setup corpus is restricted by historical incumbent rank; only an additional filter is evaluated',
                      'Historical borrow, cap, halts and SMG membership are not imputed; returns are conditional',
                      'Training thresholds are selected before each season; no reference/friend tickers select entries']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));return report


def run(packet_path,signals_folder,out):
    from smg.adaptive_firm import PENALTIES
    packet=repair_legacy_volume(json.loads(gzip.decompress(packet_path.read_bytes())))
    rows=add_outcomes(samples(packet['records'],packet['raw'],packet['split'],packet['sessions'],firm_dates=packet['first_dates']),packet['split'],packet['raw'])
    variants=[compare(packet,rows,signals_folder,out/f'l2-{p}',p) for p in PENALTIES]
    passed=[r for r in variants if r['promotion_gate']['passed']]
    chosen=max(passed or variants,key=lambda r:r['promotion_gate']['aggregate_stressed_profit_improvement'])
    report={'status':'DAILY_CACHED_THREE_YEAR_REPLAY','selected_l2':chosen['l2'],
            'promotion_gate':chosen['promotion_gate'],'results':chosen['results'],'variants':variants,
            'provider_requests':0,'years':[2023,2024,2025],
            'packet_sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),
            'signals_sha256':hashlib.sha256(''.join((signals_folder/f'{y}-PRECLOSE_ONLY-signals.json').read_text(encoding='utf-8') for y in (2023,2024,2025)).encode()).hexdigest(),
            'limits':chosen['limits']+['Three fixed regularization recipes disclosed; fresh prospective decisions still required']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));return report,rows
