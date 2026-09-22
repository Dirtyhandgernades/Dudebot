"""Small deterministic ranking model for 20% declines within 1–3 sessions.

The holdout labels are never used for fitting or threshold selection. This is a
ranking experiment over independently discovered firm-linked issuers, not a
claim of executable profit or a substitute for borrow/eligibility evidence.
"""
from __future__ import annotations

import math
from collections import defaultdict
import numpy as np

FEATURES=('return_21','return_5','return_1','drawdown_21','volume_ratio_20','failed_prev_low','range_pct')

def feature_row(history):
    if len(history)<22:return None
    last=history[-1];previous=history[-21:-1]
    if any(float(x.get('c',0))<=0 for x in history[-22:]):return None
    volume=sum(float(x.get('v',0)) for x in previous)/20
    if volume<=0:return None
    values=[last['c']/history[-22]['c']-1,last['c']/history[-6]['c']-1,last['c']/history[-2]['c']-1,
        last['c']/max(x['h'] for x in history[-22:])-1,last['v']/volume,
        float(last['c']<history[-2]['l']),(last['h']-last['l'])/last['c']]
    return values

def earliest_firm_dates(records):
    found={}
    for row in records:
        if 'VERIFIED_LISTED_FIRM_RELATIONSHIP' not in row.get('reasons',[]):continue
        ticker=row.get('ticker');day=row.get('decision_at','')[:10]
        if ticker and day and day<found.get(ticker,'9999-99-99'):found[ticker]=day
    return found

def samples(records,raw,adjusted,sessions):
    available=earliest_firm_dates(records);rows=[]
    for ticker,first in available.items():
        series=adjusted.get(ticker,{});raw_series=raw.get(ticker,{})
        for i in range(22,len(sessions)-8):
            day=sessions[i]
            if day<first:continue
            history_days=sessions[i-21:i+1]
            if any(d not in series for d in history_days):continue
            current_raw=raw_series.get(day);entry=series.get(sessions[i+1])
            if not current_raw or current_raw['c']<=3 or not entry:continue
            x=feature_row([series[d] for d in history_days])
            # The existing 12% pump and RVOL preference defines the candidate
            # population. The model ranks candidates; it does not weaken gates.
            if x is None or x[0]<.12 or x[4]<1:continue
            # Entry is the next close (i+1); label the following 1–3 closes.
            future=[series.get(d) for d in sessions[i+2:i+5]]
            if any(v is None for v in future):continue
            decline=min(v['c'] for v in future)/entry['c']-1
            rows.append({'ticker':ticker,'signal_date':day,'entry_date':sessions[i+1],
                'x':x,'label':int(decline<=-.20),'max_decline_1_3':decline})
    return rows

def _sigmoid(values):
    values=np.clip(values,-35,35);return 1/(1+np.exp(-values))

def fit(rows,iterations=1200,rate=.08,l2=.02):
    if len(rows)<20 or len({r['label'] for r in rows})<2:return None
    x=np.asarray([r['x'] for r in rows],dtype=float);y=np.asarray([r['label'] for r in rows],dtype=float)
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-12]=1
    z=(x-mean)/scale;weights=np.zeros(z.shape[1]);bias=0.;pos=max(y.sum(),1);neg=max(len(y)-y.sum(),1)
    sample_weight=np.where(y==1,len(y)/(2*pos),len(y)/(2*neg))
    for _ in range(iterations):
        error=(_sigmoid(z@weights+bias)-y)*sample_weight
        weights-=rate*((z.T@error)/len(y)+l2*weights)
        bias-=rate*error.mean()
    return {'features':FEATURES,'mean':mean.tolist(),'scale':scale.tolist(),'weights':weights.tolist(),'bias':bias,
        'training_samples':len(rows),'training_positives':int(y.sum())}

def predict(model,rows):
    if model is None:return []
    x=np.asarray([r['x'] for r in rows],dtype=float)
    z=(x-np.asarray(model['mean']))/np.asarray(model['scale'])
    return _sigmoid(z@np.asarray(model['weights'])+model['bias']).tolist()

def auc(labels,scores):
    pos=[s for y,s in zip(labels,scores) if y];neg=[s for y,s in zip(labels,scores) if not y]
    if not pos or not neg:return None
    return sum((p>n)+.5*(p==n) for p in pos for n in neg)/(len(pos)*len(neg))

def metrics(rows,scores,threshold=None):
    if not rows:return {'samples':0,'positives':0,'auc':None,'threshold':threshold,'selected':0,'precision':None,'recall':None}
    labels=[r['label'] for r in rows]
    if threshold is None:threshold=float(np.quantile(scores,.90)) if scores else 1
    selected=[i for i,s in enumerate(scores) if s>=threshold];tp=sum(labels[i] for i in selected);positives=sum(labels)
    return {'samples':len(rows),'positives':positives,'prevalence':positives/len(rows),'auc':auc(labels,scores),
        'threshold':threshold,'selected':len(selected),'precision':tp/len(selected) if selected else None,
        'recall':tp/positives if positives else None,'brier':sum((s-y)**2 for s,y in zip(scores,labels))/len(rows)}

def walk_forward_report(records,raw,adjusted,sessions):
    rows=samples(records,raw,adjusted,sessions)
    train=[r for r in rows if r['signal_date'][:4] in {'2022','2023'}]
    validation=[r for r in rows if r['signal_date'][:4]=='2024']
    holdout=[r for r in rows if r['signal_date'][:4]=='2025']
    model=fit(train);train_scores=predict(model,train);validation_scores=predict(model,validation)
    validation_metrics=metrics(validation,validation_scores)
    threshold=validation_metrics['threshold']
    holdout_scores=predict(model,holdout)
    return {'status':'TRAINED' if model else 'INSUFFICIENT_TRAINING_DATA','target':'at least 20% close decline 1-3 sessions after next-close entry',
        'candidate_gate':'independently discovered firm relationship; price > $3; trailing-21 return >=12%; volume ratio >=1',
        'splits':{'train':'2022-2023','validation':'2024','holdout':'2025'},'model':model,
        'train':metrics(train,train_scores,threshold),'validation':validation_metrics,
        'holdout':metrics(holdout,holdout_scores,threshold),
        'limitations':['Historical borrow, market cap, halts and SMG availability are not imputed','Overlapping daily samples are correlated','Model ranking cannot establish fraud or guarantee a decline']}
