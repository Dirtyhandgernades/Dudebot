"""Point-in-time daily outcome review; never selects a trade with future prices."""
from collections import Counter
from datetime import date,datetime,timedelta,timezone
import json

URL='https://data.alpaca.markets/v2/stocks/bars'

def record_scan(store,all_candidates,evaluations,now):
    day=str(now.date())
    firm=sorted({c.ticker for c in all_candidates if c.pipeline=='FIRM_WATCH'})
    store.put('watch_census:'+day,{'at':now.isoformat(),'firm_symbols':firm})
    for e in evaluations:
        key='scan_day:'+day+':'+e.candidate.pipeline+':'+e.candidate.ticker
        store.put(key,{'at':now.isoformat(),'ticker':e.candidate.ticker,'pipeline':e.candidate.pipeline,
            'status':e.status,'reasons':e.reasons,'price':e.snapshot.price if e.snapshot else None,
            'borrow':(e.shortability or {}).get('borrow_status')})

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
    rows=[]
    for symbol in sorted(symbols):
        series=sorted((d,b) for d,b in bars.get(symbol,{}).items() if day<=d<=today)
        base=next((b for d,b in series if d==day),None)
        future=[(d,b) for d,b in series if d>day][:3]
        e=by_symbol.get(symbol)
        record={'ticker':symbol,'pipeline':(e or {}).get('pipeline','FIRM_WATCH'),
            'scan_status':(e or {}).get('status','NOT_SELECTED_FOR_SCAN'),
            'scan_reasons':(e or {}).get('reasons',['FIRM_SCAN_CAPACITY']),
            'alert_sent':symbol in sent,'signal_close':base.get('c') if base else None,
            'followup_sessions':len(future),'three_session_complete':len(future)==3}
        if base and base.get('c',0)>0 and future:
            record['next_close_change_pct']=round(100*(future[0][1]['c']/base['c']-1),2)
            record['worst_followup_close_change_pct']=round(100*(min(b['c'] for _,b in future)/base['c']-1),2)
            record['outcome']='MISSED_20PCT_CLOSE_DROP' if record['worst_followup_close_change_pct']<=-20 and symbol not in sent else 'FLAGGED_20PCT_CLOSE_DROP' if record['worst_followup_close_change_pct']<=-20 else 'NO_20PCT_CLOSE_DROP'
        else:record['outcome']='DATA_GAP'
        rows.append(record)
    return rows

def review(store,http,headers,now):
    today=str(now.date());days=sorted({key.split(':')[1] for key,_ in store.items('watch_census:')
        if str(now.date()-timedelta(days=10))<=key.split(':')[1]<today})
    symbols=sorted({symbol for day in days for symbol in store.get('watch_census:'+day,{}).get('firm_symbols',[])}|
        {v['ticker'] for day in days for _,v in store.items('scan_day:'+day+':')})
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
    return {'reviewed_at':now.isoformat(),'scan_days':len(days),'symbols':len(symbols),
        'market_requests':requests,'research_priority_symbols':priority[:8],'reviews':output,
        'limitations':['Close-to-close outcomes only; intraday rugs can be missed',
            'Borrow, market cap, halts and game availability are not reconstructed historically',
            'A missed outcome is diagnostic, not evidence that a short was executable',
            'Feedback changes research order only; it does not relax any live eligibility rule']}
