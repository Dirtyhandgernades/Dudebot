"""Offline fixtures for the frozen ZIP byte/CRC/member integrity gate."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
import zipfile
from backtest.obsidian_pinned_zip_restore_audit import inspect_zip, jsonl_symbols


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


if __name__ == "__main__":
    unittest.main()
