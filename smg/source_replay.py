"""Independent, bounded source-triggered historical screening replay.

Reference events are opened only after discovery and market decisions finish.
This first pass covers selected independent filings and their next 20 sessions,
not the complete three-year market universe. Unknown historical cap/halts stay gaps.
"""
import csv,hashlib,json,os,re,sqlite3,time
from collections import Counter,defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from bs4 import BeautifulSoup
from .backtest import START,END,public_at,decision_time,prior_sessions,write_json
from .cli import settings
from .live_firms import extract_watch
from .models import Snapshot,HaltCheck
from .firm_first import firm_structure,evaluate_firm_first
from .rules import EntityList
from .market import calendar
from .transport import Http

UTC=timezone.utc

def select_sources(db_path,per_quarter=6):
    """Selection uses only dated firm-search hits; no ticker/reference input."""
    db=sqlite3.connect(db_path)
    rows=[(i,json.loads(s)) for i,s in db.execute('SELECT id,source FROM hits')];db.close()
    buckets=defaultdict(list)
    priority={'20-F':0,'10-K':1,'424B4':2,'6-K':3,'8-K':4}
    for identifier,s in rows:
        day=date.fromisoformat(s['file_date'])
        if not START<=day<=END or len(s.get('ciks',[]))!=1 or s['form'] not in priority:continue
        buckets[(day.year,(day.month-1)//3)].append((identifier,s))
    selected=[]
    for quarter,items in sorted(buckets.items()):
        used=set()
        for identifier,s in sorted(items,key=lambda x:(priority[x[1]['form']],x[1]['file_date'],x[0])):
            if s['ciks'][0] in used:continue
            selected.append((identifier,s));used.add(s['ciks'][0])
            if len(used)>=per_quarter:break
    return selected

def parse_source(identifier,src,raw,entries):
    accession,filename=identifier.split(':',1)
    url=f"https://www.sec.gov/Archives/edgar/data/{int(src['ciks'][0])}/{accession.replace('-','')}/{filename}"
    soup=BeautifulSoup(raw,'html.parser')
    symbols={e.get_text(' ',strip=True) for e in soup.find_all(attrs={'name':'dei:TradingSymbol'})}
    exchange_facts={e.get_text(' ',strip=True).upper() for e in soup.find_all(attrs={'name':'dei:SecurityExchangeName'})}
    names=[e.get_text(' ',strip=True) for e in soup.find_all(attrs={'name':'dei:EntityRegistrantName'})]
    for e in soup(['script','style','ix:header']):e.decompose()
    text=' '.join(soup.get_text(' ',strip=True).split())
    symbols|=set(re.findall(r'(?:Nasdaq|NASDAQ|NYSE)\s*[:：]\s*([A-Z]{1,6})\b',text))
    symbols|=set(re.findall(r'(?:trading |ticker |trading ticker )?symbol\s+[“"\']([A-Z]{1,6})[”"\']',text))
    exchange='XNYS' if exchange_facts & {'NYSE','XNYS'} else 'XNAS' if exchange_facts & {'NASDAQ','XNAS'} else None
    if exchange is None:
        if re.search(r'(?:listed|trade[sd]?|trading)\s+(?:on|in)\s+(?:the\s+)?Nasdaq',text,re.I):exchange='XNAS'
        elif re.search(r'(?:listed|trade[sd]?|trading)\s+(?:on|in)\s+(?:the\s+)?New York Stock Exchange',text,re.I):exchange='XNYS'
    if len(symbols)!=1 or exchange is None:return None,'SOURCE_SYMBOL_OR_EXCHANGE_UNRESOLVED'
    doc=dict(url=url,text=text,date=src['file_date'],sha256=hashlib.sha256(raw.encode()).hexdigest())
    known=public_at({'filed_at':src['file_date']})
    c=extract_watch(dict(cik=src['ciks'][0],ticker=next(iter(symbols)),name=names[0] if names else 'Issuer CIK '+src['ciks'][0],exchange=exchange),[doc],known,entries)
    return c,'FIRM_CANDIDATE_EXTRACTED' if c else 'NO_ATTACHED_LISTED_FIRM_ROLE_RECOGNIZED'

def main():
    root=Path.cwd();cfg,entries=settings(root);entities=EntityList(entries)
    indexes=list((root/'backtest/runtime').rglob('firm-search.sqlite'))
    if not indexes:raise ValueError('Independent SEC firm-search checkpoint is required')
    selected=select_sources(indexes[0]);http=Http();started=time.monotonic()
    cache=root/'backtest/runtime/source-replay';cache.mkdir(parents=True,exist_ok=True)
    candidates=[];sources=[]
    for identifier,src in selected:
        if time.monotonic()-started>240:break
        accession,filename=identifier.split(':',1)
        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession) or '..' in filename:continue
        url=f"https://www.sec.gov/Archives/edgar/data/{int(src['ciks'][0])}/{accession.replace('-','')}/{filename}"
        path=cache/(hashlib.sha256(url.encode()).hexdigest()+'.html')
        try:
            if not path.exists():path.write_text(http.text(url,headers={'User-Agent':os.environ['SEC_USER_AGENT']}),encoding='utf8')
            c,status=parse_source(identifier,src,path.read_text(encoding='utf8'),entries)
            sources.append(dict(id=identifier,filed_at=src['file_date'],status=status,ticker=c.ticker if c else None,source_url=url))
            if c:candidates.append(c)
        except Exception as exc:sources.append(dict(id=identifier,status='SOURCE_ERROR',error_type=type(exc).__name__))
    jobs=defaultdict(list)
    for c in candidates:
        known=public_at({'filed_at':str(c.event_date)})
        if known.date()>END:continue
        days=calendar(known.year).sessions_in_range(str(known.date()),str(min(END,known.date()+timedelta(days=60))))
        times=[decision_time(s.date(),cfg) for s in days]
        times=[t for t in times if t and t>=known][:20]
        for now in times:jobs[now].append(c)
    records=[];market_requests=0;headers={'APCA-API-KEY-ID':os.environ['ALPACA_API_KEY'],'APCA-API-SECRET-KEY':os.environ['ALPACA_SECRET_KEY']}
    for now,group in sorted(jobs.items()):
        if time.monotonic()-started>600:break
        effective=now-timedelta(minutes=16)
        query=dict(symbols=','.join(sorted({c.ticker for c in group})),timeframe='1Min',start=(effective-timedelta(minutes=5)).isoformat(),
                   end=(effective-timedelta(minutes=1)).isoformat(),asof=str(now.date()),feed='sip',adjustment='raw',limit=10000)
        path=cache/(hashlib.sha256(json.dumps(query,sort_keys=True).encode()).hexdigest()+'.json')
        try:
            if path.exists():data=json.loads(path.read_text())
            else:
                data=http.json('https://data.alpaca.markets/v2/stocks/bars',params=query,headers=headers);market_requests+=1
                if data.get('next_page_token'):raise ValueError('UNEXPECTED_SAMPLE_PAGINATION')
                write_json(path,data)
        except Exception as exc:
            for c in group:records.append(dict(ticker=c.ticker,decision_at=now.isoformat(),status='DATA_GAP',reasons=['MARKET_PROVIDER_ERROR:'+type(exc).__name__],source_date=str(c.event_date)))
            continue
        for original in group:
            # Re-evaluate known source facts; this does not certify later context coverage.
            c=original.model_copy(update={'reviewed_at':now});structure=firm_structure(c,cfg,entities,now)
            rows=(data.get('bars') or {}).get(c.ticker,[]);s=None
            if rows:
                last=max(rows,key=lambda r:r['t']);observed=datetime.fromisoformat(last['t'].replace('Z','+00:00'))
                if observed<=effective-timedelta(minutes=1):
                    s=Snapshot(asof=effective,price_time=observed,price=last['c'],monthly_return=None,one_day_return=None,five_day_return=None,
                        drawdown_pct=0,rvol=None,rvol20=None,baseline_sessions=0,cumulative_volume=0,baseline_volume=None,
                        source_url='https://data.alpaca.markets/v2/stocks/bars',feed='sip',declared_delay_minutes=16,flags=['CONTEXT_METRICS_NOT_CALCULATED'])
            h=HaltCheck(checked_at=now,status='UNKNOWN',reason='Historical halt archive unavailable',source_url='')
            result=evaluate_firm_first(c,cfg,entities,now,s,h)
            gaps=['HISTORICAL_MARKET_CAP_NOT_VERIFIED','HISTORICAL_HALT_NOT_VERIFIED','LATER_FILING_CONTEXT_NOT_CERTIFIED','SYMBOL_INTERVAL_NOT_CERTIFIED']
            firm_price=structure.status=='STRUCTURAL_MATCH' and s is not None and s.price>3 and 0<=(effective-s.price_time).total_seconds()<=300
            records.append(dict(ticker=c.ticker,cik=c.cik,decision_at=now.isoformat(),status=result.status,reasons=result.reasons,
                source_date=str(c.event_date),source_url=c.matches[0].evidence.url,firms=[m['name'] for m in structure.matches],
                raw_price=s.price if s else None,firm_and_price_match=firm_price,unresolved=gaps,
                review_scope='Source-triggered first-20-session sample; no full context or eligibility certification'))
    # Holdout boundary: labels are first read here, after all selections/decisions.
    with (root/'backtest/reference_events.csv').open() as stream:events=list(csv.DictReader(stream))
    comparisons=[]
    for e in events:
        prior=set(prior_sessions(date.fromisoformat(e['event_date']),20))
        before=[r for r in records if r['ticker']==e['ticker'] and date.fromisoformat(r['decision_at'][:10]) in prior]
        partial=[r for r in before if r.get('firm_and_price_match')]
        result='CONDITIONAL_FIRM_AND_PRICE_MATCH' if partial else 'SAMPLED_WITHOUT_FIRM_PRICE_MATCH' if before else 'NOT_COVERED_BY_THIS_BATCH'
        comparisons.append(dict(event_id=e['event_id'],ticker=e['ticker'],event_date=e['event_date'],result=result,
            sampled_decisions=len(before),first_conditional_match=partial[0]['decision_at'] if partial else '',
            unresolved='Market cap, historical halts, later context and symbol intervals remain unverified'))
    out=root/'reports/source-replay';out.mkdir(parents=True,exist_ok=True)
    write_json(out/'sources.json',sources);write_json(out/'decisions.json',records)
    with (out/'event_comparison.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(comparisons[0]));writer.writeheader();writer.writerows(comparisons)
    summary=dict(status='PARTIAL_SOURCE_TRIGGERED_REPLAY',start=str(START),end=str(END),source_selection='Six independent CIKs per quarter; annual filings then priced IPO/event filings; no reference input',
        selected_sources=len(selected),sources_processed=len(sources),extracted_candidates=len(candidates),candidate_symbols=sorted({c.ticker for c in candidates}),
        evaluated_decisions=len(records),planned_decisions=sum(len(v) for v in jobs.values()),market_requests=market_requests,
        screening_counts=dict(Counter(r['status'] for r in records)),comparison_counts=dict(Counter(r['result'] for r in comparisons)),
        conditional_reference_symbols=sorted({r['ticker'] for r in comparisons if r['result']=='CONDITIONAL_FIRM_AND_PRICE_MATCH'}),
        verified_detections=0,verified_misses=None,full_detection_rate=None,universe_complete=False,
        limitations=['Partial independently selected source sample, not a full daily universe replay','No historical cap/halts or complete source-context certification','Raw historical prices used for the $3 gate; no split-adjusted future price leakage','Conditional firm-price matches are not eligible alerts'])
    write_json(out/'summary.json',summary);print(json.dumps(summary))

if __name__=='__main__':main()
