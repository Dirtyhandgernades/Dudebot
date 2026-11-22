from copy import deepcopy

import pytest

from smg.intraday_replay import STRATEGY, decision_window
from smg.swing_backtest import simulate
from tests.test_intraday_replay import packet


def run_delay(delay, timestamp_day='2025-11-06'):
    data = packet()
    _, _, decision, cutoff = decision_window(timestamp_day)
    event = dict(ticker='ABC', decision_at=decision.isoformat(),
                 data_cutoff=cutoff.isoformat(), decision_price=10,
                 timing_trigger=STRATEGY, dump_structure_score=25)
    original = deepcopy(event)
    result = simulate(data['raw'], data['split'], ['ABC'], data['sessions'],
                      start='2025-11-06', end='2025-11-10', hold=1,
                      strategy=STRATEGY, firm_dates=data['firm_dates'],
                      position_target=10000, buying_power=100000,
                      signal_share_sizing=True, intraday_signals={'2025-11-06': [event]},
                      research_entry_delay=delay)
    assert event == original
    return result


def test_delayed_entry_keeps_signal_day_across_weekend():
    result = run_delay(1)
    trade = result['trades'][0]
    assert trade['signal_date'] == '2025-11-06'
    assert trade['entry_date'] == '2025-11-07'
    assert trade['exit_date'] == '2025-11-10'
    assert result['signal_events'][0]['decision_at'].startswith('2025-11-06')


def test_original_path_remains_same_session():
    trade = run_delay(0)['trades'][0]
    assert trade['signal_date'] == trade['entry_date'] == '2025-11-06'


def test_delay_rejects_future_observation():
    with pytest.raises(ValueError, match='timestamps'):
        run_delay(1, '2025-11-07')


@pytest.mark.parametrize('delay', [-1, 2, True, 1.0])
def test_delay_rejects_unsupported_values(delay):
    with pytest.raises(ValueError, match='delay'):
        run_delay(delay)
