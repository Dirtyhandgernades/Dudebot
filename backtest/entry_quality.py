"""Prior-only entry tests; audit labels never select firms, data or candidates."""
import argparse,gzip,json,hashlib
from collections import defaultdict,Counter
from datetime import datetime,date,timezone
from pathlib import Path
import numpy as np
import yaml
from smg.entry_features import features,context,confirmed,before_news,FEATURES
from smg.action_learning import policy_outcome,fit_policy,policy_scores
from smg.risk_model import samples,matured_before
from smg.market import session_bounds
from smg.rules import EntityList
from smg.game_rules import is_excluded_symbol
from smg.game_firm_replay import research_entries
from smg.exposure import POLICY
from smg.swing_backtest import simulate
from backtest.repair_study import held_issuer,independent_rows

POLICIES=('BASELINE','CHART_CONFIRMED','FOCUS_CONTEXT','RETURN_AND_TAIL')


def prepare(packet,entities):
    by=defaultdict(list)
    for r in packet['records']:by[r['ticker']].append(r)
    index={d:i for i,d in enumerate(packet['sessions'])};rows=[]
    for r in samples(packet['records'],packet['raw'],packet['split'],packet['sessions'],firm_dates=packet['first_dates']):
        t=r['ticker'];day=r['signal_date']
        if is_excluded_symbol(t) or (len(t)==5 and t.isalpha()):continue
        at=session_bounds(date.fromisoformat(day))[1];i=index[day]
        history=[packet['split'][t][d] for d in packet['sessions'][i-21:i+1]]
        x=features(history,by[t],packet.get('news',{}).get(t,[]),at,entities)
        known=[v for v in by[t] if datetime.fromisoformat(v['decision_at'].replace('Z','+00:00'))<=at]
        ciks={str(int(v['cik'])) for v in known if v.get('cik')};cik=next(iter(ciks)) if len(ciks)==1 else None
        outcome=policy_outcome(r,packet['split'],packet['raw'])
        if x is not None and outcome['policy_net_return'] is not None:
            # Sparse/mixed-provider headlines remain audit-only, not learned
            # negatives. The first14 features are prices and dated firm tiers.
            rows.append({**r,**outcome,'x':x[:14],'issuer_cik':cik,'held_issuer':held_issuer(t,cik)})
    return by,index,rows


def model_before(rows,cutoff,start):
    train=independent_rows([r for r in matured_before(rows,cutoff,start) if not r['held_issuer']])
    model=fit_policy(train)
    threshold=max(.02,float(np.median([v['return_rank'] for v in policy_scores(model,train)]))) if model else None
    return model,threshold,train


def run(packet,folder,out,corpus):
    out.mkdir(parents=True,exist_ok=True)
    entities=EntityList(research_entries(yaml.safe_load(Path('config/entities.yaml').read_text(encoding='utf-8')))).entries
    by,index,rows=prepare(packet,entities);results=[];audit=[]
    for year in (2023,2024,2025):
        model,threshold,train=model_before(rows,f'{year}-01-01',f'{year-2}-01-01')
        events=json.loads((folder/f'{year}-PRECLOSE_ONLY-signals.json').read_text())
        selections={p:defaultdict(list) for p in POLICIES};counts=Counter()
        for day,items in events.items():
            for event in items:
                t=event['ticker'];at=datetime.fromisoformat(event['decision_at']);i=index[day]
                history=[packet['split'][t][d] for d in packet['sessions'][i-22:i]]
                x=features(history,by[t],packet.get('news',{}).get(t,[]),at,entities)
                priorities,links=context(by[t],at,entities);news=before_news(packet.get('news',{}).get(t,[]),at)
                score=policy_scores(model,[{'x':x[:14]}])[0] if model and x is not None else None
                keep={'BASELINE':True,'CHART_CONFIRMED':confirmed(event.get('observed_chart')),
                      'FOCUS_CONTEXT':any(v<=1 for v in priorities.values()),
                      'RETURN_AND_TAIL':bool(score and score['return_rank']>=threshold and
                          score['profitability_rank']>=.5 and score['tail_loss_rank']<=.25)}
                label=policy_outcome({'ticker':t,'entry_date':day},packet['split'],packet['raw'])
                audit.append({'corpus':corpus,'year':year,'ticker':t,'decision_at':at.isoformat(),
                    'data_cutoff':event['data_cutoff'],'quote':event['decision_price'],
                    'chart':event.get('observed_chart'),'source_policy':event.get('source_policy'),
                    'dated_firms':links,'dated_news':news,'news_status':'ARCHIVED_RECENT_ITEMS' if news else 'NO_ARCHIVED_RECENT_ITEMS_NOT_PROOF_OF_ABSENCE',
                    'research_scores':score,'keep':keep,'outcome':label})
                counts['with_archived_news' if news else 'without_archived_news']+=1
                if event.get('observed_chart') is None:counts['missing_observed_chart']+=1
                for p,accepted in keep.items():
                    if accepted:selections[p][day].append(event)
        for p in POLICIES:
            chosen=selections[p];symbols=sorted({e['ticker'] for es in chosen.values() for e in es})
            row={'corpus':corpus,'year':year,'policy':p,'training_rows':len(train),
                 'training_latest_label':max((r['label_end'] for r in train),default=None),
                 'return_threshold':threshold,'signal_count':sum(map(len,chosen.values())),
                 'news_coverage':dict(counts),'model_available':bool(model),'automatic_promotion':False}
            row['status']='CHART_DATA_UNAVAILABLE' if p=='CHART_CONFIRMED' and counts['missing_observed_chart'] else 'EVALUATED'
            for case,bps,rate in [('base',30,.1),('stress',100,1.)]:
                result=simulate(packet['raw'],packet['split'],symbols,packet['sessions'],
                    start=f'{year}-09-08',end=f'{year}-12-05',hold=3,
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',firm_dates=packet['first_dates'],
                    intraday_signals=chosen,signal_share_sizing=True,risk_controls=True,
                    position_target=50000,buying_power=150000,max_position_equity_fraction=.30,
                    decision_price_buffer=1.2,smg_cash_interest=True,cost_bps=bps,borrow_rate=rate,exposure_policy=POLICY)
                (out/f'{year}-{p}-{case}.json').write_text(json.dumps(result,indent=2))
                row[case]={k:result[k] for k in ('net_profit','closed_trades','max_observed_drawdown_pct','borrow_execution')}
            results.append(row)
        (out/f'{year}-return-model.json').write_text(json.dumps({'model':model,'threshold':threshold},indent=2))
    (out/'entry-audit.json').write_text(json.dumps(audit,indent=2))
    final,threshold,train=model_before(rows,'2026-01-01','2024-01-01')
    return results,{'model':final,'return_threshold':threshold,'features':FEATURES[:14],
        'training_samples':len(train),'training_latest_label':max((r['label_end'] for r in train),default=None)}


