"""Synthetic, outcome-blind regression for all-source EOD intake."""
import unittest
from datetime import date
from backtest.obsidian_eod_source_preflight import preflight

COLLECTED = "2026-10-27T23:49:00Z"
DAY = date(2026, 10, 27)
PRIOR = date(2026, 10, 26)


def row(group, host, close="8.00", prior="10.00", observed="2026-10-27T20:10:00Z"):
    return {"source_id": group + "_daily", "provider_group": group,
            "url": "https://" + host + "/history", "symbol": "ZZZZ",
            "session_date": "2026-10-27", "previous_session_date": "2026-10-26",
            "kind": "regular_close", "session_complete": True,
            "regular_close": close, "previous_regular_close": prior,
            "observed_at": observed}


class SourcePreflightTests(unittest.TestCase):
    def test_two_agreeing_sources_still_not_official_or_smg_verified(self):
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), row("two", "two.example")], COLLECTED)
        self.assertEqual(r["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")
        self.assertFalse(r["eligible_for_frozen_forward_scoring"])
        self.assertFalse(r["corporate_action_and_security_identity_verified"])

    def test_third_conflicting_source_cannot_be_silently_ignored(self):
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), row("two", "two.example"), row("three", "three.example", close="8.11")], COLLECTED)
        self.assertIn("CONFLICTING_REGULAR_CLOSE_REPORTS", r["issues"])
        self.assertEqual(r["supplied_reports"], 3)
        self.assertEqual(r["status"], "BLOCKED_SOURCE_EVIDENCE")

    def test_same_provider_alias_is_not_independent(self):
        r = preflight("ZZZZ", DAY, PRIOR, [row("vendor", "us.vendor.example"), row("vendor", "ca.vendor.example")], COLLECTED)
        self.assertIn("INSUFFICIENT_DISTINCT_HOST_AND_PROVIDER_EVIDENCE", r["issues"])

    def test_intraday_snapshot_is_not_eod(self):
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), row("two", "two.example", observed="2026-10-27T19:59:59Z")], COLLECTED)
        self.assertIn("STALE_OR_UNTIMED_SOURCE", r["issues"])

    def test_prior_close_conflict_blocks(self):
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), row("two", "two.example", prior="10.02")], COLLECTED)
        self.assertIn("CONFLICTING_PREVIOUS_CLOSE_REPORTS", r["issues"])

    def test_wrong_security_and_malformed_are_not_dropped(self):
        other = row("two", "two.example")
        other["symbol"] = "NOT_ZZZZ"
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), other, None], COLLECTED)
        self.assertIn("WRONG_SECURITY_SESSION_OR_PRICE_KIND", r["issues"])
        self.assertIn("MALFORMED_SOURCE_RECORD", r["issues"])

    def test_future_dated_source_is_rejected(self):
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), row("two", "two.example", observed="2026-10-28T01:00:00Z")], COLLECTED)
        self.assertIn("STALE_OR_UNTIMED_SOURCE", r["issues"])

    def test_half_cent_tolerance_boundary(self):
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), row("two", "two.example", close="8.005")], COLLECTED)
        self.assertEqual(r["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")


if __name__ == "__main__":
    unittest.main()
