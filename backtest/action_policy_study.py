"""Past-only return/risk learning, compared with dump-probability ranking.

Fixed policies, unchanged independent discovery, no provider calls. Disclosure
of every tested policy prevents hiding bad years behind a selected 2025 result.
"""
import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from datetime import date,timedelta
from pathlib import Path
import numpy as np
from smg.action_learning import add_outcomes,fit_policy,policy_scores
from backtest.repair_study import independent_rows,portfolio,fixed_trade_cost_sensitivity

POLICIES=('DUMP_PROBABILITY_BASELINE','POLICY_RETURN','RETURN_PROFIT_AND_TAIL','RETURN_RISK_STOP_COOLDOWN')


def choose_rows(rows,values,threshold,policy):
    chosen=[]
    for row,value in zip(rows,values):
        if value['return_rank']<threshold:continue
        if policy in {'RETURN_PROFIT_AND_TAIL','RETURN_RISK_STOP_COOLDOWN'} and (
                value['profitability_rank']<.55 or value['tail_loss_rank']>.25):continue
        chosen.append({**row,'score':value['return_rank'],'prediction':value})
    return chosen


def run(packet,rows,out):
    out.mkdir(parents=True,exist_ok=True);rows=add_outcomes(rows,packet['split'],packet['raw']);results=[]
    diagnostic={'known_outcomes':sum(r['policy_net_return'] is not None for r in rows),
        'dump_hits_that_policy_loses':sum(r['policy_net_return'] is not None and r['policy_net_return']<=0 and r['dump_20pct_occurs'] for r in rows),
        'dump_hits':sum(r.get('dump_20pct_occurs',0) for r in rows),
        'missing_or_rejected_outcomes':dict(Counter(r['status'] for r in rows if r['policy_net_return'] is None))}
    for year in (2023,2024,2025):
        cutoff=f'{year}-01-01';cal_start=str(date(year,1,1)-timedelta(days=180))
        past_dates=sorted({r['signal_date'] for r in rows if r['policy_net_return'] is not None and r['label_end']<cutoff and not r['held_issuer']})
        if past_dates:cal_start=max(cal_start,past_dates[int(.70*len(past_dates))])
        training=independent_rows([r for r in rows if r['policy_net_return'] is not None and r['label_end']<cal_start and not r['held_issuer']])
        test=[r for r in rows if f'{year}-09-08'<=r['signal_date'] and r['label_end']<=f'{year}-12-05']
        policy_model=fit_policy(training)
        if not policy_model:
            results.append({'year':year,'status':'PRIOR_TRAINING_INSUFFICIENT'});continue
        train_values=policy_scores(policy_model,training);values=policy_scores(policy_model,test)
        # Thresholds depend only on old training observations; no optimizing
        # to the evaluation-year profit, tickers, or reference event dates.
        utility_threshold=max(.02,float(np.quantile([v['return_rank'] for v in train_values],.90)))
        baseline_threshold=float(np.quantile([v['dump_rank'] for v in train_values],.90));baseline_values=[v['dump_rank'] for v in values]
        (out/f'{year}-models.json').write_text(json.dumps({'policy_model':policy_model,
            'utility_threshold':utility_threshold,'dump_threshold':baseline_threshold,
            'training_latest_label':max(r['label_end'] for r in training)},indent=2))
        for policy in POLICIES:
            if policy=='DUMP_PROBABILITY_BASELINE':
                selected=[{**r,'score':s} for r,s in zip(test,baseline_values) if s>=baseline_threshold]
            else:selected=choose_rows(test,values,utility_threshold,policy)
            cooldown=3 if policy=='RETURN_RISK_STOP_COOLDOWN' else 0
            result={'year':year,'policy':policy,'training_samples':len(training),'signals':len(selected),
                'training_latest_label':max(r['label_end'] for r in training),
                'execution_counts':dict(Counter(r['execution'] for r in selected)),
                'known_selected_outcomes':sum(r['policy_net_return'] is not None for r in selected),
                'policy_profitable_selected':sum((r.get('policy_profitable') or 0) for r in selected),
                'tail_losses_selected':sum((r.get('tail_loss') or 0) for r in selected),
                'misleading_dump_hits_selected':sum(r['policy_net_return'] is not None and r['policy_net_return']<=0 and r.get('dump_20pct_occurs',0) for r in selected),
                'live_enabled':False}
            for case,bps,rate,strict in [('base',30,.1,False),('stress',100,1.,False),('strict',30,.1,True)]:
                p=portfolio(selected,packet['raw'],packet['split'],packet['sessions'],year,
                            strict,bps,rate,stop_cooldown_sessions=cooldown)
                if case=='base':base=p
                (out/f'{year}-{policy}-{case}.json').write_text(json.dumps(p,indent=2))
                result[case]={k:p[k] for k in ('net_profit','ending_balance','closed_trades','max_drawdown_pct','gaps')}
                if p['trades']:
                    with (out/f'{year}-{policy}-{case}-trades.csv').open('w',newline='',encoding='utf-8') as f:
                        writer=csv.DictWriter(f,fieldnames=list(p['trades'][0]));writer.writeheader();writer.writerows(p['trades'])
            result['same_trades_cost_stress']=fixed_trade_cost_sensitivity(base,packet['split'])
            held=independent_rows([r for r in selected if r['held_issuer'] and r['policy_net_return'] is not None])
            result['held_issuer_policy_windows']={'windows':len(held),'profitable':sum(r['policy_profitable'] for r in held),
                'net_return_sum':sum(r['policy_net_return'] for r in held),'tail_losses':sum(r['tail_loss'] for r in held)}
            results.append(result)
            print(json.dumps({'year':year,'policy':policy,'signals':len(selected),'base':result['base'],
                              'same_trade_stress':result['same_trades_cost_stress']['net_profit']}),flush=True)
    gates=[]
    for policy in POLICIES:
        entries=[r for r in results if r.get('policy')==policy];failures=[]
        if len(entries)!=3:failures.append('THREE_YEAR_COVERAGE_MISSING')
        for r in entries:
            for key in ('base','stress','same_trades_cost_stress'):
                if r[key]['net_profit'] is None or r[key]['net_profit']<=0:failures.append(str(r['year'])+'_'+key.upper()+'_NOT_PROFITABLE')
            if r['held_issuer_policy_windows']['windows']<10:failures.append(str(r['year'])+'_HELD_ISSUER_SAMPLE_SMALL')
        gates.append({'policy':policy,'historical_gate':'PASS' if not failures else 'FAIL','failures':failures,
            'deployment_gate':'RESEARCH_ONLY_REQUIRES_PROSPECTIVE_AND_EXECUTION_EVIDENCE','live_enabled':False})
    summary={'status':'POLICY_OBJECTIVE_RESEARCH','diagnostic':diagnostic,'results':results,'gates':gates,
        'provider_requests':0,'frozen_forward_changed':False,'limitations':[
            'Reused dates; all tested variants disclosed, no fresh holdout claim',
            'The return head is a regularized estimate, not guaranteed dollar profit or certified confidence',
            'All base and stress profits conditional on absent historical execution evidence',
            'Outcome labels follow next-close entry and delayed stop/target mechanics']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    return summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packet',required=True);parser.add_argument('--observations',required=True)
    parser.add_argument('--out',default='outputs/backtest/action-policy-2026-10-06');args=parser.parse_args()
    packet=json.loads(gzip.decompress(Path(args.packet).read_bytes()));rows=json.loads(gzip.decompress(Path(args.observations).read_bytes()))
    run(packet,rows,Path(args.out))


if __name__=='__main__':main()
