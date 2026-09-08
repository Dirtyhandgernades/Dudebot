"""Free SEC index discovery, incremental local parsing, and persisted review records."""
from datetime import date,timedelta
import re,json,hashlib,time
from .models import Candidate
from .rules import years_ago

class Discovery:
    def __init__(self,sec,parser,store,cfg):
        self.sec=sec;self.parser=parser;self.store=store;self.cfg=cfg
        self.issues=[];self.downloads=0
    def queue(self,now):
        universe=self.sec.universe();by_cik={}
        for r in universe:
            if not re.fullmatch('[A-Z]{5}',r['ticker']):by_cik.setdefault(str(r['cik']),[]).append(r)
        # Historical IPO leads come from prospectus filings, not an extra paid IPO calendar.
        since=years_ago(now.date(),self.cfg.ipo_max_age_years)
        through=self.store.get('ipo_index_through')
        if through:since=max(since,date.fromisoformat(through)-timedelta(days=2))
        ipo_rows=self.sec.quarterly_events(since,now.date(),set(by_cik),forms={'424B4'})
        direct_since=now.date()-timedelta(days=self.cfg.direct_offering_backfill_days)
        rows=self.sec.quarterly_events(direct_since,now.date(),set(by_cik))
        try:rows+=self.sec.current_events(set(by_cik))
        except Exception as exc:self.issues.append('Same-day SEC feed unavailable: '+type(exc).__name__)
        for pipeline,records in [('RECENT_IPO',ipo_rows),('DIRECT_OFFERING',rows)]:
            for row in records:
                choices=by_cik[row['cik']]
                if len(choices)!=1:
                    self.issues.append('Ambiguous share-class mapping for CIK '+row['cik']);continue
                u=choices[0];key='job:'+pipeline+':'+row['accession']
                self.store.put(key,dict(row,pipeline=pipeline,ticker=u['ticker'],name=u['name'],exchange='XNYS' if u.get('exchange')=='NYSE' else 'XNAS'))
        self.store.put('universe_asof',now.isoformat())
        self.store.put('ipo_index_through',str(now.date()))
    def docs_for(self,job,now):
        if self.downloads>=self.cfg.filings_max_downloads_per_run:raise RuntimeError('DOWNLOAD_BUDGET_REACHED')
        item=self.sec.document(job['url']);self.downloads+=1
        docs=[dict(item,date=job['date'],context_only=False)]
        text=item['text']
        if job['pipeline']=='RECENT_IPO' and not re.search(r'(?:our|its|the company.s) initial public offering|This is an initial public offering',text,re.I):return docs
        if job['pipeline']=='DIRECT_OFFERING' and not re.search(r'registered direct offering|direct (?:public )?offering',text,re.I):return docs
        since=min(date.fromisoformat(job['date'])-timedelta(days=30),now.date()-timedelta(days=800))
        filings=self.sec.submissions(job['cik'],since)
        annual=next((r for r in filings if r['form'] in {'20-F','10-K'}),None)
        near=[r for r in filings if r['form'] in {'6-K','8-K'} and abs((date.fromisoformat(r['date'])-date.fromisoformat(job['date'])).days)<=30]
        near=sorted(near,key=lambda r:abs((date.fromisoformat(r['date'])-date.fromisoformat(job['date'])).days))[:3]
        recent=[r for r in filings if r['form'] in {'6-K','8-K'} and r['date']>=str(now.date()-timedelta(days=7))][:2]
        extra=([annual] if annual else [])+near+recent
        for r in extra:
            if any(d['url']==r['url'] for d in docs):continue
            if self.downloads>=self.cfg.filings_max_downloads_per_run:raise RuntimeError('DOWNLOAD_BUDGET_REACHED')
            item=self.sec.document(r['url']);self.downloads+=1
            docs.append(dict(item,date=r['date'],context_only=True))
        return docs
    def run(self,now):
        started=time.monotonic();self.queue(now);parsed=0
        def order(item):
            key,job=item;done=self.store.get('processed:'+key,{})
            age=(now.date()-date.fromisoformat(job['date'])).days
            active=self.store.get('candidate:'+done['candidate_key']) if done.get('candidate_key') else None
            priority=0 if job['pipeline']=='DIRECT_OFFERING' or self.cfg.ipo_focus_days[0]<=age<=self.cfg.ipo_focus_days[1] else 1 if age<=365 else 2
            return (0 if active else 1,priority,bool(done),-date.fromisoformat(job['date']).toordinal())
        for key,job in sorted(self.store.items('job:'),key=order):
            if time.monotonic()-started>9*60 or parsed>=self.cfg.parser_max_filings_per_run:
                self.issues.append('RUN_BUDGET_REACHED; pending work retained');break
            last=self.store.get('processed:'+key,{})
            if last.get('checked_day')==str(now.date()):continue
            if last.get('not_applicable'):continue
            if job['pipeline']=='DIRECT_OFFERING' and job['date']<str(now.date()-timedelta(days=self.cfg.direct_offering_backfill_days)):continue
            if job['pipeline']=='RECENT_IPO' and job['date']<str(years_ago(now.date(),self.cfg.ipo_max_age_years)):continue
            try:
                docs=self.docs_for(job,now)
                candidate=self.parser.extract(job,docs,now);parsed+=1
                done={'checked_day':str(now.date()),'not_applicable':candidate is None}
                if candidate:
                    previous=self.store.get('candidate:'+candidate.key)
                    # Preserve the earliest verified original IPO date across prospectus updates.
                    if previous and candidate.pipeline=='RECENT_IPO' and previous.get('ipo_date'):
                        old=date.fromisoformat(previous['ipo_date'])
                        if candidate.ipo_date is None or old<candidate.ipo_date:
                            candidate.ipo_date=old;candidate.evidence['ipo_date']=Candidate.model_validate(previous).evidence['ipo_date']
                        # A later prospectus cannot replace the original transaction's price/size.
                        if date.fromisoformat(previous['event_date'])<candidate.event_date:
                            prior=Candidate.model_validate(previous)
                            for field in ['offer_price','offer_gross','currency','base_shares','terms_unambiguous','event_date']:
                                setattr(candidate,field,getattr(prior,field))
                            for field in ['offer_price','offer_gross','currency']:
                                if field in prior.evidence:candidate.evidence[field]=prior.evidence[field]
                    self.store.put('candidate:'+candidate.key,candidate.model_dump(mode='json'));done['candidate_key']=candidate.key
                self.store.put('processed:'+key,done)
            except Exception as exc:
                self.issues.append(job['ticker']+': '+str(exc) if isinstance(exc,(ValueError,RuntimeError)) else job['ticker']+': '+type(exc).__name__)
                if 'BUDGET_REACHED' in str(exc):break
        self.store.put('discovery_issues',self.issues)
        return self.candidates(now)
    def candidates(self,now):
        result=[]
        for _,raw in self.store.items('candidate:'):
            c=Candidate.model_validate(raw)
            if c.pipeline=='DIRECT_OFFERING' and c.event_date<now.date()-timedelta(days=self.cfg.direct_offering_backfill_days):continue
            result.append(c)
        return result
