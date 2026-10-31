"""Synthetic-only source body binding; never an authenticated close."""
import copy
import hashlib
import json
import unittest
from datetime import date

from backtest.obsidian_eod_source_body_binding_shadow import audit_body_bindings

DAY = date(2026, 10, 28)
PRIOR = date(2026, 10, 27)
COLLECTED = "2026-10-28T20:10:00Z"


def packet():
    reports, receipts = [], []
    for i, host in enumerate(("provider-a.example", "provider-b.example")):
        report = {
            "source_id": "source-" + str(i), "provider_organization": "group-" + str(i),
            "source_url": "https://" + host + "/close?key=DO_NOT_ECHO_" + str(i),
            "symbol": "TEST", "session_date": "2026-10-28",
            "previous_session_date": "2026-10-27",
            "security_id": "TEST-ISSUER", "previous_security_id": "TEST-ISSUER",
            "issuer_class": "COMMON", "previous_issuer_class": "COMMON",
            "kind": "regular_close", "session_complete": True,
            "observed_at": "2026-10-28T20:06:00Z",
            "regular_close": "8.00", "previous_regular_close": "10.00",
            "regular_close_asof": "2026-10-28T20:00:00Z",
            "previous_regular_close_asof": "2026-10-27T20:00:00Z",
            "corporate_action": {
                "status": "NONE", "coverage_start": "2026-10-27",
                "coverage_end": "2026-10-28",
                "checked_at": "2026-10-28T20:05:00Z",
                "previous_close_basis": "UNADJUSTED",
            },
        }
        body = json.dumps({k: v for k, v in report.items()
                           if k != "source_url"},
                          sort_keys=True).encode()
        reports.append(report)
        receipts.append({
            "source_id": report["source_id"],
            "provider_organization": report["provider_organization"],
            "requested_url": report["source_url"],
            "response_url": report["source_url"],
            "http_status": 200, "http_method": "GET",
            "content_type": "application/json; charset=utf-8",
            "retrieved_at": "2026-10-28T20:08:00Z",
            "raw_body": body, "body_sha256": hashlib.sha256(body).hexdigest(),
        })
    return reports, receipts


def replace_body(receipts, index, body):
    receipts[index]["raw_body"] = body
    receipts[index]["body_sha256"] = hashlib.sha256(body).hexdigest()


