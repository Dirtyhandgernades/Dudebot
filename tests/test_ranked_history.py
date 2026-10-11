from datetime import datetime,timedelta,timezone
import pytest
from smg.ranked_firm import daily_history
from smg.storage import Store


@pytest.mark.parametrize('clock,through,end',[
    ('2026-10-09T20:58:00+00:00','2026-10-09','2026-10-09T20:42:00Z'),
    ('2026-10-09T20:15:00+00:00','2026-10-08','2026-10-08T23:59:59Z'),
    ('2026-10-11T19:00:00+00:00','2026-10-09','2026-10-09T23:59:59Z'),
    ('2026-11-06T21:16:00+00:00','2026-11-06','2026-11-06T21:00:00Z'),
])
def test_daily_sip_history_never_requests_recent_or_future_window(tmp_path,monkeypatch,clock,through,end):
    monkeypatch.setenv('ALPACA_API_KEY','fixture');monkeypatch.setenv('ALPACA_SECRET_KEY','fixture')
    now=datetime.fromisoformat(clock);queries=[]
    class HTTP:
        def json(self,url,params,headers):
            queries.append(dict(params))
            assert datetime.fromisoformat(params['end'].replace('Z','+00:00'))<=now-timedelta(minutes=16)
            return {'bars':{'A':[{'t':through+'T04:00:00Z','c':10}]}}
    store=Store(tmp_path/'s.db');history,count=daily_history(store,HTTP(),['A'],now)
    assert count==2 and history['through']==through
    assert all(q['end']==end and q['feed']=='sip' for q in queries)
    assert daily_history(store,HTTP(),['A'],now)[1]==0


def test_preflight_probes_real_sip_access_even_when_cache_is_warm(monkeypatch):
    from smg.ranked_firm import provider_preflight
    monkeypatch.setenv('ALPACA_API_KEY','fixture');monkeypatch.setenv('ALPACA_SECRET_KEY','fixture')
    now=datetime(2026,10,11,19,tzinfo=timezone.utc)
    class HTTP:
        def json(self,url,params,headers):
            assert params['feed']=='sip' and params['limit']==10 and params['symbols']=='SPY'
            assert datetime.fromisoformat(params['end'].replace('Z','+00:00'))==now-timedelta(minutes=16)
            return {'bars':{'SPY':[{'c':10}]}}
    assert provider_preflight(HTTP(),now)['status']=='VERIFIED'
