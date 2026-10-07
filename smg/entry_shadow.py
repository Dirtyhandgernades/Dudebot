"""Frozen prospective entry-quality research, never alerts, orders or promotion."""
import argparse,json,hashlib,os,math
from pathlib import Path
from datetime import datetime,timezone,date,timedelta
from smg.storage import Store,GitHubState
from smg.transport import Http
from smg.market import session_bounds
from smg.entry_features import confirmed
from smg.action_learning import policy_outcome,policy_scores


def contract(root):
    path=root/'config/entry_quality_trial.json'
    if not path.exists():return None
    spec=json.loads(path.read_text(encoding='utf-8'))
    if spec.get('live_enabled') or spec.get('automatic_promotion'):raise ValueError('ENTRY_TRIAL_CANNOT_PROMOTE')
    for p,sha in spec['source_sha256'].items():
        source=(root/p).resolve()
        if not source.is_relative_to(root) or hashlib.sha256(source.read_text(encoding='utf-8').encode()).hexdigest()!=sha:raise ValueError('ENTRY_TRIAL_SOURCE_CHANGED')
    return spec


def capture(store,root,now):
    spec=contract(root)
    if not spec:return {'status':'NOT_STAGED','captured':0}
    bounds=session_bounds(now.date());published=datetime.fromisoformat(spec['published_at'])
    if not bounds or not bounds[1]-timedelta(minutes=20)<=now<bounds[1]:return {'status':'OUTSIDE_PRECLOSE','captured':0}
    if published>now:raise ValueError('ENTRY_TRIAL_NOT_YET_PUBLISHED')
    head=spec.get('return_head',{})
    if head.get('model') and (not head.get('training_latest_label') or head['training_latest_label']>=str(published.date())):
        raise ValueError('ENTRY_TRIAL_UNMATURED_TRAINING')
    digest=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest();key='entry_quality_contract:'+spec['id']
    prior=store.get(key)
    if prior and prior['sha256']!=digest:raise ValueError('ENTRY_TRIAL_CHANGED_WITHOUT_VERSION')
    if not prior:store.put(key,{'sha256':digest,'spec':spec,'registered_at':now.isoformat()})
    count=0
    for _,row in store.items('ranked_evaluation:'):
        if row['status']!='QUALIFIED' and 'ADAPTIVE_RANK_DEFERRED' not in row.get('reasons',[]):continue
        facts=row.get('ranking_evidence',{});rank=facts.get('ranked_firm',{});trial=facts.get('entry_research',{});event=rank.get('event',{})
        if rank.get('policy_id')!=spec['parent_policy']:continue
        try:
            at=datetime.fromisoformat(event['decision_at']);cutoff=datetime.fromisoformat(event['data_cutoff']);x=trial['x']
            if at.tzinfo is None or cutoff.tzinfo is None or not published<=at<=now or (now-at).total_seconds()>300 or at-cutoff<timedelta(minutes=16):continue
            if at.date()!=now.date() or len(x)!=14 or not all(math.isfinite(v) for v in x) or any(abs(a-b)>1e-10 for a,b in zip(x[:7],rank['features'])):continue
            days=rank['feature_dates']
            if len(days)!=22 or days!=sorted(set(days)) or days[-1]>=str(at.date()):continue
        except (KeyError,TypeError,ValueError):continue
        model=spec.get('return_head',{});score=policy_scores(model['model'],[{'x':x}])[0] if model.get('model') else None
        keep={'BASELINE':True,'CHART_CONFIRMED':confirmed(event.get('observed_chart')),
              'FOCUS_CONTEXT':any(v>0 for v in x[11:14]),
              'RETURN_AND_TAIL':bool(score and score['return_rank']>=model['return_threshold'] and score['profitability_rank']>=.5 and score['tail_loss_rank']<=.25)}
        candidate=row['candidate'];key='entry_quality_decision:'+spec['id']+':'+str(now.date())+':'+candidate['ticker']
        if store.get(key):continue
        store.put(key,{'contract_id':spec['id'],'contract_sha256':digest,'ticker':candidate['ticker'],'cik':candidate.get('cik'),
            'entry_date':str(now.date()),'observed_at':at.isoformat(),'captured_at':now.isoformat(),'x':x,'event':event,
            'news_rows':trial.get('news_rows',[]),'keep':keep,'scores':score,'paper_only':True});count+=1
    return {'status':'CAPTURED','captured':count,'contract_id':spec['id'],'live_changed':False}


