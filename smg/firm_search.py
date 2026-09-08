"""Independent, resumable SEC full-text discovery from the configured firms.

Search hits and automatically extracted associations are research evidence,
not verified alerts. No reference-event ticker or decline enters discovery.
"""
import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import date,timedelta
from urllib.parse import quote

from bs4 import BeautifulSoup

from .extraction import name_pattern
from .transport import Http

FORMS={'424B3','424B4','424B5','20-F','10-K','6-K','8-K','F-1','S-1'}


def query_text(entries):
    names=sorted({name for groups in entries.values() for group in groups.values() for name in group})
    return ' OR '.join('"'+name.replace('"','')+'"' for name in names)


def collect_firm_search(state,end,entries,max_pages=200):
    from .backtest import fingerprint
    agent=os.environ.get('SEC_USER_AGENT','')
    if '@' not in agent:return {'status':'NOT_RUN','reason':'SEC_USER_AGENT_MISSING'}
    state.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(state/'firm-search.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS queries (key TEXT PRIMARY KEY, start TEXT, end TEXT, offset INTEGER, total INTEGER, status TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS hits (query_set TEXT, id TEXT, source TEXT, PRIMARY KEY(query_set,id))')
    query=query_text(entries); version=fingerprint({'q':query,'forms':sorted(FORMS),'end':str(end)})
    # Search recent years first, then historical firm associations back to 2001.
    for year in range(end.year,2000,-1):
        first=date(year,1,1);last=min(end,date(year,12,31));key=version+':'+str(first)+':'+str(last)
        db.execute('INSERT OR IGNORE INTO queries VALUES (?,?,?,?,?,?)',(key,str(first),str(last),0,None,'PENDING'))
    db.commit();http=Http();pages=0;errors=[];started=time.monotonic()
    try:
        while pages<max_pages and time.monotonic()-started<360:
            item=db.execute("SELECT key,start,end,offset FROM queries WHERE key LIKE ? AND status='PENDING' ORDER BY start DESC LIMIT 1",(version+':%',)).fetchone()
            if not item:break
            key,first,last,offset=item
            try:
                response=http.json('https://efts.sec.gov/LATEST/search-index',headers={'User-Agent':agent},params={
                    'q':query,'forms':','.join(sorted(FORMS)),'dateRange':'custom','startdt':first,'enddt':last,'from':offset})
                if response.get('timed_out') or response.get('_shards',{}).get('failed',0):
                    raise ValueError('INCOMPLETE_SEARCH_RESPONSE')
                block=response['hits'];total=block['total'];count=total['value'] if isinstance(total,dict) else total
                relation=total.get('relation','eq') if isinstance(total,dict) else 'eq'
                hits=block['hits'];pages+=1
                if count>=10000 or relation!='eq':
                    left=date.fromisoformat(first);right=date.fromisoformat(last)
                    if left==right:
                        with db:db.execute("UPDATE queries SET status='TRUNCATED',total=? WHERE key=?",(count,key))
                        continue
                    middle=left+(right-left)//2
                    with db:
                        db.execute("UPDATE queries SET status='SPLIT',total=? WHERE key=?",(count,key))
                        for a,b in [(left,middle),(middle+timedelta(days=1),right)]:
                            child=version+':'+str(a)+':'+str(b)
                            db.execute('INSERT OR IGNORE INTO queries VALUES (?,?,?,?,?,?)',(child,str(a),str(b),0,None,'PENDING'))
                    continue
                if not hits and offset<count:raise ValueError('EMPTY_SEARCH_PAGE_BEFORE_TOTAL')
                with db:
                    for hit in hits:
                        src=hit['_source']
                        if not first<=src['file_date']<=last:
                            raise ValueError('SEARCH_DATE_FILTER_MISMATCH')
                        if src.get('form','').removesuffix('/A') in FORMS:
                            db.execute('INSERT OR IGNORE INTO hits VALUES (?,?,?)',(version,hit['_id'],json.dumps(src)))
                    new_offset=offset+len(hits)
                    db.execute('UPDATE queries SET offset=?,total=?,status=? WHERE key=?',
                               (new_offset,count,'DONE' if new_offset>=count else 'PENDING',key))
            except Exception as exc:
                errors.append({'error_type':type(exc).__name__,'http_status':getattr(exc,'status',None),'start':first,'end':last,'offset':offset})
                # Some large EFTS result sets fail on later pages. Preserve hits
                # and retry smaller date ranges, with a bounded attempt count.
                if getattr(exc,'status',None) in {500,502,503,504} and first<last:
                    left=date.fromisoformat(first);right=date.fromisoformat(last)
                    middle=left+(right-left)//2
                    with db:
                        db.execute("UPDATE queries SET status='SPLIT' WHERE key=?",(key,))
                        for a,b in [(left,middle),(middle+timedelta(days=1),right)]:
                            child=version+':'+str(a)+':'+str(b)
                            db.execute('INSERT OR IGNORE INTO queries VALUES (?,?,?,?,?,?)',(child,str(a),str(b),0,None,'PENDING'))
                    pages+=1
                    if len(errors)<8:continue
                break
        counts=dict(db.execute('SELECT status,count(*) FROM queries WHERE key LIKE ? GROUP BY status',(version+':%',)).fetchall())
        return {'status':'SEARCH_INDEX_COMPLETE' if not counts.get('PENDING') and not counts.get('TRUNCATED') and not errors else 'PARTIAL_FIRM_SEARCH',
                'query_set':version,'date_start':'2001-01-01','date_end':str(end),'pages_this_run':pages,'query_counts':counts,
                'document_hits':db.execute('SELECT count(*) FROM hits WHERE query_set=?',(version,)).fetchone()[0],
                'errors':errors,'universe_complete':False,
                'limitations':['Exact configured-name search can miss aliases and OCR/text variants','Search hits require source and role review; metadata display names are not historical ticker mappings']}
    finally:db.close()


