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

    def test_sibling_hosts_cannot_pose_as_independent_provider_groups(self):
        r, t = packet()
        for index, subdomain in enumerate(("quotes.vendor.example", "close.vendor.example")):
            url = "https://" + subdomain + "/official-close"
            r[index]["source_url"] = url
            t[index]["requested_url"] = t[index]["response_url"] = url
        result = self.run_audit(r, t)
        self.assertEqual(result["byte_consistent_count"], 2)
        self.assertIn("TWO_DISTINCT_SOURCE_HOST_PARENT_HINTS_NOT_ESTABLISHED", result["issues"])
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_SOURCE_HOST_PARENT_HINT", result["issues"])
        self.assertFalse(result["official_close_verified"])

    def test_parent_and_subdomain_cannot_pose_as_two_providers(self):
        r, t = packet()
        url = "https://api.a.example/official-close"
        r[1]["source_url"] = url
        t[1]["requested_url"] = t[1]["response_url"] = url
        result = self.run_audit(r, t)
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_SOURCE_HOST_PARENT_HINT", result["issues"])
        self.assertEqual(result["indexed_count"], 2)

    def test_shared_parent_alias_cannot_hide_behind_third_provider(self):
        r, t = packet()
        extra_report = copy.deepcopy(r[0])
        extra_receipt = copy.deepcopy(t[0])
        extra_report["source_id"] = extra_receipt["source_id"] = "source-2"
        extra_report["provider_organization"] = extra_receipt["provider_organization"] = "third-claimed-group"
        extra_report["source_url"] = extra_receipt["requested_url"] = extra_receipt["response_url"] = "https://data.a.example/close"
        extra_receipt["raw_body"] = b'{"provider":"third-claimed-group","close":"8.00"}'
        extra_receipt["body_sha256"] = hashlib.sha256(extra_receipt["raw_body"]).hexdigest()
        r.append(extra_report)
        t.append(extra_receipt)
        result = self.run_audit(r, t)
        self.assertEqual(result["indexed_count"], 3)
        self.assertEqual(result["byte_consistent_count"], 3)
        self.assertIn("CLAIMED_PROVIDER_GROUPS_SHARE_SOURCE_HOST_PARENT_HINT", result["issues"])

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

    def test_unsafe_receipt_url_authorities_are_censored(self):
        unsafe = (
            "https://a.example:8443/close",
            "https://user:pass@a.example/close",
            "https://a.example./close",
            "https://a.example:bogus/close",
            "https://a.example/close" + chr(10) + "extra",
        )
        for url in unsafe:
            with self.subTest(url=repr(url)):
                r, t = packet()
                r[0]["source_url"] = url
                t[0]["requested_url"] = t[0]["response_url"] = url
                result = self.run_audit(r, t)
                self.assertEqual(result["indexed_count"], 2)
                self.assertEqual(result["byte_consistent_count"], 1)
                self.assertIn("SOURCE_ORGANIZATION_URL_OR_REDIRECT_MISMATCH",
                              result["all_source_rows"][0]["issues"])
                self.assertFalse(result["official_close_verified"])

    def test_unsafe_third_receipt_does_not_hide_behind_valid_pair(self):
        r, t = packet()
        third_report, third_receipt = copy.deepcopy(r[0]), copy.deepcopy(t[0])
        third_report["source_id"] = third_receipt["source_id"] = "source-2"
        third_report["provider_organization"] = third_receipt["provider_organization"] = "independent-c"
        url = "https://c.example:9999/close"
        third_report["source_url"] = url
        third_receipt["requested_url"] = third_receipt["response_url"] = url
        third_receipt["raw_body"] = b'{"provider":"independent-c","close":"8.00"}'
        third_receipt["body_sha256"] = hashlib.sha256(third_receipt["raw_body"]).hexdigest()
        r.append(third_report)
        t.append(third_receipt)
        result = self.run_audit(r, t)
        self.assertEqual(result["indexed_count"], 3)
        self.assertEqual(result["byte_consistent_count"], 2)
        self.assertEqual(result["status"], "BLOCKED_RECEIPT_INTEGRITY")
        self.assertIn("SOURCE_ORGANIZATION_URL_OR_REDIRECT_MISMATCH",
                      result["all_source_rows"][2]["issues"])
        self.assertFalse(result["eligible_for_frozen_scoring"])

    def test_non_https_source_rejected(self):
        r, t = packet()
        r[0]["source_url"] = t[0]["requested_url"] = t[0]["response_url"] = "http://a.example/close"
        result = self.run_audit(r, t)
        self.assertIn("SOURCE_ORGANIZATION_URL_OR_REDIRECT_MISMATCH", result["issues"])

    def test_local_ip_and_malformed_dns_receipt_hosts_are_censored(self):
        unsafe = (
            "https://127.0.0.1/close",
            "https://169.254.169.254/close",
            "https://[::1]/close",
            "https://localhost/close",
            "https://a.local/close",
            "https://api.internal/close",
            "https://-bad.example/close",
            "https://good..example/close",
            "https://bad-.example/close",
            "https://\u0430.example/close",
        )
        for url in unsafe:
            with self.subTest(url=url):
                reports, receipts = packet()
                reports[0]["source_url"] = url
                receipts[0]["requested_url"] = receipts[0]["response_url"] = url
                result = self.run_audit(reports, receipts)
                self.assertEqual(result["indexed_count"], 2)
                self.assertEqual(result["byte_consistent_count"], 1)
                self.assertIn("SOURCE_ORGANIZATION_URL_OR_REDIRECT_MISMATCH",
                              result["all_source_rows"][0]["issues"])
                self.assertFalse(result["official_close_verified"])


if __name__ == "__main__":
    unittest.main()
