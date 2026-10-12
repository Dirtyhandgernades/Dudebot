import copy
from datetime import date, timedelta
import pytest
from backtest.entry_failure_audit import keep, validate_event, future_diagnostic
from smg.market import session_bounds, calendar


def event():
    day = '2025-09-12'; opened, closed = session_bounds(date.fromisoformat(day))
    at = closed - timedelta(minutes=15); cutoff = at - timedelta(minutes=16)
    return {'ticker': 'ABC', 'decision_at': at.isoformat(), 'data_cutoff': cutoff.isoformat(),
            'last_complete_at': (cutoff-timedelta(minutes=4)).isoformat(), 'decision_price': 10,
            'observed_chart': {'change_from_prior_close': .15, 'close_location': .2,
                               'upper_wick': .6, 'below_prior_low': False,
                               'red_candle': True, 'failed_recent_high': True}}


def test_old_exhaustion_or_future_dump_cannot_bypass_current_confirmation():
    e = event(); e['source_policy'] = 'PRIOR_CLOSE_EXHAUSTION_REVALIDATED_PRICE'
    assert keep(e, 'BASELINE')
    for policy in ('NO_CONTINUING_PUMP', 'OBSERVED_CONFIRMATION', 'PRIOR_LOW_BREAK', 'FAILED_HIGH_REJECTION'):
        assert not keep(e, policy)
    before = keep(e, 'FAILED_HIGH_REJECTION')
    e['future_return'] = -.99
    assert keep(e, 'FAILED_HIGH_REJECTION') == before


def test_missing_or_nonfinite_chart_is_unknown_not_confirmation():
    e = event()
    assert not keep({k: v for k, v in e.items() if k != 'observed_chart'}, 'OBSERVED_CONFIRMATION')
    for value in (float('nan'), float('inf'), True):
        changed = copy.deepcopy(e); changed['observed_chart']['change_from_prior_close'] = value
        assert not keep(changed, 'NO_CONTINUING_PUMP')
    with pytest.raises(ValueError): keep(e, 'RETROSPECTIVE_BEST_EXIT')


def test_explicit_prior_low_and_failed_high_confirmation():
    e = event(); e['observed_chart']['change_from_prior_close'] = -.01
    assert keep(e, 'NO_CONTINUING_PUMP') and keep(e, 'FAILED_HIGH_REJECTION')
    e['observed_chart']['below_prior_low'] = True
    assert keep(e, 'PRIOR_LOW_BREAK') and keep(e, 'OBSERVED_CONFIRMATION')


def test_entry_cutoff_and_exchange_close_are_checked():
    e = event(); validate_event(e, '2025-09-12')
    changed = {**e, 'last_complete_at': e['decision_at']}
    with pytest.raises(ValueError): validate_event(changed, '2025-09-12')
    changed = {**e, 'decision_at': session_bounds(date(2025, 9, 12))[1].isoformat()}
    with pytest.raises(ValueError): validate_event(changed, '2025-09-12')


def test_eventual_dump_is_separate_from_losing_exit_and_missing_prices():
    days = [str(d.date()) for d in calendar(2025).sessions_in_range('2025-09-12', '2025-10-03')]
    bars = {d: {'c': 10} for d in days}; bars[days[1]] = {'c': 7}; bars[days[2]] = {'c': 12}
    packet = {'sessions': days, 'split': {'ABC': bars}}
    trade = {'ticker': 'ABC', 'entry_date': days[0], 'exit_date': days[2], 'pnl': -2000,
             'notional': 10000, 'entry_fee': 35, 'entry_price': 10}
    d = future_diagnostic(trade, event(), packet)
    assert d['category'] == 'DROP_HIT_POLICY_LOSS' and d['sessions_to_first_20pct_lower_close'] == 1
    assert d['fixed_exit_counterfactual_pnl']['1'] > 0 and d['fixed_exit_counterfactual_pnl']['2'] < 0
    bars.pop(days[2]); assert future_diagnostic(trade, event(), packet)['category'] == 'THREE_SESSION_PRICE_WINDOW_UNKNOWN'


def test_four_session_decline_does_not_count_as_target_horizon_hit():
    days = [str(d.date()) for d in calendar(2025).sessions_in_range('2025-09-12', '2025-10-03')]
    bars = {d: {'c': 10} for d in days}; bars[days[4]] = {'c': 8}
    trade = {'ticker': 'ABC', 'entry_date': days[0], 'exit_date': days[3], 'pnl': -80,
             'notional': 10000, 'entry_fee': 35, 'entry_price': 10}
    d = future_diagnostic(trade, event(), {'sessions': days, 'split': {'ABC': bars}})
    assert d['category'] == 'DROP_OUTSIDE_THREE_SESSION_HORIZON'
    assert d['sessions_to_first_20pct_lower_close'] == 4
