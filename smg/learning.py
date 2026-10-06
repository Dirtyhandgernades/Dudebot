"""Point-in-time daily outcome review; never selects a trade with future prices."""
from collections import Counter
from datetime import date,datetime,timedelta,timezone
import json
from .market import calendar,session_bounds

URL='https://data.alpaca.markets/v2/stocks/bars'

def record_scan(store,all_candidates,evaluations,now):
    day=str(now.date())
    firm=sorted({c.ticker for c in all_candidates if c.pipeline=='FIRM_WATCH'})
    store.put('watch_census:'+day,{'at':now.isoformat(),'firm_symbols':firm})
    for e in evaluations:
        key='scan_day:'+day+':'+e.candidate.pipeline+':'+e.candidate.ticker
        previous=store.get(key,{})
        features=previous.get('feature_snapshot')
        if e.snapshot is not None:
            # Keep one latest timestamped feature snapshot per symbol/lane/day
            # for future point-in-time learning, without archiving every scan.
            features={'observed_at':now.isoformat()}
            for field in ('asof','price_time','price','monthly_return','five_day_return','one_day_return',
                          'drawdown_pct','rvol','rvol20','baseline_sessions','feed','declared_delay_minutes','flags','source_url'):
                value=getattr(e.snapshot,field,None)
                features[field]=value.isoformat() if isinstance(value,datetime) else value
        store.put(key,{'at':now.isoformat(),'ticker':e.candidate.ticker,'pipeline':e.candidate.pipeline,
            'status':e.status,'reasons':e.reasons,'price':e.snapshot.price if e.snapshot else None,
            'borrow':(e.shortability or {}).get('borrow_status'),
            'feature_snapshot':features,'first_observed_at':previous.get('first_observed_at',now.isoformat())})

def outcome_rows(store,bars,day,today):
    census=store.get('watch_census:'+day,{})
    evaluations=[v for _,v in store.items('scan_day:'+day+':')]
    by_symbol={}
    for value in evaluations:
        if value['ticker'] not in by_symbol or value['pipeline']=='FIRM_WATCH':
            by_symbol[value['ticker']]=value
    symbols=set(census.get('firm_symbols',[]))|set(by_symbol)
    sent={v.get('ticker') for _,v in store.items('trade_alert_history:'+day+':') if v.get('status')=='SENT'}
    sent.update(v.get('ticker') for _,v in store.items('trade_alert_state:')
        if v.get('status')=='SENT' and v.get('sent_at','')[:10]==day)
    start=date.fromisoformat(day)
    expected=[str(d.date()) for d in calendar(start.year).sessions_in_range(
        day,str(start+timedelta(days=15))) if str(d.date())>day][:3]
    rows=[]
    for symbol in sorted(symbols):
        series=bars.get(symbol,{})
        base=series.get(day)
        future=[(d,series[d]) for d in expected if d<=today and d in series]
        e=by_symbol.get(symbol)
        record={'ticker':symbol,'pipeline':(e or {}).get('pipeline','FIRM_WATCH'),
            'scan_status':(e or {}).get('status','NOT_SELECTED_FOR_SCAN'),
            'scan_reasons':(e or {}).get('reasons',['FIRM_SCAN_CAPACITY']),
            'alert_sent':symbol in sent,'signal_close':base.get('c') if base else None,
            'followup_sessions':len(future),'three_session_complete':len(future)==3,
            'expected_followup_sessions':expected,
            'missing_completed_sessions':[d for d in expected if d<=today and d not in series]}
        if base and base.get('c',0)>0 and future:
            record['next_close_change_pct']=round(100*(series[expected[0]]['c']/base['c']-1),2) if expected[0] in series else None
            change=min(b['c'] for _,b in future)/base['c']-1
            record['worst_followup_close_change_pct']=round(100*change,2)
            # Do not round a 19.999% decline into a 20% label, or call a
            # missing early session a complete three-session negative.
            hit=change<=-.20+1e-10
            record['outcome']=('MISSED_20PCT_CLOSE_DROP' if symbol not in sent else 'FLAGGED_20PCT_CLOSE_DROP') if hit else (
                'DATA_GAP' if record['missing_completed_sessions'] else
                'NO_20PCT_CLOSE_DROP' if record['three_session_complete'] else 'PENDING_3_SESSION_OUTCOME')
        elif base and base.get('c',0)>0 and not record['missing_completed_sessions']:
            record['outcome']='PENDING_3_SESSION_OUTCOME'
        else:record['outcome']='DATA_GAP'
        rows.append(record)
    return rows

