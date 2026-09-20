from datetime import timedelta
from pathlib import Path
import yaml
from smg.demo import NOW,candidate,snapshot
from smg.models import HaltCheck
from smg.rules import EntityList
from smg.runner import Scanner
from smg.storage import Store
from smg.volatility import evaluate_volatility

ENTITIES=EntityList(yaml.safe_load(Path('config/entities.yaml').read_text()))

def broad():
    c=candidate('VOLA');c.pipeline='VOLATILITY_WATCH';c.event_id='VOLATILITY';c.matches=[]
    c.offer_price=None;c.offer_gross=None;c.terms_unambiguous=False;c.status='unknown'
    return c

def market():
    s=snapshot();s.asof-=timedelta(minutes=16);s.price_time-=timedelta(minutes=16)
    s.feed='sip';s.declared_delay_minutes=16;s.monthly_return=30;s.one_day_return=-5;s.drawdown_pct=-10;s.rvol=1.2
    return s

def test_broad_lane_can_qualify_without_listed_firm_but_needs_stronger_market_setup():
    from test_live_firms import CFG
    h=HaltCheck(checked_at=NOW,status='CLEAR',reason='fixture',source_url='https://example.com/halt')
    e=evaluate_volatility(broad(),CFG,ENTITIES,NOW,market(),h)
    assert e.status=='QUALIFIED' and e.signal_side=='SHORT'
    assert 'NO_LISTED_FIRM_MATCH' in e.reasons and 'PUMP_FAILURE_SHORT' in e.reasons
    from smg.notify import digest
    assert 'VOLATILITY SHORT' in digest([e],NOW,CFG)[0]['embeds'][0]['title']
    weak=market();weak.monthly_return=2;weak.one_day_return=-1;weak.drawdown_pct=-2;weak.rvol=1
    assert evaluate_volatility(broad(),CFG,ENTITIES,NOW,weak,h).status=='MARKET_NOT_CONFIRMED'

def test_broad_lane_keeps_hard_exclusions():
    from test_live_firms import CFG
    h=HaltCheck(checked_at=NOW,status='CLEAR',reason='fixture',source_url='https://example.com/halt')
    c=broad();c.ticker='ABCDE'
    assert evaluate_volatility(c,CFG,ENTITIES,NOW,market(),h).status=='EXCLUDED'
    c=broad();c.is_acquisition_corp=True
    assert evaluate_volatility(c,CFG,ENTITIES,NOW,market(),h).status=='EXCLUDED'

def test_current_borrow_gate_runs_before_expensive_history(tmp_path):
    from test_live_firms import CFG
    class Http:
        def json(self,url,**kwargs):
            assert '/v2/assets/' in url
            return {'symbol':'VOLA','tradable':True,'shortable':False,'borrow_status':'not_shortable'}
    class Market:
        http=Http();headers={};calls=0
        def bars(self,*args,**kwargs):self.calls+=1;raise AssertionError('minute history should not be requested')
    class Halts:
        def check(self,ticker,now):return HaltCheck(checked_at=now,status='CLEAR',reason='fixture',source_url='https://example.com/halt')
    provider=Market();result=Scanner(provider,Halts(),CFG,ENTITIES,Store(tmp_path/'state.db')).scan([broad()],NOW)[0]
    assert result.status=='REVIEW_REQUIRED' and 'CURRENT_BORROW_NOT_EXECUTABLE' in result.reasons
    assert provider.calls==0
