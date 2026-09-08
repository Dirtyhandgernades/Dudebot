from datetime import timedelta
import pytest
from smg.demo import snapshot,candidate,NOW
from smg.game_rules import eligibility,NasdaqMarketCaps
from smg.models import Config
from smg.firm_first import firm_structure
from test_firm_first import ENTITIES

@pytest.mark.parametrize('price,cap,status',[(3,25_000_000,'EXCLUDED'),(3.01,25_000_000,None),(4,24_999_999,'EXCLUDED'),(4,None,'REVIEW_REQUIRED')])
def test_game_boundaries(price,cap,status):
    s=snapshot();s.price=price;s.market_cap=cap
    assert eligibility(s,Config(),NOW)[0]==status

def test_future_market_cap_cannot_validate_a_historical_stock():
    s=snapshot();s.market_cap_observed_at=NOW+timedelta(days=1)
    assert eligibility(s,Config(),NOW)[0]=='REVIEW_REQUIRED'

def test_nyse_allowed_and_otc_still_excluded():
    c=candidate();c.exchange='XNYS'
    assert firm_structure(c,Config(),ENTITIES,NOW).status=='STRUCTURAL_MATCH'
    c.exchange='OTC';assert firm_structure(c,Config(),ENTITIES,NOW).status=='EXCLUDED'

def test_current_market_cap_fetch_is_cached_and_has_source():
    class Http:
        calls=0
        def json(self,*a,**kw):
            self.calls+=1
            return {'data':{'table':{'rows':[{'symbol':'DEMO','marketCap':'25,000,000'}]}}}
    http=Http();caps=NasdaqMarketCaps(http);s=snapshot();s.market_cap=None
    caps.apply(candidate(),s,NOW);caps.apply(candidate(),s,NOW)
    assert s.market_cap==25_000_000 and s.market_cap_observed_at==NOW and http.calls==2
    assert s.market_cap_source.startswith('https://api.nasdaq.com/')
