"""Automatic, versioned challenger research and prospective promotion.

The only permitted live change is an extra rank filter on fully gated firm
signals. No orders, larger sizes, relaxed eligibility or source-based accusations.
Historical seasons are reused diagnostics; promotion also needs decisions
recorded before fresh outcomes. A challenger stays frozen until evaluated.
"""
import argparse
import hashlib
import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import numpy as np
from .action_learning import policy_outcome
from .risk_model import fit, predict, FEATURES
from .market import session_bounds
from .storage import Store, GitHubState
from .transport import Http

UTC=timezone.utc
RECIPE='PROFITABLE_POLICY_MEDIAN_FILTER_V1'
PENALTIES=(.02,.1,.5)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def context(spec):
    # The id changes with the implementation or allowed gates, not with prices.
    return digest({'implementation':spec['implementation_sha256'],
                   'base_model':spec['model'],'base_threshold':spec['rank_threshold'],
                   'entry_policy':spec['entry_policy'],'recipe':RECIPE,
                   'inputs':spec.get('adaptive_research_inputs',{})})


def valid_model(candidate,spec,now):
    if not spec.get('automatic_improvement_enabled') or not candidate or candidate.get('context')!=context(spec):return False
    body={k:v for k,v in candidate.items() if k not in ('id','created_at','promoted_at')}
    if candidate.get('id')!='adaptive-'+digest(body)[:20]:return False
    try:
        created=datetime.fromisoformat(candidate['created_at'])
        model=candidate['model']
        return (candidate.get('l2') in PENALTIES and created.tzinfo is not None and created<=now and candidate['training_latest_label']<str(created.date())
                and model['features']==list(FEATURES) and all(len(model[k])==7 for k in ('mean','scale','weights'))
                and all(math.isfinite(v) for k in ('mean','scale','weights') for v in model[k])
                and all(v>0 for v in model['scale']) and math.isfinite(model['bias'])
                and 0<=candidate['threshold']<=1)
    except (KeyError,ValueError,TypeError):return False


def make_candidate(rows,spec,now,penalty=.02):
    # Only completed outcomes strictly before this date enter training. Keeping
    # the complete delayed-policy loss prevents a later dump from excusing a squeeze.
    known=[{**r,'label':r['policy_profitable']} for r in rows
           if r.get('policy_net_return') is not None and r['label_end']<str(now.date())
           and len(r.get('x',[]))==7 and all(math.isfinite(v) for v in r['x'])]
    if penalty not in PENALTIES:raise ValueError('Unregistered training recipe')
    model=fit(known,l2=penalty)
    if not model:return None
    model['features']=list(FEATURES)
    body={'recipe':RECIPE,'l2':penalty,'context':context(spec),'model':model,
          'threshold':float(np.quantile(predict(model,known),.5)),
          'training_latest_label':max(r['label_end'] for r in known),'training_samples':len(known)}
    return {**body,'id':'adaptive-'+digest(body)[:20],'created_at':now.isoformat()}


def record_decision(store,candidate,result,spec,now):
    """Persist both kept and rejected BASE-qualified entries before labels exist."""
    if not valid_model(candidate,spec,now) or result.status!='QUALIFIED':return
    key='adaptive_decision:'+candidate['id']+':'+str(now.date())+':'+result.candidate.ticker
    if store.get(key):return
    facts=result.ranking_evidence['ranked_firm'];event=facts['event']
    score=predict(candidate['model'],[{'x':facts['features']}])[0]
    store.put(key,{'model_id':candidate['id'],'context':candidate['context'],
                  'ticker':result.candidate.ticker,'cik':result.candidate.cik,
                  'entry_date':str(now.date()),'observed_at':now.isoformat(),
                  'data_cutoff':event['data_cutoff'],'x':facts['features'],
                  'base_eligible':True,'keep':score>=candidate['threshold'],
                  'score':score,'decision_price':event['decision_price']})


def record_base(store,result,spec,now):
    key='adaptive_base_decision:'+context(spec)+':'+str(now.date())+':'+result.candidate.ticker
    if store.get(key):return
    facts=result.ranking_evidence['ranked_firm']
    store.put(key,{'context':context(spec),'ticker':result.candidate.ticker,'cik':result.candidate.cik,
                  'entry_date':str(now.date()),'observed_at':now.isoformat(),
                  'data_cutoff':facts['event']['data_cutoff'],'x':facts['features'],
                  'history_dates':facts['feature_dates'],'base_eligible':True})