def gates(results):
    output={}
    for policy in POLICIES[1:]:
        checks=[];improvement=0;unknown=False
        for row in [r for r in results if r['policy']==policy]:
            base=next(r for r in results if r['corpus']==row['corpus'] and r['year']==row['year'] and r['policy']=='BASELINE')
            failures=[]
            if row.get('status')!='EVALUATED':failures.append(row['status'])
            for case in ('base','stress'):
                if row[case]['net_profit'] is None or row[case]['net_profit']<=0:failures.append(case+'_NOT_PROFITABLE')
                if row[case]['closed_trades']<2:failures.append(case+'_SPARSE_TRADES')
                if row[case]['max_observed_drawdown_pct']>25:failures.append(case+'_DRAWDOWN')
            if row['base']['net_profit'] is not None and base['base']['net_profit'] is not None and row['base']['net_profit']<.9*base['base']['net_profit']:failures.append('PROFIT_REGRESSION')
            if row['stress']['net_profit'] is None or base['stress']['net_profit'] is None:unknown=True
            else:improvement+=row['stress']['net_profit']-base['stress']['net_profit']
            checks.append({'corpus':row['corpus'],'year':row['year'],'failures':failures})
        output[policy]={'passed_historical':bool(checks) and not unknown and not any(c['failures'] for c in checks) and improvement>=500,
                        'checks':checks,'aggregate_stress_improvement':None if unknown else improvement,'fresh_gate_pending':True,'live_enabled':False}
    return output


def main():
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);p.add_argument('--expanded',required=True)
    p.add_argument('--original-signals',required=True);p.add_argument('--expanded-signals',required=True)
    p.add_argument('--out',default='reports/entry-quality');a=p.parse_args();out=Path(a.out);all_results=[];prospective={}
    for name,packet,folder in [('original',a.original,a.original_signals),('expanded',a.expanded,a.expanded_signals)]:
        results,model=run(json.loads(gzip.decompress(Path(packet).read_bytes())),Path(folder),out/name,name)
        all_results+=results;prospective[name]={'input_sha256':hashlib.sha256(Path(packet).read_bytes()).hexdigest(),**model}
    report={'status':'ENTRY_QUALITY_RESEARCH','results':all_results,'gates':gates(all_results),'prospective_models':prospective,
        'provider_requests':0,'live_changed':False,'limits':['Historical execution evidence remains unknown',
        'Repeatedly inspected corpora are comparative diagnostics, not untouched holdouts',
        'News is timestamped audit context; sparse/mixed-provider coverage is not a learned absence signal',
        'Return/profit/tail scores are research ranks, not calibrated confidence']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'gates':report['gates']}))


if __name__=='__main__':main()
