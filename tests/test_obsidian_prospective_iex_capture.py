"""Offline research-only IEX capture tests. No provider calls."""
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from backtest.obsidian_iex_prospective import collect, persist, verify, classify

AT = datetime(2026, 10, 27, 19, 50, tzinfo=timezone.utc)


def snap(price, trade_at="2026-10-27T19:49:00Z"):
    return {"latestTrade": {"p": price, "t": trade_at},
            "prevDailyBar": {"c": 10, "t": "2026-10-26T19:59:00Z"}}


class Provider:
    def __init__(self, data=None):
        self.data = data if data is not None else {"AAAA": snap(9.3), "BBBB": snap(6.8),
                                                     "CCCC": snap(11)}
    def assets(self):
        return [{"symbol": x, "exchange": "NASDAQ", "status": "active"} for x in self.data]
    def snapshots(self, symbols):
        return {x: self.data[x] for x in symbols}


class IEXCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / "prospective"

    def test_capture_and_replay(self):
        rows, manifest = collect(Provider(), clock=lambda: AT)
        persist(rows, manifest, self.dest)
        result = verify(self.dest)
        self.assertEqual(result["universe_count"], 3)
        self.assertEqual(result["watch_count"], 1)
        self.assertFalse(result["trade_authorized"])
        self.assertEqual(manifest["status_counts"]["IEX_EXHAUSTED_PRICE_ONLY"], 1)

    def test_outside_window_rejected(self):
        with self.assertRaisesRegex(ValueError, "CAPTURE_CLOCK_OUTSIDE_PRE_CLOSE"):
            collect(Provider(), clock=lambda: AT + timedelta(hours=2))

    def test_stale_trade_not_watch(self):
        self.assertEqual(classify(snap(9.3, "2026-10-27T19:20:00Z"), AT),
                         "STALE_OR_FUTURE_IEX_TRADE")

    def test_future_trade_not_watch(self):
        self.assertEqual(classify(snap(9.3, "2026-10-27T19:51:00Z"), AT),
                         "STALE_OR_FUTURE_IEX_TRADE")

    def test_missing_snapshot_counted(self):
        p = Provider()
        p.snapshots = lambda symbols: {"AAAA": snap(9.3)}
        rows, manifest = collect(p, clock=lambda: AT)
        self.assertEqual(manifest["status_counts"]["MISSING_SNAPSHOT"], 2)
        persist(rows, manifest, self.dest)
        self.assertEqual(verify(self.dest)["universe_count"], 3)

    def test_unknown_extra_snapshot_rejected(self):
        p = Provider()
        p.snapshots = lambda symbols: {"ZZZZ": snap(9.3)}
        with self.assertRaisesRegex(ValueError, "INVALID_SNAPSHOT_SYMBOLS"):
            collect(p, clock=lambda: AT)

    def test_tampered_status_rejected_even_with_updated_hash(self):
        rows, manifest = collect(Provider(), clock=lambda: AT)
        persist(rows, manifest, self.dest)
        data = (self.dest / "universe.jsonl").read_text()
        self.assertIn("IEX_EARLY_WEAKNESS_WATCH_ONLY", data)
        (self.dest / "universe.jsonl").write_text(data.replace(
            "IEX_EARLY_WEAKNESS_WATCH_ONLY", "IEX_EXHAUSTED_PRICE_ONLY"))
        import hashlib
        m = json.loads((self.dest / "manifest.json").read_text())
        m["universe_sha256"] = hashlib.sha256((self.dest / "universe.jsonl").read_bytes()).hexdigest()
        (self.dest / "manifest.json").write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, "STATUS_REPLAY_MISMATCH"):
            verify(self.dest)

    def test_write_once(self):
        rows, manifest = collect(Provider(), clock=lambda: AT)
        persist(rows, manifest, self.dest)
        with self.assertRaises(FileExistsError):
            persist(rows, manifest, self.dest)


if __name__ == "__main__":
    unittest.main()