def review(store,http,headers,now):
    effective=now-timedelta(minutes=16)
    bounds=session_bounds(now.date())
    last_day=now.date() if bounds is None or effective>=bounds[1] else now.date()-timedelta(days=1)
    today=str(last_day);days=sorted({key.split(':')[1] for key,_ in store.items('watch_census:')
        if str(now.date()-timedelta(days=10))<=key.split(':')[1]<today})
    symbols=sorted({symbol for day in days for symbol in store.get('watch_census:'+day,{}).get('firm_symbols',[])}|
        {v['ticker'] for day in days for _,v in store.items('scan_day:'+day+':')}|
        {v['ticker'] for _,v in store.items('forward_forecast:') if str(now.date()-timedelta(days=10))<=v['signal_date']<=today})
    bars={};requests=0
    for offset in range(0,len(symbols),100):
        params={'symbols':','.join(symbols[offset:offset+100]),'timeframe':'1Day',
            'start':str(now.date()-timedelta(days=11))+'T00:00:00Z',
            'end':(now-timedelta(minutes=16)).isoformat(),
            'feed':'sip','adjustment':'split','limit':10000,'sort':'asc'}
        seen=set()
        while True:
            data=http.json(URL,params=params,headers=headers);requests+=1
            for symbol,series in (data.get('bars') or {}).items():
                bars.setdefault(symbol,{}).update({bar['t'][:10]:bar for bar in series})
            token=data.get('next_page_token')
            if not token:break
            if token in seen:raise ValueError('Repeated Alpaca outcome-review page token')
            seen.add(token)
            params['page_token']=token
    raw_bars={};raw_failures=[]
    forward_symbols=sorted({v['ticker'] for _,v in store.items('forward_forecast:')
        if str(now.date()-timedelta(days=10))<=v['signal_date']<=today})
    for offset in range(0,len(forward_symbols),100):
        params={'symbols':','.join(forward_symbols[offset:offset+100]),'timeframe':'1Day',
                'start':str(now.date()-timedelta(days=11))+'T00:00:00Z','end':effective.isoformat(),
                'feed':'sip','adjustment':'raw','asof':'-','limit':10000,'sort':'asc'}
        seen=set()
        while True:
            try:data=http.json(URL,params=params,headers=headers);requests+=1
            except Exception as exc:
                raw_failures.append({'symbols':forward_symbols[offset:offset+100],'error_type':type(exc).__name__})
                break
            for symbol,series in (data.get('bars') or {}).items():
                raw_bars.setdefault(symbol,{}).update({bar['t'][:10]:bar for bar in series})
            token=data.get('next_page_token')
            if not token:break
            if token in seen:raise ValueError('Repeated raw forward-review page token')
            seen.add(token);params['page_token']=token
    output=[]
    for day in days:
        rows=outcome_rows(store,bars,day,today)
        counts=Counter(row['outcome'] for row in rows)
        item={'scan_date':day,'reviewed_at':now.isoformat(),'counts':dict(counts),
            'misses':[r for r in rows if r['outcome']=='MISSED_20PCT_CLOSE_DROP'],
            'data_gaps':[r for r in rows if r['outcome']=='DATA_GAP'],
            'all_rows':rows}
        store.put('outcome_review:'+day,item);output.append(item)
    recent=set(days[-2:]);priority=[]
    for item in reversed(output):
        if item['scan_date'] not in recent:continue
        for row in item['misses']:
            if row['pipeline']=='FIRM_WATCH' and row['ticker'] not in priority:
                priority.append(row['ticker'])
    store.put('learning_priority',{'reviewed_at':now.isoformat(),'firm_symbols':priority[:8],
        'basis':'Recent watched firm names with a >=20% subsequent close decline; research order only'})
    from .shadow import review as review_forward
    forward=review_forward(store,bars,today,now,raw_bars)
    return {'reviewed_at':now.isoformat(),'scan_days':len(days),'symbols':len(symbols),
        'market_requests':requests,'research_priority_symbols':priority[:8],'reviews':output,'frozen_forward':forward,
        'forward_raw_failures':raw_failures,
        'limitations':['Close-to-close outcomes only; intraday rugs can be missed',
            'Borrow, market cap, halts and game availability are not reconstructed historically',
            'A missed outcome is diagnostic, not evidence that a short was executable',
            'Feedback changes research order only; it does not relax any live eligibility rule']}
