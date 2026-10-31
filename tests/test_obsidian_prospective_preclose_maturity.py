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
             "provider_conflict": True, "collected_at": "2026-10-30T21:01:00Z"},
            {"ticker": "BBBB", "session_date": DAYS[0],
             "regular_close": 6.8},
        ]
        report = build(self.capture, calendar(), rows,
                       "2026-11-05T22:00:00Z")
        categories = report["per_horizon"][0]["categories"]
        self.assertEqual(categories["SOURCE_CONFLICT"], 0)
        self.assertEqual(categories["CENSORED_BLOCKED"], 2)
        self.assertEqual(categories["CENSORED_MISSING"], 1)
        self.assertEqual(report["per_horizon"][0]["unverified_conflict_claims_as_of"], 1)
        self.assertEqual(categories["VERIFIED"], 0)
        self.assertFalse(report["independent_official_close_authentication_performed"])

    def test_bare_provider_conflict_is_only_an_unverified_claim(self):
        row = {"ticker": "AAAA", "session_date": DAYS[0],
               "provider_conflict": True, "collected_at": "2026-10-30T21:01:00Z"}
        report = build(self.capture, calendar(), [row],
                       "2026-10-30T22:00:00Z")
        horizon = report["per_horizon"][0]
        self.assertEqual(horizon["categories"]["SOURCE_CONFLICT"], 0)
        self.assertEqual(horizon["categories"]["CENSORED_BLOCKED"], 1)
        self.assertEqual(horizon["unverified_conflict_claims_as_of"], 1)
        self.assertEqual(sum(horizon["unverified_conflict_claims_by_watch"].values()), 1)
        row_result = report["rows"][0]["horizons"][0]
        self.assertTrue(row_result["provider_conflict_claimed_as_of_unverified"])
        self.assertEqual(row_result["reason"], "SUPPLIED_CONFLICT_CLAIM_FAILED_STRUCTURAL_GATE")
        self.assertFalse(row_result["official_close_authenticated"])

    def test_future_source_conflict_does_not_leak_into_past_as_of(self):
        row = {"ticker": "AAAA", "session_date": DAYS[0],
               "provider_conflict": True, "collected_at": "2026-11-02T21:00:00Z"}
        report = build(self.capture, calendar(), [row],
                       "2026-10-30T22:00:00Z")
        h0 = report["per_horizon"][0]["categories"]
        self.assertEqual(h0["SOURCE_CONFLICT"], 0)
        self.assertEqual(h0["CENSORED_BLOCKED"], 0)
        self.assertEqual(h0["CENSORED_MISSING"], 3)
        self.assertEqual(report["provided_source_rows"], 0)
        self.assertEqual(report["per_horizon"][0]["unverified_conflict_claims_as_of"], 0)
        self.assertEqual(report["rows"][0]["horizons"][0]["reason"],
                         "NO_SUPPLIED_OUTCOME_ROW")
        self.assertEqual(report["verified_outcomes"], 0)

    def test_future_session_source_structure_is_not_visible_at_past_as_of(self):
        row = {"ticker": "AAAA", "session_date": DAYS[1],
               "provider_conflict": True,
               "collected_at": "2026-11-02T22:00:00Z"}
        report = build(self.capture, calendar(), [row],
                       "2026-10-30T22:00:00Z")
        h1 = report["rows"][0]["horizons"][1]
        self.assertEqual(h1["category"], "NOT_YET_MATURE")
        self.assertEqual(h1["source_evidence"], "NOT_YET_OBSERVABLE")
        self.assertFalse(h1["provider_conflict_claimed_as_of_unverified"])
        self.assertEqual(report["per_horizon"][1]["unverified_conflict_claims_as_of"], 0)
        self.assertEqual(report["verified_outcomes"], 0)

    def test_postclose_future_receipt_structure_is_not_visible_at_past_as_of(self):
        row = {"ticker": "AAAA", "session_date": DAYS[0],
               "provider_conflict": True,
               "collected_at": "2026-11-02T21:00:00Z"}
        report = build(self.capture, calendar(), [row],
                       "2026-10-30T22:00:00Z")
        h0 = report["rows"][0]["horizons"][0]
        self.assertEqual(h0["category"], "CENSORED_MISSING")
        self.assertEqual(h0["source_evidence"], "MISSING_EOD_SOURCE_ROW")
        self.assertEqual(h0["reason"], "NO_SUPPLIED_OUTCOME_ROW")
        self.assertFalse(h0["provider_conflict_claimed_as_of_unverified"])
        self.assertEqual(report["verified_outcomes"], 0)

    def test_future_receipts_cannot_change_historical_asof_inventory(self):
        # Future evidence must be indistinguishable from no evidence at all,
        # including the public supplied-row count and full prefix inventory.
        row = {"ticker": "AAAA", "session_date": DAYS[0],
               "collected_at": "2026-11-03T22:00:00Z",
               "provider_conflict": True}
        cutoff = "2026-11-02T22:30:00Z"
        baseline = build(self.capture, calendar(), [], cutoff)
        with_future = build(self.capture, calendar(), [row], cutoff)
        self.assertEqual(with_future, baseline)
        after_receipt = build(self.capture, calendar(), [row],
                              "2026-11-04T22:30:00Z")
        self.assertEqual(after_receipt["provided_source_rows"], 1)
        self.assertEqual(after_receipt["per_horizon"][0]
                         ["unverified_conflict_claims_as_of"], 1)

    def test_future_rows_still_fail_duplicate_and_cohort_validation(self):
        future = {"ticker": "AAAA", "session_date": DAYS[0],
                  "collected_at": "2026-11-03T22:00:00Z"}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OUTSIDE"):
            build(self.capture, calendar(), [future, future],
                  "2026-10-30T22:00:00Z")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OUTSIDE"):
            build(self.capture, calendar(),
                  [{**future, "ticker": "NOT_IN_COHORT"}],
                  "2026-10-30T22:00:00Z")

    def test_observable_rejected_source_still_exposes_structural_censor_reason(self):
        row = {"ticker": "AAAA", "session_date": DAYS[0],
               "collected_at": "2026-10-30T21:01:00Z"}
        report = build(self.capture, calendar(), [row],
                       "2026-10-30T22:00:00Z")
        h0 = report["rows"][0]["horizons"][0]
        self.assertEqual(h0["category"], "CENSORED_BLOCKED")
        self.assertEqual(h0["source_evidence"], "SUPPLIED_EOD_EVIDENCE_BLOCKED")
        self.assertFalse(h0["official_close_authenticated"])

    def test_preclose_source_conflict_cannot_be_called_postclose(self):
        row = {"ticker": "AAAA", "session_date": DAYS[0],
               "provider_conflict": True, "collected_at": "2026-10-30T19:59:00Z"}
        report = build(self.capture, calendar(), [row],
                       "2026-10-30T22:00:00Z")
        h0 = report["per_horizon"][0]["categories"]
        self.assertEqual(h0["SOURCE_CONFLICT"], 0)
        self.assertEqual(h0["CENSORED_BLOCKED"], 1)
        self.assertEqual(report["rows"][0]["horizons"][0]["reason"],
                         "SOURCE_RECEIPT_NOT_POSTCLOSE_OR_AFTER_AS_OF")

    def test_unstamped_conflict_does_not_override_source_censoring(self):
        row = {"ticker": "AAAA", "session_date": DAYS[0],
               "provider_conflict": True}
        report = build(self.capture, calendar(), [row],
                       "2026-11-05T22:00:00Z")
        self.assertEqual(report["per_horizon"][0]["categories"]["SOURCE_CONFLICT"], 0)
        self.assertEqual(report["per_horizon"][0]["categories"]["CENSORED_BLOCKED"], 1)

    def test_calendar_checked_after_as_of_is_rejected_for_every_horizon(self):
        # A calendar source checked later cannot be claimed in an earlier
        # as-of report, even when there are no supplied price outcome rows.
        for horizon in range(4):
            with self.subTest(horizon=horizon):
                rows = calendar()
                rows[horizon]["source_checked_at"] = "2026-11-02T12:00:00Z"
                with self.assertRaisesRegex(
                        ValueError, "CALENDAR_SOURCE_CHECK_AFTER_REPORT_AS_OF"):
                    build(self.capture, rows, [], "2026-10-30T21:30:00Z")

    def test_calendar_checked_at_exact_as_of_with_offset_is_allowed(self):
        rows = calendar()
        rows[3]["source_checked_at"] = "2026-10-30T16:30:00-05:00"
        report = build(self.capture, rows, [], "2026-10-30T21:30:00Z")
        self.assertEqual(report["expected_issuer_session_slots"], 12)
        self.assertEqual(report["verified_outcomes"], 0)
        self.assertEqual(
            report["per_horizon"][0]["categories"]["CENSORED_MISSING"], 3)

    def test_as_of_cannot_precede_original_capture_completion(self):
        with self.assertRaisesRegex(ValueError, "AS_OF_PRECEDES_ORIGINAL"):
            build(self.capture, calendar(), [], "2026-10-30T19:49:00Z")

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