def extract_associations(text,entries):
    found=[]
    role_terms={'underwriter':r'underwrit|placement agent','auditor':r'audit|independent registered public accounting','counsel':r'counsel|legal matters|legal advis[oe]r'}
    for role,groups in entries.items():
        for category,names in groups.items():
            for name in names:
                for match in re.finditer(name_pattern(name),text,re.I):
                    passage=text[max(0,match.start()-300):min(len(text),match.end()+300)]
                    if re.search(role_terms[role],passage,re.I):
                        found.append({'name':name,'role':role,'category':category,'quote':passage,
                            'verification':'AUTOMATED_ROLE_PROXIMITY_REQUIRES_REVIEW'})
                        break
    return found


def audit_firm_hits(state,query_set,entries,max_documents=80):
    from .backtest import public_at,write_json
    db=sqlite3.connect(state/'firm-search.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS observations (query_set TEXT, id TEXT, result TEXT, PRIMARY KEY(query_set,id))')
    http=Http();errors=[];started=time.monotonic();processed=0
    try:
        jobs=db.execute('''SELECT id,source FROM hits WHERE query_set=? AND id NOT IN
            (SELECT id FROM observations WHERE query_set=?) ORDER BY json_extract(source,'$.file_date') DESC,id LIMIT ?''',
            (query_set,query_set,max_documents)).fetchall()
        for identifier,source in jobs:
            if time.monotonic()-started>300:break
            src=json.loads(source)
            if len(src.get('ciks',[]))!=1:
                result={'id':identifier,'status':'AMBIGUOUS_COISSUER','source':src}
            else:
                try:
                    accession,filename=identifier.split(':',1)
                    if '..' in filename or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession):
                        raise ValueError('UNRECOGNIZED_DOCUMENT_ID')
                    url=f"https://www.sec.gov/Archives/edgar/data/{int(src['ciks'][0])}/{accession.replace('-','')}/{quote(filename,safe='/')}"
                    cache=state/'firm-documents'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
                    if cache.exists():doc=json.loads(cache.read_text())
                    else:
                        raw=http.text(url,headers={'User-Agent':os.environ['SEC_USER_AGENT']})
                        doc={'url':url,'raw_text':raw,'sha256':hashlib.sha256(raw.encode()).hexdigest()}
                        write_json(cache,doc)
                    soup=BeautifulSoup(doc['raw_text'],'html.parser')
                    # Inline XBRL facts are dated source observations, not current search display names.
                    tickers=sorted({tag.get_text(' ',strip=True) for tag in soup.find_all(attrs={'name':'dei:TradingSymbol'})})
                    exchanges=sorted({tag.get_text(' ',strip=True) for tag in soup.find_all(attrs={'name':'dei:SecurityExchangeName'})})
                    for element in soup(['script','style','ix:header']):element.decompose()
                    text=' '.join(soup.get_text(' ',strip=True).split())
                    associations=extract_associations(text,entries)
                    result={'id':identifier,'cik':src['ciks'][0],'source_url':url,'filed_at':src['file_date'],
                        'known_at':public_at({'filed_at':src['file_date']}).isoformat(),'source_sha256':doc['sha256'],
                        'source_ticker_facts':tickers,'source_exchange_facts':exchanges,
                        'status':'FIRM_ROLE_REVIEW_LEAD' if associations else 'NO_ROLE_ASSOCIATION_RECOGNIZED',
                        'associations':associations,'hard_exclusion_status':'UNVERIFIED',
                        'gaps':['ROLE_SEMANTICS_REVIEW_REQUIRED','HISTORICAL_TICKER_INTERVAL_UNVERIFIED','SPAC_STATUS_REVIEW_REQUIRED','HISTORICAL_HALT_COVERAGE_MISSING']}
                except Exception as exc:
                    errors.append({'id':identifier,'error_type':type(exc).__name__,'http_status':getattr(exc,'status',None)})
                    if getattr(exc,'status',None) in {401,403,429}:break
                    continue
            with db:db.execute('INSERT INTO observations VALUES (?,?,?)',(query_set,identifier,json.dumps(result)))
            processed+=1
        records=[json.loads(r[0]) for r in db.execute('SELECT result FROM observations WHERE query_set=? ORDER BY id',(query_set,))]
        return {'status':'PARTIAL_ROLE_AUDIT','documents_this_run':processed,'documents_audited':len(records),
                'role_review_leads':sum(r['status']=='FIRM_ROLE_REVIEW_LEAD' for r in records),'errors':errors,
                'verified_detections':None},records
    finally:db.close()
