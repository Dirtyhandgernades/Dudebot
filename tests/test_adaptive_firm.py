import json
from datetime import datetime,timedelta,timezone,date
from copy import deepcopy
from smg.adaptive_firm import (digest,context,valid_model,make_candidate,apply_active,
                              observed_pairs,paired_gate,nightly,mature_outcome,RECIPE)
from smg.storage import Store
from smg.market import calendar,session_bounds
from smg.risk_model import FEATURES
from tests.test_ranked_firm import evaluate,NOW

UTC=timezone.utc


def spec():
    return {'implementation_sha256':{'fixture':'sha'},'model':{'fixture':'base'},
            'rank_threshold':.4,'entry_policy':'PRECLOSE_ONLY','automatic_improvement_enabled':True}


def candidate(policy=None,now=None):
    policy=policy or spec();now=now or datetime(2026,10,6,23,tzinfo=UTC)
    body={'recipe':RECIPE,'context':context(policy),'l2':.5,
          'model':{'features':list(FEATURES),'mean':[0]*7,'scale':[1]*7,'weights':[1]+[0]*6,'bias':0},
          'threshold':.5,'training_latest_label':str((now-timedelta(days=90)).date()),'training_samples':100}
    return {**body,'id':'adaptive-'+digest(body)[:20],'created_at':now.isoformat()}


def test_model_identity_covers_weights_and_preserves_promotion_metadata():
    s=spec();c=candidate(s);now=datetime(2026,10,7,23,tzinfo=UTC)
    assert valid_model(c,s,now)
    assert valid_model({**c,'promoted_at':now.isoformat()},s,now)
    bad=deepcopy(c);bad['model']['weights'][0]=20
    assert not valid_model(bad,s,now)
    changed=deepcopy(s);changed['implementation_sha256']['fixture']='new'
    assert not valid_model(c,changed,now)
    assert not valid_model(c,{**s,'automatic_improvement_enabled':False},now)


def test_training_does_not_learn_missing_or_unmatured_outcomes():
    rows=[{'x':[i/40]*7,'policy_net_return':.1 if i%2 else -.2,
           'policy_profitable':i%2,'label_end':'2025-12-05'} for i in range(40)]
    now=datetime(2026,10,6,23,tzinfo=UTC)
    first=make_candidate(rows,spec(),now)
    rows+=[{'x':[999]*7,'policy_net_return':10,'policy_profitable':1,'label_end':'2026-10-07'},
           {'policy_net_return':None,'label_end':'2025-12-01'}]
    assert make_candidate(rows,spec(),now)==first


def test_overlay_cannot_qualify_unknown_borrow_or_relax_exclusions(tmp_path):
    store=Store(tmp_path/'state');s=spec();c=candidate(s,NOW-timedelta(days=1));store.put('adaptive_active',c)
    r=evaluate(borrow=None)
    assert apply_active(store,r,s,NOW).status=='REVIEW_REQUIRED'
    assert not store.items('adaptive_base_decision:')
    r=evaluate();before=r.ranking_evidence['ranked_firm']['position_target']
    apply_active(store,r,s,NOW)
    assert len(store.items('adaptive_base_decision:'))==1
    assert r.ranking_evidence['ranked_firm']['position_target']==before


def test_unknown_and_partial_outcomes_cannot_be_saved_as_success(tmp_path):
    store=Store(tmp_path/'state');row={'ticker':'TEST','entry_date':'2026-10-07'};s=spec()
    assert mature_outcome(store,row,s,datetime(2026,10,8,23,tzinfo=UTC))['policy_net_return'] is None
    days=['2026-10-07','2026-10-08','2026-10-09','2026-10-12']
    prices={'TEST':{d:{'c':10-i} for i,d in enumerate(days)}}
    store.put('ranked_daily_history',{'split':prices,'raw':prices})
    assert mature_outcome(store,row,s,datetime(2026,10,12,18,tzinfo=UTC))['status']=='OUTCOME_NOT_MATURE'
    assert not store.items('adaptive_outcome:')
    observed=mature_outcome(store,row,s,datetime(2026,10,12,23,tzinfo=UTC))
    assert observed['policy_net_return']>0
    prices['TEST'][days[-1]]['c']=999;store.put('ranked_daily_history',{'split':prices,'raw':prices})
    assert mature_outcome(store,row,s,datetime(2026,10,13,23,tzinfo=UTC))==observed


