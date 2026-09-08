from datetime import date,timedelta
from pathlib import Path
import pytest,yaml

from smg.demo import candidate,snapshot,NOW
from smg.models import Config,HaltCheck
from smg.rules import EntityList,evaluate
from smg.firm_first import evaluate_firm_first

ENTITIES=EntityList(yaml.safe_load(Path('config/entities.yaml').read_text()))
CFG=Config(surge_return_min_pct=12,ipo_low_priority_surge_max_pct=23)


def run(c=None,halt_status='CLEAR',monthly=-10):
    c=c or candidate()
    s=snapshot();s.feed='sip';s.declared_delay_minutes=16
    s.asof-=timedelta(minutes=16);s.price_time-=timedelta(minutes=16)
    s.monthly_return=monthly;s.rvol=.2
    h=HaltCheck(checked_at=NOW,status=halt_status,reason='test',source_url='https://example.com')
    return evaluate_firm_first(c,CFG,ENTITIES,NOW,s,h)


def test_unpumped_old_ipo_outside_terms_and_geography_stays_firm_match():
    c=candidate();c.offer_price=1;c.offer_gross=100_000_000;c.operations_country='US';c.ipo_date=date(2010,1,1)
    r=run(c)
    assert r.status=='QUALIFIED'
    assert 'NOT_YET_PUMPED_OR_BELOW_PREFERRED_SURGE' in r.reasons
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
    assert run(monthly=None).status=='QUALIFIED'


def test_wei_wei_is_highest_entity_priority():
    c=candidate();c.matches[0].name='Wei, Wei & Co. LLP';c.matches[0].role='auditor'
    assert run(c).rank[0]==-1
    assert run(candidate()).rank[0]==0


def test_old_ipo_underwriter_does_not_establish_direct_transaction():
    c=candidate('TEST','DIRECT_OFFERING');c.matches[0].relationship='historical'
    assert run(c).status=='REVIEW_REQUIRED'
