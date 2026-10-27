"""Adversarial offline tests for point-in-time outcome validation."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_prospective_capture import collect, persist
from backtest.obsidian_prospective_outcomes import evaluate, InvalidOutcome

AT = datetime(2026, 10, 26, 19, 50, tzinfo=timezone.utc)


class Provider:
    def assets(self):
        return [{"symbol": x, "status": "active", "exchange": "NASDAQ"}
                for x in ("AAAA", "BBBB", "CCCC")]

    def snapshots(self, symbols):
        prices = {"AAAA": 9.5, "BBBB": 7.0, "CCCC": 11.0}
        return {x: {"latestTrade": {"p": prices[x], "t": "2026-10-26T19:49:00Z"},
                    "prevDailyBar": {"c": 10, "t": "2026-10-23T04:00:00Z"},
                    "minuteBar": {"t": "2026-10-26T19:48:00Z"}} for x in symbols}


def outcome(symbol, close):
    return {"ticker": symbol, "verified": True, "regular_session": True,
            "corporate_actions_clear": True, "provider_conflict": False,
            "source_url": "https://example.org/independent-eod",
            "previous_regular_close": 10, "previous_session_date": "2026-10-23",
            "regular_close": close, "close_at": "2026-10-26T20:00:00Z",
            "collected_at": "2026-10-26T20:05:00Z"}


class ProspectiveOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.capture = self.root / "capture"
        persist(*collect(Provider(), clock=lambda: AT), destination=self.capture)
        self.outcomes = self.root / "outcomes.jsonl"

    def run_rows(self, rows):
        self.outcomes.write_text("".join(json.dumps(x) + "\n" for x in rows))
        return evaluate(self.capture, self.outcomes)

    def test_matched_price_only_counts_not_trade_claim(self):
        result = self.run_rows([outcome("AAAA", 7), outcome("BBBB", 9),
                                outcome("CCCC", 7)])
        self.assertEqual(result["verified_collapse_count"], 2)
        self.assertEqual(result["price_only_watch_collapse_count"], 1)
        self.assertEqual(result["unwatched_verified_collapse_count"], 1)
        self.assertEqual(result["price_only_recall_conditional_on_verified_outcomes"], .5)
        self.assertIsNone(result["smg_eligible_recall"])
        self.assertIsNone(result["after_cost_pnl"])
        self.assertFalse(result["trade_authorized"])

    def test_missing_outcome_is_censored(self):
        result = self.run_rows([outcome("AAAA", 7)])
        self.assertEqual(result["outcomes_missing_or_censored"], 2)
        self.assertEqual(result["verified_collapse_count"], 1)

    def test_after_hours_quote_is_not_regular_close(self):
        row = outcome("AAAA", 6)
        row["close_at"] = "2026-10-26T20:30:00Z"
        result = self.run_rows([row])
        self.assertEqual(result["outcomes_verified"], 0)

    def test_future_data_and_backdated_collection_censored(self):
        row = outcome("AAAA", 6)
        row["collected_at"] = "2026-10-26T19:59:00Z"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_conflicting_provider_censored(self):
        row = outcome("AAAA", 6)
        row["provider_conflict"] = True
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_corporate_action_unresolved_censored(self):
        row = outcome("AAAA", 6)
        row["corporate_actions_clear"] = None
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_prior_session_mismatch_censored(self):
        row = outcome("AAAA", 6)
        row["previous_session_date"] = "2026-10-22"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_duplicate_outcomes_rejected(self):
        with self.assertRaises(InvalidOutcome):
            self.run_rows([outcome("AAAA", 7), outcome("AAAA", 8)])

    def test_out_of_universe_outcome_rejected(self):
        with self.assertRaises(InvalidOutcome):
            self.run_rows([outcome("ZZZZ", 7)])

    def test_tampered_capture_rejected(self):
        (self.capture / "candidates.jsonl").write_text("")
        with self.assertRaises(Exception):
            self.run_rows([outcome("AAAA", 7)])

    def test_empty_outcomes_no_invented_performance(self):
        result = self.run_rows([])
        self.assertIsNone(result["price_only_recall_conditional_on_verified_outcomes"])
        self.assertIsNone(result["price_only_precision_conditional_on_verified_outcomes"])
        self.assertEqual(result["outcomes_missing_or_censored"], 3)


if __name__ == "__main__":
    unittest.main()
