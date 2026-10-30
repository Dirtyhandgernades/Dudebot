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

    def test_previous_intraday_print_cannot_be_reference_close(self):
        calendar = cal()
        calendar["previous_regular_close_at"] = "2026-10-27T14:30:00Z"
        a, b = row(), row("b", "two", "two.example")
        for source in (a, b):
            source["previous_regular_close_asof"] = calendar["previous_regular_close_at"]
        result = check([a, b], calendar)
        self.assertEqual(result["retained_report_count"], 2)
        self.assertEqual(result["structurally_valid_report_count"], 2)
        self.assertIn("PREVIOUS_REGULAR_CLOSE_TIME_CONFLICT", result["issues"])
        self.assertEqual(result["structural_status"], "BLOCKED_CENSORED")
        self.assertFalse(result["official_regular_close_verified"])

    def test_previous_early_close_requires_separate_protocol(self):
        calendar = cal()
        calendar["previous_regular_close_at"] = "2026-10-27T17:00:00Z"
        a, b = row(), row("b", "two", "two.example")
        for source in (a, b):
            source["previous_regular_close_asof"] = calendar["previous_regular_close_at"]
        result = check([a, b], calendar)
        self.assertIn("PREVIOUS_REGULAR_CLOSE_TIME_CONFLICT", result["issues"])
        self.assertIn("PREVIOUS_EARLY_CLOSE_REQUIRES_SEPARATE_NONFROZEN_PROTOCOL", result["issues"])
        self.assertTrue(result["outcome_censored_pending_external_evidence"])

    def test_ambiguous_calendar_early_close_flag_is_censored(self):
        calendar = cal()
        calendar["early_close"] = "false"
        result = check([row(), row("b", "two", "two.example")], calendar)
        self.assertIn("INVALID_EARLY_CLOSE_CALENDAR_FLAG", result["issues"])
        self.assertEqual(result["structural_status"], "BLOCKED_CENSORED")

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

    def test_every_source_claim_and_digest_are_auditable(self):
        import hashlib
        import json
        first = row()
        first["source_url"] = "https://one.example/eod?apiKey=DO_NOT_ECHO"
        result = check([first, row("b", "two", "two.example")])
        receipt = result["source_rows"][0]
        expected = hashlib.sha256(json.dumps(
            first, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False).encode("utf-8")).hexdigest()
        self.assertEqual(receipt["supplied_report_sha256"], expected)
        self.assertEqual(receipt["source_claims"]["regular_close"], "7.99")
        self.assertEqual(receipt["source_claims"]["previous_regular_close"], "10")
        self.assertEqual(receipt["source_claims"]["security_id"], "ISSUER1:COMMON")
        self.assertEqual(receipt["source_claims"]["regular_close_asof"], "2026-10-28T20:00:00Z")
        self.assertNotIn("DO_NOT_ECHO", str(result))
        self.assertFalse(result["raw_source_packets_archived_by_module"])
        self.assertTrue(result["all_supplied_rows_indexed"])

    def test_distinct_claim_price_groups_include_conflicting_third(self):
        result = check([row(), row("b", "two", "two.example"),
                        row("c", "three", "three.example", "8.2")])
        self.assertEqual(result["price_claim_groups"], [
            {"regular_close": "7.99", "previous_regular_close": "10",
             "source_indices": [0, 1], "claimed_20pct_drop": True},
            {"regular_close": "8.2", "previous_regular_close": "10",
             "source_indices": [2], "claimed_20pct_drop": False},
        ])
        self.assertIn("SOURCE_CLAIM_20PCT_CLASSIFICATION_DISAGREEMENT", result["issues"])
        self.assertFalse(result["official_regular_close_verified"])

    def test_malformed_non_dict_and_non_json_are_indexed_and_censored(self):
        result = check([row(), ["unexpected", "list"], object()])
        self.assertEqual(result["retained_report_count"], 3)
        self.assertEqual(result["source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertIsNotNone(result["source_rows"][1]["supplied_report_sha256"])
        self.assertIsNone(result["source_rows"][2]["supplied_report_sha256"])
        self.assertIn("MALFORMED_SOURCE_RECORD", result["issues"])
        self.assertIn("NON_JSON_SOURCE_RECORD_NOT_REPRODUCIBLY_HASHABLE", result["issues"])

    def test_invalid_third_price_is_retained_as_claim_not_validated(self):
        third = row("c", "three", "three.example", close="NOT_A_PRICE")
        result = check([row(), row("b", "two", "two.example"), third])
        self.assertEqual(result["source_rows"][2]["source_claims"]["regular_close"], "NOT_A_PRICE")
        self.assertEqual(result["source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertEqual(len(result["price_claim_groups"]), 1)
        self.assertIn("INVALID_CLOSE_OR_PRIOR_PRICE", result["issues"])

    def test_missing_rows_are_censored_not_negative_outcomes(self):
        r = check([])
        self.assertIn("NO_EOD_SOURCE_REPORTS", r["issues"])
        self.assertIsNone(r["verified_20pct_prediction_success"])

    def test_rejected_third_source_price_conflict_remains_visible(self):
        third = row("c", "three", "three.example", close="8.2")
        third["regular_close_asof"] = "2026-10-28T19:59:35Z"
        result = check([row(), row("b", "two", "two.example"), third])
        self.assertEqual(len(result["price_claim_groups"]), 1)
        self.assertEqual(len(result["all_parseable_price_claim_groups"]), 2)
        conflicting = result["all_parseable_price_claim_groups"][1]
        self.assertEqual(conflicting["rejected_source_indices"], [2])
        self.assertEqual(conflicting["structurally_valid_source_indices"], [])
        self.assertIn("REJECTED_SOURCE_PRICE_CLAIM_NOT_IN_VALID_SET", result["issues"])
        self.assertIn("ALL_PARSEABLE_SOURCE_CLAIMS_STRADDLE_20PCT_THRESHOLD", result["issues"])
        self.assertFalse(result["official_regular_close_verified"])

    def test_all_parseable_claim_view_accounts_for_unparseable_rows(self):
        bad = row("c", "three", "three.example", close="INVALID")
        result = check([row(), row("b", "two", "two.example"), bad, ["bad"]])
        self.assertEqual(result["unparseable_price_claim_source_indices"], [2, 3])
        self.assertEqual(result["all_parseable_price_claim_groups"][0]["source_indices"], [0, 1])
        self.assertEqual(result["retained_report_count"], 4)

    def test_order_and_calendar_changes_have_distinct_packet_fingerprints(self):
        a, b = row(), row("b", "two", "two.example")
        original = check([a, b])
        reordered = check([b, a])
        altered_calendar = cal()
        altered_calendar["exchange_calendar_url"] = "https://other.example/calendar"
        changed = check([a, b], altered_calendar)
        self.assertNotEqual(original["supplied_input_packet_sha256"],
                            reordered["supplied_input_packet_sha256"])
        self.assertNotEqual(original["supplied_input_packet_sha256"],
                            changed["supplied_input_packet_sha256"])
        self.assertNotEqual(original["supplied_calendar_sha256"],
                            changed["supplied_calendar_sha256"])
        self.assertTrue(original["outcome_censored_pending_external_evidence"])

    def test_non_json_packet_censored_without_false_audit_digest(self):
        result = check([row(), object()])
        self.assertIsNone(result["supplied_input_packet_sha256"])
        self.assertIn("NON_JSON_INPUT_PACKET_NOT_REPRODUCIBLY_HASHABLE", result["issues"])
        self.assertFalse(result["official_regular_close_verified"])

    def test_extreme_finite_close_censored_without_losing_third_source(self):
        third = row("c", "three", "three.example", close="1e1000000")
        result = check([row(), row("b", "two", "two.example"), third])
        self.assertEqual(result["supplied_report_count"], 3)
        self.assertEqual(result["retained_report_count"], 3)
        self.assertTrue(result["all_supplied_rows_indexed"])
        self.assertEqual(result["unparseable_price_claim_source_indices"], [2])
        self.assertEqual(result["source_rows"][2]["source_claims"]["regular_close"], "1e1000000")
        self.assertEqual(result["source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertIn("INVALID_CLOSE_OR_PRIOR_PRICE", result["issues"])
        self.assertEqual(result["structural_status"], "BLOCKED_CENSORED")
        self.assertIsNone(result["verified_20pct_prediction_success"])

    def test_extreme_finite_prior_and_tiny_close_censored_without_crash(self):
        for close, prior in (("7.99", "1e1000000"), ("1e-1000000", "10")):
            with self.subTest(close=close, prior=prior):
                third = row("c", "three", "three.example", close=close, prior=prior)
                result = check([row(), row("b", "two", "two.example"), third])
                self.assertEqual(result["retained_report_count"], 3)
                self.assertEqual(result["unparseable_price_claim_source_indices"], [2])
                self.assertEqual(result["source_rows"][2]["status"], "REJECTED_CENSORED")
                self.assertIn("INVALID_CLOSE_OR_PRIOR_PRICE", result["issues"])
                self.assertEqual(result["all_parseable_price_claim_groups"][0]["source_indices"], [0, 1])
                self.assertFalse(result["official_regular_close_verified"])



    def test_calendar_claim_requires_official_exchange_host_and_safe_https_authority(self):
        """A caller-supplied arbitrary or credentialed calendar cannot pass even structurally."""
        bad_urls = (
            "https://other.example/calendar",
            "https://user:secret@www.nyse.com/calendar",
            "https://www.nyse.com:8443/calendar",
            "https://www.nyse.com./calendar",
            "https://www.nyse.com/calendar#fragment",
            "https://www.nyse.com/ca\\nendar",
        )
        for url in bad_urls:
            with self.subTest(calendar_url=url):
                calendar = cal()
                calendar["exchange_calendar_url"] = url
                result = check([row(), row("b", "two", "two.example")], calendar)
                self.assertIn("UNVERIFIED_OR_INVALID_EXCHANGE_SESSION_CHAIN", result["issues"])
                self.assertEqual(result["retained_report_count"], 2)
                self.assertEqual(result["structural_status"], "BLOCKED_CENSORED")
                self.assertFalse(result["official_regular_close_verified"])

    def test_malformed_third_source_url_cannot_hide_conflicting_price_claim(self):
        """Rejected third-party close still appears in the complete conflict inventory."""
        bad_urls = (
            "https://user:secret@three.example/eod",
            "https://three.example:8443/eod",
            "https://three.example./eod",
            "https://three.example/eod#fragment",
            "https://three.example/eod\\nnext",
        )
        for url in bad_urls:
            with self.subTest(source_url=url):
                third = row("c", "three", "three.example", close="8.2")
                third["source_url"] = url
                result = check([row(), row("b", "two", "two.example"), third])
                self.assertEqual(result["retained_report_count"], 3)
                self.assertTrue(result["all_supplied_rows_indexed"])
                self.assertEqual(result["source_rows"][2]["status"], "REJECTED_CENSORED")
                self.assertIn("SOURCE_OWNERSHIP_OR_URL_MISSING", result["issues"])
                self.assertIn("ALL_PARSEABLE_SOURCE_CLAIMS_STRADDLE_20PCT_THRESHOLD", result["issues"])
                self.assertIn("REJECTED_SOURCE_PRICE_CLAIM_NOT_IN_VALID_SET", result["issues"])
                self.assertFalse(result["official_regular_close_verified"])


if __name__ == "__main__":
    unittest.main()
