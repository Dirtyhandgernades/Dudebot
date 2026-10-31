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

    def test_distinct_price_providers_shared_action_host_fail_closed(self):
        b = row("b", "beta", "beta.example")
        b["corporate_action_evidence"]["source_url"] = "https://alpha.example/actions"
        result = check([row(), b])
        self.assertIn("TWO_DISTINCT_CORPORATE_ACTION_SOURCE_HOSTS_NOT_ESTABLISHED", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_CENSORED")
        self.assertEqual(result["retained_report_count"], 2)
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_rejected_third_action_host_cannot_establish_independence(self):
        b = row("b", "beta", "beta.example")
        b["corporate_action_evidence"]["source_url"] = "https://alpha.example/another-path"
        c = row("c", "gamma", "gamma.example")
        c["corporate_action_evidence"]["status"] = "SPLIT"
        result = check([row(), b, c])
        self.assertIn("TWO_DISTINCT_CORPORATE_ACTION_SOURCE_HOSTS_NOT_ESTABLISHED", result["issues"])
        self.assertEqual(result["all_source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertEqual(result["retained_report_count"], 3)
        self.assertTrue(result["outcome_censored_pending_external_evidence"])

    def test_action_source_parent_alias_is_not_independent(self):
        a, b = row(), row("b", "beta", "beta.example")
        a["corporate_action_evidence"]["source_url"] = "https://api.action-vendor.example/actions"
        b["corporate_action_evidence"]["source_url"] = "https://data.action-vendor.example/actions"
        result = check([a, b])
        self.assertIn("TWO_DISTINCT_ACTION_SOURCE_PARENT_HINTS_NOT_ESTABLISHED", result["issues"])
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_ACTION_SOURCE_PARENT_HINT", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_CENSORED")

    def test_third_provider_cannot_hide_action_source_alias(self):
        a, b = row(), row("b", "beta", "beta.example")
        a["corporate_action_evidence"]["source_url"] = "https://api.shared-action.example/actions"
        b["corporate_action_evidence"]["source_url"] = "https://data.shared-action.example/actions"
        result = check([a, b, row("c", "gamma", "gamma.example")])
        self.assertEqual(result["structurally_valid_report_count"], 3)
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_ACTION_SOURCE_PARENT_HINT", result["issues"])
        self.assertEqual(result["retained_report_count"], 3)

    def test_price_source_parent_alias_not_hidden_by_third_provider(self):
        a, b = row(), row("b", "beta", "beta.example")
        a["source_url"] = "https://api.feed-vendor.example/close"
        b["source_url"] = "https://data.feed-vendor.example/close"
        result = check([a, b, row("c", "gamma", "gamma.example")])
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_PRICE_SOURCE_PARENT_HINT", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_CENSORED")

    def test_unsafe_action_or_price_url_is_censored(self):
        invalid = ("https://beta.example:444/actions",
                   "https://user@beta.example/actions",
                   "https://beta.example/actions#fragment",
                   "https://beta.example/actions\nInjected: value",
                   "https://[broken/actions")
        for url in invalid:
            with self.subTest(url=url):
                b = row("b", "beta", "beta.example")
                b["corporate_action_evidence"]["source_url"] = url
                result = check([row(), b])
                self.assertIn("ACTION_SOURCE_PROVENANCE_MISSING", result["issues"])
                self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
                self.assertEqual(result["retained_report_count"], 2)
        b = row("b", "beta", "beta.example")
        b["source_url"] = "https://beta.example:444/close"
        result = check([row(), b])
        self.assertIn("PROVIDER_OR_SOURCE_URL_NOT_EVIDENCED", result["issues"])

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

    def test_unhashable_action_claim_censored_not_crash(self):
        b = row("b", "beta", "beta.example")
        b["corporate_action_evidence"]["status"] = ["UNHASHABLE"]
        b["corporate_action_evidence"]["previous_close_basis"] = {"bad": "basis"}
        result = check([row(), b])
        self.assertIn("ACTION_OR_PREVIOUS_CLOSE_BASIS_UNRESOLVED", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")

    def test_rejected_third_prior_issuer_class_conflict_is_indexed(self):
        third = row("c", "gamma", "gamma.example")
        third["previous_issuer_class"] = "ADR"
        result = check([row(), row("b", "beta", "beta.example"), third])
        self.assertIn("CROSS_SOURCE_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT", result["issues"])
        self.assertNotIn("CROSS_SOURCE_ISSUER_CLASS_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["all_source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertEqual(result["previous_issuer_class_claim_groups"], [
            {"previous_issuer_class": "ADR",
             "structurally_valid_source_indices": [], "rejected_source_indices": [2]},
            {"previous_issuer_class": "COMMON",
             "structurally_valid_source_indices": [0, 1], "rejected_source_indices": []},
        ])
        self.assertFalse(result["official_close_verified"])

    def test_rejected_third_action_prior_identity_conflict_is_indexed(self):
        third = row("c", "gamma", "gamma.example")
        third["corporate_action_evidence"]["previous_security_id"] = "OTHER:ADR"
        result = check([row(), row("b", "beta", "beta.example"), third])
        self.assertIn("CROSS_SOURCE_ACTION_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT",
                      result["issues"])
        self.assertNotIn("CROSS_SOURCE_SECURITY_IDENTITY_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["all_source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertEqual(result["action_previous_security_id_claim_groups"], [
            {"action_previous_security_id": "ID:COMMON",
             "structurally_valid_source_indices": [0, 1], "rejected_source_indices": []},
            {"action_previous_security_id": "OTHER:ADR",
             "structurally_valid_source_indices": [], "rejected_source_indices": [2]},
        ])
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_missing_third_prior_class_and_action_identity_are_censored(self):
        third = row("c", "gamma", "gamma.example")
        third.pop("previous_issuer_class")
        third["corporate_action_evidence"].pop("previous_security_id")
        result = check([row(), row("b", "beta", "beta.example"), third])
        self.assertEqual(result["unparseable_previous_issuer_class_claim_source_indices"], [2])
        self.assertEqual(result["unparseable_action_previous_security_id_claim_source_indices"], [2])
        self.assertNotIn("CROSS_SOURCE_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT", result["issues"])
        self.assertNotIn("CROSS_SOURCE_ACTION_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT",
                         result["issues"])
        self.assertEqual(result["all_source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertTrue(result["outcome_censored_pending_external_evidence"])

    def test_invalid_session_chain_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "VALID_SESSION_CHAIN_REQUIRED"):
            audit_action_identity("ZZZZ", DAY, DAY, [], COLLECTED)


if __name__ == "__main__":
    unittest.main()
