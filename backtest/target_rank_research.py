"""Expanding-window fast-dump ranking over cached independent firm inputs.

No forward outcome selects an event. All evaluated years have previously
been inspected, so this remains retrospective research, not a fresh holdout.
"""
import gzip
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

from smg.intraday_replay import confirmed_hybrid_events
from smg.models import Config
from smg.risk_model import samples,feature_row,fit,predict,metrics,matured_before
from smg.swing_backtest import simulate
from backtest.confirmation_comparison import drop_timing


def run():
    source=Path('outputs/backtest/hybrid-37386241124')
    out=Path('outputs/backtest/target-rank-2026-10-05');out.mkdir(parents=True,exist_ok=True)
    packet=json.loads(gzip.decompress((source/'firm-timing-inputs.json.gz').read_bytes()))
    records=json.loads((source/'discovery-decisions.json').read_text())
    rows=samples(records,packet['raw'],packet['split'],packet['sessions'],firm_dates=packet['firm_dates'])
    index={d:i for i,d in enumerate(packet['sessions'])};cfg=Config(**packet['config'])
    summaries=[]
    for year in (2023,2024,2025):
        cutoff=f'{year}-01-01'
        train=matured_before(rows,cutoff)
        model=fit(train)
        if model is None:
            summaries.append({'year':year,'status':'INSUFFICIENT_TRAINING_DATA'});continue
        train_scores=predict(model,train)
        thresholds={'top_half':float(np.quantile(train_scores,.50)),
                    'top_quartile':float(np.quantile(train_scores,.75)),
                    'top_decile':float(np.quantile(train_scores,.90))}
        events=json.loads((source/f'{year}-hybrid-signals.json').read_text())
        confirmed,_=confirmed_hybrid_events(packet,events)
        scores={};feature_gaps=0
        for day,es in events.items():
            i=index[day]
            for event in es:
                history=[packet['split'].get(event['ticker'],{}).get(d) for d in packet['sessions'][i-22:i]]
                x=feature_row(history) if len(history)==22 and all(history) else None
                if x is None:feature_gaps+=1;continue
                scores[(day,event['ticker'])]=predict(model,[{'x':x}])[0]
        (out/f'{year}-model.json').write_text(json.dumps({'training_last_label_date':max(r['label_end'] for r in train),
            'model':model,'training_rank_metrics':metrics(train,train_scores),
            'thresholds':thresholds},indent=2),encoding='utf-8')
        for policy in ('top_half','top_quartile','top_decile','confirmed_top_quartile','top_half_30pct'):
            threshold=thresholds['top_quartile' if policy.startswith('confirmed') else policy.removesuffix('_30pct')]
            pool=confirmed if policy.startswith('confirmed') else events
            selected={day:[{**e,'historical_rank':scores[(day,e['ticker'])]} for e in es
                if (day,e['ticker']) in scores and scores[(day,e['ticker'])]>=threshold] for day,es in pool.items()}
            caps=.30 if policy.endswith('_30pct') else .25
            targets=(50000,) if policy.endswith('_30pct') else (30000,50000)
            for target,case,bps,borrow in [(t,c,b,r) for t in targets
                    for c,b,r in (('base',30,.1),('stress',100,1.0))]:
                result=simulate(packet['raw'],packet['split'],packet['cohorts'][f'{year}-09-08']['short'],
                    packet['sessions'],start=f'{year}-09-08',end=f'{year}-12-05',hold=3,
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',cost_bps=bps,borrow_rate=borrow,
                    position_target=target,buying_power=150000,firm_dates=packet['firm_dates'],firm_cfg=cfg,
                    risk_controls=True,signal_share_sizing=True,intraday_signals=selected,smg_cash_interest=True,
                    max_position_equity_fraction=caps)
                (out/f'{year}-{policy}-{target}-{case}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                fields=['ticker','signal_date','entry_date','exit_date','exit_reason','shares','entry_price','notional','pnl','return_pct']
                with (out/f'{year}-{policy}-{target}-{case}-trades.csv').open('w',newline='',encoding='utf-8') as f:
                    writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(result['trades'])
                row={'year':year,'policy':policy,'position_target':target,'max_position_equity_fraction':caps,'cost_case':case,'rank_threshold':threshold,
                    'training_samples':len(train),'training_positives':sum(r['label'] for r in train),
                    'training_warning':'FEWER_THAN_TEN_POSITIVE_OUTCOMES' if sum(r['label'] for r in train)<10 else None,
                    'training_latest_label':max(r['label_end'] for r in train),'feature_gaps':feature_gaps,
                    **{k:result[k] for k in ('net_profit','ending_balance','signals','closed_trades','max_observed_drawdown_pct')},
                    'drop_timing':drop_timing(result,packet,f'{year}-12-05')}
                summaries.append(row)
                print(json.dumps({k:v for k,v in row.items() if k!='drop_timing'}),flush=True)
    (out/'summary.json').write_text(json.dumps({'status':'RETROSPECTIVE_RESEARCH_ONLY','results':summaries,
        'live_enabled':False,'threshold_selection':'Fixed training-score quantiles, not future profit or labels',
        'input_sha256':hashlib.sha256((source/'firm-timing-inputs.json.gz').read_bytes()).hexdigest(),
        'score_is_calibrated_probability':False,'limitations':[
            'Current intraday setups are ranked with preceding complete daily features, not future intraday features',
            'The training population and intraday setup population differ; scores need independent calibration',
            'All tested years previously inspected; overlapping daily outcomes are correlated',
            'Historical eligibility/borrow/halts/corporate-action and exact margin gaps remain']} ,indent=2),encoding='utf-8')


if __name__=='__main__':run()
