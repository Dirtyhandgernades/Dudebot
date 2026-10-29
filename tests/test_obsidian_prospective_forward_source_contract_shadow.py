"""Synthetic regression: frozen scorer source acceptance vs stricter shadow intake."""
import copy
import unittest

from backtest.obsidian_forward_source_contract_shadow import audit_outcome_source_contract
from backtest.obsidian_iex_outcomes import corroborated
from backtest.obsidian_prospective_capture import asof

DAY = "2026-10-27"
PRIOR = "2026-10-26"


def source(group, host, close=8.0, asof_at="2026-10-27T20:00:00Z"):
    return {
        "source_id": group + "_history", "provider_group": group,
        "url": "https://" + host + "/prices",
        "symbol": "ZZZZ", "session_date": DAY, "previous_session_date": PRIOR,
        "kind": "regular_close", "session_complete": True,
        "regular_close": close, "previous_regular_close": 10.0,
        "regular_close_asof": asof_at,
        "observed_at": "2026-10-27T20:07:00Z", "verified": True,
    }


def outcome():
    return {
        "ticker": "ZZZZ", "previous_session_date": PRIOR,
        "regular_close": 8.0, "previous_regular_close": 10.0,
        "regular_session": True, "verified": True, "provider_conflict": False,
        "close_at": "2026-10-27T20:00:00Z",
        "collected_at": "2026-10-27T20:12:00Z",
        "independent_eod_sources": [
            source("independent_a", "a.example"),
            source("independent_b", "b.example"),
        ],
    }


class ShadowContractTests(unittest.TestCase):
    def check(self, row):
        return audit_outcome_source_contract(row, DAY)

    def test_consistent_sources_do_not_promote_to_official_or_trade(self):
        result = self.check(outcome())
        self.assertEqual(result["status"], "SHADOW_SOURCES_CONSISTENT_NOT_OFFICIAL")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])
        self.assertFalse(result["trade_authorized"])
        self.assertFalse(result["source_inventory_completeness_externally_verified"])

    def test_legacy_frozen_source_contract_accepts_missing_asof_but_shadow_blocks(self):
        row = outcome()
        for item in row["independent_eod_sources"]:
            item.pop("regular_close_asof")
            item.pop("provider_group")
            item.pop("session_date")
            item.pop("previous_session_date")
            item.pop("symbol")
            item.pop("kind")
            item.pop("session_complete")
        self.assertTrue(corroborated(
            row, asof(row["close_at"]), asof(row["collected_at"])))
        result = self.check(row)
        self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
        self.assertEqual(result["status"], "SHADOW_SOURCE_CONTRACT_BLOCKED")

    def test_missing_source_asof_alone_blocks(self):
        row = outcome()
        row["independent_eod_sources"][1].pop("regular_close_asof")
        self.assertIn("NON_1600_ET_REGULAR_CLOSE_SOURCE", self.check(row)["issues"])

    def test_same_provider_aliases_are_not_independent(self):
        row = outcome()
        row["independent_eod_sources"][1] = source("independent_a", "alias.example")
        self.assertIn("INSUFFICIENT_DISTINCT_HOST_AND_PROVIDER_EVIDENCE",
                      self.check(row)["issues"])

    def test_third_conflicting_provider_not_silently_dropped(self):
        row = outcome()
        row["independent_eod_sources"].append(source("third", "c.example", 8.10))
        issues = self.check(row)["issues"]
        self.assertIn("CONFLICTING_REGULAR_CLOSE_REPORTS", issues)
        self.assertIn("SOURCE_TOP_LEVEL_PRICE_MISMATCH", issues)

    def test_top_level_price_cannot_disagree_with_consistent_sources(self):
        row = outcome()
        row["regular_close"] = 7.0
        self.assertIn("SOURCE_TOP_LEVEL_PRICE_MISMATCH", self.check(row)["issues"])

    def test_1600_and_35_seconds_not_exact_official_close(self):
        row = outcome()
        row["close_at"] = "2026-10-27T20:00:35Z"
        self.assertIn("TOP_LEVEL_CLOSE_NOT_EXACT_1600_ET", self.check(row)["issues"])

    def test_155935_last_print_not_official_close(self):
        row = outcome()
        row["independent_eod_sources"][1]["regular_close_asof"] = "2026-10-27T19:59:35Z"
        self.assertIn("NON_1600_ET_REGULAR_CLOSE_SOURCE", self.check(row)["issues"])

    def test_unverified_source_not_promoted(self):
        row = outcome()
        row["independent_eod_sources"][1]["verified"] = False
        self.assertIn("SOURCE_NOT_INDEPENDENTLY_VERIFIED", self.check(row)["issues"])

    def test_source_observed_before_close_not_promoted(self):
        row = outcome()
        row["independent_eod_sources"][1]["observed_at"] = "2026-10-27T19:59:00Z"
        self.assertIn("STALE_OR_UNTIMED_SOURCE", self.check(row)["issues"])

    def test_wrong_security_source_not_promoted(self):
        row = outcome()
        row["independent_eod_sources"][1]["symbol"] = "OTHER"
        self.assertIn("WRONG_SECURITY_SESSION_OR_PRICE_KIND", self.check(row)["issues"])

    def test_extreme_top_level_close_censored_without_overflow(self):
        row = outcome()
        row["regular_close"] = "1e999999999999999"
        result = self.check(row)
        self.assertEqual(result["status"], "SHADOW_SOURCE_CONTRACT_BLOCKED")
        self.assertIn("INVALID_TOP_LEVEL_PRICES", result["issues"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_extreme_source_close_censored_without_overflow(self):
        row = outcome()
        row["independent_eod_sources"][1]["regular_close"] = "1e999999999999999"
        result = self.check(row)
        self.assertIn("SOURCE_TOP_LEVEL_PRICE_MISMATCH", result["issues"])
        self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
        self.assertEqual(result["supplied_reports"], 2)
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_malformed_collection_timestamp_censors_without_crash(self):
        row = outcome()
        row["collected_at"] = "not-a-time"
        result = self.check(row)
        self.assertIn("SOURCE_PREFLIGHT_INVALID_COLLECTION_OR_INPUT", result["issues"])
        self.assertEqual(result["supplied_reports"], 2)
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_missing_reports_fail_closed(self):
        row = outcome()
        row.pop("independent_eod_sources")
        self.assertIn("COMPLETE_SOURCE_REPORT_LIST_MISSING", self.check(row)["issues"])

    def test_malformed_outcome_fail_closed(self):
        self.assertEqual(self.check(None)["status"], "SHADOW_SOURCE_CONTRACT_BLOCKED")


if __name__ == "__main__":
    unittest.main()
