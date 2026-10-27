"""Offline IEX outcome audit tests; no external data and no retroactive claims."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_iex_prospective import collect, persist
from backtest.obsidian_iex_outcomes import evaluate
from backtest.obsidian_iex_corporate_actions import ACTION_FLAGS

AT = datetime(2026, 10, 27, 19, 50, tzinfo=timezone.utc)


class Provider:
    def assets(self):
        return [{"symbol": s, "exchange": "NASDAQ", "status": "active"}
                for s in ("AAAA", "BBBB", "CCCC")]

    def snapshots(self, symbols):
        prices = {"AAAA": 9.5, "BBBB": 11, "CCCC": 7}
        return {s: {"latestTrade": {"p": prices[s], "t": "2026-10-27T19:49:00Z"},
                    "prevDailyBar": {"c": 10, "t": "2026-10-26T19:59:00Z"}}
                for s in symbols}


def outcome(ticker, close):
    row = {"ticker": ticker, "verified": True, "regular_session": True,
            "provider_conflict": False, "corporate_actions_clear": True,
            "previous_session_date": "2026-10-26",
            "previous_regular_close": 10, "regular_close": close,
            "close_at": "2026-10-27T20:00:00Z",
            "collected_at": "2026-10-27T20:10:00Z",
            "source_url": "https://example.org/verified"}
    row["corporate_action_review"] = {
        "status": "NO_ACTIONS_CONFIRMED", "verified": True,
        "reviewed_sessions": ["2026-10-26", "2026-10-27"],
        "checked_at": "2026-10-27T20:08:00Z",
        "source_url": "https://corporate-action-provider.example/independent-review",
        "prior_symbol": ticker, "current_symbol": ticker,
        "prior_security_id": "CUSIP-" + ticker,
        "current_security_id": "CUSIP-" + ticker,
        "action_flags": {key: False for key in ACTION_FLAGS},
    }
    row["independent_eod_sources"] = [
        {"source_id": "EOD_VENDOR_A", "url": "https://source-a.example/eod",
         "observed_at": "2026-10-27T20:04:00Z", "verified": True,
         "regular_close": close, "previous_regular_close": 10},
        {"source_id": "EOD_VENDOR_B", "url": "https://source-b.example/eod",
         "observed_at": "2026-10-27T20:07:00Z", "verified": True,
         "regular_close": close, "previous_regular_close": 10},
    ]
    return row


class IEXOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.capture = self.root / "capture"
        persist(*collect(Provider(), clock=lambda: AT), self.capture)
        self.outcomes = self.root / "outcomes.jsonl"

    def run_rows(self, rows):
        self.outcomes.write_text("".join(json.dumps(row) + "\n" for row in rows))
        return evaluate(self.capture, self.outcomes)

    def test_conditional_recall_without_trade_claim(self):
        report = self.run_rows([outcome("AAAA", 7), outcome("BBBB", 7), outcome("CCCC", 9)])
        self.assertEqual(report["verified_20pct_collapses"], 2)
        self.assertEqual(report["preclose_iex_watch_hits"], 1)
        self.assertEqual(report["unwatched_collapses"], 1)
        self.assertEqual(report["conditional_recall"], .5)
        self.assertIsNone(report["verified_smg_eligible_recall"])
        self.assertIsNone(report["after_cost_pnl"])

    def test_missing_outcomes_censored(self):
        report = self.run_rows([outcome("AAAA", 7)])
        self.assertEqual(report["outcomes_censored"], 2)

    def test_afterhours_bar_censored(self):
        row = outcome("AAAA", 5)
        row["close_at"] = "2026-10-27T20:30:00Z"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_conflicted_eod_censored(self):
        row = outcome("AAAA", 5)
        row["provider_conflict"] = True
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_missing_independent_sources_censored(self):
        row = outcome("AAAA", 7)
        del row["independent_eod_sources"]
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_disagreeing_independent_close_censored(self):
        row = outcome("AAAA", 7)
        row["independent_eod_sources"][1]["regular_close"] = 7.1
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_same_host_not_independent_censored(self):
        row = outcome("AAAA", 7)
        row["independent_eod_sources"][1]["url"] = "https://source-a.example/another"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_late_or_backdated_eod_source_censored(self):
        row = outcome("AAAA", 7)
        row["independent_eod_sources"][1]["observed_at"] = "2026-10-27T19:55:00Z"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_self_attested_clear_without_review_censored(self):
        row = outcome("AAAA", 7)
        del row["corporate_action_review"]
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_spinoff_censored_even_when_both_closes_agree(self):
        row = outcome("AAAA", 7)
        row["corporate_action_review"]["action_flags"]["spin_off"] = True
        self.assertEqual(self.run_rows([row])["verified_20pct_collapses"], 0)
        self.assertEqual(self.run_rows([row])["outcomes_censored"], 3)

    def test_rename_or_security_id_change_censored(self):
        row = outcome("AAAA", 7)
        row["corporate_action_review"]["current_symbol"] = "BBBB"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)
        row = outcome("AAAA", 7)
        row["corporate_action_review"]["current_security_id"] = "CUSIP-OTHER"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_split_dividend_rights_and_adr_changes_censored(self):
        for flag in ("split", "reverse_split", "special_dividend",
                     "rights_distribution", "adr_ratio_change"):
            with self.subTest(flag=flag):
                row = outcome("AAAA", 7)
                row["corporate_action_review"]["action_flags"][flag] = True
                self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_missing_action_flag_or_future_review_censored(self):
        row = outcome("AAAA", 7)
        del row["corporate_action_review"]["action_flags"]["spin_off"]
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)
        row = outcome("AAAA", 7)
        row["corporate_action_review"]["checked_at"] = "2026-10-27T20:30:00Z"
        self.assertEqual(self.run_rows([row])["outcomes_verified"], 0)

    def test_duplicate_outcomes_rejected(self):
        with self.assertRaises(ValueError):
            self.run_rows([outcome("AAAA", 7), outcome("AAAA", 7)])

    def test_empty_outcomes_no_fabricated_metrics(self):
        report = self.run_rows([])
        self.assertIsNone(report["conditional_recall"])
        self.assertIsNone(report["conditional_precision"])


if __name__ == "__main__":
    unittest.main()
