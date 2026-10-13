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


@pytest.mark.parametrize('status',[500,502,503,504])
def test_temporary_http_reads_retry_but_mutations_do_not(monkeypatch,status):
    monkeypatch.setattr('smg.transport.time.sleep',lambda _:None)
    class Session:
        def __init__(self):self.calls=0
        def request(self,*a,**kw):
            self.calls+=1
            return SimpleNamespace(status_code=status if self.calls==1 else 200,headers={})
    http=Http();http.session=Session()
    assert http.response('https://api.github.com/test').status_code==200 and http.session.calls==2
    http.session=Session()
    with pytest.raises(ProviderError):http.response('https://api.github.com/test',method='PUT')
    assert http.session.calls==1


def test_read_retry_budget_and_genuine_denial_remain_visible(monkeypatch):
    monkeypatch.setattr('smg.transport.time.sleep',lambda _:None)
    class Session:
        def __init__(self,status):self.status=status;self.calls=0
        def request(self,*a,**kw):
            self.calls+=1
            return SimpleNamespace(status_code=self.status,headers={},json=lambda:{})
    http=Http();http.session=Session(504)
    with pytest.raises(ProviderError,match='504'):http.response('https://api.github.com/test')
    assert http.session.calls==3
    http.session=Session(403)
    with pytest.raises(ProviderError,match='ACCESS_DENIED'):http.response('https://data.alpaca.markets/test')
    assert http.session.calls==1


@pytest.mark.parametrize('status',[None,500,502,503,504])
@pytest.mark.parametrize('concurrent',[False,True])
def test_failed_checkpoint_reconciles_remote_before_guarded_retry(tmp_path,monkeypatch,status,concurrent):
    monkeypatch.setenv('GITHUB_ACTIONS','false')
    store=Store(tmp_path/'state');store.put('claim','new')
    class HTTP:
        def __init__(self):self.puts=[]
        def json(self,url,**kw):
            if kw.get('method')=='PUT':
                self.puts.append(kw['body']['sha'])
                if len(self.puts)==1:raise ProviderError('api.github.com',status)
                return {'content':{'sha':'accepted'}}
            return {'sha':'other-writer' if concurrent else 'old'}
    http=HTTP();b=GitHubState(http,'o/r','fixture');b.sha='old';b.branch_exists=True
    if concurrent:
        with pytest.raises(ProviderError):b.checkpoint(store)
        assert http.puts==['old'] and b.sha=='old'
    else:
        b.checkpoint(store);assert http.puts==['old','old'] and b.sha=='accepted'


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


@pytest.mark.parametrize('changed',[False,True])
def test_compressed_git_read_verifies_blob_and_preserves_checkout(tmp_path,monkeypatch,changed):
    source=Store(tmp_path/'source');source.put('known',1);content=source.path.read_bytes()
    digest=GitHubState.blob_sha(content);calls=[]
    def run(command,**kwargs):
        args=command[1:];calls.append(args)
        value=b''
        if args[:3]==['remote','get-url','origin']:value=b'https://github.com/o/r.git'
        elif args[0]=='rev-parse':value=digest.encode()
        elif args[0]=='cat-file':value=content
        return SimpleNamespace(returncode=0,stdout=value,stderr=b'')
    monkeypatch.setattr('subprocess.run',run);b=GitHubState(None,'o/r','fixture');path=tmp_path/'runtime/state.sqlite';path.parent.mkdir();path.write_bytes(b'preserve')
    if changed:
        with pytest.raises(ProviderError,match='STATE_SHA_CONFLICT'):b.git_restore(path,'a'*40)
        assert path.read_bytes()==b'preserve'
    else:
        b.git_restore(path,digest);assert path.read_bytes()==content and b.sha==digest and b.writer_transport=='git'
    assert not any(a[0] in ['checkout','reset','push'] for a in calls)


