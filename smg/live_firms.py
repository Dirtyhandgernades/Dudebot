"""Bounded current-filing firm discovery. No reference tickers or paid services."""
from datetime import date,timedelta
import hashlib,re,time
from urllib.parse import quote

from .models import Candidate,EntityMatch,Evidence
from .extraction import evidence,name_pattern,search
from .firm_search import query_text


def extract_watch(job,docs,now,entries):
    primary=docs[0];matches=[];proofs={};notes=[]
    for role,groups in entries.items():
        for names in groups.values():
            for name in names:
                pattern=name_pattern(name)
                # Require role language attached to the named party, not just
                # a name somewhere in the same filing or an unrelated adviser.
                roles={'auditor':r'(?:our\s+)?(?:independent registered public accounting firm|independent auditor|auditor)',
                       'counsel':r'(?:U\.?S\.?\s+)?(?:legal counsel|counsel|legal adviser)',
                       'underwriter':r'(?:sole |joint |lead |co-)?(?:underwriter|book.runner|placement agent)'}
                role_rx=roles[role]
                expressions=[pattern+r'[^;\n]{0,120}?(?:\b(?:acted|acting|serves|served|is|are|was|were|as)\b)[^;\n]{0,60}?'+role_rx,
                             role_rx+r'\s*[,(:-]?\s*(?:is|was|are|were|of)?\s*'+pattern,
                             pattern+r'\s*[,(:-]\s*(?:our\s+)?'+role_rx]
                hit=next((h for rx in expressions if (h:=search([primary],rx))),None)
                if not hit:continue
                passage=hit[0].group()
                if re.search(r'\b(?:not|terminated|dismissed|former|no longer)\b',passage,re.I):continue
                matches.append(EntityMatch(name=name,role=role,relationship='historical' if role=='underwriter' else 'current',evidence=hit[2]))
    if not matches:return None
    acquisition=search(docs,r'\b(?:we are|we were|the company is|the company was)\s+(?:a |an )?(?:blank.check company|special purpose acquisition company)\b')
    business=search(docs,r'\b(?:we|the company)\s+(?:(?:are|is)\s+(?:(?:a|an|the)\s+)?(?:[\w,-]+\s+){0,6}(?:provider|manufacturer|operator|developer|supplier|distributor)|(?:manufacture|manufactures|develop|develops|operate|operates|provide|provides|sell|sells)\s+[^.]{10,180})',re.I)
    classification=None
    if acquisition:classification=True;proofs['is_acquisition_corp']=acquisition[2]
    elif re.search(r'\bacquisition\s+corp(?:oration)?\b',job['name'],re.I):classification=True
    elif business:classification=False;proofs['is_acquisition_corp']=business[2]
    security=search([primary],r'\b(?:ordinary shares|common stock|common shares|American depositary shares)\b')
    if security:proofs['security_type']=security[2]
    for doc in docs[1:]:
        if search([doc],r'(?:dismissed|terminated|change.{0,30}|engaged|appointed).{0,90}(?:auditor|accounting firm|counsel|placement agent)',re.I):
            notes.append('RELATIONSHIP_CHANGE_REVIEW: '+doc['url'])
        if search([doc],r'ADS ratio|depositary share ratio|ticker change',re.I):notes.append('ADS ratio or ticker change requires review')
    return Candidate(pipeline='FIRM_WATCH',cik=job['cik'],ticker=job['ticker'],name=job['name'],event_id='FIRMS',
        exchange='XNAS',operations_country=None,ipo_date=None,event_date=date.fromisoformat(primary['date']),status='unknown',
        security_type='ADS' if security and 'depositary' in security[0].group().lower() else 'CS' if security else None,
        is_acquisition_corp=classification,offer_price=None,offer_gross=None,currency=None,base_shares=None,
        terms_unambiguous=False,matches=matches,evidence=proofs,notes=notes+['Current listed-firm watch; no transaction terms inferred.'],reviewed_at=now)


