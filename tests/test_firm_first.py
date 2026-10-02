from datetime import date,timedelta
from pathlib import Path
import pytest,yaml

from smg.demo import candidate,snapshot,NOW
from smg.models import Config,HaltCheck
from smg.rules import EntityList,evaluate
from smg.firm_first import evaluate_firm_first

ENTITIES=EntityList(yaml.safe_load(Path('config/entities.yaml').read_text()))
CFG=Config(surge_return_min_pct=12,ipo_low_priority_surge_max_pct=23,firm_timing_trade_alerts_enabled=True)


def run(c=None,halt_status='CLEAR',monthly=-10,daily=0,rvol=.2):
    c=c or candidate()
    s=snapshot();s.feed='sip';s.declared_delay_minutes=16
    s.asof-=timedelta(minutes=16);s.price_time-=timedelta(minutes=16)
    s.monthly_return=monthly;s.one_day_return=daily;s.rvol=rvol;s.drawdown_pct=-20
    h=HaltCheck(checked_at=NOW,status=halt_status,reason='test',source_url='https://example.com')
    return evaluate_firm_first(c,CFG,ENTITIES,NOW,s,h)


def test_unpumped_old_ipo_outside_terms_and_geography_stays_watch_only():
    c=candidate();c.offer_price=1;c.offer_gross=100_000_000;c.operations_country='US';c.ipo_date=date(2010,1,1)
    r=run(c)
    assert r.status=='MARKET_NOT_CONFIRMED'
    assert 'FIRM_WATCH_NO_SHORT_TIMING_TRIGGER' in r.reasons
    assert 'PREFERENCE_GAP:IPO_TOO_OLD' in r.reasons
    assert evaluate(c,CFG,ENTITIES,NOW).status=='EXCLUDED'


@pytest.mark.parametrize('case',['five_letters','spac','halt'])
def test_three_hard_exclusions(case):
    c=candidate()
    if case=='five_letters':c.ticker='ABCDE'
    if case=='spac':c.is_acquisition_corp=True
    assert run(c,'HALTED' if case=='halt' else 'CLEAR').status=='EXCLUDED'


def test_missing_firm_or_unknown_classification_cannot_pass():
    c=candidate();c.matches=[]
    assert run(c).status=='REVIEW_REQUIRED'
    c=candidate();c.is_acquisition_corp=None
    assert run(c).status=='REVIEW_REQUIRED'


def test_unknown_halt_separate_from_verified_alert():
    assert run(halt_status='UNKNOWN').status=='MATCH_EXCEPT_UNKNOWN_HALT'


def test_no_monthly_history_allowed_as_context():
    assert run(monthly=None).status=='MARKET_NOT_CONFIRMED'


def test_firm_watch_requires_independent_short_timing_before_trade_alert():
    assert run(monthly=-22,daily=-6,rvol=.7).status=='MARKET_NOT_CONFIRMED'
    result=run(monthly=-22,daily=-6,rvol=1.4)
    assert result.status=='QUALIFIED'
    assert 'FIRM_BREAKDOWN_SHORT' in result.reasons
    result=run(monthly=24,daily=-3.5,rvol=1.1)
    assert result.status=='QUALIFIED'
    assert 'FIRM_PUMP_FAILURE_SHORT' in result.reasons

def test_failed_policy_stays_research_only_in_production(monkeypatch):
    monkeypatch.setattr(CFG,'firm_timing_trade_alerts_enabled',False)
    result=run(monthly=24,daily=-3.5,rvol=1.1)
    assert result.status=='REVIEW_REQUIRED'
    assert 'FIRM_PUMP_FAILURE_SHORT' in result.reasons
    assert 'FIRM_TIMING_POLICY_RESEARCH_ONLY_FAILED_VALIDATION' in result.reasons


def test_wei_wei_is_highest_entity_priority():
    c=candidate();c.matches[0].name='Wei, Wei & Co. LLP';c.matches[0].role='auditor'
    assert run(c,daily=-6,rvol=1.4).rank[0]==-1
    assert run(candidate(),daily=-6,rvol=1.4).rank[0]==0


def test_old_ipo_underwriter_does_not_establish_direct_transaction():
    c=candidate('TEST','DIRECT_OFFERING');c.matches[0].relationship='historical'
    assert run(c).status=='REVIEW_REQUIRED'
