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

def firm_watch_lead_report(records,raw,adjusted,sessions,periods,cohorts):
    """Measure a firm-first watch versus its timing trigger without winner seeding.

    A watch is visible only after its independently discovered firm evidence.
    Each label uses the *future* five closes for evaluation, never selection.
    """
    from .swing_backtest import signal
    first_dates=earliest_firm_dates(records);index={day:i for i,day in enumerate(sessions)}
    output=[]
    for start,end in periods:
        total=positive=timed=timed_positive=gaps=0
        watched_symbols=set();positive_symbols=set();timed_symbols=set()
        for ticker in cohorts[start]['short']:
            first=first_dates.get(ticker,'9999-99-99')
            series=adjusted.get(ticker,{});raw_series=raw.get(ticker,{})
            for day in sessions:
                if day<start or day>end or day<first:continue
                i=index[day]
                if i<21 or i+5>=len(sessions):continue
                current=raw_series.get(day)
                if not current or current.get('c',0)<=3:continue
                span=sessions[i-21:i+6]
                if any(d not in series for d in span):gaps+=1;continue
                history=[series[d] for d in span[:22]]
                base=history[-1]['c']
                if base<=0:gaps+=1;continue
                future=[series[d]['c'] for d in span[22:]]
                fall=min(future)/base-1<=-.20
                timing='PUMP_FAILURE_SHORT' in signal(history)
                total+=1;watched_symbols.add(ticker)
                if fall:positive+=1;positive_symbols.add(ticker)
                if timing:
                    timed+=1;timed_symbols.add(ticker)
                    if fall:timed_positive+=1
        events=[]
        for ticker in cohorts[start]['short']:
            series=adjusted.get(ticker,{});raw_series=raw.get(ticker,{})
            in_drop=False
            for i,day in enumerate(sessions):
                if day<start or day>end or i<5:continue
                prior=sessions[i-5:i]
                if day not in series or any(d not in series for d in prior):
                    in_drop=False;continue
                peak=max(series[d]['c'] for d in prior)
                drop=peak>0 and series[day]['c']/peak-1<=-.20
                if not drop:in_drop=False;continue
                if in_drop:continue
                in_drop=True
                watch=[];timing=[];eligible_evidence=eligible_price=0
                for j in range(max(21,i-5),i):
                    signal_day=sessions[j]
                    if signal_day<first_dates.get(ticker,'9999-99-99'):continue
                    eligible_evidence+=1
                    price=raw_series.get(signal_day)
                    if not price or price.get('c',0)<=3:continue
                    eligible_price+=1
                    history_days=sessions[j-21:j+1]
                    if any(d not in series for d in history_days):continue
                    watch.append(signal_day)
                    if 'PUMP_FAILURE_SHORT' in signal([series[d] for d in history_days]):timing.append(signal_day)
                events.append({'ticker':ticker,'drop_date':day,'five_session_peak_close':round(peak,4),
                    'drop_close':round(series[day]['c'],4),'drop_pct':round(100*(series[day]['c']/peak-1),2),
                    'prior_firm_watch_date':watch[0] if watch else None,
                    'prior_timing_trigger_date':timing[0] if timing else None,
                    'watch_gap_reason':None if watch else ('FIRM_EVIDENCE_NOT_YET_PUBLIC' if not eligible_evidence else
                        'PRICE_GATE_OR_RAW_BAR_MISSING' if not eligible_price else 'INCOMPLETE_22_SESSION_HISTORY'),
                    'firm_watch_lead_sessions':i-index[watch[0]] if watch else None,
                    'timing_lead_sessions':i-index[timing[0]] if timing else None})
        output.append({'start':start,'end':end,'firm_watch_days':total,
            'watch_symbols':len(watched_symbols),'five_session_drop_windows':positive,
            'drop_window_symbols':len(positive_symbols),'watch_day_drop_rate':positive/total if total else None,
            'timing_trigger_days':timed,'timing_trigger_symbols':len(timed_symbols),
            'timing_trigger_drop_windows':timed_positive,
            'timing_trigger_precision':timed_positive/timed if timed else None,
            'timing_trigger_window_recall':timed_positive/positive if positive else None,
            'missing_five_session_windows':gaps,
            'distinct_drop_events':len(events),
            'events_previously_on_firm_watch':sum(e['prior_firm_watch_date'] is not None for e in events),
            'events_with_prior_timing_trigger':sum(e['prior_timing_trigger_date'] is not None for e in events),
            'event_rows':events})
    return {'target':'At least 20% lower close within the next five sessions from the watch-day close',
        'periods':output,'limitations':['Daily windows overlap; these are not independent trade events',
        'A continuous firm watch is research coverage, not a profitable entry or calibrated probability',
        'Only independently discovered firm issuers with complete bars and a raw price above $3 are counted',
        'Historical borrow, market cap, halts and SMG availability remain unverified']}
