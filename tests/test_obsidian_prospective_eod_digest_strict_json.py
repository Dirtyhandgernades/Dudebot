"""Synthetic strict-JSON evidence fingerprints; never market observations."""
import unittest
from datetime import date

from backtest.obsidian_eod_conflict_inventory import report_digest, inventory
from backtest.obsidian_eod_action_identity_shadow import audit_action_identity


class StrictJsonEvidenceDigestTests(unittest.TestCase):
    def test_numeric_and_boolean_object_keys_cannot_alias_string_keys(self):
        canonical = report_digest({"1": "value", "true": "other"})
        self.assertEqual(len(canonical), 64)
        self.assertIsNone(report_digest({1: "value", "true": "other"}))
        self.assertIsNone(report_digest({"1": "value", True: "other"}))
        self.assertIsNone(report_digest({"nested": {"null": "x", None: "y"}}))

    def test_tuple_cannot_alias_list_and_nested_tuples_are_rejected(self):
        self.assertIsNotNone(report_digest({"rows": ["a", "b"]}))
        self.assertIsNone(report_digest({"rows": ("a", "b")}))
        self.assertIsNone(report_digest({"rows": [{"extra": (1, 2)}]}))

    def test_cycles_and_invalid_unicode_fail_closed(self):
        packet = {"source": "test"}
        packet["cycle"] = packet
        self.assertIsNone(report_digest(packet))
        self.assertIsNone(report_digest({"source": chr(0xD800)}))

    def test_valid_json_claim_is_stable_across_dict_key_order(self):
        a = {"outer": {"a": [1, True, None], "b": 2.5}, "source": "x"}
        b = {"source": "x", "outer": {"b": 2.5, "a": [1, True, None]}}
        self.assertEqual(report_digest(a), report_digest(b))

    def test_action_packet_with_nested_numeric_key_is_censored(self):
        day, previous = date(2026, 10, 28), date(2026, 10, 27)
        row = {
            "source_id": "a", "provider_organization": "alpha",
            "source_url": "https://alpha.example/close", "symbol": "ZZZZ",
            "session_date": day.isoformat(), "previous_session_date": previous.isoformat(),
            "security_id": "ID:COMMON", "previous_security_id": "ID:COMMON",
            "issuer_class": "COMMON", "previous_issuer_class": "COMMON",
            "observed_at": "2026-10-28T20:25:00Z",
            "corporate_action_evidence": {
                "source_url": "https://alpha.example/actions",
                "security_id": "ID:COMMON", "previous_security_id": "ID:COMMON",
                "issuer_class": "COMMON", "previous_issuer_class": "COMMON",
                "status": "NONE", "previous_close_basis": "UNADJUSTED",
                "coverage_start": previous.isoformat(), "coverage_end": day.isoformat(),
                "checked_at": "2026-10-28T20:30:00Z",
                "vendor_extra": {1: "ambiguous"},
            },
        }
        result = audit_action_identity(
            "ZZZZ", day, previous, [row], "2026-10-28T21:00:00Z")
        self.assertIsNone(result["supplied_action_packet_sha256"])
        self.assertIsNone(result["all_source_rows"][0]["supplied_report_sha256"])
        self.assertIn("NON_JSON_ACTION_PACKET_NOT_REPRODUCIBLY_HASHABLE", result["issues"])
        self.assertIn("NON_JSON_ACTION_SOURCE_RECORD_NOT_REPRODUCIBLY_HASHABLE", result["issues"])
        self.assertEqual(result["status"], "BLOCKED_CENSORED")
        self.assertFalse(result["official_close_verified"])


if __name__ == "__main__":
    unittest.main()