def prospective(store,c,s,monkeypatch,good=True):
    days=[str(d.date()) for d in calendar(2026).sessions_in_range('2026-10-07','2026-11-30')][:25]
    for i in range(50):
        day=days[i//2];observed=session_bounds(date.fromisoformat(day))[1]-timedelta(minutes=20)
        keep=i%5!=0;x=[1 if keep else -1]+[0]*6
        from smg.risk_model import predict
        r={'model_id':c['id'],'context':c['context'],'ticker':'TEST'+str(i),'cik':str(i),
           'entry_date':day,'observed_at':observed.isoformat(),'data_cutoff':(observed-timedelta(minutes=16)).isoformat(),
           'base_eligible':True,'keep':keep,'score':predict(c['model'],[{'x':x}])[0],'x':x}
        store.put('adaptive_decision:'+c['id']+':'+day+':'+r['ticker'],r)
    def outcome(store,row,spec,now):
        label=str(calendar(2026).session_offset(row['entry_date'],3).date())
        net=.10 if row['keep'] else -.10 if good else .10
        return {'status':'POLICY_OUTCOME_OBSERVED','policy_net_return':net,'stress_policy_net_return':net*.8,
                'label_end':label,'policy_profitable':int(net>0)}
    monkeypatch.setattr('smg.adaptive_firm.mature_outcome',outcome)


def study(passed=True):
    return {'promotion_gate':{'passed':passed},'selected_l2':.5,
            'variants':[{'l2':.5,'promotion_gate':{'passed':passed}}]}


def test_automatic_promotion_requires_both_history_and_new_paired_outcomes(tmp_path,monkeypatch):
    store=Store(tmp_path/'state');s=spec();c=candidate(s);store.put('adaptive_staged',c)
    now=datetime(2026,12,1,23,tzinfo=UTC)
    empty=nightly(store,s,study(),[],now)
    assert empty['prospective']['passed'] is False and not store.get('adaptive_active')
    prospective(store,c,s,monkeypatch)
    blocked=nightly(store,s,study(False),[],now)
    assert blocked['prospective']['passed'] is True and not store.get('adaptive_active')
    promoted=nightly(store,s,study(),[],now)
    assert promoted['status']=='PROMOTED_ADDITIONAL_RANK_FILTER'
    assert valid_model(store.get('adaptive_active'),s,now) and not store.get('adaptive_staged')


def test_invalid_decision_flags_do_not_manufacture_promotion(tmp_path,monkeypatch):
    store=Store(tmp_path/'state');s=spec();c=candidate(s);prospective(store,c,s,monkeypatch)
    key,row=store.items('adaptive_decision:')[0];row['keep']=not row['keep'];store.put(key,row)
    rows,gaps=observed_pairs(store,c,s,datetime(2026,12,1,23,tzinfo=UTC))
    assert len(rows)==49 and gaps['INVALID_DECISION']==1
    assert paired_gate(rows)['passed'] is False


def test_daily_workflow_is_hosted_cached_and_contains_no_webhook():
    from pathlib import Path
    import yaml
    w=yaml.safe_load(Path('.github/workflows/daily-adaptive.yml').read_text())
    assert w['concurrency']['group']=='smg-state-writer-v2'
    assert w['concurrency']['queue']=='max'
    job=w['jobs']['learn'];assert 'DISCORD_WEBHOOK_URL' not in job['env']
    steps=job['steps'];assert any(s.get('uses')=='actions/cache/restore@v4' for s in steps)
    assert any('smg.adaptive_firm' in s.get('run','') for s in steps)


def test_regressing_active_filter_rolls_back_without_reactivating_it(tmp_path,monkeypatch):
    store=Store(tmp_path/'state');s=spec();c=candidate(s)
    c['promoted_at']='2026-10-06T23:05:00+00:00';store.put('adaptive_active',c)
    prospective(store,c,s,monkeypatch,good=False)
    report=nightly(store,s,study(),[],datetime(2026,12,1,23,tzinfo=UTC))
    assert report['rollback']=='PAIRED_REGRESSION'
    assert store.get('adaptive_active') is None
    assert store.get('adaptive_retired:'+c['id'])['reason']=='PAIRED_REGRESSION'


def test_better_than_original_is_not_better_than_current_promoted_model():
    rows=[{'ticker':str(i),'entry_date':'2026-10-'+str(7+i//2),
           'keep':i%5!=0,'policy_net_return':.1 if i%5 else -.1,
           'stress_policy_net_return':.08 if i%5 else -.08} for i in range(50)]
    assert paired_gate(rows)['passed']
    identical_parent={(r['entry_date'],r['ticker']):r['keep'] for r in rows}
    assert not paired_gate(rows,identical_parent)['passed']
