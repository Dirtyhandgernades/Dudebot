"""Offline fixtures for the frozen ZIP byte/CRC/member integrity gate."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
import zipfile
from backtest.obsidian_pinned_zip_restore_audit import (inspect_zip, jsonl_symbols,
    cohort_identity_report, CAPTURE_COHORT_IDS)


class PinnedRestoreTests(unittest.TestCase):
    def make_zip(self, entries):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, body in entries:
                archive.writestr(name, body)
        return raw.getvalue()

    def test_exact_zip_digest_crc_and_members(self):
        raw = self.make_zip([("manifest.json", '{}'), ("universe.jsonl", '{"ticker":"A"}\n')])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "capture.zip"
            path.write_bytes(raw)
            files = inspect_zip(path, hashlib.sha256(raw).hexdigest(),
                                ("manifest.json", "universe.jsonl"))
            self.assertEqual(files["manifest.json"], b"{}")
            with self.assertRaisesRegex(ValueError, "PINNED_ZIP_SHA256_MISMATCH"):
                inspect_zip(path, "0" * 64, ("manifest.json", "universe.jsonl"))
            with self.assertRaisesRegex(ValueError, "ZIP_MEMBER_SET_MISMATCH"):
                inspect_zip(path, hashlib.sha256(raw).hexdigest(), ("manifest.json",))

    def test_duplicate_member_and_unsafe_path_rejected(self):
        for entries, reason in [([("same.json", "a"), ("same.json", "b")], "DUPLICATE_ZIP_MEMBER"),
                                ([("../escape.json", "a")], "UNSAFE_ZIP_MEMBER_PATH")]:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as folder:
                raw = self.make_zip(entries)
                path = Path(folder) / "bad.zip"
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, reason):
                    inspect_zip(path, hashlib.sha256(raw).hexdigest(), tuple(n for n, _ in entries))

    def test_duplicate_and_missing_issuer_identity_rejected(self):
        self.assertEqual(jsonl_symbols(b'{"ticker":"A"}\n{"ticker":"B"}\n'), ["A", "B"])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SYMBOL"):
            jsonl_symbols(b'{"ticker":"A"}\n{"ticker":"A"}\n')
        with self.assertRaisesRegex(ValueError, "MISSING_SYMBOL"):
            jsonl_symbols(b'{"ticker":"A"}\n{}\n')

    def cohort_fixture(self):
        original = [f"T{i:05d}" for i in range(8510)]
        captures = {artifact_id: list(original) for artifact_id in CAPTURE_COHORT_IDS}
        monitor = original[:127] + [f"OFF{i:03d}" for i in range(9)]
        roster_sha = hashlib.sha256(("\\n".join(sorted(monitor)) + "\\n").encode()).hexdigest()
        return captures, list(original), monitor, roster_sha

    def test_exact_cohort_identity_and_nine_off_universe_monitors(self):
        captures, ledger, monitor, roster_sha = self.cohort_fixture()
        result = cohort_identity_report(captures, ledger, monitor, roster_sha)
        self.assertTrue(result["capture_and_maturity_symbol_sets_identical"])
        self.assertEqual(result["monitor_on_original_universe_count"], 127)
        self.assertEqual(result["monitor_off_original_universe_count"], 9)
        self.assertEqual(result["monitor_off_original_universe_symbols"],
                         [f"OFF{i:03d}" for i in range(9)])
        self.assertFalse(result["off_universe_names_added_to_frozen_cohort"])

    def test_same_denominator_but_different_symbol_cannot_pass(self):
        captures, ledger, monitor, roster_sha = self.cohort_fixture()
        captures[12995764777][-1] = "REPLACEMENT"
        with self.assertRaisesRegex(ValueError, "CROSS_ARTIFACT_COHORT_IDENTITY_DRIFT"):
            cohort_identity_report(captures, ledger, monitor, roster_sha)
        captures, ledger, monitor, roster_sha = self.cohort_fixture()
        ledger[-1] = "REPLACEMENT"
        with self.assertRaisesRegex(ValueError, "MATURITY_LEDGER_COHORT_IDENTITY_DRIFT"):
            cohort_identity_report(captures, ledger, monitor, roster_sha)

    def test_same_size_modified_monitor_fails_frozen_roster_digest(self):
        captures, ledger, monitor, roster_sha = self.cohort_fixture()
        monitor[-1] = "NEW_OFFBOARD"
        with self.assertRaisesRegex(ValueError, "FROZEN_136_ROSTER_SHA256_MISMATCH"):
            cohort_identity_report(captures, ledger, monitor, roster_sha)


if __name__ == "__main__":
    unittest.main()
