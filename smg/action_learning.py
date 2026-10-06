"""Learn policy returns and squeeze losses separately from dump occurrence.

No orders, messages, provider calls, frozen weight changes or live promotion.
Daily-provider and prospective regular-session features never mix in a fit.
"""
import argparse
import json
import math
import sqlite3
from collections import Counter
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import numpy as np
from .market import calendar,session_bounds
from .risk_model import feature_row,predict


def policy_outcome(row,split,raw=None,cost_bps=30,borrow_rate=.1):
    """End-of-day stop/target exits execute at the following close, not the low."""
    entry=row['entry_date'];ticker=row['ticker'];series=split.get(ticker,{})
    days=[str(d.date()) for d in calendar(int(entry[:4])).sessions_in_range(entry,str(date.fromisoformat(entry)+timedelta(days=15)))][:4]
    if len(days)!=4 or any(d not in series or not isinstance(series[d].get('c'),(int,float)) or
            not math.isfinite(series[d]['c']) or series[d]['c']<=0 for d in days):
        return {'status':'OUTCOME_UNAVAILABLE','policy_net_return':None,'tail_loss':None}
    if raw is not None:
        bar=raw.get(ticker,{}).get(entry)
        if not bar:return {'status':'RAW_ENTRY_UNAVAILABLE','policy_net_return':None,'tail_loss':None}
        if bar['c']<=3:return {'status':'ENTRY_PRICE_REJECTED','policy_net_return':None,'tail_loss':None}
    base=series[entry]['c'];exit_day=days[3];reason='THREE_SESSION_LIMIT'
    for i in (1,2):
        previous_return=1-series[days[i]]['c']/base
        if previous_return<=-.12:exit_day=days[i+1];reason='STOP_FROM_PRIOR_CLOSE';break
        if previous_return>=.20:exit_day=days[i+1];reason='TARGET_FROM_PRIOR_CLOSE';break
    ratio=series[exit_day]['c']/base;elapsed=(date.fromisoformat(exit_day)-date.fromisoformat(entry)).days
    # Commission fraction refers to a fixed $25k research notional. Actual
    # portfolio fees are recomputed using the real simulated shares/notional.
    net=1-ratio-(cost_bps/10000)*(1+ratio)-10/25000-borrow_rate*elapsed/365
    used=days[:days.index(exit_day)+1];adverse=max(series[d]['c']/base-1 for d in used)
    return {'status':'POLICY_OUTCOME_OBSERVED','entry_date':entry,'exit_date':exit_day,'exit_reason':reason,
            'policy_net_return':net,'policy_profitable':int(net>0),'tail_loss':int(net<=-.30),
            'max_adverse_close_return':adverse,'dump_20pct_occurs':int(min(series[d]['c'] for d in days[1:])/base-1<=-.20+1e-10),
            'label_end':days[-1],'commission_notional_assumption':25000}


def add_outcomes(rows,split,raw=None):
    return [{**row,**policy_outcome(row,split,raw)} for row in rows]


def normalized_x(rows):
    x=np.clip(np.asarray([r['x'] for r in rows],float),-20,20)
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-10]=1
    return (x-mean)/scale,mean,scale


def fit_policy(rows,penalty=.5):
    known=[r for r in rows if r.get('policy_net_return') is not None]
    if len(known)<30:return None
    z,mean,scale=normalized_x(known);a=np.column_stack([z,np.ones(len(z))]);y=np.asarray([r['policy_net_return'] for r in known])
    regularizer=np.diag([penalty]*z.shape[1]+[0.])
    # Do not clip financial loss targets: a 200% squeeze is not a 30% loss.
    weights=np.linalg.solve(a.T@a/len(a)+regularizer,a.T@y/len(a))
    model={'mean':mean.tolist(),'scale':scale.tolist(),'weights':weights[:-1].tolist(),'bias':float(weights[-1]),
           'features':list(range(z.shape[1])),'fit':'RIDGE_POLICY_NET_RETURN','penalty':penalty,
           'training_samples':len(known),'training_latest_label':max(r['label_end'] for r in known)}
    heads={}
    for target in ('policy_profitable','tail_loss','dump_20pct_occurs'):
        labels=np.asarray([r[target] for r in known],float);w=np.zeros(z.shape[1]);b=math.log((labels.sum()+.5)/(len(labels)-labels.sum()+.5))
        for _ in range(600):
            p=1/(1+np.exp(-np.clip(z@w+b,-35,35)));error=p-labels
            w-=.05*(z.T@error/len(z)+.1*w);b-=.05*error.mean()
        heads[target]={'mean':mean.tolist(),'scale':scale.tolist(),'weights':w.tolist(),'bias':float(b),'features':model['features']}
    return {'return_model':model,**heads,'live_enabled':False,'confidence_sizing_enabled':False,
            'score_semantics':'RESEARCH_EXPECTED_RETURN_AND_UNCALIBRATED_RISK_RANKS'}