def review(store,root,now):
    spec=contract(root)
    if not spec:return {'status':'NOT_STAGED'}
    registered=store.get('entry_quality_contract:'+spec['id']);known=[];unknown=0
    cache=store.get('ranked_daily_history',{})
    for _,row in store.items('entry_quality_decision:'+spec['id']+':'):
        if not registered or row['contract_sha256']!=registered['sha256']:raise ValueError('ENTRY_TRIAL_UNKNOWN_CONTRACT')
        key='entry_quality_outcome:'+spec['id']+':'+row['entry_date']+':'+row['ticker'];labels=store.get(key)
        if not labels:
            labels=policy_outcome(row,cache.get('split',{}),cache.get('raw',{}))
            if labels['policy_net_return'] is None:unknown+=1;continue
            end=session_bounds(date.fromisoformat(labels['label_end']))[1]
            if end+timedelta(minutes=16)>now:unknown+=1;continue
            stress=policy_outcome(row,cache.get('split',{}),cache.get('raw',{}),cost_bps=100,borrow_rate=1.)
            labels={**labels,'stress_net_return':stress['policy_net_return']};store.put(key,labels)
        known.append({**row,**labels})
    ends={};rows=[]
    for r in sorted(known,key=lambda v:(v['entry_date'],v['ticker'])):
        issuer=r.get('cik') or r['ticker']
        if r['entry_date']<=ends.get(issuer,''):continue
        ends[issuer]=r['label_end'];rows.append(r)
    gates={}
    for p in ('CHART_CONFIRMED','FOCUS_CONTEXT','RETURN_AND_TAIL'):
        kept=[r for r in rows if r['keep'][p]];rejected=[r for r in rows if not r['keep'][p]]
        halves=(rows[:len(rows)//2],rows[len(rows)//2:])
        paired=lambda part,field:-sum(r[field] for r in part if not r['keep'][p])
        ready=len(rows)>=50 and len(ends)>=10 and len({r['entry_date'] for r in rows})>=20 and len(kept)>=20 and len(rejected)>=10
        improved=ready and all(sum(r[field] for r in kept)>0 and paired(rows,field)>0 and
            all(paired(part,field)>0 for part in halves) for field in ('policy_net_return','stress_net_return'))
        gates[p]={'fresh_passed':bool(improved),'historical_passed':spec.get('historical_gates',{}).get(p,{}).get('passed_historical',False),
                  'enough_fresh_evidence':bool(ready),'automatic_promotion':False}
    return {'status':'COLLECTING_PROSPECTIVE_OUTCOMES' if not rows else 'REVIEWED','matured_nonoverlapping':len(rows),
        'unknown_outcomes':unknown,'issuers':len(ends),'sessions':len({r['entry_date'] for r in rows}),
        'policies':{p:{'kept':sum(r['keep'][p] for r in rows),
            'paired_base_return_improvement':-sum(r['policy_net_return'] for r in rows if not r['keep'][p]),
            'paired_stress_return_improvement':-sum(r['stress_net_return'] for r in rows if not r['keep'][p])} for p in ('CHART_CONFIRMED','FOCUS_CONTEXT','RETURN_AND_TAIL')},
        'fresh_validation':gates,'automatic_promotion':False,'live_changed':False,'limits':['Paired fixed-notional paper returns are not account profit','Historical gate failures remain failures; prospective research cannot silently promote']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--review',action='store_true');a=p.parse_args();root=Path.cwd();path=root/'runtime/state.sqlite';now=datetime.now(timezone.utc);backend=None
    if os.environ.get('GITHUB_ACTIONS')=='true':
        backend=GitHubState(Http(),os.environ['GITHUB_REPOSITORY'],os.environ['GITHUB_TOKEN']);backend.restore(path)
    store=Store(path)
    try:
        result=review(store,root,now) if a.review else capture(store,root,now)
        folder=root/'reports';folder.mkdir(exist_ok=True);(folder/'entry-quality-shadow.json').write_text(json.dumps(result,indent=2))
        if backend:backend.checkpoint(store)
        print(json.dumps(result))
    finally:store.db.close()


if __name__=='__main__':main()
