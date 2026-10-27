"""Research-only regression for the immutable preclose label-gap shadow audit."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_iex_prospective import collect, persist
from backtest.obsidian_iex_preclose_band_gap_audit import evaluate, SHADOW_LABEL

AT = datetime(2026, 10, 27, 19, 50, tzinfo=timezone.utc)


def snap(price, previous=10, trade_at="2026-10-27T19:49:00Z"):
    return {"latestTrade": {"p": price, "t": trade_at},
            "prevDailyBar": {"c": previous, "t": "2026-10-26T19:59:00Z"}}


class Provider:
    def __init__(self):
        self.snapshots_data = {
            "AAAA": snap(8.2),  # -18%, legacy no-watch, shadow gap
            "BBBB": snap(3.4, 4.02),  # -15.42%, legacy no-watch, shadow gap
            "CCCC": snap(8.6),  # -14%, original watch unchanged
            "DDDD": snap(7.3),  # -27%, original exhausted
            "EEEE": snap(11),  # no watch, no gap
            "FFFF": snap(8.2, trade_at="2026-10-27T19:10:00Z"),  # stale, no gap
            "GGGG": snap(0.6, 0.8),  # -25%, exhausted boundary
            "HHHH": snap(8.51),  # -14.9%, original watch (avoid float boundary ambiguity)
        }

    def assets(self):
        return [{"symbol": s, "exchange": "NASDAQ", "status": "active"}
                for s in self.snapshots_data]

    def snapshots(self, symbols):
        return {s: self.snapshots_data[s] for s in symbols}


class PrecloseGapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.capture = Path(self.tmp.name) / "preclose"
        persist(*collect(Provider(), clock=lambda: AT), self.capture)

    def test_shadow_gap_and_legacy_watch_are_distinct(self):
        report = evaluate(self.capture)
        self.assertEqual(report["captured_universe"], 8)
        self.assertEqual(report["shadow_intermediate_gap_count"], 2)
        self.assertEqual(report["original_watch_count"], 2)
        self.assertEqual(report["gap_indicative_both_prices_at_least_3"], 2)
        self.assertEqual([r["ticker"] for r in report["rows"]], ["AAAA", "BBBB"])
        self.assertTrue(all(r["shadow_research_status"] == SHADOW_LABEL for r in report["rows"]))
        self.assertTrue(all(r["original_screen_status"] == "IEX_NO_EARLY_PRICE_ONLY_WATCH"
                            for r in report["rows"]))
        self.assertIsNone(report["conditional_precision"])
        self.assertIsNone(report["confirmed_future_20pct_early_hits"])

    def test_read_only_raw_capture(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.capture.iterdir() if p.is_file()}
        evaluate(self.capture)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.capture.iterdir() if p.is_file()}
        self.assertEqual(before, after)

    def test_tampered_original_status_fails_even_with_rehashed_file(self):
        file = self.capture / "universe.jsonl"
        rows = [json.loads(line) for line in file.read_text().splitlines()]
        rows[0]["screen_status"] = "IEX_EARLY_WEAKNESS_WATCH_ONLY"
        raw = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode()
        file.write_bytes(raw)
        manifest_file = self.capture / "manifest.json"
        manifest = json.loads(manifest_file.read_text())
        manifest["universe_sha256"] = hashlib.sha256(raw).hexdigest()
        manifest_file.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            evaluate(self.capture)

    def test_missing_snapshot_not_shadow_watch(self):
        p = Provider()
        p.snapshots_data["IIII"] = None
        root = Path(self.tmp.name) / "with_missing"
        persist(*collect(p, clock=lambda: AT), root)
        report = evaluate(root)
        self.assertEqual(report["captured_universe"], 9)
        self.assertEqual(report["shadow_intermediate_gap_count"], 2)


if __name__ == "__main__":
    unittest.main()
