import json
from datetime import date,datetime,timedelta,timezone
from types import SimpleNamespace
import pytest
from smg.models import Snapshot,Config,HaltCheck
from smg.market import calendar
from smg.shadow import capture,contract,review
from smg.storage import Store

NOW=datetime(2026,9,8,19,40,tzinfo=timezone.utc)


def fixture(tmp_path):
    spec={'id':'test-v1','frozen_at':'2026-09-01T00:00:00+00:00','start_date':'2026-09-08','end_date':'2026-11-10',
        'model':{'mean':[0]*7,'scale':[1]*7,'weights':[0]*7,'bias':0},'rank_threshold':.4,
        'data_delay_minutes':16,'decision_window_minutes_before_close':30,
        'calibration':None,'live_trade_enabled':False,'confidence_sizing_enabled':False,
        'profiles':{'baseline':{'initial':100000,'position_target':30000,'buying_power':150000,'max_position_equity_fraction':.25}}}
    path=tmp_path/'freeze.json';path.write_text(json.dumps(spec))
    days=[str(d.date()) for d in calendar(2026).sessions_in_range('2026-07-01','2026-09-04')][-22:]
    history=[{'date':d,'c':10,'h':10.1,'l':9.9,'v':1000} for d in days]
    cutoff=NOW-timedelta(minutes=16)
    partial={'o':14,'c':14,'h':17,'l':13,'v':4000,'last_complete_at':cutoff.isoformat()}
    snapshot=Snapshot(asof=cutoff,price_time=cutoff-timedelta(minutes=1),price=14,monthly_return=40,
        one_day_return=40,five_day_return=40,drawdown_pct=-18,rvol=4,rvol20=4,baseline_sessions=60,
        cumulative_volume=4000,baseline_volume=1000,source_url='fixture',feed='sip',declared_delay_minutes=16,
        market_cap=100000000,market_cap_observed_at=NOW,market_cap_source='fixture',market_cap_basis='fixture',
        research_history=history,research_partial=partial)
    c=SimpleNamespace(ticker='ABC',pipeline='FIRM_WATCH',is_acquisition_corp=False,exchange='NASDAQ')
    e=SimpleNamespace(candidate=c,snapshot=snapshot,matches=[{'firm':'fixture'}],
        halt=HaltCheck(checked_at=NOW,status='CLEAR',reason='fixture',source_url='fixture'),
        shortability={'status':'CURRENT','tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'})
    return Store(tmp_path/'state.sqlite'),path,spec,e


def test_forward_contract_is_immutable_and_forecast_does_not_rewrite(tmp_path):
    store,path,spec,e=fixture(tmp_path)
    result=capture(store,[e],NOW,Config(),path)
    assert result['counts']['SELECTED']==1
    row=store.items('forward_forecast:')[0][1]
    assert row['paper_eligible'] is True
    e.snapshot.price=1000
    assert capture(store,[e],NOW+timedelta(minutes=1),Config(),path)['counts']['ALREADY_CAPTURED']==1
    assert store.items('forward_forecast:')[0][1]==row
    # Windows CRLF or JSON formatting must not invalidate the same contract.
    path.write_bytes(json.dumps(spec,indent=2).replace('\n','\r\n').encode())
    contract(store,path,NOW)
    spec['rank_threshold']=.6;path.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='FROZEN'):contract(store,path,NOW)


def test_forward_current_borrow_and_cap_gating_stays_separate_from_detection(tmp_path):
    store,path,_,e=fixture(tmp_path)
    e.snapshot.market_cap=None;e.shortability={'status':'UNAVAILABLE'}
    capture(store,[e],NOW,Config(),path)
    row=store.items('forward_forecast:')[0][1]
    assert row['selected'] and not row['paper_eligible']
    assert row['game_status']=='REVIEW_REQUIRED'


def test_forward_review_censors_horizon_and_keeps_paper_positions_open(tmp_path):
    store,path,_,e=fixture(tmp_path)
    capture(store,[e],NOW,Config(),path)
    bars={'ABC':{'2026-09-08':{'c':14},'2026-09-09':{'c':10}}}
    result=review(store,bars,'2026-09-09',NOW+timedelta(days=1),bars)[0]
    assert result['matured']==0 and result['rows'][0]['outcome']=='HIT_20_PERCENT'
    portfolio=result['paper_portfolios']['baseline']
    assert portfolio['closed_trades']==0 and portfolio['unresolved_open_positions']==1
    assert portfolio['ending_balance'] is None and portfolio['marked_ending_equity']>100000
    bars['ABC'].update({'2026-09-10':{'c':9},'2026-09-11':{'c':8}})
    result=review(store,bars,'2026-09-11',NOW+timedelta(days=3),bars)[0]
    assert result['matured']==1 and result['selected_hits']==1
    assert result['confidence_sizing_enabled'] is False


def test_forward_no_setup_or_future_quote_does_not_create_a_forecast(tmp_path):
    store,path,_,e=fixture(tmp_path)
    e.snapshot.asof=NOW
    result=capture(store,[e],NOW,Config(),path)
    assert result['counts']['DATA_CONTRACT_MISMATCH']==1
    assert store.items('forward_forecast:')==[]


def test_frozen_forecast_rejects_changed_implementation(tmp_path):
    store,path,spec,_=fixture(tmp_path)
    spec['implementation_sha256']={'smg/shadow.py':'incorrect-digest'}
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='FROZEN_IMPLEMENTATION_CHANGED'):contract(store,path,NOW)


def test_optional_raw_provider_failure_is_labeled_without_losing_split_review(tmp_path):
    from smg.learning import review as daily_review
    store,path,_,e=fixture(tmp_path)
    capture(store,[e],NOW,Config(),path)
    class Http:
        def json(self,url,**kwargs):
            if kwargs['params']['adjustment']=='raw':raise RuntimeError('fixture failure')
            return {'bars':{'ABC':[{'t':'2026-09-08T20:00:00Z','c':14},
                                   {'t':'2026-09-09T20:00:00Z','c':10}]}}
    result=daily_review(store,Http(),{},datetime(2026,9,9,23,35,tzinfo=timezone.utc))
    assert result['forward_raw_failures'][0]['error_type']=='RuntimeError'
    assert result['frozen_forward'][0]['rows'][0]['outcome']=='HIT_20_PERCENT'
