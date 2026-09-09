from datetime import timedelta
import pytest
from smg.cloud_dispatch import bundle,dispatch_key,endpoint_url
from smg.demo import NOW
from test_firm_first import run,CFG

def test_bundle_preserves_checks_and_embed_from_real_evaluation():
    e=run();cfg=CFG.model_copy(update={'screening_profile':'firm_first'})
    result=bundle([e],NOW,NOW+timedelta(seconds=90),cfg)
    item=result['items'][0]
    assert item['ticker']==e.candidate.ticker and item['firm_matches']==len(e.matches)
    assert item['halt_status']=='CLEAR' and item['classification_evidence']
    assert item['payload']['embeds'][0]['title'].startswith(e.candidate.ticker)
    e.halt.status='UNKNOWN'
    assert bundle([e],NOW,NOW+timedelta(seconds=90),cfg)['items']==[]

def test_stale_at_target_is_not_uploaded_as_qualified():
    e=run();e.snapshot.price_time-=timedelta(minutes=4)
    cfg=CFG.model_copy(update={'screening_profile':'firm_first'})
    assert bundle([e],NOW,NOW+timedelta(seconds=90),cfg)['items']==[]

def test_dispatcher_address_and_secret_derivation():
    assert endpoint_url('https://dudebot-dispatch.example.workers.dev/')=='https://dudebot-dispatch.example.workers.dev'
    for url in ['http://a.workers.dev','https://a.workers.dev.evil.com','https://x@a.workers.dev','https://a.workers.dev/prepare']:
        with pytest.raises(ValueError):endpoint_url(url)
    assert len(dispatch_key('fake-secret'))==64
    assert dispatch_key('fake-secret')!=dispatch_key('different-secret')

def test_hosted_seed_requires_reviewed_firm_structure_and_preserves_evidence():
    from smg.cloud_dispatch import seed_candidates
    from test_live_firms import watch,ENTRIES
    from smg.rules import EntityList
    c=watch();c.matches[0].evidence.url='https://www.sec.gov/Archives/edgar/data/1/report.htm'
    packet=seed_candidates([c],NOW,CFG,EntityList(ENTRIES))
    assert packet['candidates'][0]['ticker']==c.ticker
    assert packet['candidates'][0]['firms'][0]['role']=='auditor'
    c.reviewed_at-=timedelta(hours=27)
    assert seed_candidates([c],NOW,CFG,EntityList(ENTRIES))['candidates']==[]
