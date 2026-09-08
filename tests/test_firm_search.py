import sqlite3
from datetime import date

from smg.firm_search import collect_firm_search,extract_associations,query_text


def test_firm_query_is_independent_of_reference_labels():
    entries={'auditor':{'SUPER':['Wei, Wei & Co. LLP']},'counsel':{'Listed':['Loeb and Loeb LLP']}}
    q=query_text(entries)
    assert 'Wei, Wei & Co. LLP' in q and 'Loeb and Loeb LLP' in q
    assert ' OR ' in q and 'reported_drop_pct' not in q


def test_search_resumes_next_query_without_repeating_completed_page(tmp_path,monkeypatch):
    monkeypatch.setenv('SEC_USER_AGENT','test test@example.com')
    calls=[]
    def response(self,url,**kwargs):
        p=kwargs['params'];calls.append(p)
        year=p['startdt'][:4]
        return {'hits':{'total':{'value':1,'relation':'eq'},'hits':[{'_id':year+':doc.htm',
            '_source':{'form':'20-F','file_date':p['startdt'],'ciks':['1']}}]}}
    monkeypatch.setattr('smg.firm_search.Http.json',response)
    entries={'auditor':{'Listed':['UHY']}}
    one=collect_firm_search(tmp_path,date(2025,7,28),entries,max_pages=1)
    two=collect_firm_search(tmp_path,date(2025,7,28),entries,max_pages=1)
    assert one['document_hits']==1 and two['document_hits']==2
    assert calls[0]['startdt']=='2025-01-01' and calls[1]['startdt']=='2024-01-01'
    assert not two['universe_complete']


def test_ambiguous_search_totals_split_instead_of_truncating(tmp_path,monkeypatch):
    monkeypatch.setenv('SEC_USER_AGENT','test test@example.com')
    monkeypatch.setattr('smg.firm_search.Http.json',lambda *a,**k:{'hits':{'total':{'value':10000,'relation':'gte'},'hits':[]}})
    r=collect_firm_search(tmp_path,date(2025,7,28),{'auditor':{'Listed':['UHY']}},max_pages=1)
    assert r['query_counts']['SPLIT']==1 and r['status']=='PARTIAL_FIRM_SEARCH'


def test_name_alone_is_not_a_verified_role():
    entries={'auditor':{'Listed':['UHY']}}
    assert extract_associations('UHY appears in this document without any role.',entries)==[]
    r=extract_associations('UHY was our auditor.',entries)
    assert r[0]['verification']=='AUTOMATED_ROLE_PROXIMITY_REQUIRES_REVIEW'


def test_server_error_splits_range_and_preserves_resume(tmp_path,monkeypatch):
    from smg.transport import ProviderError
    monkeypatch.setenv('SEC_USER_AGENT','test test@example.com')
    def fail(*args,**kwargs):raise ProviderError('efts.sec.gov',500)
    monkeypatch.setattr('smg.firm_search.Http.json',fail)
    entries={'auditor':{'Listed':['UHY']}}
    one=collect_firm_search(tmp_path,date(2025,7,28),entries,max_pages=1)
    assert one['pages_this_run']==1 and one['query_counts']['SPLIT']==1
    calls=[]
    def ok(*args,**kwargs):
        calls.append(kwargs['params'])
        return {'hits':{'total':{'value':0,'relation':'eq'},'hits':[]}}
    monkeypatch.setattr('smg.firm_search.Http.json',ok)
    two=collect_firm_search(tmp_path,date(2025,7,28),entries,max_pages=1)
    assert calls[0]['startdt']>'2025-01-01'
    assert two['query_counts']['DONE']==1
