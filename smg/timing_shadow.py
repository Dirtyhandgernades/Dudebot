"""Prospective paper comparison of timing filters; cannot change alerts/orders."""
import argparse,json,hashlib,os
from pathlib import Path
from datetime import datetime,timezone,timedelta,date
from .storage import Store,GitHubState
from .transport import Http
from .market import session_bounds
from .action_learning import policy_outcome
from backtest.firm_timing_study import keep,POLICIES


def capture(store,root,now):
    spec=json.loads((root/'config/ranked_firm_alerts.json').read_text(encoding='utf-8'))
    from .ranked_firm import valid_policy
    if not valid_policy(spec,root,now):return {'status':'BEFORE_FIRST_SESSION','captured':0}
    bounds=session_bounds(now.date())
    if not bounds or not bounds[1]-timedelta(minutes=20)<=now<bounds[1]:return {'status':'OUTSIDE_PRECLOSE','captured':0}
    inputs={p:hashlib.sha256((root/p).read_text(encoding='utf-8').encode()).hexdigest()
            for p in ('smg/timing_shadow.py','backtest/firm_timing_study.py','smg/action_learning.py','smg/market.py')}
    manifest={'parent_policy':spec['id'],'source_hashes':inputs,'policies':list(POLICIES),'live_enabled':False}
    signature=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    contract='timing-'+signature[:20]
    if not store.get('timing_shadow_contract:'+contract):
        store.put('timing_shadow_contract:'+contract,{'signature':signature,'manifest':manifest,'published_at':now.isoformat()})
    count=0
    for _,result in store.items('ranked_evaluation:'):
        if result['status']!='QUALIFIED' and 'ADAPTIVE_RANK_DEFERRED' not in result.get('reasons',[]):continue
        facts=result.get('ranking_evidence',{}).get('ranked_firm',{});event=facts.get('event',{})
        if facts.get('policy_id')!=spec['id']:continue
        try:
            observed=datetime.fromisoformat(event['decision_at']);cutoff=datetime.fromisoformat(event['data_cutoff'])
            if observed.tzinfo is None or cutoff.tzinfo is None or not 0<=(now-observed).total_seconds()<=300 or now-cutoff<timedelta(minutes=16):continue
        except (KeyError,ValueError,TypeError):continue
        c=result['candidate'];key='timing_shadow_decision:'+contract+':'+str(now.date())+':'+c['ticker']
        if store.get(key):continue
        store.put(key,{'contract_id':contract,'signature':signature,'ticker':c['ticker'],'cik':c['cik'],
                       'entry_date':str(now.date()),'captured_at':now.isoformat(),'event':event,
                       'keep':{p:keep(event,p) for p in POLICIES}});count+=1
    return {'status':'SHADOW_CAPTURED','captured':count,'contract_id':contract,'live_changed':False,'provider_requests':0}


def review(store,now):
    cache=store.get('ranked_daily_history',{});groups={};unknown=0
    for _,row in store.items('timing_shadow_decision:'):
        contract=store.get('timing_shadow_contract:'+row['contract_id'],{})
        try:
            root=Path.cwd()
            if any(hashlib.sha256((root/p).read_text(encoding='utf-8').encode()).hexdigest()!=h
                   for p,h in contract['manifest']['source_hashes'].items()):continue
            captured=datetime.fromisoformat(row['captured_at']);published=datetime.fromisoformat(contract['published_at'])
            bounds=session_bounds(date.fromisoformat(row['entry_date']))
            if not bounds or captured.tzinfo is None or captured<published or captured>now or not bounds[1]-timedelta(minutes=20)<=captured<bounds[1] or row['signature']!=contract['signature']:continue
            if row['keep']!={p:keep(row['event'],p) for p in POLICIES}:continue
            key='timing_shadow_outcome:'+row['contract_id']+':'+row['entry_date']+':'+row['ticker']
            labels=store.get(key)
            if not labels:
                labels=policy_outcome(row,cache.get('split',{}),cache.get('raw',{}))
                if labels['policy_net_return'] is None:unknown+=1;continue
                if session_bounds(date.fromisoformat(labels['label_end']))[1]+timedelta(minutes=16)>now:unknown+=1;continue
                store.put(key,labels)
            groups.setdefault(row['contract_id'],[]).append({**row,**labels})
        except (KeyError,ValueError,TypeError):continue
    reports=[]
    for contract,rows in groups.items():
        ends={};independent=[]
        for row in sorted(rows,key=lambda r:(r['entry_date'],r['ticker'])):
            issuer=row.get('cik') or row['ticker']
            if row['entry_date']<=ends.get(issuer,''):continue
            independent.append(row);ends[issuer]=row['label_end']
        reports.append({'contract_id':contract,'matured_nonoverlapping':len(independent),
            'policies':{p:{'kept':sum(r['keep'][p] for r in independent),
                          'paired_paper_return_sum':sum(r['policy_net_return'] for r in independent if r['keep'][p]),
                          'improvement_over_baseline':-sum(r['policy_net_return'] for r in independent if not r['keep'][p])}
                        for p in POLICIES},'automatic_promotion':False})
    return {'asof':now.isoformat(),'status':'REVIEWED' if reports else 'COLLECTING_PROSPECTIVE_TIMING',
            'reports':reports,'unknown_outcomes':unknown,'provider_requests':0,'live_changed':False,
            'limitation':'Paper paired-return sums are not account profit. Reused historical filters failed the sparse2023 gates.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--review',action='store_true');a=p.parse_args();root=Path.cwd();path=root/'runtime/state.sqlite';now=datetime.now(timezone.utc);backend=None
    if os.environ.get('GITHUB_ACTIONS')=='true':
        backend=GitHubState(Http(),os.environ['GITHUB_REPOSITORY'],os.environ['GITHUB_TOKEN']);backend.restore(path)
    store=Store(path)
    try:
        now=datetime.now(timezone.utc)  # Capture time follows state restoration.
        result=review(store,now) if a.review else capture(store,root,now)
        # Share the loaded state and one checkpoint with entry research.
        # No extra market requests or state restore/save subprocess is needed.
        from .entry_shadow import capture as entry_capture,review as entry_review
        entry=entry_review(store,root,now) if a.review else entry_capture(store,root,now)
        (root/'reports').mkdir(exist_ok=True)
        (root/'reports/entry-quality-shadow.json').write_text(json.dumps(entry,indent=2))
        result['entry_quality']=entry
        folder=root/'reports';folder.mkdir(exist_ok=True);(folder/'timing-shadow.json').write_text(json.dumps(result,indent=2))
        if backend:backend.checkpoint(store)
        print(json.dumps(result))
    finally:store.db.close()


if __name__=='__main__':main()
