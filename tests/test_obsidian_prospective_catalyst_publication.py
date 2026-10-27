"""Offline adversarial catalyst publication timing regression tests."""
import unittest
from backtest.obsidian_catalyst_publication_guard import catalyst_asof_status as check


class CatalystPublicationGuardTests(unittest.TestCase):
    def test_artv_internal_approval_is_not_oct26_public_signal(self):
        self.assertEqual(check(
            "2026-10-26T19:50:00Z", "2026-10-27T11:30:00Z",
            "2026-10-27T13:13:55Z", internal_at="2026-10-22T12:00:00Z"),
            "POST_DECISION_PUBLICATION_NOT_PRIOR_PUBLIC_SIGNAL")

    def test_oct27_morning_public_release_is_available_after_730(self):
        self.assertEqual(check(
            "2026-10-27T12:49:00Z", "2026-10-27T11:30:00Z",
            "2026-10-27T13:13:55Z"),
            "PUBLIC_AT_DECISION_NOT_PROOF_SCREENED_OR_ACTIONABLE")

    def test_future_source_is_rejected(self):
        self.assertEqual(check(
            "2026-10-27T12:49:00Z", "2026-10-27T14:00:00Z",
            "2026-10-27T13:13:55Z"),
            "INCONSISTENT_FUTURE_OBSERVATION")

    def test_missing_publication_not_backdated(self):
        self.assertEqual(check(
            "2026-10-26T19:50:00Z", None, "2026-10-27T13:13:55Z"),
            "MISSING_OR_INVALID_PUBLICATION_CLOCK")

    def test_private_board_approval_does_not_change_public_timing(self):
        self.assertEqual(check(
            "2026-10-26T19:50:00Z", "2026-10-27T11:30:00Z",
            "2026-10-27T13:13:55Z", internal_at="2026-10-21T12:00:00Z"),
            check("2026-10-26T19:50:00Z", "2026-10-27T11:30:00Z",
                  "2026-10-27T13:13:55Z"))

    def test_bad_naive_clock_rejected(self):
        self.assertEqual(check(
            "2026-10-26T19:50:00", "2026-10-27T11:30:00Z",
            "2026-10-27T13:13:55Z"),
            "MISSING_OR_INVALID_PUBLICATION_CLOCK")


if __name__ == "__main__":
    unittest.main()
