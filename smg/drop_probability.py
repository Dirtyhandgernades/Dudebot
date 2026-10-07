"""Empirical probabilities from independent, timestamped firm entry episodes.

Target is a20% closing-price drop after the closing entry, not an intraday low
or a profitable short. Rank bands are fixed before evaluation. Previously
inspected years remain reused evidence, and Wilson intervals are approximate.
"""
import json,gzip,math
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
from .market import calendar

TARGETS=('day_1','day_2','day_3','severe_50pct_day_3')


def outcome(row,split,raw):
    day=row['entry_date'];series=split.get(row['ticker'],{})
    days=[str(d.date()) for d in calendar(int(day[:4])).sessions_in_range(day,str(date.fromisoformat(day)+timedelta(days=15)))][:4]
    if len(days)!=4 or any(d not in series or not math.isfinite(series[d].get('c',float('nan'))) or series[d]['c']<=0 for d in days):return None
    if raw.get(row['ticker'],{}).get(day,{}).get('c',0)<=3:return None
    returns=[series[d]['c']/series[day]['c']-1 for d in days[1:]]
    return {'label_end':days[-1],**{f'day_{h}':int(min(returns[:h])<=-.20+1e-10) for h in (1,2,3)},
            'severe_50pct_day_3':int(min(returns)<=-.50+1e-10)}


def independent(rows):
    result=[];ends={}
    for r in sorted(rows,key=lambda r:(r['entry_date'],r['ticker'])):
        issuer=r.get('cik') or r['ticker']
        if r['entry_date']<=ends.get(issuer,''):continue
        result.append(r);ends[issuer]=r['label_end']
    return result


def summarize(rows):
    n=len(rows);output={}
    for target in TARGETS:
        hits=sum(r[target] for r in rows)
        if not n:continue
        p=hits/n;z=1.96;denom=1+z*z/n
        center=(p+z*z/(2*n))/denom;spread=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
        output[target]={'hits':hits,'estimate':(hits+.5)/(n+1),'wilson_95':[max(0,center-spread),min(1,center+spread)]}
    return {'samples':n,'issuers':len({r.get('cik') or r['ticker'] for r in rows}),
            'latest_label':max((r['label_end'] for r in rows),default=None),'targets':output}


def build(rows):
    rows=independent(rows);bins=[]
    for lo,hi in ((0,.5),(.5,.7),(.7,1.000001)):
        bins.append({'rank_min':lo,'rank_max':min(1,hi),**summarize([r for r in rows if lo<=r['rank_score']<hi])})
    return {'method':'EMPIRICAL_FIXED_RANK_BANDS_JEFFREYS_MEAN','target':'20pct lower close within1/2/3 sessions after closing entry',
            'minimum_samples':30,'minimum_issuers':5,'pooled':summarize(rows),'bins':bins,
            'limits':['Previously inspected years; not untouched live calibration',
                      'Historical borrow/cap/halts/SMG membership remain unverified',
                      'Only independently sourced preclose firm setups; not a whole-market probability',
                      'Approximate intervals assume independent episodes; market/issuer correlations remain']}


def estimate(reference,rank):
    if not reference or not isinstance(rank,(int,float)) or not math.isfinite(rank) or not 0<=rank<=1:return {'status':'INSUFFICIENT_DATA'}
    cohort=next((b for b in reference['bins'] if b['rank_min']<=rank and (rank<b['rank_max'] or rank==b['rank_max']==1)
                 and b['samples']>=reference['minimum_samples'] and b['issuers']>=reference['minimum_issuers']),None)
    scope='COMPARABLE_RANK_BAND' if cohort else 'POOLED_FIRM_SETUP_REFERENCE'
    cohort=cohort or reference['pooled']
    if cohort['samples']<reference['minimum_samples'] or cohort['issuers']<reference['minimum_issuers']:
        return {'status':'INSUFFICIENT_DATA','samples':cohort['samples']}
    return {'status':'ESTIMATED_HISTORICAL_REFERENCE','scope':scope,'samples':cohort['samples'],
            'issuers':cohort['issuers'],'latest_label':cohort['latest_label'],'targets':cohort['targets'],
            'is_guarantee':False,'is_live_calibrated':False}


def historical(packet_path,signals_folder):
    packet=json.loads(gzip.decompress(Path(packet_path).read_bytes()));rows=[];gaps=0
    identities={}
    for r in packet['records']:
        try:stamp=datetime.fromisoformat(r['decision_at'])
        except (KeyError,ValueError,TypeError):continue
        if stamp.tzinfo is not None:identities.setdefault(r['ticker'],[]).append((stamp.astimezone(timezone.utc),r.get('cik')))
    for y in (2023,2024,2025):
        events=json.loads((Path(signals_folder)/f'{y}-PRECLOSE_ONLY-signals.json').read_text())
        for day,signals in events.items():
            for event in signals:
                observed=datetime.fromisoformat(event['decision_at'])
                known=[r for r in identities.get(event['ticker'],[]) if r[0]<=observed]
                if not known:gaps+=1;continue
                row={'ticker':event['ticker'],'cik':max(known,key=lambda r:r[0])[1],'entry_date':day,
                     'rank_score':event['training_rank'],'observed_at':event['decision_at']}
                labels=outcome(row,packet['split'],packet['raw'])
                if labels is None:gaps+=1;continue
                rows.append({**row,**labels})
    rows=independent(rows);reference=build(rows)
    # Forecast2025 using ONLY labels that finished before2025. Inspect all
    # horizons and preserve misses, not just eventual20% hits or profitable fills.
    train=[r for r in rows if r['label_end']<'2025-01-01'];test=[r for r in rows if r['entry_date'].startswith('2025')]
    evaluation={}
    for target in TARGETS:
        predictions=[(r,estimate(build([earlier for earlier in rows if earlier['label_end']<r['entry_date']]),r['rank_score'])) for r in test]
        predictions=[(r,p) for r,p in predictions if p['status']!='INSUFFICIENT_DATA']
        evaluation[target]={'tested':len(predictions),'status':'ROLLING_MATURED_PAST_ONLY_2025' if predictions else 'INSUFFICIENT_EARLIER_CALIBRATION',
                            'brier':sum((p['targets'][target]['estimate']-r[target])**2 for r,p in predictions)/len(predictions) if predictions else None,
                            'mean_estimate':sum(p['targets'][target]['estimate'] for r,p in predictions)/len(predictions) if predictions else None,
                            'observed_rate':sum(r[target] for r,p in predictions)/len(predictions) if predictions else None}
    return {'reference':reference,'chronological_2025':evaluation,'rows':rows,'unknown_or_entry_rejected':gaps,'provider_requests':0}
