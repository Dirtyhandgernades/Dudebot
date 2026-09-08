from datetime import date,timedelta
from pathlib import Path
import pytest,yaml
from smg.models import Config,HaltCheck
from smg.rules import evaluate,EntityList,years_ago,normalize_name
from smg.demo import candidate,snapshot,NOW

@pytest.fixture
def cfg():return Config(surge_return_min_pct=100)
@pytest.fixture
def entities():return EntityList(yaml.safe_load(Path('config/entities.yaml').read_text()))
@pytest.fixture
def clear():return HaltCheck(checked_at=NOW,status='CLEAR',reason='test',source_url='https://example.com/halts')
def run(c,cfg,entities,clear,**kw):return evaluate(c,cfg,entities,NOW,kw.get('market',snapshot()),kw.get('halt',clear))

@pytest.mark.parametrize('value,expected',[(14_999_999,'EXCLUDED'),(15_000_000,'QUALIFIED'),(30_000_000,'QUALIFIED'),(30_000_001,'EXCLUDED')])
def test_gross_boundaries(value,expected,cfg,entities,clear):
    c=candidate();c.offer_gross=value
    assert run(c,cfg,entities,clear).status==expected
@pytest.mark.parametrize('value,expected',[(3.99,'EXCLUDED'),(4,'QUALIFIED'),(10,'QUALIFIED'),(10.01,'EXCLUDED')])
def test_price_boundaries(value,expected,cfg,entities,clear):
    c=candidate();c.offer_price=value
    assert run(c,cfg,entities,clear).status==expected
@pytest.mark.parametrize('d,expected',[(date(2023,9,8),'QUALIFIED'),(date(2023,9,7),'EXCLUDED'),(date(2026,9,9),'EXCLUDED')])
def test_ipo_age(d,expected,cfg,entities,clear):
    c=candidate();c.ipo_date=d
    assert run(c,cfg,entities,clear).status==expected

def test_leap_year():assert years_ago(date(2024,2,29),3)==date(2021,2,28)
def test_five_letters_excluded_independently(cfg,entities,clear):
    c=candidate('FIVER');assert not c.is_acquisition_corp
    assert 'FIVE_LETTER_TICKER' in run(c,cfg,entities,clear).reasons

def test_short_symbol_spac(cfg,entities,clear):
    c=candidate('SPAC');c.is_acquisition_corp=True
    assert 'ACQUISITION_CORPORATION' in run(c,cfg,entities,clear).reasons

def test_halt_wins_huge_return(cfg,entities,clear):
    s=snapshot();s.monthly_return=1500
    assert run(candidate(),cfg,entities,clear,market=s,halt=clear.model_copy(update={'status':'HALTED'})).status=='EXCLUDED'

def test_unknown_or_stale_halt(cfg,entities,clear):
    assert run(candidate(),cfg,entities,clear,halt=None).status=='REVIEW_REQUIRED'
    assert run(candidate(),cfg,entities,clear,halt=clear.model_copy(update={'checked_at':NOW-timedelta(minutes=6)})).status=='REVIEW_REQUIRED'

@pytest.mark.parametrize('rvol,expected',[(1,'QUALIFIED'),(.99,'MARKET_NOT_CONFIRMED'),(None,'REVIEW_REQUIRED')])
def test_rvol(rvol,expected,cfg,entities,clear):
    s=snapshot();s.rvol=rvol
    assert run(candidate(),cfg,entities,clear,market=s).status==expected

def test_null_surge_threshold_blocks_ipo_only(cfg,entities,clear):
    cfg.surge_return_min_pct=None
    assert run(candidate(),cfg,entities,clear).status=='CONFIG_REQUIRED'
    assert run(candidate('DOFR','DIRECT_OFFERING'),cfg,entities,clear).status=='QUALIFIED'

def test_direct_us_and_old_allowed(cfg,entities,clear):
    c=candidate('DOFR','DIRECT_OFFERING');c.operations_country='US';c.ipo_date=date(2010,1,1)
    r=run(c,cfg,entities,clear)
    assert r.status=='QUALIFIED' and r.rank[0]==1

def test_any_one_counsel(cfg,entities,clear):
    c=candidate();c.matches[0].name='Loeb & Loeb LLP';c.matches[0].role='counsel'
    assert run(c,cfg,entities,clear).status=='QUALIFIED'

def test_entity_substrings_do_not_match(cfg,entities,clear):
    c=candidate();c.matches[0].name='Cathay Securities Something Else'
    assert run(c,cfg,entities,clear).status=='REVIEW_REQUIRED'

def test_old_underwriter_cannot_qualify_direct(cfg,entities,clear):
    c=candidate('DOFR','DIRECT_OFFERING');c.matches[0].relationship='historical'
    assert run(c,cfg,entities,clear).status=='REVIEW_REQUIRED'

def test_missing_evidence_and_short_history(cfg,entities,clear):
    c=candidate();del c.evidence['offer_gross']
    assert run(c,cfg,entities,clear).status=='REVIEW_REQUIRED'
    s=snapshot();s.monthly_return=None
    assert run(candidate(),cfg,entities,clear,market=s).status=='REVIEW_REQUIRED'

def test_stale_future_prices(cfg,entities,clear):
    for stamp in [NOW-timedelta(minutes=6),NOW+timedelta(seconds=1)]:
        s=snapshot();s.price_time=stamp
        assert run(candidate(),cfg,entities,clear,market=s).status=='REVIEW_REQUIRED'

def test_reverse_split_review(cfg,entities,clear):
    s=snapshot();s.flags=['CORPORATE_ACTION_REVIEW']
    assert run(candidate(),cfg,entities,clear,market=s).status=='REVIEW_REQUIRED'

def test_priority_age(cfg,entities,clear):
    young=candidate();old=candidate();old.ipo_date=date(2024,1,1)
    assert run(young,cfg,entities,clear).rank < run(old,cfg,entities,clear).rank


def test_delayed_market_data_uses_declared_lag_but_halts_use_current_time(cfg,entities,clear):
    m=snapshot();m.feed='sip';m.declared_delay_minutes=16
    m.asof-=timedelta(minutes=16);m.price_time-=timedelta(minutes=16)
    assert run(candidate(),cfg,entities,clear,market=m).status=='QUALIFIED'
    m.price_time-=timedelta(minutes=6)
    assert 'STALE_OR_FUTURE_MARKET_DATA' in run(candidate(),cfg,entities,clear,market=m).reasons


def test_wrong_feed_does_not_pass_confirmation(cfg,entities,clear):
    m=snapshot();m.feed='iex'
    assert 'DATA_FEED_MISMATCH' in run(candidate(),cfg,entities,clear,market=m).reasons