def policy_scores(model,rows):
    if not model or not rows:return []
    clipped=[{'x':np.clip(r['x'],-20,20).tolist()} for r in rows];return_model=model['return_model']
    z=(np.asarray([r['x'] for r in clipped])-return_model['mean'])/return_model['scale']
    returns=np.minimum(z@np.asarray(return_model['weights'])+return_model['bias'],1.)
    profitable=predict(model['policy_profitable'],clipped);tail=predict(model['tail_loss'],clipped)
    dump=predict(model['dump_20pct_occurs'],clipped)
    return [{'return_rank':float(value),'profitability_rank':win,'tail_loss_rank':loss,'dump_rank':drop}
            for value,win,loss,drop in zip(returns,profitable,tail,dump)]


def forward_review(path,now=None):
    """Read only the existing forecast/price ledger. Missing outcomes stay unknown."""
    now=now or datetime.now(timezone.utc)
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    values={k:json.loads(v) for k,v in db.execute("SELECT key,value FROM kv WHERE key LIKE 'forward_forecast:%' OR key LIKE 'forward_prices:%' OR key LIKE 'forward_contract:%'")};db.close()
    split={k.removeprefix('forward_prices:split:'):v for k,v in values.items() if k.startswith('forward_prices:split:')}
    raw={k.removeprefix('forward_prices:raw:'):v for k,v in values.items() if k.startswith('forward_prices:raw:')}
    # A manual daytime review cannot treat the current partial daily bar as final.
    for data in (split,raw):
        for series in data.values():
            for day in list(series):
                bounds=session_bounds(date.fromisoformat(day))
                if not bounds or bounds[1]+timedelta(minutes=16)>now:del series[day]
    groups={};invalid=0
    for key,forecast in values.items():
        if not key.startswith('forward_forecast:'):continue
        try:
            observed=datetime.fromisoformat(forecast['observed_at'].replace('Z','+00:00'))
            bounds=session_bounds(date.fromisoformat(forecast['signal_date']))
            if observed.tzinfo is None or observed>now or not bounds or not bounds[0]<=observed<bounds[1]:raise ValueError('Invalid forecast time')
            contract=values.get('forward_contract:'+forecast['contract_id'],{})
            if not contract.get('sha256') or forecast.get('contract_sha256')!=contract['sha256']:raise ValueError('Unknown forecast contract')
            if not forecast['feature_basis'].startswith('REGULAR_SESSION_MINUTE_AGGREGATES'):raise ValueError('Different feature basis')
            history_days=[r['date'] for r in forecast['history']]
            if len(history_days)!=22 or history_days!=sorted(set(history_days)) or history_days[-1]>=forecast['signal_date']:
                raise ValueError('History contains current/future features')
            cutoff=datetime.fromisoformat(forecast['event']['data_cutoff'].replace('Z','+00:00'))
            if cutoff.tzinfo is None or observed-cutoff<timedelta(minutes=16):raise ValueError('Delay missing')
            x=feature_row(forecast['history'])
            if x is None or not all(math.isfinite(v) for v in x):raise ValueError('Missing forecast features')
        except (ValueError,KeyError,TypeError):invalid+=1;continue
        contract=forecast['contract_id'];groups.setdefault(contract,[]).append({
            'ticker':forecast['ticker'],'signal_date':forecast['signal_date'],'entry_date':forecast['signal_date'],
            'x':x,'paper_eligible':forecast['paper_eligible'],'feature_basis':forecast['feature_basis']})
    reports=[]
    for contract,forecasts in groups.items():
        # Never pool contracts or daily-provider training with this live feature basis.
        rows=add_outcomes(forecasts,split,raw);known=[];ends={}
        for row in sorted(rows,key=lambda r:(r['signal_date'],r['ticker'])):
            if row['policy_net_return'] is None or row['signal_date']<=ends.get(row['ticker'],''):continue
            known.append(row);ends[row['ticker']]=row['label_end']
        tail_count=sum(r['tail_loss'] for r in known);profit_count=sum(r['policy_profitable'] for r in known)
        ready=len(known)>=50 and tail_count>=5 and profit_count>=10 and len({r['ticker'] for r in known})>=5
        proposed=fit_policy(known) if ready else None
        reports.append({'contract_id':contract,'forecasts':len(rows),'mature_nonoverlapping':len(known),
                        'classification_hits_with_policy_loss':sum(r.get('dump_20pct_occurs')==1 and r['policy_net_return']<=0 for r in known),
                        'tail_losses':tail_count,'profitable_outcomes':profit_count,'status':'RESEARCH_CANDIDATE_ONLY' if ready else 'COLLECTING_OBSERVED_OUTCOMES',
                        'proposed_model':proposed,'rows':rows,'live_enabled':False})
    return {'asof':now.isoformat(),'status':'REVIEWED' if groups else 'INVALID_FORECASTS_ONLY' if invalid else 'NO_FORECASTS_YET','reports':reports,
            'invalid_forecasts':invalid,'provider_requests':0,'frozen_policy_changed':False,'automatic_promotion':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('--state',default='runtime/state.sqlite');p.add_argument('--out',default='reports/action-policy-learning.json');args=p.parse_args()
    result=forward_review(args.state);out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:result[k] for k in ('status','invalid_forecasts','provider_requests','automatic_promotion')}))


if __name__=='__main__':main()
