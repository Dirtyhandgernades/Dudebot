from backtest.firm_timing_study import keep
from smg.timing_shadow import review
from smg.storage import Store
from datetime import datetime,timezone


def test_timing_confirmation_uses_quote_information_never_future_fill():
    prior={'source_policy':'PRIOR_CLOSE_EXHAUSTION_REVALIDATED_PRICE','observed_change_from_prior_close':.01}
    assert keep(prior,'PRIOR_GAIN_MAX_2PCT')
    assert not keep(prior,'PRIOR_NONPOSITIVE') and not keep(prior,'CURRENT_ONLY')
    prior['future_close']=.001
    assert keep(prior,'PRIOR_GAIN_MAX_2PCT')
    prior['observed_change_from_prior_close']=.03
    assert not keep(prior,'PRIOR_GAIN_MAX_2PCT')
    assert keep({'source_policy':'FIRM_INTRADAY_EXHAUSTION_RESEARCH'},'CURRENT_ONLY')


def test_timing_shadow_stays_research_only_when_no_fresh_labels_exist(tmp_path):
    s=Store(tmp_path/'state');r=review(s,datetime(2026,10,7,23,tzinfo=timezone.utc))
    assert r['status']=='COLLECTING_PROSPECTIVE_TIMING' and not r['live_changed']
    assert r['provider_requests']==0