class BindingShadowTests(unittest.TestCase):
    def check(self, reports=None, receipts=None):
        r, t = packet()
        return audit_body_bindings(DAY, PRIOR, r if reports is None else reports,
                                   t if receipts is None else receipts, COLLECTED)

    def test_matching_bytes_and_claims_still_censored(self):
        result = self.check()
        self.assertEqual(result["byte_bound_unauthenticated_count"], 2)
        self.assertEqual(result["status"], "BODY_CONSISTENT_EXTERNAL_AUTH_PENDING")
        self.assertFalse(result["official_close_verified"])
        self.assertFalse(result["eligible_for_frozen_scoring"])
        self.assertIsNone(result["verified_20pct_prediction_success"])

    def test_claim_not_present_in_body_rejected(self):
        r, t = packet()
        r[1]["regular_close"] = "7.00"
        result = self.check(r, t)
        self.assertIn("BODY_REPORT_PRICE_MISMATCH_REGULAR_CLOSE", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)

    def test_third_source_body_conflict_is_not_dropped(self):
        r, t = packet()
        third_r, third_t = copy.deepcopy(r[1]), copy.deepcopy(t[1])
        third_r["source_id"] = third_t["source_id"] = "source-2"
        third_r["provider_organization"] = third_t["provider_organization"] = "group-2"
        third_r["source_url"] = third_t["requested_url"] = third_t["response_url"] = "https://provider-c.example/close"
        third_r["regular_close"] = "9.00"
        body = json.loads(third_t["raw_body"])
        body["source_id"], body["regular_close"] = "source-2", "9.00"
        replace_body([third_t], 0, json.dumps(body).encode())
        r.append(third_r)
        t.append(third_t)
        result = self.check(r, t)
        self.assertEqual(result["indexed_count"], 3)
        self.assertIn("PARSED_BODY_PRICE_CLAIM_CONFLICT", result["issues"])
        self.assertIn("PARSED_BODY_CLAIMS_STRADDLE_20PCT_THRESHOLD", result["issues"])
        self.assertEqual(len(result["all_parseable_body_price_claim_groups"]), 2)

    def test_duplicate_json_keys_rejected(self):
        r, t = packet()
        replace_body(t, 1, t[1]["raw_body"][:-1] + b', "symbol":"TEST"}')
        result = self.check(r, t)
        self.assertIn("INVALID_DUPLICATE_OR_NONFINITE_JSON_BODY", result["issues"])

    def test_oversized_valid_json_is_not_parsed_or_hashed(self):
        r, t = packet()
        # A syntactically valid response exceeding the receipt-layer 5 MB
        # bound must never reach the JSON parser or mask the other source.
        original = json.loads(t[1]["raw_body"])
        original["padding"] = "x" * 5_000_000
        replace_body(t, 1, json.dumps(original).encode())
        result = self.check(r, t)
        self.assertIn("MISSING_OVERSIZED_OR_NONBYTE_RESPONSE_BODY", result["issues"])
        self.assertIn("BODY_EMPTY_OR_OVERSIZED_NO_PARSE", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertIsNone(result["all_source_rows"][1]["raw_body_sha256_computed"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)
        self.assertEqual(len(result["all_parseable_body_price_claim_groups"]), 1)
        self.assertFalse(result["official_close_verified"])

    def test_empty_body_is_not_parsed_or_hashed(self):
        r, t = packet()
        replace_body(t, 1, b"")
        result = self.check(r, t)
        self.assertIn("BODY_EMPTY_OR_OVERSIZED_NO_PARSE", result["issues"])
        self.assertIsNone(result["all_source_rows"][1]["raw_body_sha256_computed"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)

    def test_missing_receipt_keeps_original_index(self):
        r, t = packet()
        result = self.check(r, t[:1])
        self.assertEqual(result["indexed_count"], 2)
        self.assertIn("MISSING_OR_MALFORMED_SOURCE_RECEIPT", result["all_source_rows"][1]["issues"])

    def test_nonfinite_json_rejected(self):
        r, t = packet()
        replace_body(t, 1, t[1]["raw_body"][:-1] + b', "bogus":NaN}')
        result = self.check(r, t)
        self.assertIn("INVALID_DUPLICATE_OR_NONFINITE_JSON_BODY", result["issues"])

    def test_action_status_mismatch_rejected(self):
        r, t = packet()
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["status"] = "SPLIT"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_REPORT_ACTION_MISMATCH_STATUS", result["issues"])
        self.assertIn("ACTION_WINDOW_OR_STATUS_NOT_CLEARED", result["issues"])

    def test_action_coverage_gap_rejected(self):
        r, t = packet()
        r[1]["corporate_action"]["coverage_start"] = "2026-10-28"
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["coverage_start"] = "2026-10-28"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("ACTION_WINDOW_OR_STATUS_NOT_CLEARED", result["issues"])

    def test_security_identity_not_stable(self):
        r, t = packet()
        r[1]["previous_security_id"] = "OLD-ISSUER"
        body = json.loads(t[1]["raw_body"])
        body["previous_security_id"] = "OLD-ISSUER"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_SECURITY_IDENTITY_NOT_STABLE", result["issues"])

    def test_claimed_asof_wrong_session_rejected(self):
        r, t = packet()
        r[1]["regular_close_asof"] = "2026-10-27T20:00:00Z"
        body = json.loads(t[1]["raw_body"])
        body["regular_close_asof"] = "2026-10-27T20:00:00Z"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_CLOSE_ASOF_SESSION_DATE_MISMATCH", result["issues"])

    def test_provider_claim_must_be_present_in_original_body(self):
        r, t = packet()
        r[1]["provider_organization"] = "rebranded-unverified"
        t[1]["provider_organization"] = "rebranded-unverified"
        result = self.check(r, t)
        self.assertIn("BODY_REPORT_FIELD_MISMATCH_PROVIDER_ORGANIZATION", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)

    def test_body_publication_after_receipt_is_censored(self):
        r, t = packet()
        r[1]["observed_at"] = "2026-10-28T20:09:00Z"
        body = json.loads(t[1]["raw_body"])
        body["observed_at"] = r[1]["observed_at"]
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_PUBLICATION_RECEIPT_CHRONOLOGY_INVALID", result["issues"])

    def test_body_publication_before_close_is_censored(self):
        r, t = packet()
        r[1]["observed_at"] = "2026-10-28T19:59:00Z"
        body = json.loads(t[1]["raw_body"])
        body["observed_at"] = r[1]["observed_at"]
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_PUBLICATION_RECEIPT_CHRONOLOGY_INVALID", result["issues"])

    def test_action_check_before_close_is_censored(self):
        r, t = packet()
        r[1]["corporate_action"]["checked_at"] = "2026-10-28T19:59:00Z"
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["checked_at"] = "2026-10-28T19:59:00Z"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("ACTION_CHECK_TIME_INVALID", result["issues"])

    def test_embedded_action_check_after_publication_is_censored(self):
        r, t = packet()
        # After source publication at 20:06 but before retrieval at 20:08:
        # a timestamp-consistent HTTP receipt cannot validate time travel.
        r[1]["corporate_action"]["checked_at"] = "2026-10-28T20:07:00Z"
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["checked_at"] = r[1]["corporate_action"]["checked_at"]
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("EMBEDDED_ACTION_CHECK_POSTDATES_SOURCE_PUBLICATION", result["issues"])
        self.assertNotIn("ACTION_CHECK_TIME_INVALID", result["all_source_rows"][1]["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)
        self.assertFalse(result["official_close_verified"])

    def test_embedded_action_checked_before_publication_still_unauthenticated(self):
        result = self.check()
        self.assertNotIn("EMBEDDED_ACTION_CHECK_POSTDATES_SOURCE_PUBLICATION", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 2)
        self.assertFalse(result["official_close_verified"])

    def test_action_check_after_receipt_is_censored(self):
        r, t = packet()
        r[1]["corporate_action"]["checked_at"] = "2026-10-28T20:09:00Z"
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["checked_at"] = "2026-10-28T20:09:00Z"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("ACTION_CHECK_TIME_INVALID", result["issues"])

    def test_huge_finite_json_exponent_is_censored_without_crashing_inventory(self):
        r, t = packet()
        r[1]["regular_close"] = "1e999999999"
        body = json.loads(t[1]["raw_body"])
        body["regular_close"] = "1e999999999"
        raw = json.dumps(body).replace('"regular_close": "1e999999999"',
                                       '"regular_close": 1e999999999').encode()
        replace_body(t, 1, raw)
        result = self.check(r, t)
        self.assertEqual(result["indexed_count"], 2)
        self.assertIn("BODY_REPORT_PRICE_MISMATCH_REGULAR_CLOSE", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_unparseable_decimal_exponent_keeps_other_source_evidence(self):
        r, t = packet()
        raw = t[1]["raw_body"].replace(
            b'"regular_close": "8.00"',
            b'"regular_close": 1e9999999999999999999999')
        self.assertNotEqual(raw, t[1]["raw_body"])
        replace_body(t, 1, raw)
        result = self.check(r, t)
        self.assertEqual(result["indexed_count"], 2)
        self.assertIn("INVALID_DUPLICATE_OR_NONFINITE_JSON_BODY", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)
        self.assertEqual(len(result["all_parseable_body_price_claim_groups"]), 1)

    def test_tiny_finite_json_exponent_cannot_underflow_threshold(self):
        r, t = packet()
        r[1]["previous_regular_close"] = "1e-999999999"
        body = json.loads(t[1]["raw_body"])
        body["previous_regular_close"] = "1e-999999999"
        raw = json.dumps(body).replace('"previous_regular_close": "1e-999999999"',
                                       '"previous_regular_close": 1e-999999999').encode()
        replace_body(t, 1, raw)
        result = self.check(r, t)
        self.assertEqual(result["indexed_count"], 2)
        self.assertIn("BODY_REPORT_PRICE_MISMATCH_PREVIOUS_REGULAR_CLOSE", result["issues"])
        self.assertFalse(result["official_close_verified"])

    def test_no_secrets_or_raw_json_appear_in_result(self):
        result = self.check()
        output = repr(result)
        self.assertNotIn("DO_NOT_ECHO", output)
        self.assertNotIn('"symbol"', output)
        self.assertNotIn("provider-a.example", output)

    def test_http_error_still_rejected_even_if_body_matches(self):
        r, t = packet()
        t[1]["http_status"] = 401
        result = self.check(r, t)
        self.assertIn("NON_SUCCESSFUL_OR_NON_GET_HTTP_CLAIM", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)

    def test_unsupported_media_censored(self):
        r, t = packet()
        t[1]["content_type"] = "text/html"
        result = self.check(r, t)
        self.assertIn("NOT_EXPLICIT_APPLICATION_JSON", result["issues"])

    def test_boolean_price_not_accepted(self):
        r, t = packet()
        r[1]["regular_close"] = True
        body = json.loads(t[1]["raw_body"])
        body["regular_close"] = True
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_REPORT_PRICE_MISMATCH_REGULAR_CLOSE", result["issues"])

    def test_current_1559_trade_not_exact_regular_close(self):
        r, t = packet()
        r[1]["regular_close_asof"] = "2026-10-28T19:59:00Z"
        body = json.loads(t[1]["raw_body"])
        body["regular_close_asof"] = r[1]["regular_close_asof"]
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_CLOSE_ASOF_NOT_EXACT_1600_ET", result["issues"])
        self.assertFalse(result["official_close_verified"])

    def test_current_1601_afterhours_not_exact_regular_close(self):
        r, t = packet()
        r[1]["regular_close_asof"] = "2026-10-28T20:01:00Z"
        body = json.loads(t[1]["raw_body"])
        body["regular_close_asof"] = r[1]["regular_close_asof"]
        replace_body(t, 1, json.dumps(body).encode())
        self.assertIn("BODY_CLOSE_ASOF_NOT_EXACT_1600_ET", self.check(r, t)["issues"])

    def test_prior_1559_trade_not_exact_previous_close(self):
        r, t = packet()
        r[1]["previous_regular_close_asof"] = "2026-10-27T19:59:00Z"
        body = json.loads(t[1]["raw_body"])
        body["previous_regular_close_asof"] = r[1]["previous_regular_close_asof"]
        replace_body(t, 1, json.dumps(body).encode())
        self.assertIn("BODY_CLOSE_ASOF_NOT_EXACT_1600_ET", self.check(r, t)["issues"])

    def test_prior_1601_afterhours_not_exact_previous_close(self):
        r, t = packet()
        r[1]["previous_regular_close_asof"] = "2026-10-27T20:01:00Z"
        body = json.loads(t[1]["raw_body"])
        body["previous_regular_close_asof"] = r[1]["previous_regular_close_asof"]
        replace_body(t, 1, json.dumps(body).encode())
        self.assertIn("BODY_CLOSE_ASOF_NOT_EXACT_1600_ET", self.check(r, t)["issues"])

    def test_adjusted_previous_close_basis_is_censored(self):
        r, t = packet()
        r[1]["corporate_action"]["previous_close_basis"] = "ADJUSTED"
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["previous_close_basis"] = "ADJUSTED"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("ACTION_WINDOW_OR_STATUS_NOT_CLEARED", result["issues"])
        self.assertIn("PARSED_BODY_PREVIOUS_CLOSE_BASIS_CLAIM_CONFLICT", result["issues"])

    def test_missing_previous_close_basis_is_censored(self):
        r, t = packet()
        del r[1]["corporate_action"]["previous_close_basis"]
        body = json.loads(t[1]["raw_body"])
        del body["corporate_action"]["previous_close_basis"]
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_REPORT_ACTION_MISMATCH_PREVIOUS_CLOSE_BASIS", result["issues"])
        self.assertIn("ACTION_WINDOW_OR_STATUS_NOT_CLEARED", result["issues"])

    def test_cross_source_security_identity_conflict_is_not_hidden(self):
        r, t = packet()
        r[1]["security_id"] = r[1]["previous_security_id"] = "OTHER-ISSUER"
        body = json.loads(t[1]["raw_body"])
        body["security_id"] = body["previous_security_id"] = "OTHER-ISSUER"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("PARSED_BODY_SECURITY_ID_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 2)
        self.assertEqual(result["status"], "BLOCKED_CENSORED")

    def test_cross_source_issuer_class_conflict_is_not_hidden(self):
        r, t = packet()
        r[1]["issuer_class"] = r[1]["previous_issuer_class"] = "ADR"
        body = json.loads(t[1]["raw_body"])
        body["issuer_class"] = body["previous_issuer_class"] = "ADR"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("PARSED_BODY_ISSUER_CLASS_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_CENSORED")


    def test_supplied_early_close_and_prior_regular_close_still_censored(self):
        # Synthetic 2026-11-27 early-close fixture; no calendar authentication.
        r, t = packet()
        for i in range(2):
            r[i].update({
                "session_date": "2026-11-27",
                "previous_session_date": "2026-11-25",
                "regular_close_asof": "2026-11-27T18:00:00Z",
                "previous_regular_close_asof": "2026-11-25T21:00:00Z",
                "observed_at": "2026-11-27T18:06:00Z",
            })
            r[i]["corporate_action"].update({
                "coverage_start": "2026-11-25",
                "coverage_end": "2026-11-27",
                "checked_at": "2026-11-27T18:05:00Z",
            })
            t[i]["retrieved_at"] = "2026-11-27T18:08:00Z"
            replace_body(t, i, json.dumps(
                {k: v for k, v in r[i].items() if k != "source_url"},
                sort_keys=True).encode())
        args = (date(2026, 11, 27), date(2026, 11, 25), r, t,
                "2026-11-27T18:10:00Z")
        kwargs = {
            "session_close_at": "2026-11-27T18:00:00Z",
            "previous_session_close_at": "2026-11-25T21:00:00Z",
        }
        result = audit_body_bindings(*args, **kwargs)
        self.assertEqual(result["byte_bound_unauthenticated_count"], 2)
        self.assertEqual(result["status"], "BODY_CONSISTENT_EXTERNAL_AUTH_PENDING")
        self.assertFalse(result["official_close_verified"])
        self.assertFalse(result["exchange_calendar_and_corporate_actions_authenticated"])

        # A 16:00 ET print must not substitute for the actual 13:00 ET close.
        r[1]["regular_close_asof"] = "2026-11-27T21:00:00Z"
        replace_body(t, 1, json.dumps(
            {k: v for k, v in r[1].items() if k != "source_url"},
            sort_keys=True).encode())
        wrong = audit_body_bindings(*args, **kwargs)
        self.assertIn("BODY_CLOSE_ASOF_NOT_EXACT_EXCHANGE_SESSION_CLOSE",
                      wrong["all_source_rows"][1]["issues"])
        self.assertFalse(wrong["official_close_verified"])

        # Without an explicit early-close time, the legacy 16:00 assumption
        # fails closed on a 13:10 ET receipt.
        with self.assertRaisesRegex(ValueError, "POSTCLOSE_COLLECTION_TIMESTAMP_REQUIRED"):
            audit_body_bindings(*args)

    def test_invalid_supplied_session_close_times_fail_closed(self):
        r, t = packet()
        with self.assertRaisesRegex(ValueError, "EXTERNAL_SESSION_CLOSE_TIMESTAMP_INVALID"):
            audit_body_bindings(DAY, PRIOR, r, t, COLLECTED,
                                session_close_at="2026-10-28T18:00:00Z")
        with self.assertRaisesRegex(ValueError, "EXTERNAL_PREVIOUS_SESSION_CLOSE_TIMESTAMP_INVALID"):
            audit_body_bindings(DAY, PRIOR, r, t, COLLECTED,
                                previous_session_close_at="2026-10-27T18:00:00Z")


    def test_rejected_prior_security_identity_conflict_from_original_bytes(self):
        r, t = packet()
        r[1]["previous_security_id"] = "DIFFERENT-PRIOR-ISSUER"
        body = json.loads(t[1]["raw_body"])
        body["previous_security_id"] = "DIFFERENT-PRIOR-ISSUER"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_SECURITY_IDENTITY_NOT_STABLE", result["issues"])
        self.assertIn("PARSED_BODY_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT", result["issues"])
        self.assertNotIn("PARSED_BODY_SECURITY_ID_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertFalse(result["official_close_verified"])

    def test_rejected_prior_issuer_class_conflict_from_original_bytes(self):
        r, t = packet()
        r[1]["previous_issuer_class"] = "ADR"
        body = json.loads(t[1]["raw_body"])
        body["previous_issuer_class"] = "ADR"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("PARSED_BODY_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT", result["issues"])
        self.assertNotIn("PARSED_BODY_ISSUER_CLASS_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")

    def test_action_record_prior_identity_mismatch_is_byte_bound_and_censored(self):
        r, t = packet()
        r[1]["corporate_action"]["previous_security_id"] = "TEST-ISSUER"
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["previous_security_id"] = "DIFFERENT-ISSUER"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_REPORT_ACTION_MISMATCH_PREVIOUS_SECURITY_ID", result["issues"])
        self.assertIn("BODY_ACTION_IDENTITY_NOT_STABLE", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 1)
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_rejected_action_record_prior_identity_conflict_is_retained(self):
        r, t = packet()
        for i, value in enumerate(("TEST-ISSUER", "DIFFERENT-ISSUER")):
            r[i]["corporate_action"]["previous_security_id"] = value
            body = json.loads(t[i]["raw_body"])
            body["corporate_action"]["previous_security_id"] = value
            replace_body(t, i, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("PARSED_BODY_ACTION_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT",
                      result["issues"])
        self.assertIn("BODY_ACTION_IDENTITY_NOT_STABLE", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertFalse(result["official_close_verified"])

    def test_distinct_symbols_cannot_pass_cross_provider_identity_check(self):
        # Both receipts and JSON bodies are internally consistent, but they
        # refer to different tickers. Same prices cannot erase the mismatch.
        r, t = packet()
        r[1]["symbol"] = "OTHER"
        body = json.loads(t[1]["raw_body"])
        body["symbol"] = "OTHER"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("PARSED_BODY_SYMBOL_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["byte_bound_unauthenticated_count"], 2)
        self.assertEqual(result["status"], "BLOCKED_CENSORED")
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_rejected_third_source_symbol_disagreement_is_retained(self):
        # An invalid third source must remain in the complete conflict
        # inventory instead of being dropped in favor of agreeing sources.
        r, t = packet()
        third_r, third_t = copy.deepcopy(r[1]), copy.deepcopy(t[1])
        third_r["source_id"] = third_t["source_id"] = "source-2"
        third_r["provider_organization"] = third_t["provider_organization"] = "group-2"
        third_r["source_url"] = third_t["requested_url"] = third_t["response_url"] = "https://provider-c.example/close"
        third_r["symbol"] = "OTHER"
        third_r["previous_security_id"] = "WRONG-PRIOR-ISSUER"
        body = json.loads(third_t["raw_body"])
        body.update(source_id="source-2", symbol="OTHER",
                    previous_security_id="WRONG-PRIOR-ISSUER")
        replace_body([third_t], 0, json.dumps(body).encode())
        r.append(third_r)
        t.append(third_t)
        result = self.check(r, t)
        self.assertEqual(result["indexed_count"], 3)
        self.assertIn("PARSED_BODY_SYMBOL_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["all_source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertFalse(result["official_close_verified"])

    def test_agreeing_symbol_does_not_create_symbol_conflict(self):
        result = self.check()
        self.assertNotIn("PARSED_BODY_SYMBOL_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["status"], "BODY_CONSISTENT_EXTERNAL_AUTH_PENDING")


    def test_rejected_current_session_date_disagreement_is_in_full_inventory(self):
        r, t = packet()
        r[1]["session_date"] = "2026-10-27"
        body = json.loads(t[1]["raw_body"])
        body["session_date"] = "2026-10-27"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_WRONG_SESSION_PAIR", result["issues"])
        self.assertIn("PARSED_BODY_SESSION_DATE_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertFalse(result["official_close_verified"])

    def test_rejected_previous_session_date_disagreement_is_in_full_inventory(self):
        r, t = packet()
        r[1]["previous_session_date"] = "2026-10-26"
        body = json.loads(t[1]["raw_body"])
        body["previous_session_date"] = "2026-10-26"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("BODY_WRONG_SESSION_PAIR", result["issues"])
        self.assertIn("PARSED_BODY_PREVIOUS_SESSION_DATE_CLAIM_CONFLICT", result["issues"])
        self.assertEqual(result["all_source_rows"][1]["status"], "REJECTED_CENSORED")
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_rejected_third_source_action_window_start_conflict_is_retained(self):
        r, t = packet()
        third_r, third_t = copy.deepcopy(r[1]), copy.deepcopy(t[1])
        third_r["source_id"] = third_t["source_id"] = "source-2"
        third_r["provider_organization"] = third_t["provider_organization"] = "group-2"
        third_r["source_url"] = third_t["requested_url"] = third_t["response_url"] = "https://provider-c.example/close"
        third_r["corporate_action"]["coverage_start"] = "2026-10-26"
        body = json.loads(third_t["raw_body"])
        body["source_id"] = "source-2"
        body["provider_organization"] = "group-2"
        body["corporate_action"]["coverage_start"] = "2026-10-26"
        replace_body([third_t], 0, json.dumps(body).encode())
        r.append(third_r)
        t.append(third_t)
        result = self.check(r, t)
        self.assertEqual(result["indexed_count"], 3)
        self.assertIn("PARSED_BODY_ACTION_COVERAGE_START_CLAIM_CONFLICT", result["issues"])
        self.assertIn("ACTION_WINDOW_OR_STATUS_NOT_CLEARED", result["issues"])
        self.assertEqual(result["all_source_rows"][2]["status"], "REJECTED_CENSORED")
        self.assertFalse(result["official_close_verified"])

    def test_rejected_action_window_end_conflict_is_retained(self):
        r, t = packet()
        r[1]["corporate_action"]["coverage_end"] = "2026-10-29"
        body = json.loads(t[1]["raw_body"])
        body["corporate_action"]["coverage_end"] = "2026-10-29"
        replace_body(t, 1, json.dumps(body).encode())
        result = self.check(r, t)
        self.assertIn("PARSED_BODY_ACTION_COVERAGE_END_CLAIM_CONFLICT", result["issues"])
        self.assertIn("ACTION_WINDOW_OR_STATUS_NOT_CLEARED", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_CENSORED")

    def test_agreeing_session_and_action_windows_have_no_window_conflict(self):
        result = self.check()
        for issue in (
            "PARSED_BODY_SESSION_DATE_CLAIM_CONFLICT",
            "PARSED_BODY_PREVIOUS_SESSION_DATE_CLAIM_CONFLICT",
            "PARSED_BODY_ACTION_COVERAGE_START_CLAIM_CONFLICT",
            "PARSED_BODY_ACTION_COVERAGE_END_CLAIM_CONFLICT",
        ):
            self.assertNotIn(issue, result["issues"])
        self.assertEqual(result["status"], "BODY_CONSISTENT_EXTERNAL_AUTH_PENDING")

if __name__ == "__main__":
    unittest.main()
