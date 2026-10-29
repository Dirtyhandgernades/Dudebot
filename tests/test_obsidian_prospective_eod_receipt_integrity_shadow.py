"""Synthetic only: no network receipts, source authentication, or forecasts."""
import copy
import hashlib
import unittest
from datetime import date

from backtest.obsidian_eod_receipt_integrity_shadow import audit_receipts

DAY = date(2026, 10, 28)
COLLECTED = "2026-10-28T20:10:00Z"


def packet():
    reports, receipts = [], []
    for i, (group, host) in enumerate((("independent-a", "a.example"),
                                       ("independent-b", "b.example"))):
        url = f"https://{host}/official-close?key=secret-{i}"
        body = (f'{{"provider":"{group}","close":"8.00"}}').encode()
        reports.append({"source_id": f"source-{i}", "provider_organization": group,
                        "source_url": url, "regular_close": "8.00"})
        receipts.append({"source_id": f"source-{i}", "provider_organization": group,
                         "requested_url": url, "response_url": url,
                         "http_status": 200, "http_method": "GET",
                         "content_type": "application/json; charset=utf-8",
                         "retrieved_at": "2026-10-28T20:08:00Z",
                         "raw_body": body, "body_sha256": hashlib.sha256(body).hexdigest()})
    return reports, receipts


class ReceiptIntegrityTests(unittest.TestCase):
    def run_audit(self, reports=None, receipts=None):
        r, t = packet()
        return audit_receipts(DAY, r if reports is None else reports,
                              t if receipts is None else receipts, COLLECTED)

    def test_two_matching_bytes_still_not_official_or_authenticated(self):
        result = self.run_audit()
        self.assertEqual(result["status"], "BYTE_CONSISTENT_EXTERNAL_AUTH_PENDING")
        self.assertEqual(result["byte_consistent_count"], 2)
        self.assertFalse(result["official_close_verified"])
        self.assertFalse(result["source_price_claim_parsed_and_bound_to_body"])
        self.assertIsNone(result["verified_20pct_prediction_success"])
        self.assertFalse(result["smg_trade_authorized"])

    def test_modified_body_rejects_digest(self):
        r, t = packet()
        t[1]["raw_body"] += b"X"
        result = self.run_audit(r, t)
        self.assertIn("RESPONSE_BODY_SHA256_MISMATCH", result["issues"])
        self.assertEqual(result["byte_consistent_count"], 1)

    def test_missing_third_receipt_keeps_every_report(self):
        r, t = packet()
        r.append({**r[1], "source_id": "source-2"})
        result = self.run_audit(r, t)
        self.assertEqual(result["indexed_count"], 3)
        self.assertIn("REPORT_RECEIPT_COUNT_MISMATCH_NO_SELECTIVE_OMISSION", result["issues"])
        self.assertIn("MISSING_OR_MALFORMED_SOURCE_RECEIPT", result["all_source_rows"][2]["issues"])

    def test_extra_receipt_not_silently_dropped(self):
        r, t = packet()
        t.append(copy.deepcopy(t[1]))
        result = self.run_audit(r, t)
        self.assertEqual(result["indexed_count"], 3)
        self.assertIn("MISSING_OR_MALFORMED_SOURCE_REPORT", result["all_source_rows"][2]["issues"])

    def test_provider_alias_does_not_establish_independence(self):
        r, t = packet()
        r[1]["provider_organization"] = t[1]["provider_organization"] = "independent-a"
        result = self.run_audit(r, t)
        self.assertIn("TWO_DISTINCT_PROVIDER_ORGANIZATIONS_AND_HOSTS_NOT_ESTABLISHED", result["issues"])

    def test_mirrored_body_does_not_establish_independence(self):
        r, t = packet()
        t[1]["raw_body"] = t[0]["raw_body"]
        t[1]["body_sha256"] = t[0]["body_sha256"]
        result = self.run_audit(r, t)
        self.assertIn("IDENTICAL_RAW_PAYLOAD_ACROSS_SOURCES_INDEPENDENCE_UNPROVEN", result["issues"])

    def test_redirect_to_different_host_is_censored(self):
        r, t = packet()
        t[1]["response_url"] = "https://third.example/close"
        result = self.run_audit(r, t)
        self.assertIn("SOURCE_ORGANIZATION_URL_OR_REDIRECT_MISMATCH", result["issues"])

    def test_stale_and_future_receipts_censored(self):
        r, t = packet()
        t[0]["retrieved_at"] = "2026-10-28T19:59:59Z"
        t[1]["retrieved_at"] = "2026-10-28T20:11:00Z"
        result = self.run_audit(r, t)
        self.assertEqual(result["byte_consistent_count"], 0)
        self.assertIn("RECEIPT_TIMESTAMP_OUTSIDE_POSTCLOSE_WINDOW", result["issues"])

    def test_malformed_receipt_is_indexed(self):
        r, t = packet()
        t[1] = ["invalid"]
        result = self.run_audit(r, t)
        self.assertIn("MISSING_OR_MALFORMED_SOURCE_RECEIPT", result["all_source_rows"][1]["issues"])

    def test_nonbyte_body_and_http_failure_are_censored(self):
        r, t = packet()
        t[1]["raw_body"] = "text"
        t[1]["http_status"] = 403
        result = self.run_audit(r, t)
        self.assertIn("MISSING_OVERSIZED_OR_NONBYTE_RESPONSE_BODY", result["issues"])
        self.assertIn("NON_SUCCESSFUL_OR_NON_GET_HTTP_CLAIM", result["issues"])

    def test_no_url_credentials_or_body_echoed(self):
        r, t = packet()
        result = self.run_audit(r, t)
        output = repr(result)
        self.assertNotIn("secret-0", output)
        self.assertNotIn("secret-1", output)
        self.assertNotIn('"close"', output)

    def test_non_postclose_collection_rejected(self):
        r, t = packet()
        with self.assertRaisesRegex(ValueError, "POSTCLOSE_COLLECTION"):
            audit_receipts(DAY, r, t, "2026-10-28T19:59:59Z")

    def test_non_https_source_rejected(self):
        r, t = packet()
        r[0]["source_url"] = t[0]["requested_url"] = t[0]["response_url"] = "http://a.example/close"
        result = self.run_audit(r, t)
        self.assertIn("SOURCE_ORGANIZATION_URL_OR_REDIRECT_MISMATCH", result["issues"])


if __name__ == "__main__":
    unittest.main()
