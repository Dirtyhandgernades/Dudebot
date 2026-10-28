"""Synthetic matched-cohort lock tests. No prices or actual performance."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from backtest.obsidian_matched_cohort_lock import lock


def row(ticker, morning, intraday, transition, same_id=True, same_ref=True):
    return {"ticker": ticker, "morning_status": morning,
            "intraday_status": intraday, "transition": transition,
            "same_asset_id": same_id, "same_iex_previous_bar": same_ref}


EARLY = "IEX_INDICATIVE_EARLY_2_TO_15"
OTHER = "IEX_INDICATIVE_OTHER"
STALE = "STALE_OR_FUTURE_IEX_PRINT"


class MatchedCohortLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.m = Path(self.tmp.name) / "morning"
        self.i = Path(self.tmp.name) / "intraday"
        self.m.mkdir()
        self.i.mkdir()
        (self.m / "manifest.json").write_text(json.dumps({
            "phase": "MORNING", "finished_at": "2026-10-28T14:16:00Z"}))
        (self.i / "manifest.json").write_text(json.dumps({
            "phase": "INTRADAY", "finished_at": "2026-10-28T17:48:00Z"}))

    def run_rows(self, rows):
        counts = {"union_symbols": len(rows),
                  "morning_watches": sum(r["morning_status"] == EARLY for r in rows),
                  "intraday_watches": sum(r["intraday_status"] == EARLY for r in rows)}
        fake = {"session_date": "2026-10-28",
                "morning_universe_sha256": "a" * 64,
                "intraday_universe_sha256": "b" * 64,
                "counts": counts, "full_unselected_union_ledger": rows}
        with patch("backtest.obsidian_matched_cohort_lock.compare", return_value=fake):
            return lock(self.m, self.i)

    def test_one_symbol_one_case_earliest_watch_wins(self):
        result = self.run_rows([row("AAAA", EARLY, EARLY, "PERSISTENT_PRICE_ONLY_WATCH")])
        self.assertEqual(result["counts"]["union_symbols"], 1)
        self.assertEqual(result["counts"]["any_original_price_watch"], 1)
        self.assertEqual(result["full_original_union_rows"][0]["first_original_watch_phase"], "MORNING")
        self.assertEqual(result["full_original_union_rows"][0]["first_original_watch_decision_not_before"], "2026-10-28T14:16:00+00:00")
        self.assertIsNone(result["precision"])
        self.assertFalse(result["matched_outcome_scoring_enabled"])

    def test_new_intraday_comparable_vs_stale_morning(self):
        report = self.run_rows([
            row("NEW", OTHER, EARLY, "NEW_COMPARABLE_IEX_THRESHOLD_CROSSING"),
            row("STALE", STALE, EARLY, "PREVIOUSLY_UNUSABLE_OR_BLOCKED_NOT_NEW_ONSET")])
        new, stale = report["full_original_union_rows"]
        self.assertEqual(new["watch_onset_interpretation"], "NEW_COMPARABLE_INTRADAY_IEX_THRESHOLD_CROSSING")
        self.assertEqual(stale["watch_onset_interpretation"], "INTRADAY_VISIBLE_ONSET_NOT_ESTABLISHED")
        self.assertEqual(report["counts"]["first_intraday_price_watch"], 2)

    def test_missing_and_changed_security_retained_not_eligible(self):
        result = self.run_rows([
            row("ABSENT", "NOT_IN_MORNING_UNIVERSE", EARLY, "ADDED_TO_UNIVERSE_NOT_PROVEN_NEW_SIGNAL", None, None),
            row("CHANGED", EARLY, OTHER, "WATCH_DROPPED_OR_UNOBSERVABLE", False, False),
            row("NO", OTHER, OTHER, "NOT_A_WATCH_AT_EITHER_CAPTURE")])
        a, b, c = result["full_original_union_rows"]
        self.assertEqual(a["matched_source_status"], "UNMATCHED_CAPTURE_UNIVERSE")
        self.assertEqual(b["matched_source_status"], "QUARANTINED_SECURITY_IDENTITY_CHANGE")
        self.assertIsNone(c["first_original_watch_phase"])
        self.assertEqual(result["counts"]["union_symbols"], 3)
        self.assertTrue(all(not r["automatically_scoreable"] for r in (a, b, c)))

    def test_changed_previous_bar_is_quarantined(self):
        r = self.run_rows([row("X", EARLY, EARLY, "PERSISTENT_BUT_SOURCE_NOT_COMPARABLE", True, False)])
        self.assertEqual(r["full_original_union_rows"][0]["matched_source_status"],
                         "QUARANTINED_REFERENCE_CHANGE_OR_MISSING")

    def test_duplicate_ticker_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            self.run_rows([row("X", OTHER, OTHER, "NONE"),
                           row("X", OTHER, OTHER, "NONE")])

    def test_capture_timestamps_must_be_ordered(self):
        (self.i / "manifest.json").write_text(json.dumps({
            "phase": "INTRADAY", "finished_at": "2026-10-28T13:00:00Z"}))
        with self.assertRaisesRegex(ValueError, "TIMESTAMPS"):
            self.run_rows([])

    def test_cannot_claim_performance_from_any_cohort(self):
        r = self.run_rows([row("X", EARLY, OTHER, "WATCH_DROPPED_OR_UNOBSERVABLE")])
        self.assertEqual(r["externally_verified_outcome_rows"], 0)
        self.assertIsNone(r["recall"])
        self.assertIsNone(r["after_cost_pnl"])
        self.assertFalse(r["correlated_scans_counted_as_independent_events"])


if __name__ == "__main__":
    unittest.main()
