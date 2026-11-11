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
            "observed_at": observed,
            "regular_close_asof": "2026-10-27T20:00:00Z",
            "previous_regular_close_asof": "2026-10-26T20:00:00Z"}


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

    def test_reused_source_id_with_different_claimed_provider_is_blocked(self):
        first = row("one", "one.example")
        second = row("two", "two.example")
        second["source_id"] = first["source_id"]
        result = preflight("ZZZZ", DAY, PRIOR, [first, second], COLLECTED)
        self.assertIn("DUPLICATE_SOURCE_ID", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_repeated_source_id_is_not_hidden_by_invalid_second_report(self):
        first = row("one", "one.example")
        second = row("two", "two.example")
        second["source_id"] = first["source_id"]
        second["regular_close_asof"] = "2026-10-27T19:59:59Z"
        result = preflight("ZZZZ", DAY, PRIOR, [first, second], COLLECTED)
        self.assertIn("DUPLICATE_SOURCE_ID", result["issues"])
        self.assertIn("NON_1600_ET_REGULAR_CLOSE_SOURCE", result["issues"])

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

    def test_155935_last_trade_cannot_masquerade_as_official_close(self):
        print_source = row("two", "two.example")
        print_source["regular_close_asof"] = "2026-10-27T19:59:35Z"
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), print_source], COLLECTED)
        self.assertIn("NON_1600_ET_REGULAR_CLOSE_SOURCE", r["issues"])
        self.assertEqual(r["status"], "BLOCKED_SOURCE_EVIDENCE")

    def test_late_trade_after_close_is_not_close(self):
        late = row("two", "two.example")
        late["regular_close_asof"] = "2026-10-27T20:00:01Z"
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), late], COLLECTED)
        self.assertIn("NON_1600_ET_REGULAR_CLOSE_SOURCE", r["issues"])

    def test_missing_price_asof_is_not_inferred_from_observed_at(self):
        missing = row("two", "two.example")
        missing.pop("regular_close_asof")
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), missing], COLLECTED)
        self.assertIn("NON_1600_ET_REGULAR_CLOSE_SOURCE", r["issues"])

    def test_eastern_offset_equivalent_close_asof_is_accepted(self):
        east = row("two", "two.example")
        east["regular_close_asof"] = "2026-10-27T16:00:00-04:00"
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), east], COLLECTED)
        self.assertEqual(r["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")

    def test_missing_previous_close_asof_is_censored(self):
        stale = row("two", "two.example")
        stale.pop("previous_regular_close_asof")
        result = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), stale], COLLECTED)
        self.assertIn("PREVIOUS_CLOSE_NOT_EXACT_1600_ET_SOURCE", result["issues"])
        self.assertEqual(result["accepted_reports"], 1)
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_previous_intraday_print_cannot_be_previous_regular_close(self):
        stale = row("two", "two.example")
        stale["previous_regular_close_asof"] = "2026-10-26T19:59:35Z"
        result = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), stale], COLLECTED)
        self.assertIn("PREVIOUS_CLOSE_NOT_EXACT_1600_ET_SOURCE", result["issues"])

    def test_previous_early_close_requires_separate_calendar_protocol(self):
        early = row("two", "two.example")
        early["previous_regular_close_asof"] = "2026-10-26T17:00:00Z"
        result = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), early], COLLECTED)
        self.assertIn("PREVIOUS_CLOSE_NOT_EXACT_1600_ET_SOURCE", result["issues"])

    def test_previous_close_equivalent_eastern_offset_is_accepted(self):
        east = row("two", "two.example")
        east["previous_regular_close_asof"] = "2026-10-26T16:00:00-04:00"
        result = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example"), east], COLLECTED)
        self.assertEqual(result["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")

    def test_half_cent_agreement_straddling_20pct_boundary_is_censored(self):
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example", close="8.000"),
            row("two", "two.example", close="8.005"),
        ], COLLECTED)
        self.assertIn("TWENTY_PERCENT_THRESHOLD_STRADDLED", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_sub_tolerance_previous_close_difference_blocks_threshold_reference(self):
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example", close="8.00", prior="10.000"),
            row("two", "two.example", close="8.00", prior="10.001"),
        ], COLLECTED)
        self.assertIn("THRESHOLD_REFERENCE_PREVIOUS_CLOSE_DISAGREEMENT", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_extreme_finite_previous_close_is_censored_not_audit_crash(self):
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example"),
            row("two", "two.example", prior="1e999999999999999"),
        ], COLLECTED)
        self.assertEqual(result["supplied_reports"], 2)
        self.assertEqual(result["accepted_reports"], 1)
        self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_extreme_finite_current_close_is_censored_not_audit_crash(self):
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example"),
            row("two", "two.example", close="1e999999999999999"),
        ], COLLECTED)
        self.assertEqual(result["supplied_reports"], 2)
        self.assertEqual(result["accepted_reports"], 1)
        self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")

    def test_half_cent_tolerance_boundary_away_from_event_threshold(self):
        # Pure price tolerance remains intact; an exact 20% boundary is
        # separately censored even when the prices agree within half a cent.
        r = preflight("ZZZZ", DAY, PRIOR, [row("one", "one.example", close="8.500"), row("two", "two.example", close="8.505")], COLLECTED)
        self.assertEqual(r["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")

    def test_unsafe_source_url_authorities_are_censored_without_crash(self):
        invalid_urls = (
            "http://two.example/history",
            "https://user@two.example/history",
            "https://two.example:444/history",
            "https://two.example/history#fragment",
            "https://[broken/history",
            "https://two.example/history\nInjected: header",
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                second = row("two", "two.example")
                second["url"] = url
                result = preflight("ZZZZ", DAY, PRIOR, [
                    row("one", "one.example"), second], COLLECTED)
                self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
                self.assertEqual(result["supplied_reports"], 2)
                self.assertEqual(result["accepted_reports"], 1)
                self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_claimed_independent_groups_on_same_parent_host_are_censored(self):
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "api.vendor.example"),
            row("two", "data.vendor.example")], COLLECTED)
        self.assertIn("INSUFFICIENT_DISTINCT_PROVIDER_PARENT_HOST_EVIDENCE", result["issues"])
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_SOURCE_HOST_PARENT_HINT", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")

    def test_third_distinct_host_cannot_hide_cross_group_alias(self):
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "api.vendor.example"),
            row("two", "data.vendor.example"),
            row("three", "independent.example")], COLLECTED)
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_SOURCE_HOST_PARENT_HINT", result["issues"])
        self.assertEqual(result["supplied_reports"], 3)
        self.assertEqual(result["accepted_reports"], 3)
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])


    def test_local_ip_and_malformed_dns_hosts_cannot_count_as_independent_eod_sources(self):
        unsafe = (
            "127.0.0.1", "169.254.169.254", "[::1]", "localhost",
            "a.local", "api.internal", "-bad.example", "good..example",
            "bad-.example", "\u0430.example",
        )
        for hostname in unsafe:
            with self.subTest(hostname=hostname):
                result = preflight("ZZZZ", DAY, PRIOR, [
                    row("one", "one.example"), row("two", hostname)], COLLECTED)
                self.assertEqual(result["accepted_reports"], 1)
                self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
                self.assertFalse(result["eligible_for_frozen_forward_scoring"])


    def test_case_and_whitespace_provider_aliases_are_not_independent(self):
        first = row("Acme Market Data", "one.example")
        second = row("  aCME   MARKET data  ", "two.example")
        result = preflight("ZZZZ", DAY, PRIOR, [first, second], COLLECTED)
        self.assertEqual(result["accepted_reports"], 2)
        self.assertEqual(result["distinct_provider_groups"], 1)
        self.assertIn("INSUFFICIENT_DISTINCT_HOST_AND_PROVIDER_EVIDENCE", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_case_and_whitespace_source_receipt_alias_is_duplicate(self):
        first = row("one", "one.example")
        second = row("two", "two.example")
        second["source_id"] = "  ONE_DAILY  "
        result = preflight("ZZZZ", DAY, PRIOR, [first, second], COLLECTED)
        self.assertEqual(result["accepted_reports"], 2)
        self.assertIn("DUPLICATE_SOURCE_ID", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_SOURCE_EVIDENCE")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_same_parent_same_normalized_group_plus_independent_third(self):
        first = row("Acme Data", "api.vendor.example")
        second = row(" acme   DATA ", "data.vendor.example")
        third = row("Independent", "independent.example")
        result = preflight("ZZZZ", DAY, PRIOR, [first, second, third], COLLECTED)
        self.assertEqual(result["accepted_reports"], 3)
        self.assertEqual(result["distinct_provider_groups"], 2)
        self.assertNotIn("CLAIMED_PROVIDER_GROUPS_SHARE_SOURCE_HOST_PARENT_HINT", result["issues"])
        self.assertEqual(result["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])



    def test_high_precision_half_cent_conflict_cannot_round_into_agreement(self):
        # Default Decimal(28) subtraction rounds this to exactly 0.005.
        # Preserve the supplied digits and censor the complete source set.
        low = "100." + "0" * 60 + "1"
        high = "100.005" + "0" * 57 + "2"
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example", close=low),
            row("two", "two.example", close=high),
        ], COLLECTED)
        self.assertEqual(result["accepted_reports"], 2)
        self.assertIn("CONFLICTING_REGULAR_CLOSE_REPORTS", result["issues"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_high_precision_20pct_threshold_cannot_round_away_straddle(self):
        # Exact 80%-of-prior threshold lies between the two claimed closes;
        # Decimal(28) rounds the threshold down to 8.0 and misses it.
        prior = "10." + "0" * 59 + "1"
        below = "8." + "0" * 60 + "4"
        above = "8." + "0" * 60 + "9"
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example", close=below, prior=prior),
            row("two", "two.example", close=above, prior=prior),
        ], COLLECTED)
        self.assertEqual(result["accepted_reports"], 2)
        self.assertIn("TWENTY_PERCENT_THRESHOLD_STRADDLED", result["issues"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_overprecision_vendor_claim_is_censored_without_denominator_loss(self):
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example"),
            row("two", "two.example", prior="1." + "0" * 101 + "1"),
        ], COLLECTED)
        self.assertEqual(result["supplied_reports"], 2)
        self.assertEqual(result["accepted_reports"], 1)
        self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_unicode_equivalent_provider_names_do_not_create_independence(self):
        first = row("Caf\u00e9 Data", "one.example")
        second = row("Cafe\u0301 Data", "two.example")
        result = preflight("ZZZZ", DAY, PRIOR, [first, second], COLLECTED)
        self.assertEqual(result["distinct_provider_groups"], 1)
        self.assertIn("INSUFFICIENT_DISTINCT_HOST_AND_PROVIDER_EVIDENCE", result["issues"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_unicode_equivalent_source_ids_are_duplicate(self):
        first = row("one", "one.example")
        second = row("two", "two.example")
        first["source_id"] = "Caf\u00e9 receipt"
        second["source_id"] = "Cafe\u0301 receipt"
        result = preflight("ZZZZ", DAY, PRIOR, [first, second], COLLECTED)
        self.assertIn("DUPLICATE_SOURCE_ID", result["issues"])
        self.assertEqual(result["supplied_reports"], 2)

    def test_invisible_format_control_in_source_labels_is_censored(self):
        for field in ("provider_group", "source_id"):
            with self.subTest(field=field):
                second = row("two", "two.example")
                second[field] += "\u200b"
                result = preflight("ZZZZ", DAY, PRIOR,
                                   [row("one", "one.example"), second], COLLECTED)
                self.assertEqual(result["accepted_reports"], 1)
                self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
                self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_rejected_third_source_price_conflict_remains_visible(self):
        third = row("three", "three.example", close="8.20")
        third["symbol"] = "WRONG"
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example"), row("two", "two.example"), third], COLLECTED)
        self.assertEqual(result["accepted_reports"], 2)
        self.assertEqual(result["supplied_reports"], 3)
        self.assertIn("WRONG_SECURITY_SESSION_OR_PRICE_KIND", result["issues"])
        self.assertIn("ALL_SUPPLIED_REGULAR_CLOSE_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(
            result["all_parseable_regular_close_claim_groups"],
            [{"claimed_regular_close": "8.00", "source_indices": [0, 1]},
             {"claimed_regular_close": "8.20", "source_indices": [2]}])
        self.assertTrue(result["untrusted_claim_inventory_not_official"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_rejected_third_source_threshold_straddle_even_within_tolerance(self):
        third = row("three", "three.example", close="8.001")
        third["observed_at"] = "2026-10-27T19:59:59Z"
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example"), row("two", "two.example"), third], COLLECTED)
        self.assertEqual(result["accepted_reports"], 2)
        self.assertIn("STALE_OR_UNTIMED_SOURCE", result["issues"])
        self.assertIn("ALL_SUPPLIED_CLAIMS_STRADDLE_20PCT_THRESHOLD", result["issues"])
        self.assertNotIn("ALL_SUPPLIED_REGULAR_CLOSE_CLAIM_CONFLICT", result["issues"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_rejected_third_source_previous_reference_disagreement_is_not_dropped(self):
        third = row("three", "three.example", prior="10.001")
        third["kind"] = "last_trade"
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example"), row("two", "two.example"), third], COLLECTED)
        self.assertIn("WRONG_SECURITY_SESSION_OR_PRICE_KIND", result["issues"])
        self.assertIn("ALL_SUPPLIED_PREVIOUS_CLOSE_REFERENCE_DISAGREEMENT", result["issues"])
        self.assertEqual(result["accepted_reports"], 2)
        self.assertEqual(len(result["all_parseable_previous_close_claim_groups"]), 2)
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])

    def test_unparseable_third_source_claim_not_invented_as_price(self):
        third = row("three", "three.example", close="not-a-price")
        third["symbol"] = "WRONG"
        result = preflight("ZZZZ", DAY, PRIOR, [
            row("one", "one.example"), row("two", "two.example"), third], COLLECTED)
        self.assertEqual(result["supplied_reports"], 3)
        self.assertEqual(result["accepted_reports"], 2)
        self.assertEqual(len(result["all_parseable_regular_close_claim_groups"]), 1)
        self.assertNotIn("ALL_SUPPLIED_REGULAR_CLOSE_CLAIM_CONFLICT", result["issues"])
        self.assertIn("INVALID_SOURCE_PROVENANCE_OR_PRICE", result["issues"])
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])


if __name__ == "__main__":
    unittest.main()
