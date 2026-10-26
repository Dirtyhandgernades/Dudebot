"""Offline adversarial tests for prospective artifact integrity verification."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_prospective_capture import collect, persist
from backtest.obsidian_prospective_verify import InvalidCapture, verify_capture

AT = datetime(2026, 10, 26, 19, 50, tzinfo=timezone.utc)


def snapshot(price):
    return {"latestTrade": {"p": price, "t": "2026-10-26T19:49:00Z"},
            "prevDailyBar": {"c": 10, "t": "2026-10-23T04:00:00Z"},
            "minuteBar": {"t": "2026-10-26T19:48:00Z"}}


class Provider:
    def __init__(self, prices=None):
        self.prices = prices if prices is not None else {"AAAA": 9.5, "BBBB": 7, "CCCC": 11}

    def assets(self):
        return [{"symbol": symbol, "status": "active", "exchange": "NASDAQ"}
                for symbol in self.prices]

    def snapshots(self, symbols):
        return {symbol: snapshot(self.prices[symbol]) for symbol in symbols}


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "capture"
        persist(*collect(Provider(), clock=lambda: AT), destination=self.root)

    def rewrite_jsonl(self, name, rows, update_hash=None):
        data = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode()
        (self.root / name).write_bytes(data)
        if update_hash:
            manifest_path = self.root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest[update_hash] = hashlib.sha256(data).hexdigest()
            manifest_path.write_text(json.dumps(manifest))

    def test_complete_capture_verifies_but_remains_non_executable(self):
        result = verify_capture(self.root)
        self.assertEqual(result["universe_count"], 3)
        self.assertEqual(result["watch_count"], 2)
        self.assertEqual(result["blocked_count"], 2)
        self.assertFalse(result["trade_authorized"])

    def test_tampered_universe_hash_rejected(self):
        path = self.root / "universe.jsonl"
        path.write_bytes(path.read_bytes().replace(b"\n", b" \n", 1))
        with self.assertRaisesRegex(InvalidCapture, "UNIVERSE_HASH_MISMATCH"):
            verify_capture(self.root)

    def test_truncated_candidate_file_rejected(self):
        path = self.root / "candidates.jsonl"
        path.write_bytes(path.read_bytes().rstrip(b"\n"))
        with self.assertRaisesRegex(InvalidCapture, "TRUNCATED_CANDIDATES"):
            verify_capture(self.root)

    def test_rehashed_price_tampering_still_rejected_by_provenance(self):
        rows = [json.loads(line) for line in (self.root / "candidates.jsonl").read_text().splitlines()]
        rows[0]["decision_price"] = 4
        self.rewrite_jsonl("candidates.jsonl", rows, "candidate_sha256")
        with self.assertRaisesRegex(InvalidCapture, "CANDIDATE_PROVENANCE_MISMATCH"):
            verify_capture(self.root)

    def test_rehashed_universe_missingness_rejected(self):
        rows = [json.loads(line) for line in (self.root / "universe.jsonl").read_text().splitlines()]
        rows[0]["screen_status"] = "NO_PRICE_ONLY_A_OR_B_SETUP"
        self.rewrite_jsonl("universe.jsonl", rows, "universe_sha256")
        with self.assertRaisesRegex(InvalidCapture, "STATUS_COUNTS_MISMATCH"):
            verify_capture(self.root)

    def test_modified_frozen_journal_rejected(self):
        path = self.root / "journal.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["audit"]["status"] = "RESEARCH_ELIGIBLE_NOT_EXECUTABLE"
        self.rewrite_jsonl("journal.jsonl", rows)
        with self.assertRaisesRegex(InvalidCapture, "FROZEN_JOURNAL_MISMATCH"):
            verify_capture(self.root)

    def test_rehashed_future_received_at_rejected(self):
        rows = [json.loads(line) for line in (self.root / "universe.jsonl").read_text().splitlines()]
        rows[0]["received_at"] = "2026-10-26T20:05:00+00:00"
        self.rewrite_jsonl("universe.jsonl", rows, "universe_sha256")
        with self.assertRaisesRegex(InvalidCapture, "INVALID_UNIVERSE_CHRONOLOGY"):
            verify_capture(self.root)

    def test_empty_watch_set_has_no_journal_and_is_valid(self):
        other = Path(self.temp.name) / "no-candidates"
        persist(*collect(Provider({"AAAA": 11}), clock=lambda: AT), destination=other)
        result = verify_capture(other)
        self.assertEqual(result["watch_count"], 0)
        self.assertFalse((other / "journal.jsonl").exists())

    def test_missing_journal_rejected(self):
        (self.root / "journal.jsonl").unlink()
        with self.assertRaisesRegex(InvalidCapture, "MISSING_JOURNAL"):
            verify_capture(self.root)


if __name__ == "__main__":
    unittest.main()
