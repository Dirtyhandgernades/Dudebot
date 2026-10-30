"""Synthetic preclose maturity-ledger regression tests; no vendor or trade calls."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_iex_prospective import collect, persist
from backtest.obsidian_prospective_maturity_ledger import build

AT = datetime(2026, 10, 30, 19, 50, tzinfo=timezone.utc)
DAYS = ("2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04")
PREVIOUS = ("2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03")


class Provider:
    def assets(self):
        return [
            {"symbol": ticker, "exchange": "NASDAQ", "status": "active"}
            for ticker in ("AAAA", "BBBB", "CCCC")
        ]

    def snapshots(self, symbols):
        prices = {"AAAA": 9.3, "BBBB": 6.8, "CCCC": 10.1}
        return {
            ticker: {
                "latestTrade": {"p": prices[ticker],
                                "t": "2026-10-30T19:49:00Z"},
                "prevDailyBar": {"c": 10,
                                 "t": "2026-10-29T19:59:00Z"},
            }
            for ticker in symbols
        }


def calendar():
    return [
        {"session_date": day, "previous_regular_session": previous,
         "session_open": True, "independently_checked": True,
         "regular_close_at": day + (
             "T16:00:00-04:00" if day == "2026-10-30"
             else "T16:00:00-05:00"),
         "source_url": "https://www.nyse.com/trade/hours-calendars",
         "source_checked_at": "2026-10-30T19:00:00Z"}
        for day, previous in zip(DAYS, PREVIOUS)
    ]


class PrecloseMaturityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.capture = Path(temporary.name) / "original"
        persist(*collect(Provider(), clock=lambda: AT), self.capture)

    def test_original_preclose_cohort_keeps_all_horizons_and_rejections(self):
        report = build(self.capture, calendar(), [],
                       "2026-10-30T21:30:00Z")
        self.assertEqual(report["capture_phase"], "PRECLOSE")
        self.assertTrue(report["preclose_is_separate_unmatched_cohort"])
        self.assertEqual(report["original_universe_count"], 3)
        self.assertEqual(report["expected_issuer_session_slots"], 12)
        self.assertEqual(report["per_horizon"][0]["categories"]["CENSORED_MISSING"], 3)
        for horizon in report["per_horizon"][1:]:
            self.assertEqual(horizon["categories"]["NOT_YET_MATURE"], 3)
        statuses = {r["ticker"]: r["original_status"] for r in report["rows"]}
        self.assertEqual(statuses["AAAA"], "IEX_EARLY_WEAKNESS_WATCH_ONLY")
        self.assertEqual(statuses["BBBB"], "IEX_EXHAUSTED_PRICE_ONLY")
        self.assertEqual(statuses["CCCC"], "IEX_NO_EARLY_PRICE_ONLY_WATCH")
        self.assertEqual(sum(r["original_price_only_watch"] for r in report["rows"]), 1)
        self.assertEqual(report["verified_outcomes"], 0)
        self.assertIsNone(report["verified_precision"])
        self.assertFalse(report["predictive_edge_proven"])

    def test_malformed_and_conflicting_supplied_rows_stay_censored(self):
        rows = [
            {"ticker": "AAAA", "session_date": DAYS[0],
             "provider_conflict": True},
            {"ticker": "BBBB", "session_date": DAYS[0],
             "regular_close": 6.8},
        ]
        report = build(self.capture, calendar(), rows,
                       "2026-11-05T22:00:00Z")
        categories = report["per_horizon"][0]["categories"]
        self.assertEqual(categories["SOURCE_CONFLICT"], 1)
        self.assertEqual(categories["CENSORED_BLOCKED"], 1)
        self.assertEqual(categories["CENSORED_MISSING"], 1)
        self.assertEqual(categories["VERIFIED"], 0)
        self.assertFalse(report["independent_official_close_authentication_performed"])

    def test_duplicate_and_outside_outcomes_fail_closed(self):
        row = {"ticker": "AAAA", "session_date": DAYS[0]}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OUTSIDE"):
            build(self.capture, calendar(), [row, row], "2026-11-05T22:00:00Z")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OUTSIDE"):
            build(self.capture, calendar(),
                  [{"ticker": "ZZZZ", "session_date": DAYS[0]}],
                  "2026-11-05T22:00:00Z")

    def test_tampered_original_preclose_capture_rejected(self):
        original = self.capture / "universe.jsonl"
        original.write_bytes(original.read_bytes().replace(b"AAAA", b"ZZZZ"))
        with self.assertRaisesRegex(ValueError, "HASH_OR_TRUNCATION"):
            build(self.capture, calendar(), [], "2026-11-05T22:00:00Z")

    def test_preclose_not_conflated_with_morning_or_intraday(self):
        report = build(self.capture, calendar(), [], "2026-11-05T22:00:00Z")
        self.assertEqual(report["capture_phase"], "PRECLOSE")
        self.assertTrue(report["preclose_is_separate_unmatched_cohort"])
        self.assertEqual(report["per_horizon"][3]["categories"]["CENSORED_MISSING"], 3)
        self.assertFalse(report["frozen_original_labels_modified"])


if __name__ == "__main__":
    unittest.main()
