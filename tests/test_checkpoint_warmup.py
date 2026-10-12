from datetime import datetime, timezone
from types import SimpleNamespace
import json
import pytest
from backtest.checkpoint_warmup import PairedWarmupBars
from backtest.checkpoint_learning import run
from backtest.intraday_checkpoint_study import run as checkpoint_run


class FakeBars:
    def __init__(self, limit=4):
        self.provider = SimpleNamespace(max_requests=limit)
        self.requests = 0; self.cache = {}
    def get(self, symbols, start, end, mode):
        ticker = symbols[0]; key = (ticker, mode)
        if key not in self.cache:
            if self.requests >= self.provider.max_requests: raise RuntimeError('REQUEST_BUDGET')
            self.requests += 1; self.cache[key] = [{'c': 10}]
        return {ticker: self.cache[key]}


def test_small_budget_finishes_pairs_and_reuses_them_at_second_offset():
    base = FakeBars(4); client = PairedWarmupBars(base, period_budget=2)
    start = datetime(2024, 4, 1, tzinfo=timezone.utc); end = datetime(2024, 7, 1, tzinfo=timezone.utc)
    first = client.get(['ABC', 'DEF'], start, end, 'raw')
    assert list(first) == ['ABC'] and base.requests == 2
    assert list(client.get(['ABC', 'DEF'], start, end, 'split')) == ['ABC']
    assert base.requests == 2 and client.gaps['2024-04-01']['unavailable_symbol_pairs'] == 1
    # A later daily run reuses the finished pair and completes the next symbol.
    base.requests = 0; client = PairedWarmupBars(base, period_budget=2)
    assert list(client.get(['ABC', 'DEF'], start, end, 'raw')) == ['ABC', 'DEF']
    assert base.requests == 2


def test_missing_pair_is_unknown_and_never_written_as_empty_data():
    base = FakeBars(0); client = PairedWarmupBars(base)
    at = datetime(2024, 4, 1, tzinfo=timezone.utc)
    assert client.get(['ABC'], at, at, 'raw') == {}
    assert base.cache == {} and base.requests == 0


def test_warmup_cannot_inject_game_season_decisions(tmp_path):
    warmup = tmp_path/'warmup'/'15'; warmup.mkdir(parents=True)
    (warmup/'2018-PRECLOSE_ONLY-signals.json').write_text(json.dumps({'2018-09-12': []}))
    with pytest.raises(ValueError, match='test-season'):
        run({'sessions': [], 'records': []}, tmp_path/'checkpoints', tmp_path/'out', tmp_path/'warmup')


def test_research_period_must_be_real_and_increasing_before_any_request(tmp_path):
    with pytest.raises(ValueError): checkpoint_run({}, None, tmp_path, years=(2024,), season_start='06-30', season_end='04-01')
    with pytest.raises(ValueError): checkpoint_run({}, None, tmp_path, years=(2024,), season_start='02-31', season_end='06-30')
