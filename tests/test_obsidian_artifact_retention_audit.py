"""Fail-closed tests for the read-only OBSIDIAN retention manifest."""
import copy
import unittest

from backtest.obsidian_artifact_retention_audit import PINNED, BRANCH, audit

NOW = "2026-10-30T23:46:00Z"


def packets():
    return [
        {"run_id": run, "artifacts": [{
            "id": artifact_id, "digest": "sha256:" + digest,
            "created_at": "2026-10-30T19:47:00Z",
            "expires_at": "2027-01-28T19:47:00Z",
            "expired": False, "size_in_bytes": 1024,
            "workflow_run": {"id": run, "head_branch": BRANCH},
        }]} for run, artifact_id, digest, _role, _n in PINNED
    ]


class ArtifactRetentionAuditTests(unittest.TestCase):
    def test_all_pinned_metadata_matches_without_claiming_backup(self):
        report = audit(packets(), NOW)
        self.assertEqual(report["metadata_matched_count"], 7)
        self.assertEqual(report["blocked_count"], 0)
        self.assertEqual(report["backup_status"], "BACKUP_UNVERIFIED")
        self.assertFalse(report["official_closes_authenticated"])
        self.assertTrue(all(not x["zip_bytes_rehashed_by_this_audit"] for x in report["rows"]))

    def test_digest_mismatch_censors_only_that_receipt(self):
        source = packets()
        source[0]["artifacts"][0]["digest"] = "sha256:" + "0" * 64
        report = audit(source, NOW)
        self.assertEqual(report["blocked_count"], 1)
        self.assertIn("PINNED_METADATA_DIGEST_MISMATCH", report["rows"][0]["issues"])

    def test_expired_artifact_is_not_available(self):
        source = packets()
        source[0]["artifacts"][0]["expires_at"] = "2026-10-29T00:00:00Z"
        report = audit(source, NOW)
        self.assertIn("RETENTION_DEADLINE_PASSED", report["rows"][0]["issues"])

    def test_wrong_branch_and_missing_artifact_fail_closed(self):
        source = packets()
        source[1]["artifacts"][0]["workflow_run"]["head_branch"] = "main"
        source[2]["artifacts"] = []
        report = audit(source, NOW)
        self.assertEqual(report["blocked_count"], 2)
        self.assertIn("WRONG_SOURCE_RUN_OR_BRANCH", report["rows"][1]["issues"])
        self.assertIn("ARTIFACT_MISSING_OR_DUPLICATED", report["rows"][2]["issues"])

    def test_duplicate_run_and_naive_clock_rejected(self):
        source = packets()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_RUN_PACKET"):
            audit(source + [copy.deepcopy(source[0])], NOW)
        with self.assertRaisesRegex(ValueError, "AWARE_AS_OF"):
            audit(source, "2026-10-30T23:46:00")


if __name__ == "__main__":
    unittest.main()