def mature_outcome(store,row,spec,now):
    key='adaptive_outcome:'+context(spec)+':'+row['entry_date']+':'+row['ticker']
    prior=store.get(key)
    if prior:return prior
    cache=store.get('ranked_daily_history',{})
    outcome=policy_outcome(row,cache.get('split',{}),cache.get('raw',{}))
    if outcome['policy_net_return'] is not None:
        if session_bounds(date.fromisoformat(outcome['label_end']))[1]+timedelta(minutes=16)>now:
            return {'status':'OUTCOME_NOT_MATURE','policy_net_return':None}
        stress=policy_outcome(row,cache.get('split',{}),cache.get('raw',{}),cost_bps=100,borrow_rate=1.)
        outcome={**outcome,'label_observed_at':now.isoformat(),'stress_policy_net_return':stress['policy_net_return']}
        store.put(key,outcome)
    return outcome


def base_training(store,spec,now):
    rows=[];ends={}
    for _,r in sorted(store.items('adaptive_base_decision:'+context(spec)+':'),key=lambda kv:(kv[1]['entry_date'],kv[1]['ticker'])):
        try:
            observed=datetime.fromisoformat(r['observed_at']);cutoff=datetime.fromisoformat(r['data_cutoff'])
            bounds=session_bounds(date.fromisoformat(r['entry_date']));days=r['history_dates']
            if (not bounds or observed.tzinfo is None or cutoff.tzinfo is None or observed>now or not r['base_eligible']
                or not bounds[1]-timedelta(minutes=20)<=observed<bounds[1] or observed-cutoff<timedelta(minutes=16)
                or len(days)!=22 or days!=sorted(set(days)) or days[-1]>=r['entry_date']
                or len(r['x'])!=7 or not all(math.isfinite(v) for v in r['x'])):continue
            outcome=mature_outcome(store,r,spec,now);issuer=r.get('cik') or r['ticker']
            if outcome['policy_net_return'] is None or r['entry_date']<=ends.get(issuer,''):continue
            rows.append({**r,**outcome});ends[issuer]=outcome['label_end']
        except (ValueError,TypeError,KeyError):continue
    return rows


def apply_active(store,result,spec,now):
    """A research model cannot qualify an otherwise excluded/review-only stock."""
    if result.status!='QUALIFIED':return result
    record_base(store,result,spec,now)
    staged=store.get('adaptive_staged');active=store.get('adaptive_active')
    for candidate in (staged,active):record_decision(store,candidate,result,spec,now)
    if not valid_model(active,spec,now):return result
    evidence=result.ranking_evidence['ranked_firm']
    score=predict(active['model'],[{'x':evidence['features']}])[0]
    evidence['adaptive']={'model_id':active['id'],'rank':score,'is_probability':False,
                          'threshold':active['threshold'],'scope':'ADDITIONAL_BASE_QUALIFIED_FILTER'}
    if score<active['threshold']:
        result.status='REVIEW_REQUIRED';result.reasons.append('ADAPTIVE_RANK_DEFERRED')
        result.signal_side=None
    return result


def observed_pairs(store,candidate,spec,now,since=None):
    if not valid_model(candidate,spec,now):return [],{'INVALID_CANDIDATE':1}
    gaps={};known=[];ends={}
    for _,r in sorted(store.items('adaptive_decision:'+candidate['id']+':'),key=lambda kv:(kv[1]['entry_date'],kv[1]['ticker'])):
        if since and r.get('observed_at','')<since:continue
        try:
            observed=datetime.fromisoformat(r['observed_at']);cutoff=datetime.fromisoformat(r['data_cutoff'])
            bounds=session_bounds(date.fromisoformat(r['entry_date']))
            if (r['context']!=candidate['context'] or not r['base_eligible'] or not bounds or observed>now or
                observed.tzinfo is None or cutoff.tzinfo is None or observed<datetime.fromisoformat(candidate['created_at']) or
                len(r['x'])!=7 or not all(math.isfinite(v) for v in r['x']) or
                not bounds[1]-timedelta(minutes=20)<=observed<bounds[1] or observed-cutoff<timedelta(minutes=16)):
                raise ValueError('INVALID_PROSPECTIVE_DECISION')
            # Never trust a mutable keep flag instead of the frozen model score.
            score=predict(candidate['model'],[{'x':r['x']}])[0]
            if abs(score-r['score'])>1e-10 or r['keep']!=(score>=candidate['threshold']):raise ValueError('DECISION_MODEL_MISMATCH')
            outcome=mature_outcome(store,r,spec,now)
            if outcome['policy_net_return'] is None:
                gaps[outcome['status']]=gaps.get(outcome['status'],0)+1;continue
            bounds_end=session_bounds(date.fromisoformat(outcome['label_end']))
            if bounds_end[1]+timedelta(minutes=16)>now:
                gaps['OUTCOME_NOT_MATURE']=gaps.get('OUTCOME_NOT_MATURE',0)+1;continue
            issuer=r.get('cik') or r['ticker']
            if r['entry_date']<=ends.get(issuer,''):continue
            known.append({**r,**outcome});ends[issuer]=outcome['label_end']
        except (ValueError,KeyError,TypeError):gaps['INVALID_DECISION']=gaps.get('INVALID_DECISION',0)+1
    return known,gaps


