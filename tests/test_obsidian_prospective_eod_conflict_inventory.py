"""Synthetic all-source conflict ledger tests; no real EOD observations."""
import unittest
from datetime import date
from backtest.obsidian_eod_conflict_inventory import inventory

D = date(2026, 10, 28)
P = date(2026, 10, 27)
NOW = "2026-10-28T21:00:00Z"


def cal(early=False):
    return {"session_date": D.isoformat(), "previous_session_date": P.isoformat(),
            "session_open": True, "exchange_calendar_url": "https://www.nyse.com/markets/hours-calendars",
            "regular_close_at": "2026-10-28T17:00:00Z" if early else "2026-10-28T20:00:00Z",
            "previous_regular_close_at": "2026-10-27T20:00:00Z",
            "early_close": early}


def row(source="a", group="one", domain="one.example", close="7.99", prior="10"):
    return {"source_id": source, "provider_organization": group,
            "source_url": "https://" + domain + "/eod", "symbol": "ZZZZ",
            "security_id": "ISSUER1:COMMON", "previous_security_id": "ISSUER1:COMMON",
            "session_date": D.isoformat(), "previous_session_date": P.isoformat(),
            "kind": "regular_close", "session_complete": True,
            "regular_close": close, "previous_regular_close": prior,
            "regular_close_asof": "2026-10-28T20:00:00Z",
            "previous_regular_close_asof": "2026-10-27T20:00:00Z",
            "observed_at": "2026-10-28T20:30:00Z"}


def check(rows, calendar=None):
    return inventory("ZZZZ", D, P, cal() if calendar is None else calendar, rows, NOW)


class AllSourceLedgerTests(unittest.TestCase):
    def test_two_matching_claims_remain_unverified_and_censored(self):
        r = check([row(), row("b", "two", "two.example")])
        self.assertEqual(r["structural_status"], "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING")
        self.assertFalse(r["official_regular_close_verified"])
        self.assertTrue(r["outcome_censored_pending_external_evidence"])
        self.assertIsNone(r["verified_20pct_prediction_success"])

    def test_third_conflicting_report_is_retained(self):
        r = check([row(), row("b", "two", "two.example"), row("c", "three", "three.example", "8.2")])
        self.assertEqual(r["retained_report_count"], 3)
        self.assertIn("ALL_SOURCE_REGULAR_CLOSE_CONFLICT", r["issues"])
        self.assertIn("TWENTY_PERCENT_THRESHOLD_STRADDLED", r["issues"])

    def test_bad_third_report_is_not_silently_discarded(self):
        third = row("c", "three", "three.example")
        third["regular_close_asof"] = "2026-10-28T19:59:35Z"
        r = check([row(), row("b", "two", "two.example"), third])
        self.assertEqual(r["retained_report_count"], 3)
        self.assertEqual(r["source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertIn("CLOSE_ASOF_NOT_EXACT_EXCHANGE_SESSION_END", r["issues"])

    def test_provider_aliases_do_not_count_as_independent(self):
        r = check([row(), row("b", "one", "another.example")])
        self.assertIn("TWO_DISTINCT_PROVIDER_ORGANIZATIONS_AND_HOSTS_NOT_ESTABLISHED", r["issues"])

    def test_security_id_change_censored(self):
        other = row("b", "two", "two.example")
        other["previous_security_id"] = "ISSUER0:COMMON"
        r = check([row(), other])
        self.assertIn("SECURITY_IDENTITY_NOT_MATCHED", r["issues"])

    def test_early_close_never_uses_frozen_1600_protocol(self):
        a = row()
        b = row("b", "two", "two.example")
        for r in (a, b):
            r["regular_close_asof"] = "2026-10-28T17:00:00Z"
            r["observed_at"] = "2026-10-28T18:00:00Z"
        result = check([a, b], cal(True))
        self.assertIn("EARLY_CLOSE_REQUIRES_SEPARATE_NONFROZEN_PROTOCOL", result["issues"])

    def test_future_source_and_duplicate_id_fail_closed(self):
        b = row("a", "two", "two.example")
        b["observed_at"] = "2026-10-29T00:00:00Z"
        r = check([row(), b])
        self.assertIn("DUPLICATE_OR_MISSING_SOURCE_ID", r["issues"])
        self.assertIn("SOURCE_OBSERVATION_NOT_POSTCLOSE_OR_FUTURE", r["issues"])

    def test_malformed_unhashable_source_id_censored_not_crash(self):
        bad = row("b", "two", "two.example")
        bad["source_id"] = ["unhashable"]
        r = check([row(), bad])
        self.assertEqual(r["retained_report_count"], 2)
        self.assertIn("DUPLICATE_OR_MISSING_SOURCE_ID", r["issues"])
        self.assertEqual(r["source_rows"][1]["status"], "REJECTED_CENSORED")

    def test_previous_close_disagreement_blocks(self):
        r = check([row(), row("b", "two", "two.example", prior="10.001")])
        self.assertIn("THRESHOLD_REFERENCE_PREVIOUS_CLOSE_DISAGREEMENT", r["issues"])

    def test_missing_rows_are_censored_not_negative_outcomes(self):
        r = check([])
        self.assertIn("NO_EOD_SOURCE_REPORTS", r["issues"])
        self.assertIsNone(r["verified_20pct_prediction_success"])


if __name__ == "__main__":
    unittest.main()
