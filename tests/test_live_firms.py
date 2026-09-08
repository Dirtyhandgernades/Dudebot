from datetime import timedelta
from pathlib import Path
import yaml
from smg.models import Config,HaltCheck
from smg.demo import NOW,snapshot
from smg.live_firms import extract_watch
from smg.rules import EntityList
from smg.firm_first import evaluate_firm_first
from smg.notify import digest,DiscordSender
from smg.storage import Store
from smg.transport import ProviderError

ENTRIES=yaml.safe_load(Path('config/entities.yaml').read_text())
CFG=Config(screening_profile='firm_first',surge_return_min_pct=12,ipo_low_priority_surge_max_pct=23)

def watch(text=None):
    text=text or 'We are a manufacturer of consumer products. Our ordinary shares trade on Nasdaq. Wei, Wei & Co. LLP, our independent registered public accounting firm, audited our accounts.'
    doc=dict(text=text,url='https://example.com/annual',date=str(NOW.date()),sha256='fixture')
    return extract_watch(dict(cik='1',ticker='TEST',name='Operating Company'),[doc],NOW,ENTRIES)

def test_firm_watch_unknown_terms_can_reach_live_digest():
    c=watch();assert c and c.is_acquisition_corp is False
    s=snapshot();s.asof-=timedelta(minutes=16);s.price_time-=timedelta(minutes=16)
    s.feed='sip';s.declared_delay_minutes=16;s.monthly_return=-5;s.rvol=.3
    h=HaltCheck(checked_at=NOW,status='CLEAR',reason='fixture',source_url='https://example.com/halts')
    e=evaluate_firm_first(c,CFG,EntityList(ENTRIES),NOW,s,h)
    assert e.status=='QUALIFIED' and e.rank[0]==-1
    payload=digest([e],NOW,CFG)
    assert 'FIRM-FIRST WATCH' in payload[0]['content']
    assert 'surge and RVOL floor passed' not in payload[0]['content']
    assert 'unavailable' in payload[0]['content']

def test_name_alone_and_denied_role_do_not_become_live_matches():
    assert watch('Wei, Wei & Co. LLP appears in a list.') is None
    assert watch('Wei, Wei & Co. LLP is not our auditor.') is None

def test_explicit_spac_description_excluded_even_with_business_language():
    c=watch('We are a special purpose acquisition company. We provide services for transactions. Our ordinary shares trade here. Wei, Wei & Co. LLP is our auditor.')
    assert c.is_acquisition_corp is True
    assert evaluate_firm_first(c,CFG,EntityList(ENTRIES),NOW).status=='EXCLUDED'

def test_activation_receipt_is_durable_no_ping_and_not_retried(tmp_path):
    class HTTP:
        def __init__(self):self.calls=[]
        def json(self,url,**kw):self.calls.append(kw);return {'id':'123','channel_id':'456'}
    http=HTTP();store=Store(tmp_path/'state.sqlite');checkpoints=[]
    sender=DiscordSender(http,'https://discord.com/api/webhooks/123/fake',store,lambda s:checkpoints.append(s.get('activation:v1')['status']))
    assert sender.activation('v1','Deployment receipt')['status']=='SENT'
    assert sender.activation('v1','Deployment receipt')['message_id']=='123'
    assert len(http.calls)==1 and http.calls[0]['body']['allowed_mentions']['parse']==[]
    assert checkpoints[0]=='CLAIMED'

def test_uncertain_activation_is_not_retried(tmp_path):
    class HTTP:
        calls=0
        def json(self,*a,**kw):self.calls+=1;raise ProviderError('discord.com')
    http=HTTP();sender=DiscordSender(http,'https://discord.com/api/webhooks/123/fake',Store(tmp_path/'s.db'),lambda s:None)
    assert sender.activation('v1','receipt')['status']=='DELIVERY_UNCERTAIN'
    assert sender.activation('v1','receipt')['status']=='DELIVERY_UNCERTAIN'
    assert http.calls==1

def test_context_backlog_resumes_without_downloading_reviewed_sources(tmp_path):
    from smg.live_firms import LiveFirmDiscovery
    from smg.extraction import LocalParser
    import pytest
    class Sec:
        calls=[]
        def document(self,url):
            self.calls.append(url)
            return dict(url=url,sha256='fixture',text='The company dismissed its auditor. We were a blank check company.')
    sec=Sec();store=Store(tmp_path/'context.db')
    cfg=CFG.model_copy(update={'filings_max_downloads_per_run':2})
    files=[dict(url='https://example.com/'+str(i),date=str(NOW.date())) for i in range(3)]
    one=LiveFirmDiscovery(sec,LocalParser(ENTRIES),store,cfg)
    with pytest.raises(ValueError,match='DOWNLOAD_BUDGET'):one.review_context(files)
    two=LiveFirmDiscovery(sec,LocalParser(ENTRIES),store,cfg)
    notes,acquisition=two.review_context(files)
    assert len(sec.calls)==3 and two.downloads==1
    assert len(notes)==3 and acquisition is not None

def test_new_filings_are_processed_while_backfill_cursor_is_older(tmp_path):
    from smg.live_firms import LiveFirmDiscovery
    from smg.extraction import LocalParser
    from smg.firm_search import query_text
    import hashlib
    class HTTP:
        def json(self,url,**kw):
            p=kw['params'];fresh=p['enddt']==str(NOW.date())
            hits=[{'_id':'0000000001-26-000001:annual.htm','_source':{'ciks':['1'],'file_date':str(NOW.date())}}] if fresh else []
            return {'hits':{'total':{'value':len(hits),'relation':'eq'},'hits':hits}}
    class Sec:
        http=HTTP();headers={}
        def universe(self):return [{'cik':1,'ticker':'ACTV','name':'Operating Company'}]
        def document(self,url):return dict(url=url,sha256='fixture',text='We are a manufacturer of consumer products. Our ordinary shares trade on Nasdaq. Wei, Wei & Co. LLP is our auditor.')
        def submissions(self,*a):return []
    store=Store(tmp_path/'fresh.db')
    store.put('firm_cursor',dict(version=hashlib.sha256(query_text(ENTRIES).encode()).hexdigest(),start='2025-01-01',end='2025-01-31',offset=0,done=False))
    results=LiveFirmDiscovery(Sec(),LocalParser(ENTRIES),store,CFG).run(NOW)
    assert len(results)==1 and results[0].ticker=='ACTV'
