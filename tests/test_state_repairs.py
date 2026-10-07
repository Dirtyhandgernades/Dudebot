from types import SimpleNamespace
import pytest
from smg.storage import Store,GitHubState
from smg.transport import Http,ProviderError


def test_pinned_state_restore_retains_verified_conflict_sha(tmp_path):
    local=Store(tmp_path/'original.sqlite');local.put('key',{'value':3})
    content=local.path.read_bytes()
    class HTTP:
        def __init__(self):self.calls=[]
        def response(self,url,**kwargs):
            self.calls.append((url,kwargs));return SimpleNamespace(content=content)
        def json(self,url,**kwargs):
            self.calls.append((url,kwargs))
            if kwargs.get('method')=='PUT':return {'content':{'sha':'new'}}
            return {'sha':GitHubState.blob_sha(content)}
    http=HTTP();backend=GitHubState(http,'owner/repo','fixture')
    path=tmp_path/'restored.sqlite';backend.restore(path);restored=Store(path)
    assert restored.get('key')=={'value':3} and len(http.calls)==2
    assert http.calls[1][1]['headers']['Accept']=='application/vnd.github.raw+json'
    assert '/git/blobs/'+backend.blob_sha(content) in http.calls[1][0]
    backend.checkpoint(restored);assert len(http.calls)==2
    restored.put('another',1);backend.checkpoint(restored)
    assert len(http.calls)==3 and http.calls[-1][1]['body']['sha']==backend.blob_sha(content)


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


def test_state_conflict_never_overwrites_another_writer_or_retries_in_finally(tmp_path):
    store=Store(tmp_path/'state');store.put('claim','new')
    class HTTP:
        def __init__(self):self.puts=0
        def json(self,url,**kw):
            if kw.get('method')=='PUT':self.puts+=1;raise ProviderError('api.github.com',409)
            assert kw['headers']['Accept']=='application/vnd.github.object+json'
            return {'sha':'someone-elses-change'}
    http=HTTP();b=GitHubState(http,'o/r','fixture');b.sha='old';b.branch_exists=True
    with pytest.raises(ProviderError):b.checkpoint(store)
    with pytest.raises(ProviderError):b.checkpoint(store)
    assert http.puts==1 and b.sha=='old'


def test_state_accepts_exact_acknowledged_content_without_resending(tmp_path):
    store=Store(tmp_path/'state');store.put('claim','new');desired=GitHubState.blob_sha(store.path.read_bytes())
    class HTTP:
        def __init__(self):self.puts=0
        def json(self,url,**kw):
            if kw.get('method')=='PUT':self.puts+=1;raise ProviderError('api.github.com',403)
            return {'sha':desired}
    http=HTTP();b=GitHubState(http,'o/r','fixture');b.sha='old';b.branch_exists=True
    b.checkpoint(store);assert b.sha==desired and http.puts==1


def test_state_retries409_once_with_same_expected_sha_only(tmp_path):
    store=Store(tmp_path/'state');store.put('claim','new')
    class HTTP:
        def __init__(self):self.puts=[]
        def json(self,url,**kw):
            if kw.get('method')=='PUT':
                self.puts.append(kw['body']['sha'])
                if len(self.puts)==1:raise ProviderError('api.github.com',409)
                return {'content':{'sha':'accepted'}}
            return {'sha':'old'}
    http=HTTP();b=GitHubState(http,'o/r','fixture');b.sha='old';b.branch_exists=True
    b.checkpoint(store);assert http.puts==['old','old']


def test_immutable_blob_checksum_mismatch_does_not_replace_state(tmp_path):
    source=Store(tmp_path/'source');source.put('known',1);data=source.path.read_bytes()
    class HTTP:
        def json(self,*a,**kw):return {'sha':'a'*40}
        def response(self,*a,**kw):return SimpleNamespace(content=data)
    path=tmp_path/'restore';path.write_bytes(b'preserve')
    with pytest.raises(ValueError,match='checksum'):GitHubState(HTTP(),'o/r','fixture').restore(path)
    assert path.read_bytes()==b'preserve'


def test_transient_read_retries_and_secondary_limit_is_not_reported_as_permission(monkeypatch):
    import requests
    monkeypatch.setattr('smg.transport.time.sleep',lambda _:None)
    class Session:
        def __init__(self):self.calls=0
        def request(self,*a,**kw):
            self.calls+=1
            if self.calls==1:raise requests.exceptions.ChunkedEncodingError('broken stream')
            return SimpleNamespace(status_code=200,headers={})
    http=Http();http.session=Session()
    assert http.response('https://api.github.com/test').status_code==200 and http.session.calls==2
    class Limited:
        def __init__(self):self.calls=0
        def request(self,*a,**kw):
            self.calls+=1
            return SimpleNamespace(status_code=403,headers={},json=lambda:{'message':'You have exceeded a secondary rate limit.'})
    http.session=Limited()
    with pytest.raises(ProviderError,match='SECONDARY_RATE_LIMIT'):http.response('https://api.github.com/test')
    assert http.session.calls==1


def test_compressed_git_state_write_keeps_other_files_and_never_force_pushes(tmp_path,monkeypatch):
    store=Store(tmp_path/'runtime/state.sqlite');store.put('value',1)
    b=GitHubState(None,'o/r','fixture');b.sha='old';content=store.path.read_bytes();desired=b.blob_sha(content);calls=[]
    def run(command,**kwargs):
        args=command[1:];calls.append((args,kwargs))
        value=''
        if args[:3]==['remote','get-url','origin']:value='https://github.com/o/r.git'
        elif args[:2]==['rev-parse','FETCH_HEAD']:value='head'
        elif args[0]=='rev-parse':value='old'
        elif args[0]=='hash-object':value=desired
        elif args[0]=='write-tree':value='tree'
        elif args[0]=='commit-tree':value='commit'
        return SimpleNamespace(returncode=0,stdout=value.encode(),stderr=b'')
    monkeypatch.setattr('subprocess.run',run)
    b.git_checkpoint(store,content)
    assert b.sha==desired and b.writer_transport=='git'
    assert any(a[:2]==['read-tree','head'] for a,_ in calls)
    pushes=[a for a,_ in calls if a[0]=='push']
    assert pushes==[['push','--quiet','origin','commit:refs/heads/smg-state']]
    assert all('--force' not in a for a,_ in calls)
    assert any('GIT_INDEX_FILE' in kw['env'] for a,kw in calls if a[0]=='read-tree')
