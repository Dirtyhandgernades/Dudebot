from backtest.checkpoint_learning import checkpoint_x, models_before, eligible, issuer_before
from smg.market import calendar


def test_checkpoint_features_exclude_entry_fill_and_future_candles():
    days = [str(d.date()) for d in calendar(2025).sessions_in_range('2025-08-01', '2025-10-03')]
    bars = {d: {'o': 10, 'h': 11, 'l': 9, 'c': 10, 'v': 100} for d in days}
    packet = {'sessions': days, 'split': {'ABC': bars}}
    chart = {'change_from_prior_close': -.02, 'close_location': .2, 'upper_wick': .4,
             'red_candle': True, 'below_prior_low': True, 'lower_high': True, 'failed_recent_high': False}
    event = {'ticker': 'ABC', 'observed_chart': chart}; day = '2025-09-12'
    before = checkpoint_x(packet, event, day)
    for d in days:
        if d >= day: bars[d] = {'o': 100, 'h': 900, 'l': .01, 'c': 600, 'v': 10**9}
    assert checkpoint_x(packet, event, day) == before
    assert len(before) == 14


def test_prior_training_excludes_future_labels_holdout_and_old_lookback(monkeypatch):
    captured = []
    monkeypatch.setattr('backtest.checkpoint_learning.hold_outcome', lambda row, packet, hold: {'policy_net_return': 0})
    monkeypatch.setattr('backtest.checkpoint_learning.fit_policy', lambda rows: captured.append(rows))
    row = {'ticker': 'ABC', 'issuer_cik': '1', 'signal_date': '2024-09-12', 'entry_date': '2024-09-12',
           'label_end': '2024-09-17', 'held_issuer': False}
    rows = [row, {**row, 'label_end': '2025-01-02'}, {**row, 'held_issuer': True},
            {**row, 'signal_date': '2022-09-12'}]
    _, counts = models_before(rows, {}, 2025)
    assert counts == {1: 1, 2: 1, 3: 1} and all(len(v) == 1 for v in captured)


def test_future_filing_cannot_supply_current_issuer_identity():
    event = {'ticker': 'ABC', 'decision_at': '2025-09-12T19:45:00+00:00'}
    records = [{'ticker': 'ABC', 'decision_at': '2025-09-13T00:00:00+00:00', 'cik': '123'}]
    assert issuer_before({'records': records}, event) is None
    records.append({'ticker': 'ABC', 'decision_at': '2025-09-11T00:00:00+00:00', 'cik': '123'})
    assert issuer_before({'records': records}, event) == '123'
    records.append({'ticker': 'ABC', 'decision_at': '2025-09-10T00:00:00+00:00', 'cik': '456'})
    assert issuer_before({'records': records}, event) is None


def test_matched_candle_rank_does_not_ignore_squeeze_risk():
    score = {'return_rank': .6, 'profitability_rank': .8, 'tail_loss_rank': .1}
    assert eligible(score)
    assert not eligible({**score, 'tail_loss_rank': .4})
    assert not eligible({**score, 'return_rank': float('inf')})