class LiveFirmDiscovery:
    def __init__(self,sec,parser,store,cfg):
        self.sec=sec;self.entries=parser.entities;self.store=store;self.cfg=cfg;self.issues=[];self.downloads=0

    def queue_hits(self,hits,universe,first,last):
        for hit in hits:
            src=hit['_source'];ciks=src.get('ciks',[])
            if len(ciks)!=1:continue
            cik=str(int(ciks[0]));choices=universe.get(cik,[])
            if len(choices)!=1:continue
            if not first<=src['file_date']<=last:raise ValueError('SEARCH_DATE_MISMATCH')
            acc,filename=hit['_id'].split(':',1)
            if '..' in filename or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):continue
            u=choices[0];job=dict(cik=cik,ticker=u['ticker'],name=u['name'],date=src['file_date'],
                url=f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-","")}/{quote(filename,safe="/")}')
            self.store.put('firm_job:'+hit['_id'],job)

    def review_context(self,filings):
        """Persist small review results per immutable SEC source, not full texts."""
        notes=[];acquisition=None
        for filing in filings:
            key='firm_context:'+hashlib.sha256(filing['url'].encode()).hexdigest()
            checked=self.store.get(key)
            if checked is None:
                if self.downloads>=self.cfg.filings_max_downloads_per_run:raise ValueError('DOWNLOAD_BUDGET')
                raw=self.sec.document(filing['url']);self.downloads+=1
                doc=dict(raw,date=filing['date']);flags=[]
                if search([doc],r'(?:dismissed|terminated|change.{0,30}|engaged|appointed).{0,90}(?:auditor|accounting firm|counsel|placement agent)',re.I):
                    flags.append('RELATIONSHIP_CHANGE_REVIEW: '+filing['url'])
                if search([doc],r'ADS ratio|depositary share ratio|ticker change',re.I):flags.append('ADS ratio or ticker change requires review')
                hit=search([doc],r'\b(?:we are|we were|the company is|the company was)\s+(?:a |an )?(?:blank.check company|special purpose acquisition company)\b')
                checked={'notes':flags,'acquisition_evidence':hit[2].model_dump(mode='json') if hit else None}
                self.store.put(key,checked)
            notes.extend(checked['notes'])
            if checked['acquisition_evidence']:acquisition=checked['acquisition_evidence']
        return list(dict.fromkeys(notes)),acquisition

    def run(self,now):
        started=time.monotonic();universe={}
        for u in self.sec.universe():
            if not re.fullmatch('[A-Z]{5}',u['ticker']):universe.setdefault(str(int(u['cik'])),[]).append(u)
        q=query_text(self.entries);version=hashlib.sha256(q.encode()).hexdigest()
        # New filings must not wait behind the historical backfill cursor.
        recent_start=str(now.date()-timedelta(days=2));recent_end=str(now.date())
        try:
            recent=self.sec.http.json('https://efts.sec.gov/LATEST/search-index',headers=self.sec.headers,params={
                'q':q,'forms':'20-F,10-K,424B4,424B5,6-K,8-K','dateRange':'custom',
                'startdt':recent_start,'enddt':recent_end,'from':0})
            if recent.get('timed_out') or recent.get('_shards',{}).get('failed'):raise ValueError('INCOMPLETE_SEARCH')
            hits=recent['hits']['hits'];total=recent['hits']['total'];total=total['value'] if isinstance(total,dict) else total
            self.queue_hits(hits,universe,recent_start,recent_end)
            if total>len(hits):self.issues.append('RECENT_SEARCH_PARTIAL; additional pages remain in backfill')
        except Exception as exc:self.issues.append('Recent firm search: '+type(exc).__name__)
        cursor=self.store.get('firm_cursor',{})
        if not cursor or cursor.get('version')!=version or (cursor.get('done') and cursor['end']!=str(now.date())):
            cursor={'version':version,'start':str(now.date()-timedelta(days=450)),'end':str(now.date()),'offset':0,'done':False}
        # Eight search pages and at most 60 source reviews per run preserve cost
        # and resume backlog. Discovery is not claimed to cover every issuer.
        for _ in range(8):
            if cursor['done']:break
            try:
                data=self.sec.http.json('https://efts.sec.gov/LATEST/search-index',headers=self.sec.headers,params={
                    'q':q,'forms':'20-F,10-K,424B4,424B5,6-K,8-K','dateRange':'custom',
                    'startdt':cursor['start'],'enddt':cursor['end'],'from':cursor['offset']})
                if data.get('timed_out') or data.get('_shards',{}).get('failed'):raise ValueError('INCOMPLETE_SEARCH')
                hits=data['hits']['hits'];total=data['hits']['total'];total=total['value'] if isinstance(total,dict) else total
                if total>=10000 and cursor['start']<cursor['end']:
                    first=date.fromisoformat(cursor['start']);last=date.fromisoformat(cursor['end']);middle=first+(last-first)//2
                    cursor.setdefault('pending',[]).append([str(first),str(middle)])
                    cursor.update(start=str(middle+timedelta(days=1)),offset=0,done=False)
                    self.store.put('firm_cursor',cursor);continue
                self.queue_hits(hits,universe,cursor['start'],cursor['end'])
                cursor['offset']+=len(hits);cursor['done']=cursor['offset']>=total
                if not hits and not cursor['done']:raise ValueError('EMPTY_SEARCH_PAGE')
                if cursor['done'] and cursor.get('pending'):
                    first,last=cursor['pending'].pop();cursor.update(start=first,end=last,offset=0,done=False)
                if cursor['offset']>=10000 and not cursor['done']:
                    self.issues.append('SEARCH_RESULT_LIMIT; historical/backfill coverage incomplete');break
                self.store.put('firm_cursor',cursor)
            except Exception as exc:
                self.issues.append('Firm search: '+type(exc).__name__);break
        # Prefer current issuers already watched; then the newest unseen sources.
        jobs=sorted(self.store.items('firm_job:'),key=lambda x:x[1]['date'],reverse=True)
        fresh=[j for j in jobs if not self.store.get('firm_checked:'+j[0])]
        refresh=[j for j in jobs if self.store.get('firm_checked:'+j[0]) and self.store.get('candidate:FIRM_WATCH:'+j[1]['cik']+':FIRMS')]
        # Reserve refresh capacity so an initial backfill cannot make all live
        # candidates stale. Keep new-source capacity in the same bounded run.
        jobs=refresh[:20]+fresh+refresh[20:]
        reviewed=set();count=0
        for key,job in jobs:
            if count>=60 or self.downloads>=self.cfg.filings_max_downloads_per_run or time.monotonic()-started>300:break
            if job['cik'] in reviewed or job['cik'] not in universe or len(universe[job['cik']])!=1:continue
            if self.store.get('firm_checked:'+key)==str(now.date()):continue
            try:
                doc=self.sec.document(job['url']);self.downloads+=1
                docs=[dict(doc,date=job['date'])]
                # Refresh current symbol from today's exchange universe; never
                # reset listing age or invent an IPO date after a rename.
                current=universe[job['cik']][0];job=dict(job,ticker=current['ticker'],name=current['name'])
                filings=self.sec.submissions(job['cik'],max(date.fromisoformat(job['date']),now.date()-timedelta(days=450)))
                changes=[f for f in filings if f['date']>job['date'] and f['form'] in {'8-K','6-K','20-F','10-K'}]
                context_notes,acquisition=self.review_context(changes)
                candidate=extract_watch(job,docs,now,self.entries);count+=1
                self.store.put('firm_checked:'+key,str(now.date()))
                if candidate:
                    candidate.notes+=context_notes
                    if acquisition:
                        candidate.is_acquisition_corp=True
                        candidate.evidence['is_acquisition_corp']=Evidence.model_validate(acquisition)
                    self.store.put('candidate:'+candidate.key,candidate.model_dump(mode='json'));reviewed.add(job['cik'])
            except Exception as exc:self.issues.append(job['ticker']+': '+type(exc).__name__)
        self.store.put('discovery_issues',self.issues)
        self.store.put('live_discovery',dict(at=now.isoformat(),profile='firm_first',reviewed=count,source_downloads=self.downloads,
            search_cursor=cursor,queued_jobs=len(jobs),coverage_complete=False))
        return [Candidate.model_validate(raw) for _,raw in self.store.items('candidate:FIRM_WATCH:') if raw['cik'] in universe]
