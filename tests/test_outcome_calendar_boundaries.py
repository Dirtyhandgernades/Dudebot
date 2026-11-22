import hashlib
import json
from datetime import datetime, timezone

from backtest.obsidian_prospective_capture import collect, persist, in_window
from backtest.obsidian_prospective_outcomes import evaluate
from tests.test_obsidian_prospective_outcomes import Provider, outcome


class HolidayProvider(Provider):
    def snapshots(self, symbols):
        result = super().snapshots(symbols)
        for row in result.values():
            row['latestTrade']['t'] = '2026-11-27T17:49:00Z'
            row['prevDailyBar']['t'] = '2026-11-25T05:00:00Z'
            row['minuteBar']['t'] = '2026-11-27T17:48:00Z'
        return result


def test_early_close_capture_and_outcome_skip_thanksgiving(tmp_path):
    at = datetime(2026, 11, 27, 17, 50, tzinfo=timezone.utc)
    capture = tmp_path / 'capture'
    manifest = persist(*collect(HolidayProvider(), clock=lambda: at), destination=capture)
    data = (capture / 'universe.jsonl').read_bytes()
    assert b'\r\n' not in data
    assert hashlib.sha256(data).hexdigest() == manifest['universe_sha256']
    row = outcome('AAAA', 7)
    row.update(previous_session_date='2026-11-25', close_at='2026-11-27T18:00:00Z',
               collected_at='2026-11-27T18:05:00Z')
    path = tmp_path / 'outcomes.jsonl'
    path.write_text(json.dumps(row) + '\n')
    assert evaluate(capture, path)['outcomes_verified'] == 1
    row['close_at'] = '2026-11-27T21:00:00Z'
    row['collected_at'] = '2026-11-27T21:05:00Z'
    path.write_text(json.dumps(row) + '\n')
    assert evaluate(capture, path)['outcomes_verified'] == 0


def test_capture_rejects_holiday_and_regular_clock_on_short_session():
    assert not in_window(datetime(2026, 11, 26, 20, 50, tzinfo=timezone.utc))
    assert not in_window(datetime(2026, 11, 27, 20, 50, tzinfo=timezone.utc))
