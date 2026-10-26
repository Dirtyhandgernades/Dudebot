"""Unit tests for coverage-censored OBSIDIAN research, no provider calls."""
import unittest
from backtest.obsidian_matched_comparison import matched_events


class MatchedComparisonTests(unittest.TestCase):
    def setUp(self):
        self.day = "2025-11-06"
        self.packet = {
            "sessions": ["2025-11-05", self.day],
            "raw": {"ABC": {"2025-11-05": {"c": 10}, self.day: {"c": 9.5}}},
            "split": {"ABC": {self.day: {"c": 9.5}}},
        }
        self.event = {
            "ticker": "ABC", "decision_price": 9.5,
            "decision_at": "2025-11-06T20:40:00+00:00",
            "data_cutoff": "2025-11-06T20:24:00+00:00",
            "last_complete_at": "2025-11-06T20:20:00+00:00",
        }
        self.records = {
            "2025-11-06|ABC": {
                "status": "RECOVERED", "day": self.day,
                "ticker": "ABC", "year": 2025,
            },
        }

    def test_same_coverage_gate_for_baseline_and_challenger(self):
        base, early, audit = matched_events(
            self.packet, {self.day: [self.event]}, self.records, 2025
        )
        self.assertEqual(len(base[self.day]), 1)
        self.assertEqual(len(early[self.day]), 1)
        self.assertEqual(audit["MATCHED_BASELINE_SIGNALS"], 1)

    def test_missing_or_stale_window_is_censored_not_assumed_zero(self):
        self.records["2025-11-06|ABC"]["status"] = "PROVIDER_EMPTY_OR_STALE"
        base, early, audit = matched_events(
            self.packet, {self.day: [self.event]}, self.records, 2025
        )
        self.assertEqual(base[self.day], [])
        self.assertEqual(early[self.day], [])
        self.assertEqual(audit["CENSORED_UNVERIFIED_WINDOW"], 1)

    def test_early_filter_does_not_see_future_close(self):
        original = matched_events(self.packet, {self.day: [self.event]}, self.records, 2025)
        self.packet["raw"]["ABC"][self.day]["c"] = 3.01
        after = matched_events(self.packet, {self.day: [self.event]}, self.records, 2025)
        self.assertEqual(len(original[1][self.day]), len(after[1][self.day]))

    def test_preclose_observation_after_cutoff_fails_closed(self):
        event = dict(self.event, last_complete_at="2025-11-06T20:30:00+00:00")
        with self.assertRaisesRegex(ValueError, "LOOKAHEAD"):
            matched_events(self.packet, {self.day: [event]}, self.records, 2025)

    def test_checkpoint_identity_mismatch_fails_closed(self):
        self.records["2025-11-06|ABC"]["ticker"] = "XYZ"
        with self.assertRaisesRegex(ValueError, "IDENTITY"):
            matched_events(self.packet, {self.day: [self.event]}, self.records, 2025)

    def test_unknown_prior_price_censors(self):
        del self.packet["raw"]["ABC"]["2025-11-05"]
        base, early, audit = matched_events(
            self.packet, {self.day: [self.event]}, self.records, 2025
        )
        self.assertFalse(base[self.day])
        self.assertFalse(early[self.day])
        self.assertEqual(audit["CENSORED_MISSING_DAILY_BAR"], 1)


if __name__ == "__main__":
    unittest.main()
