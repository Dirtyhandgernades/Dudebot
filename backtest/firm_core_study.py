"""Evaluate primary firm networks, leaving broad associations on the watch list.

Network definition comes from the user's configured parties, never reference
tickers or profits. Thresholds and fits use earlier observations exclusively.
"""
import argparse
import gzip
import json
from pathlib import Path
from collections import Counter
from datetime import date,timedelta
import numpy as np
import yaml
from smg.rules import EntityList,normalize_name
from smg.action_learning import add_outcomes,fit_policy,policy_scores
from backtest.repair_study import independent_rows,portfolio,fixed_trade_cost_sensitivity


def network(row,entities):
    priorities={}
    for link in row['dated_firms']:
        role='underwriter' if link['role']=='placement_agent' else link['role']
        match=entities.get((role,normalize_name(link['name'])))
        if match:priorities[role]=min(priorities.get(role,99),match['priority'])
    return priorities.get('auditor',99)<=0 or (priorities.get('underwriter',99)<=1 and priorities.get('counsel',99)<=1)


def accelerating_upside(row,packet):
    days=packet['sessions'];i=days.index(row['signal_date']);series=packet['split'][row['ticker']]
    prior=[series[d] for d in days[i-3:i+1]]
    return all(prior[j]['c']>prior[j-1]['c'] for j in (1,2,3)) and row['x'][2]>.05 and row['x'][8]>=.75


def run(packet,rows,out):
    out.mkdir(parents=True,exist_ok=True);entries=EntityList(yaml.safe_load(Path('config/entities.yaml').read_text())).entries
    rows=add_outcomes(rows,packet['split'],packet['raw'])
    for row in rows:row['core_network']=network(row,entries);row['accelerating_upside']=accelerating_upside(row,packet)
    results=[]
    for year in (2023,2024,2025):
        cutoff=f'{year}-01-01';past=[r for r in rows if r['core_network'] and r['policy_net_return'] is not None and r['label_end']<cutoff and not r['held_issuer']]
        dates=sorted({r['signal_date'] for r in past});cal_start=max(str(date(year,1,1)-timedelta(days=180)),dates[int(.7*len(dates))]) if dates else cutoff
        training=independent_rows([r for r in past if r['label_end']<cal_start]);model=fit_policy(training)
        test=[r for r in rows if r['core_network'] and f'{year}-09-08'<=r['signal_date'] and r['label_end']<=f'{year}-12-05']
        if not model:results.append({'year':year,'status':'INSUFFICIENT_CORE_TRAINING','training_samples':len(training)});continue
        train_scores=policy_scores(model,training);values=policy_scores(model,test)
        threshold=float(np.quantile([v['dump_rank'] for v in train_scores],.5))
        return_threshold=max(.02,float(np.quantile([v['return_rank'] for v in train_scores],.5)))
        (out/f'{year}-core-model.json').write_text(json.dumps({'model':model,'dump_threshold':threshold,
            'return_threshold':return_threshold,'training_latest_label':max(r['label_end'] for r in training)},indent=2))
        for policy in ('CORE_DUMP_RANK','CORE_RETURN_RISK','CORE_NO_ACCELERATING_UPSIDE'):
            selected=[]
            for row,value in zip(test,values):
                if policy=='CORE_RETURN_RISK':
                    passed=value['return_rank']>=return_threshold and value['profitability_rank']>=.55 and value['tail_loss_rank']<=.25;rank=value['return_rank']
                else:
                    passed=value['dump_rank']>=threshold and (policy!='CORE_NO_ACCELERATING_UPSIDE' or not row['accelerating_upside']);rank=value['dump_rank']
                if passed:selected.append({**row,'score':rank})
            result={'year':year,'policy':policy,'training_samples':len(training),'signals':len(selected),'live_enabled':False}
            for case,bps,rate,strict in [('base',30,.1,False),('stress',100,1.,False),('strict',30,.1,True)]:
                p=portfolio(selected,packet['raw'],packet['split'],packet['sessions'],year,strict,bps,rate)
                if case=='base':base=p
                (out/f'{year}-{policy}-{case}.json').write_text(json.dumps(p,indent=2))
                result[case]={k:p[k] for k in ('net_profit','ending_balance','closed_trades','max_drawdown_pct')}
            result['same_trades_cost_stress']=fixed_trade_cost_sensitivity(base,packet['split'])
            held=independent_rows([r for r in selected if r['held_issuer'] and r['policy_net_return'] is not None])
            result['held_issuer_windows']=len(held);result['held_issuer_profitable']=sum(r['policy_profitable'] for r in held)
            results.append(result);print(json.dumps(result),flush=True)
    summary={'status':'PREDEFINED_CORE_NETWORK_RESEARCH','results':results,'core_observations':sum(r['core_network'] for r in rows),
        'all_observations':len(rows),'reference_used_for_selection':False,'live_enabled':False,'provider_requests':0,
        'network_definition':'Focus auditor OR high/additional underwriter plus listed counsel; historical association not fraud proof',
        'threshold_definition':'Median prior training scores within core network; return threshold at least 2%',
        'limitations':['Reused inspected years; prior-only fits do not make these fresh tests','Historical execution facts absent',
                       'Broader firms remain research watches; not every association is a trade']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));return summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packet',required=True);parser.add_argument('--observations',required=True)
    parser.add_argument('--out',default='outputs/backtest/firm-core-2026-10-06');args=parser.parse_args()
    run(json.loads(gzip.decompress(Path(args.packet).read_bytes())),json.loads(gzip.decompress(Path(args.observations).read_bytes())),Path(args.out))


if __name__=='__main__':main()