def test_hosted_transient_api_restore_uses_compressed_fallback_only_for_transients(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_ACTIONS','true');calls=[]
    monkeypatch.setattr(GitHubState,'git_restore',lambda self,path,expected:calls.append(expected))
    class HTTP:
        status=504
        def json(self,*a,**kw):raise ProviderError('api.github.com',self.status)
        def response(self,*a,**kw):raise AssertionError('unexpected')
    http=HTTP();b=GitHubState(http,'o/r','fixture');b.restore(tmp_path/'s.db');assert calls==[None]
    http.status=403
    with pytest.raises(ProviderError):b.restore(tmp_path/'s.db')
    assert calls==[None]


def test_hosted_failed_write_can_reconcile_by_git_when_contents_api_is_unavailable(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_ACTIONS','true');calls=[]
    store=Store(tmp_path/'state');store.put('claim','new')
    class HTTP:
        def json(self,*a,**kw):
            assert kw['method']=='PUT';raise ProviderError('api.github.com',504)
    def reconcile(self,store,content):calls.append(self.sha)
    monkeypatch.setattr(GitHubState,'git_checkpoint',reconcile)
    b=GitHubState(HTTP(),'o/r','fixture');b.sha='original';b.branch_exists=True;b.checkpoint(store)
    assert calls==['original']


def test_large_hosted_write_uses_same_guarded_git_transport_without_api_put(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_ACTIONS','true');calls=[]
    class HTTP:
        def json(self,*a,**kw):raise AssertionError('Large body must not use Contents PUT')
    data=b'SQLite format 3\0'+b'x'*(8*1024*1024)
    path=tmp_path/'state.sqlite';path.write_bytes(data)
    store=SimpleNamespace(path=path)
    def save(self,store,content):
        assert GitHubState.decode_state(content)==data
        calls.append((self.sha,len(content)));self.sha=self.blob_sha(content);self.writer_transport='git'
    monkeypatch.setattr(GitHubState,'git_checkpoint',save)
    backend=GitHubState(HTTP(),'o/r','fixture');backend.sha='expected';backend.branch_exists=True
    backend.checkpoint(store);assert calls==[('expected',len(GitHubState.encode_state(data)))]
    backend.checkpoint(store);assert len(calls)==1


def test_large_restore_fetches_compressed_snapshot_with_pinned_sha(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_ACTIONS','true');calls=[]
    class HTTP:
        def json(self,*a,**kw):return {'sha':'a'*40,'size':42*1024*1024}
        def response(self,*a,**kw):raise AssertionError('Do not transfer large raw body')
    monkeypatch.setattr(GitHubState,'git_restore',lambda self,path,expected:calls.append(expected))
    GitHubState(HTTP(),'o/r','fixture').restore(tmp_path/'state.sqlite')
    assert calls==['a'*40]


def test_large_write_conflict_is_latched_and_cannot_retry_or_post(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_ACTIONS','true');calls=[]
    path=tmp_path/'state.sqlite';path.write_bytes(b'x'*(8*1024*1024))
    def reject(self,store,content):
        calls.append(self.sha);raise ProviderError('github.com',409,'STATE_SHA_CONFLICT')
    monkeypatch.setattr(GitHubState,'git_checkpoint',reject)
    backend=GitHubState(None,'o/r','fixture');backend.sha='expected';backend.branch_exists=True
    with pytest.raises(ProviderError,match='STATE_SHA_CONFLICT'):backend.checkpoint(SimpleNamespace(path=path))
    with pytest.raises(ProviderError):backend.checkpoint(SimpleNamespace(path=path))
    assert calls==['expected'] and backend.sha=='expected'


def test_lossless_compaction_keeps_claims_forecasts_and_observations(tmp_path):
    store=Store(tmp_path/'state.sqlite')
    store.put('uncertain_claim',{'status':'CLAIMED'})
    store.put('frozen_forecast',{'contract':'original','x':[1,2,3]})
    store.observe('borrow','ABC','2026-10-12T13:00:00+00:00','fixture',{'status':'UNKNOWN'})
    store.put('unused_fixture','x'*(9*1024*1024));store.delete('unused_fixture')
    before=store.path.stat().st_size
    assert store.compact_if_wasteful()
    assert store.path.stat().st_size<before
    assert store.get('uncertain_claim')=={'status':'CLAIMED'}
    assert store.get('frozen_forecast')=={'contract':'original','x':[1,2,3]}
    assert store.observations('borrow')[0]['value']=={'status':'UNKNOWN'}


def test_422_is_validation_rejection_not_rate_limit_and_is_not_retried(monkeypatch):
    monkeypatch.setattr('smg.transport.time.sleep',lambda _:None)
    class Session:
        calls=0
        def request(self,*a,**kw):
            self.calls+=1
            return SimpleNamespace(status_code=422,headers={},json=lambda:{'message':'Validation Failed'})
    http=Http();http.session=Session()
    with pytest.raises(ProviderError,match='API_VALIDATION_REJECTED'):http.response('https://api.github.com/test',method='PUT')
    assert http.session.calls==1


def test_compressed_state_restore_and_same_run_reuse_keep_both_sha_guards(tmp_path,monkeypatch):
    import gzip
    monkeypatch.setenv('GITHUB_RUN_ID','compressed-fixture')
    source=Store(tmp_path/'original.sqlite');source.put('uncertain_claim',{'status':'CLAIMED'})
    raw=source.path.read_bytes();encoded=gzip.compress(raw,mtime=0);calls=[]
    class HTTP:
        def json(self,*a,**kw):calls.append('metadata');return {'sha':GitHubState.blob_sha(encoded)}
        def response(self,*a,**kw):calls.append('body');return SimpleNamespace(content=encoded)
    http=HTTP();path=tmp_path/'restore.sqlite';backend=GitHubState(http,'o/r','fixture')
    backend.restore(path)
    assert path.read_bytes()==raw and backend.sha==backend.blob_sha(encoded)
    again=GitHubState(http,'o/r','fixture');again.restore(path)
    assert calls==['metadata','body'] and again.sha==backend.sha
    store=Store(path);assert store.get('uncertain_claim')['status']=='CLAIMED'
    store.put('unsaved',1)
    GitHubState(http,'o/r','fixture').restore(path)
    assert calls==['metadata','body','metadata','body'] and path.read_bytes()==raw
