from smg.shortability import current_assets
from smg.evidence_archive import EvidenceArchiver
from smg.storage import Store
from smg.demo import NOW


def test_borrow_lookup_timeout_labels_unqueried_symbols_unavailable(monkeypatch):
    clock={'now':0};monkeypatch.setattr('time.monotonic',lambda:clock['now'])
    class Http:
        calls=[]
        def json(self,url,**kw):
            self.calls.append(url);clock['now']+=2
            return {'tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'}
    http=Http();result=current_assets(http,['AAA','BBB'],max_seconds=1)
    assert len(http.calls)==1
    assert result['assets']['AAA']['borrow_available'] is True
    assert result['assets']['BBB']=={'status':'UNAVAILABLE','reason':'ASSET_LOOKUP_TIME_BUDGET'}


def test_enrichment_timeout_leaves_unprocessed_symbols_pending(tmp_path,monkeypatch):
    clock={'now':0};monkeypatch.setattr('time.monotonic',lambda:clock['now'])
    monkeypatch.setattr('smg.evidence_archive.collect_sentiment',lambda *a,**kw:{'status':'UNAVAILABLE'})
    class Http:
        def json(self,url,**kw):
            if 'company_tickers' in url:return {'fields':[],'data':[]}
            clock['now']+=2;return {'facts':{}}
    store=Store(tmp_path/'budget.db');archiver=EvidenceArchiver(Http(),store,{}, {})
    one=archiver.collect_daily({'AAA':'1','BBB':'2'},NOW,max_symbols=8,max_seconds=1)
    assert one['processed_symbols']==['AAA'] and one['pending_after']==1
    assert 'ENRICHMENT_TIME_BUDGET' in one['failures']
    assert not store.get('evidence_daily:'+str(NOW.date())+':BBB')
    two=archiver.collect_daily({'AAA':'1','BBB':'2'},NOW,max_seconds=1)
    assert two['processed_symbols']==['BBB'] and two['pending_after']==0
