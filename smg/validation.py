"""Outcome-only missed-dump audit and empirical score calibration.

Neither function generates trade signals. Unknown coverage and overlapping
labels are reported rather than treated as negative examples.
"""
from collections import Counter
from datetime import date
import math
import numpy as np
from .game_rules import is_excluded_symbol
from .market import calendar


def missed_dumps(packet,unfiltered,selected,result,start,end):
    sessions=packet['sessions'];index={d:i for i,d in enumerate(sessions)}
    original={(d,e['ticker']) for d,es in unfiltered.items() for e in es}
    chosen={(d,e['ticker']) for d,es in selected.items() for e in es}
    rows=[];gaps=Counter()
    for ticker,series in sorted(packet['split'].items()):
        active=False
        for i,day in enumerate(sessions):
            if not start<=day<=end or i<3:continue
            span=sessions[i-3:i+1]
            expected=[str(d.date()) for d in calendar(int(day[:4])).sessions_in_range(span[0],day)]
            if span!=expected or any(d not in series for d in span):
                gaps['MISSING_OR_NONCONSECUTIVE_OUTCOME_WINDOW']+=1;active=False;continue
            peak_day=max(span[:-1],key=lambda d:series[d]['c'])
            drop=series[day]['c']/series[peak_day]['c']-1
            if drop>-.20+1e-10:active=False;continue
            if active:continue
            active=True
            prior=[d for d in span[:-1] if d>=start]
            eligible=[]
            for d in prior:
                raw=packet['raw'].get(ticker,{}).get(d)
                if d>=packet['firm_dates'].get(ticker,'9999-99-99') and raw and raw['c']>3:eligible.append(d)
            signals=[d for d in prior if (d,ticker) in original]
            picked=[d for d in prior if (d,ticker) in chosen]
            fills=[t for t in result['trades'] if t['ticker']==ticker and t['entry_date']<day<=t['exit_date']]
            if fills:reason='POSITION_OPEN_BEFORE_DROP'
            elif picked:reason='DETECTED_NO_POSITION_AT_DROP'
            elif signals:reason='RANK_OR_CONFIRMATION_FILTER_REJECTED'
            elif is_excluded_symbol(ticker) or (len(ticker)==5 and ticker.isalpha()):reason='HARD_SYMBOL_EXCLUSION'
            elif packet['firm_dates'].get(ticker,'9999-99-99')>max(prior,default='0000-00-00'):reason='FIRM_EVIDENCE_NOT_YET_PUBLIC'
            elif not eligible:
                observed=[packet['raw'].get(ticker,{}).get(d) for d in prior]
                reason=('RAW_PRICE_UNAVAILABLE' if not any(observed) else
                        'PRICE_GATE_WITH_PARTIAL_RAW_COVERAGE' if not all(observed) else 'PRICE_BELOW_3')
            else:
                incomplete=any(index[d]<22 or any(p not in series for p in sessions[index[d]-22:index[d]]) for d in eligible)
                reason='MISSING_SIGNAL_HISTORY' if incomplete else 'NO_TIMING_SETUP_OR_UNAVAILABLE_MINUTE_WINDOW'
            rows.append({'ticker':ticker,'drop_date':day,'peak_date':peak_day,'drop_pct':100*drop,
                'prior_setup_dates':signals,'prior_selected_dates':picked,'position_open':bool(fills),
                'reason':reason,'historical_borrow':'UNAVAILABLE','historical_eligibility':'UNVERIFIED'})
    return {'definition':'Distinct episodes crossing 20% below a prior close within three actual sessions',
        'events':len(rows),'reason_counts':dict(Counter(r['reason'] for r in rows)),
        'events_with_prior_selected_signal':sum(bool(r['prior_selected_dates']) for r in rows),
        'events_with_position_open':sum(r['position_open'] for r in rows),'gaps':dict(gaps),'rows':rows,
        'limitations':['Partial independently discovered firm corpus, not whole-market recall',
            'No setup and missing minute window cannot be separated without the underlying minute cache',
            'Being positioned during an event does not establish a 20% profit from the actual fill']}


def independent_rows(rows):
    """Use one nonoverlapping label window per ticker, in time order."""
    output=[];ends={}
    for row in sorted(rows,key=lambda r:(r['signal_date'],r['ticker'])):
        if row['signal_date']<=ends.get(row['ticker'],''):continue
        output.append(row);ends[row['ticker']]=row['label_end']
    return output


def fit_calibration(rows,scores):
    if len(rows)!=len(scores):raise ValueError('Calibration rows and scores must align')
    if len(rows)<30 or len({r['label'] for r in rows})<2:return None
    x=np.log(np.clip(scores,1e-6,1-1e-6)/(1-np.clip(scores,1e-6,1-1e-6)))
    y=np.asarray([r['label'] for r in rows],float);a=0.;b=math.log((y.sum()+.5)/(len(y)-y.sum()+.5))
    for _ in range(1200):
        p=1/(1+np.exp(-np.clip(a*x+b,-35,35)))
        a-=.03*(np.mean((p-y)*x)+.01*a);b-=.03*np.mean(p-y)
    return {'method':'UNWEIGHTED_PLATT_RESEARCH','a':float(a),'b':float(b),'samples':len(rows),
        'positive_outcomes':int(y.sum()),'latest_label':max(r['label_end'] for r in rows)}


def calibrated_scores(model,scores):
    if model is None:return []
    x=np.log(np.clip(scores,1e-6,1-1e-6)/(1-np.clip(scores,1e-6,1-1e-6)))
    return (1/(1+np.exp(-np.clip(model['a']*x+model['b'],-35,35)))).tolist()


def reliability(rows,scores):
    if len(rows)!=len(scores):raise ValueError('Reliability rows and scores must align')
    bins=[]
    for lo,hi in ((0,.1),(.1,.2),(.2,.4),(.4,.6),(.6,.8),(.8,1.000001)):
        selected=[(r,s) for r,s in zip(rows,scores) if lo<=s<hi]
        if not selected:continue
        n=len(selected);hits=sum(r['label'] for r,s in selected);p=hits/n;z=1.96
        center=(p+z*z/(2*n))/(1+z*z/n)
        spread=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
        bins.append({'lower':lo,'upper':min(hi,1),'n':n,'positive_outcomes':hits,
            'distinct_tickers':len({r['ticker'] for r,s in selected}),
            'mean_estimate':sum(s for r,s in selected)/n,'observed_rate':p,
            'wilson_95_interval':[center-spread,center+spread]})
    return {'samples':len(rows),'bins':bins,'confidence_sizing_enabled':False,
        'brier':sum((s-r['label'])**2 for r,s in zip(rows,scores))/len(rows) if rows else None}