def paired_gate(rows,incumbent_flags=None):
    failures=[];kept=[r for r in rows if r['keep']];rejected=[r for r in rows if not r['keep']]
    issuers={r.get('cik') or r['ticker'] for r in rows}
    if len(rows)<50:failures.append('NEED_50_MATURE_NONOVERLAPPING_DECISIONS')
    if len(issuers)<10:failures.append('NEED_10_DISTINCT_ISSUERS')
    if len({r['entry_date'] for r in rows})<20:failures.append('NEED_20_DECISION_SESSIONS')
    if len(kept)<20 or len(rejected)<10:failures.append('INSUFFICIENT_KEEP_REJECT_COMPARISON')
    # Retaining all trades is no improvement. Profitability is a paired, fixed
    # $25k return diagnostic, not an account profit or simulated margin balance.
    def parent(r):
        return True if incumbent_flags is None else incumbent_flags.get((r['entry_date'],r['ticker']))
    if any(parent(r) is None for r in rows):failures.append('INCUMBENT_COMPARISON_UNAVAILABLE')
    improvement=sum(r['policy_net_return']*(int(r['keep'])-int(parent(r) or False)) for r in rows)
    stressed=sum((r.get('stress_policy_net_return') or 0)*(int(r['keep'])-int(parent(r) or False)) for r in rows)
    if improvement<=.10:failures.append('PAIRED_COSTED_IMPROVEMENT_NOT_POSITIVE')
    if sum(r['policy_net_return'] for r in kept)<=0:failures.append('KEPT_POLICY_RETURNS_NOT_POSITIVE')
    if any(r.get('stress_policy_net_return') is None for r in rows):failures.append('STRESSED_OUTCOMES_UNAVAILABLE')
    if stressed<=.05 or sum((r.get('stress_policy_net_return') or 0) for r in kept)<=0:failures.append('STRESSED_PAIRED_RETURNS_NOT_IMPROVED')
    # Require positive paired improvement in both chronological halves.
    for half in (rows[:len(rows)//2],rows[len(rows)//2:]):
        if sum(r['policy_net_return']*(int(r['keep'])-int(parent(r) or False)) for r in half)<=0:
            failures.append('CHRONOLOGICAL_HALF_NOT_IMPROVED');break
    return {'passed':not failures,'failures':failures,'matured':len(rows),'issuers':len(issuers),
            'kept':len(kept),'rejected':len(rejected),'paired_net_return_improvement':improvement,
            'paired_stress_return_improvement':stressed,
            'semantics':'PAIRED_PAPER_RETURN_SUM_NOT_PORTFOLIO_PROFIT'}


def nightly(store,spec,study,training,now):
    report={'asof':now.isoformat(),'provider_requests':0,'orders_placed':0,
            'years':[2023,2024,2025],'automatic_promotion_enabled':True,
            'historical':study,'status':'INCUMBENT_UNCHANGED'}
    # Check an active filter independently of newly fit candidates. Unknown
    # outcomes cannot trigger an optimistic promotion or a false rollback.
    active=store.get('adaptive_active')
    if active and not valid_model(active,spec,now):
        store.observe('adaptive_lifecycle',active.get('id','INVALID'),now,'local:nightly',{'action':'ROLLBACK_INVALID_CONTEXT'})
        store.delete('adaptive_active');report['rollback']='INVALID_MODEL_CONTEXT';active=None
    if active:
        rows,gaps=observed_pairs(store,active,spec,now)
        after=[r for r in rows if r['observed_at']>active['promoted_at']][-20:]
        if len(after)>=10 and -sum(r['policy_net_return'] for r in after if not r['keep'])<-.10:
            store.observe('adaptive_lifecycle',active['id'],now,'local:nightly',{'action':'ROLLBACK_PAIRED_REGRESSION'})
            store.put('adaptive_retired:'+active['id'],{'reason':'PAIRED_REGRESSION','at':now.isoformat()})
            store.delete('adaptive_active');report['rollback']='PAIRED_REGRESSION';active=None
    staged=store.get('adaptive_staged')
    if staged and not valid_model(staged,spec,now):store.delete('adaptive_staged');staged=None
    if staged:
        rows,gaps=observed_pairs(store,staged,spec,now);parent_flags=None
        if active:
            parent_rows,parent_gaps=observed_pairs(store,active,spec,now,since=staged['created_at'])
            aligned={(r['entry_date'],r['ticker']):r for r in parent_rows}
            parent_flags={(r['entry_date'],r['ticker']):aligned[(r['entry_date'],r['ticker'])]['keep']
                          for r in rows if (r['entry_date'],r['ticker']) in aligned and
                          aligned[(r['entry_date'],r['ticker'])]['x']==r['x']}
            report['incumbent_comparison_gaps']=parent_gaps
        gate=paired_gate(rows,parent_flags)
        report['prospective']={**gate,'gaps':gaps,'model_id':staged['id']}
        report['status']='COLLECTING_PROSPECTIVE_OUTCOMES'
        variant=next((v for v in study['variants'] if v['l2']==staged['l2']),None)
        if variant and variant['promotion_gate']['passed'] and gate['passed']:
            promoted={**staged,'promoted_at':now.isoformat()}
            # promoted_at is lifecycle metadata, outside the immutable model id.
            store.put('adaptive_active',promoted);store.delete('adaptive_staged')
            if active:store.put('adaptive_retired:'+active['id'],{'reason':'REPLACED_BY_VALIDATED_CHALLENGER','at':now.isoformat()})
            store.observe('adaptive_lifecycle',staged['id'],now,'local:nightly',{'action':'PROMOTED','gate':gate})
            report['status']='PROMOTED_ADDITIONAL_RANK_FILTER';active=promoted;staged=None
    fresh=base_training(store,spec,now)
    report['fresh_training_outcomes']=len(fresh)
    candidate=make_candidate(training+fresh,spec,now,study['selected_l2'])
    report['daily_candidate']=candidate
    refreshed=not active or (candidate and candidate['id']!=active['id'] and candidate['training_samples']>=active['training_samples']+25)
    if spec.get('automatic_improvement_enabled') and not staged and refreshed and candidate and study['promotion_gate']['passed']:
        if not store.get('adaptive_retired:'+candidate['id']):
            store.put('adaptive_staged',candidate);report['status']='FROZEN_CHALLENGER_STAGED'
            store.observe('adaptive_lifecycle',candidate['id'],now,'local:nightly',{'action':'STAGED'})
    report['active_model_id']=(active or {}).get('id')
    if not study['promotion_gate']['passed']:report['status']='HISTORICAL_GATE_REJECTED_INCUMBENT_UNCHANGED'
    store.put('adaptive_last_review',{'asof':now.isoformat(),'status':report['status'],'active_model_id':report['active_model_id']})
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--signals',required=True)
    p.add_argument('--state',default='runtime/state.sqlite');p.add_argument('--out',default='reports/daily-adaptive');p.add_argument('--research-only',action='store_true');args=p.parse_args()
    from backtest.daily_adaptive_study import run
    from .ranked_firm import valid_policy
    root=Path.cwd();spec=json.loads((root/'config/ranked_firm_alerts.json').read_text());now=datetime.now(UTC)
    valid_policy(spec,root,now) # Integrity check; research may precede first session.
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    study,training=run(Path(args.packet),Path(args.signals),out/'history')
    expected=spec['adaptive_research_inputs']
    if any(study[key]!=expected[key] for key in ('packet_sha256','signals_sha256')):
        raise ValueError('ADAPTIVE_RESEARCH_INPUTS_CHANGED; publish a new version')
    backend=None
    if os.environ.get('GITHUB_ACTIONS')=='true' and not args.research_only:
        backend=GitHubState(Http(),os.environ['GITHUB_REPOSITORY'],os.environ['GITHUB_TOKEN']);backend.restore(args.state)
    store=Store(args.state)
    try:
        report=nightly(store,spec,study,training,now) if not args.research_only else {'status':'RESEARCH_ONLY','historical':study,'candidate':make_candidate(training,spec,now,study['selected_l2']),'orders_placed':0,'provider_requests':0}
        (out/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({k:v for k,v in report.items() if k not in ('historical','daily_candidate','candidate')}))
        if backend:backend.checkpoint(store)
    finally:store.db.close()


if __name__=='__main__':main()
