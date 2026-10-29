"""Synthetic action/identity conflict checks; not market observations."""
import unittest
from datetime import date
from backtest.obsidian_eod_action_identity_shadow import audit_action_identity

DAY = date(2026, 10, 28)
PREV = date(2026, 10, 27)
COLLECTED = "2026-10-28T21:00:00Z"


def row(source="a", provider="alpha", domain="alpha.example"):
    return {
        "source_id": source, "provider_organization": provider,
        "source_url": "https://" + domain + "/close", "symbol": "ZZZZ",
        "session_date": DAY.isoformat(), "previous_session_date": PREV.isoformat(),
        "security_id": "ID:COMMON", "previous_security_id": "ID:COMMON",
        "issuer_class": "COMMON", "previous_issuer_class": "COMMON",
        "observed_at": "2026-10-28T20:25:00Z",
        "corporate_action_evidence": {
            "source_url": "https://" + domain + "/actions",
            "security_id": "ID:COMMON", "previous_security_id": "ID:COMMON",
            "issuer_class": "COMMON", "status": "NONE",
            "previous_close_basis": "UNADJUSTED",
            "coverage_start": PREV.isoformat(), "coverage_end": DAY.isoformat(),
            "checked_at": "2026-10-28T20:30:00Z",
        },
    }


def check(rows):
    return audit_action_identity("ZZZZ", DAY, PREV, rows, COLLECTED)


class ActionIdentityShadowTests(unittest.TestCase):
    def test_two_matching_claims_are_not_external_proof(self):
        result = check([row(), row("b", "beta", "beta.example")])
        self.assertEqual(result["status"], "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING")
        self.assertFalse(result["official_close_verified"])
        self.assertFalse(result["security_identity_and_corporate_actions_authenticated"])
        self.assertIsNone(result["verified_20pct_prediction_success"])
        self.assertTrue(result["outcome_censored_pending_external_evidence"])

    def test_missing_action_record_censors_every_source(self):
        b = row("b", "beta", "beta.example")
        b.pop("corporate_action_evidence")
        result = check([row(), b])
        self.assertIn("ACTION_SOURCE_PROVENANCE_MISSING", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertEqual(result["retained_report_count"], 2)

    def test_conflicting_split_claim_even_from_rejected_source(self):
        b = row("b", "beta", "beta.example")
        b["corporate_action_evidence"]["status"] = "SPLIT"
        result = check([row(), b])
        self.assertIn("CROSS_SOURCE_CORPORATE_ACTION_CLAIM_CONFLICT", result["issues"])
        self.assertIn("ACTION_OR_ADJUSTED_CLOSE_REQUIRES_EXTERNAL_RECONCILIATION", result["issues"])
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_cross_provider_security_identity_conflict(self):
        b = row("b", "beta", "beta.example")
        b["security_id"] = b["previous_security_id"] = "OTHER:COMMON"
        b["corporate_action_evidence"]["security_id"] = "OTHER:COMMON"
        b["corporate_action_evidence"]["previous_security_id"] = "OTHER:COMMON"
        result = check([row(), b])
        self.assertIn("CROSS_SOURCE_SECURITY_IDENTITY_CLAIM_CONFLICT", result["issues"])

    def test_previous_close_adjustment_conflict(self):
        b = row("b", "beta", "beta.example")
        b["corporate_action_evidence"]["previous_close_basis"] = "ADJUSTED"
        result = check([row(), b])
        self.assertIn("CROSS_SOURCE_PREVIOUS_CLOSE_BASIS_CLAIM_CONFLICT", result["issues"])
        self.assertIn("ACTION_OR_ADJUSTED_CLOSE_REQUIRES_EXTERNAL_RECONCILIATION", result["issues"])

    def test_stale_action_check_is_rejected(self):
        b = row("b", "beta", "beta.example")
        b["corporate_action_evidence"]["checked_at"] = "2026-10-28T19:59:00Z"
        result = check([row(), b])
        self.assertIn("ACTION_OR_SOURCE_TIMESTAMP_NOT_POSTCLOSE", result["issues"])

    def test_incomplete_previous_to_current_window_is_rejected(self):
        b = row("b", "beta", "beta.example")
        b["corporate_action_evidence"]["coverage_start"] = "2026-10-28"
        result = check([row(), b])
        self.assertIn("CORPORATE_ACTION_WINDOW_NOT_COMPLETE", result["issues"])

    def test_same_provider_two_hosts_not_independent(self):
        result = check([row(), row("b", "alpha", "mirror.example")])
        self.assertIn("TWO_DISTINCT_PROVIDER_ORGANIZATIONS_AND_HOSTS_NOT_ESTABLISHED", result["issues"])

    def test_malformed_third_source_retained_and_censored(self):
        result = check([row(), row("b", "beta", "beta.example"), ["bad"]])
        self.assertEqual(result["retained_report_count"], 3)
        self.assertIn("MALFORMED_SOURCE_RECORD", result["issues"])
        self.assertEqual(result["all_source_rows"][2]["status"], "REJECTED_CENSORED")

    def test_source_urls_are_not_echoed_with_credentials(self):
        a = row()
        a["corporate_action_evidence"]["source_url"] += "?key=SECRET"
        result = check([a, row("b", "beta", "beta.example")])
        self.assertNotIn("SECRET", str(result))

    def test_invalid_session_chain_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "VALID_SESSION_CHAIN_REQUIRED"):
            audit_action_identity("ZZZZ", DAY, DAY, [], COLLECTED)


if __name__ == "__main__":
    unittest.main()
