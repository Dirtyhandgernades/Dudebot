from smg.swing_backtest import download


def test_expanding_universe_fetches_only_new_symbols_and_keeps_contracts_separate(tmp_path,monkeypatch):
    monkeypatch.setenv('ALPACA_API_KEY','test');monkeypatch.setenv('ALPACA_SECRET_KEY','test')
    calls=[]
    class FakeHttp:
        def json(self,url,params,headers):
            calls.append(dict(params))
            return {'bars':{s:[{'t':'2025-09-08T04:00:00Z','c':5}] for s in params['symbols'].split(',')},'next_page_token':None}
    monkeypatch.setattr('smg.swing_backtest.Http',FakeHttp)
    old,n=download(['ABC'],'2025-09-08','2025-12-05',tmp_path)
    assert n==2
    expanded,n=download(['ABC','DEF'],'2025-09-08','2025-12-05',tmp_path)
    assert n==2 and all(c['symbols']=='DEF' for c in calls[-2:])
    assert expanded['raw']['ABC']==old['raw']['ABC']
    same,n=download(['DEF','ABC'],'2025-09-08','2025-12-05',tmp_path)
    assert n==0 and same==expanded
    _,n=download(['ABC'],'2025-09-08','2025-12-06',tmp_path)
    assert n==2


def test_incomplete_pagination_cannot_become_a_complete_symbol_cache(tmp_path,monkeypatch):
    import pytest
    monkeypatch.setenv('ALPACA_API_KEY','test');monkeypatch.setenv('ALPACA_SECRET_KEY','test')
    class FakeHttp:
        def json(self,url,params,headers):
            if params.get('page_token'):raise RuntimeError('provider failed')
            return {'bars':{'ABC':[{'t':'2025-09-08T04:00:00Z','c':5}]},'next_page_token':'next'}
    monkeypatch.setattr('smg.swing_backtest.Http',FakeHttp)
    with pytest.raises(RuntimeError):download(['ABC'],'2025-09-08','2025-12-05',tmp_path)
    assert not list(tmp_path.glob('symbol-v1-*'))
