from datetime import timedelta
from smg.ranked_firm import eligible_signal
from smg.models import Config,HaltCheck
from smg.rules import EntityList
from smg.market import calendar
from smg.risk_model import FEATURES
from tests.test_live_firms import watch,ENTRIES
from smg.demo import NOW as DEMO_NOW
NOW=DEMO_NOW-timedelta(minutes=15)


def fixture():
    days=[str(d.date()) for d in calendar(NOW.year).sessions_in_range(NOW.date()-timedelta(days=60),NOW.date()-timedelta(days=1))][-22:]
    history=[{'date':d,'o':10,'h':10.1,'l':9.9,'c':10,'v':100} for d in days]
    history[-1].update(o=14,h=17,l=13,c=14,v=400)
    partial={'o':14,'h':17,'l':13,'c':14,'v':400,'last_complete_at':(NOW-timedelta(minutes=17)).isoformat()}
    spec={'id':'fixture','entry_policy':'CONFIRMED_EARLY_OR_DEFERRED_HALF','rank_threshold':.5,
          'model':{'features':FEATURES,'mean':[0]*7,'scale':[1]*7,'weights':[0]*7,'bias':5}}
    borrow={'status':'CURRENT','tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'}
    halt=HaltCheck(checked_at=NOW,status='CLEAR',reason='fixture',source_url='https://example.com/halts')
    candidate=watch();candidate.reviewed_at=NOW
    return candidate,history,partial,spec,borrow,halt


class Cap:
    def __init__(self,value=100_000_000):self.value=value
    def apply(self,c,s,now):
        s.market_cap=self.value;s.market_cap_observed_at=now;s.market_cap_source='https://example.com/cap';s.market_cap_basis='fixture'


def evaluate(**changes):
    c,h,p,policy,b,halt=fixture()
    defaults={'candidate':c,'history':h,'raw_history':h,'adjusted_partial':p,'raw_partial':p,
              'now':NOW,'cfg':Config(screening_profile='firm_first',surge_return_min_pct=12),
              'entities':EntityList(ENTRIES),'policy':policy,'borrow':b,'halt':halt,'cap':Cap()}
    defaults.update(changes);return eligible_signal(**defaults)


def test_ranked_layer_qualifies_exact_setup_without_claiming_probability():
    result=evaluate()
    assert result.status=='QUALIFIED' and result.signal_side=='SHORT'
    assert result.ranking_evidence['ranked_firm']['is_probability'] is False
    assert 'UNIFORM_TIME_VOLUME_PROJECTION' in result.snapshot.flags


def test_unknown_borrow_remains_detected_but_cannot_be_a_trade():
    result=evaluate(borrow=None)
    assert result.status=='REVIEW_REQUIRED' and result.snapshot is not None
    assert 'CURRENT_BORROW_NOT_EXECUTABLE' in result.reasons


def test_current_hard_exclusions_and_future_quote_cannot_be_bypassed_by_rank():
    c,h,p,spec,b,halt=fixture();c.ticker='ABCDE'
    assert evaluate(candidate=c).status=='EXCLUDED'
    assert evaluate(cap=Cap(24_000_000)).status=='EXCLUDED'
    halt.status='HALTED';assert evaluate(halt=halt).status=='EXCLUDED'
    p['last_complete_at']=NOW.isoformat()
    assert evaluate(raw_partial=p,adjusted_partial=p).status=='REVIEW_REQUIRED'


def test_after_close_has_no_trade_even_when_delayed_quote_is_still_in_session():
    assert evaluate(now=NOW+timedelta(hours=1)).status!='QUALIFIED'


def test_enabled_published_policy_implementation_fingerprints_match():
    import json
    from pathlib import Path
    from datetime import datetime,timezone
    from smg.ranked_firm import valid_policy
    root=Path(__file__).resolve().parents[1]
    spec=json.loads((root/'config/ranked_firm_alerts.json').read_text())
    assert valid_policy(spec,root,datetime(2026,10,7,16,tzinfo=timezone.utc)) is True
    assert spec['confidence_sizing_enabled'] is False and spec['entry_policy']=='PRECLOSE_ONLY'
