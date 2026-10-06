from types import SimpleNamespace
import pytest
from smg.storage import Store,GitHubState
from smg.transport import Http,ProviderError


def test_raw_state_restore_is_one_call_and_retains_conflict_sha(tmp_path):
    local=Store(tmp_path/'original.sqlite');local.put('key',{'value':3})
    content=local.path.read_bytes()
    class HTTP:
        def __init__(self):self.calls=[]
        def response(self,url,**kwargs):
            self.calls.append((url,kwargs));return SimpleNamespace(content=content)
        def json(self,url,**kwargs):
            self.calls.append((url,kwargs));return {'content':{'sha':'new'}}
    http=HTTP();backend=GitHubState(http,'owner/repo','fixture')
    path=tmp_path/'restored.sqlite';backend.restore(path);restored=Store(path)
    assert restored.get('key')=={'value':3} and len(http.calls)==1
    assert http.calls[0][1]['headers']['Accept']=='application/vnd.github.raw+json'
    backend.checkpoint(restored);assert len(http.calls)==1
    restored.put('another',1);backend.checkpoint(restored)
    assert len(http.calls)==2 and http.calls[-1][1]['body']['sha']==backend.blob_sha(content)


def test_invalid_raw_state_does_not_overwrite_existing_file(tmp_path):
    class HTTP:
        def response(self,*args,**kwargs):return SimpleNamespace(content=b'{"error":"not sqlite"}')
    path=tmp_path/'state.sqlite';path.write_bytes(b'preserve')
    with pytest.raises(ValueError,match='not a SQLite'):GitHubState(HTTP(),'owner/repo','fixture').restore(path)
    assert path.read_bytes()==b'preserve'


def test_only_identical_same_workflow_state_can_reuse_local_checkpoint(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_RUN_ID','fixture-run')
    source=Store(tmp_path/'source.sqlite');source.put('known',1);content=source.path.read_bytes()
    class HTTP:
        def __init__(self):self.calls=0
        def response(self,*args,**kwargs):self.calls+=1;return SimpleNamespace(content=content)
    http=HTTP();path=tmp_path/'state.sqlite'
    GitHubState(http,'owner/repo','fixture').restore(path)
    again=GitHubState(http,'owner/repo','fixture');again.restore(path)
    assert http.calls==1 and again.sha==again.blob_sha(content)
    # Mutated local data cannot be mistaken for the saved remote checkpoint.
    store=Store(path);store.put('unsaved',2);store.db.close()
    GitHubState(http,'owner/repo','fixture').restore(path);assert http.calls==2
    monkeypatch.setenv('GITHUB_RUN_ID','different-run')
    GitHubState(http,'owner/repo','fixture').restore(path);assert http.calls==3


def test_retry_rate_limited_get_but_never_retry_mutation_or_wait_early(monkeypatch):
    waits=[];monkeypatch.setattr('smg.transport.time.sleep',waits.append)
    class Session:
        def __init__(self,responses):self.responses=iter(responses);self.calls=0
        def request(self,*args,**kwargs):self.calls+=1;return next(self.responses)
    rate=SimpleNamespace(status_code=403,headers={'Retry-After':'2'})
    ok=SimpleNamespace(status_code=200,headers={})
    http=Http();http.session=Session([rate,ok])
    assert http.response('https://api.github.com/test') is ok and http.session.calls==2 and 2 in waits
    http.session=Session([rate,ok])
    with pytest.raises(ProviderError,match='RATE_LIMIT'):http.response('https://api.github.com/test',method='PUT')
    assert http.session.calls==1
    http.session=Session([SimpleNamespace(status_code=429,headers={'Retry-After':'120'})])
    with pytest.raises(ProviderError,match='RATE_LIMIT'):http.response('https://api.github.com/test')
    assert 30 not in waits and 120 not in waits
    http.session=Session([SimpleNamespace(status_code=403,headers={})])
    with pytest.raises(ProviderError,match='ACCESS_DENIED'):http.response('https://api.github.com/test')
    assert http.session.calls==1
