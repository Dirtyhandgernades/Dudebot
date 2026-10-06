"""Recheck observed pre-close firm setups against the enlarged training packet.

Original timestamped signal quotes are retained. No new historical intraday
setup is fabricated from a final daily candle. Every fixed variant is disclosed.
"""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from smg.risk_model import samples,fit,predict,feature_row,matured_before
from smg.swing_backtest import simulate
from smg.intraday_replay import scaled_hybrid_events
from backtest.repair_study import fixed_trade_cost_sensitivity


def run(packet,signals_folder,out):
    out.mkdir(parents=True,exist_ok=True)
    rows=samples(packet['records'],packet['raw'],packet['split'],packet['sessions'],firm_dates=packet['first_dates'])
    index={d:i for i,d in enumerate(packet['sessions'])};result=[]
    for year in (2023,2024,2025):
        train=matured_before(rows,f'{year}-01-01');model=fit(train)
        if not model:result.append({'year':year,'status':'TRAINING_UNAVAILABLE'});continue
        train_scores=predict(model,train);threshold=float(np.quantile(train_scores,.50))
        events=json.loads((signals_folder/f'{year}-hybrid-signals.json').read_text())
        selected={};gaps=0
        for day,candidates in events.items():
            selected[day]=[];i=index[day]
            for event in candidates:
                history=[packet['split'].get(event['ticker'],{}).get(d) for d in packet['sessions'][i-22:i]]
                x=feature_row(history) if all(history) else None
                if x is None:gaps+=1;continue
                score=predict(model,[{'x':x}])[0]
                if score>=threshold:selected[day].append({**event,'training_rank':score})
        scaled,_=scaled_hybrid_events(packet,selected)
        (out/f'{year}-model.json').write_text(json.dumps({'model':model,'threshold':threshold,'latest_training_label':max(r['label_end'] for r in train)},indent=2))
        for policy,events_for_policy,target,cap in [('TOP_HALF_30K',selected,30000,.25),
                ('TOP_HALF_50K',selected,50000,.30),('TOP_HALF_UPMOVE_HALF_SIZE',scaled,50000,.30)]:
            summary={'year':year,'policy':policy,'training_samples':len(train),'training_positive_outcomes':sum(r['label'] for r in train),
                'rank_threshold':threshold,'feature_gaps':gaps,'live_enabled':False}
            symbols=sorted({e['ticker'] for es in events_for_policy.values() for e in es})
            for case,bps,rate in [('base',30,.1),('stress',100,1.)]:
                p=simulate(packet['raw'],packet['split'],symbols,packet['sessions'],start=f'{year}-09-08',end=f'{year}-12-05',
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',hold=3,firm_dates=packet['first_dates'],
                    position_target=target,buying_power=150000,signal_share_sizing=True,risk_controls=True,
                    intraday_signals=events_for_policy,cost_bps=bps,borrow_rate=rate,smg_cash_interest=True,
                    max_position_equity_fraction=cap,decision_price_buffer=1.2)
                (out/f'{year}-{policy}-{case}.json').write_text(json.dumps(p,indent=2))
                if case=='base':base=p
                summary[case]={k:p[k] for k in ('net_profit','ending_balance','closed_trades','max_observed_drawdown_pct','gaps')}
            # Cost-only ledger excludes cash-interest changes and is therefore
            # a separate, disclosed sensitivity calculation.
            summary['same_trade_stress']=fixed_trade_cost_sensitivity({**base,'open_positions':base.get('unresolved_positions',{})},packet['split'])
            result.append(summary);print(json.dumps(summary),flush=True)
    report={'status':'TIMESTAMPED_PRECLOSE_RECHECK','results':result,'provider_requests':0,'live_enabled':False,
        'limitations':['Intraday setup archive is a partial cohort, not whole-market coverage',
                       'Historical intraday volume projection differs from live same-minute RVOL',
                       'Absent historical cap/halts/borrow/security membership remain conditional',
                       'All periods inspected previously; no guaranteed future profit']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packet',required=True);parser.add_argument('--signals',required=True)
    parser.add_argument('--out',default='outputs/backtest/preclose-recheck-2026-10-06');args=parser.parse_args()
    run(json.loads(gzip.decompress(Path(args.packet).read_bytes())),Path(args.signals),Path(args.out))


if __name__=='__main__':main()
