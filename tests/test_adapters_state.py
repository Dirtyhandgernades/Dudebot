from pathlib import Path
import base64
import pytest
from smg.storage import Store,GitHubState
from smg.transport import ProviderError
from smg.providers import Alpaca
from datetime import date,datetime,timezone,timedelta

class Responses:
    def __init__(self,items):self.items=iter(items);self.calls=[]
    def json(self,url,**kw):
        self.calls.append((url,kw));value=next(self.items)
        if isinstance(value,Exception):raise value
        return value

def test_market_pagination_and_consistent_free_feed():
    bar={'t':'2026-09-08T19:40:00Z','c':12,'h':13,'l':11,'v':1000}
    http=Responses([{'bars':{'ABCD':[bar]},'next_page_token':'page2'}, {'bars':{'ABCD':[dict(bar,t='2026-09-08T19:41:00Z')]}}])
    end=datetime(2026,9,8,19,44,tzinfo=timezone.utc)
    result=Alpaca(http,'test-key','test-secret').bars('ABCD',date(2026,5,1),end)
    assert len(result)==2 and result[-1].volume==1000
    for url,kwargs in http.calls:
        assert url=='https://data.alpaca.markets/v2/stocks/bars'
        assert kwargs['params']['feed']=='sip' and kwargs['params']['adjustment']=='split'
        assert kwargs['params']['end']==end.isoformat()
        assert kwargs['headers']=={'APCA-API-KEY-ID':'test-key','APCA-API-SECRET-KEY':'test-secret'}
    assert 'page_token' not in http.calls[0][1]['params']
    assert http.calls[1][1]['params']['page_token']=='page2'


def test_pagination_loop_fails_without_following_foreign_url():
    http=Responses([{'bars':{},'next_page_token':'https://evil.example/collect'}]*2)
    with pytest.raises(ValueError,match='pagination loop'):
        Alpaca(http,'fake','fake').bars('ABCD',date(2026,1,1),datetime(2026,9,8,19,44,tzinfo=timezone.utc))
    assert all(url=='https://data.alpaca.markets/v2/stocks/bars' for url,_ in http.calls)


def test_free_sip_does_not_allow_undelayed_configuration():
    with pytest.raises(ValueError,match='16-minute delay'):Alpaca(Responses([]),'fake','fake',delay_minutes=0)
    with pytest.raises(ValueError,match='timezone-aware'):
        Alpaca(Responses([]),'fake','fake').bars('ABCD',date(2026,1,1),date(2026,9,8))


def test_state_survives_process_reopen(tmp_path):
    path=tmp_path/'state.sqlite';s=Store(path);s.put('delivery:day',{'status':'CLAIMED'})
    reopened=Store(path);assert reopened.get('delivery:day')['status']=='CLAIMED'

def test_github_state_sha_guard_and_restore(tmp_path):
    local=Store(tmp_path/'a.sqlite');local.put('key',{'value':3});content=base64.b64encode(local.path.read_bytes()).decode()
    http=Responses([{'encoding':'base64','content':content,'sha':'expected-sha'}, {'object':{'sha':'branch-head'}}, {'content':{'sha':'new-sha'}}])
    backend=GitHubState(http,'owner/repo','fake-token');path=tmp_path/'restored.sqlite';backend.restore(path)
    restored=Store(path);assert restored.get('key')=={'value':3}
    restored.put('new',1);backend.checkpoint(restored)
    assert http.calls[-1][1]['body']['sha']=='expected-sha' and backend.sha=='new-sha'

def test_conflicting_github_write_is_not_retried_without_guard(tmp_path):
    store=Store(tmp_path/'s.sqlite');http=Responses([{'object':{'sha':'head'}},ProviderError('api.github.com',409)])
    backend=GitHubState(http,'owner/repo','fake');backend.sha='expected'
    with pytest.raises(ProviderError):backend.checkpoint(store)
    assert len(http.calls)==2 and http.calls[-1][1]['body']['sha']=='expected'
