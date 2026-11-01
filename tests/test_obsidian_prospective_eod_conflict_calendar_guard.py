"""Offline, outcome-blind regression for EOD all-source published-calendar claims.

No live vendor data, official exchange close or trading authority is inferred.
"""
import unittest
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from backtest.obsidian_eod_conflict_inventory import inventory

ET = ZoneInfo("America/New_York")


def claimed_packet(session, previous, early=False):
    close = datetime.combine(session, time(16), tzinfo=ET)
    prior_close = datetime.combine(previous, time(16), tzinfo=ET)
    observed = (close + timedelta(minutes=10)).isoformat()
    calendar = {
        "session_date": session.isoformat(),
        "previous_session_date": previous.isoformat(),
        "session_open": True,
        "exchange_calendar_url": "https://www.nyse.com/trade/hours-calendars",
        "regular_close_at": close.isoformat(),
        "previous_regular_close_at": prior_close.isoformat(),
        "early_close": early,
    }

    def source(index):
        return {
            "source_id": "receipt_" + str(index),
            "provider_organization": "provider_" + str(index),
            "source_url": "https://vendor" + str(index) + ".example/eod",
            "symbol": "ZZZZ",
            "security_id": "ISSUER:COMMON",
            "previous_security_id": "ISSUER:COMMON",
            "session_date": session.isoformat(),
            "previous_session_date": previous.isoformat(),
            "kind": "regular_close",
            "session_complete": True,
            "regular_close": "8.50",
            "previous_regular_close": "10.00",
            "regular_close_asof": close.isoformat(),
            "previous_regular_close_asof": prior_close.isoformat(),
            "observed_at": observed,
        }

    return inventory("ZZZZ", session, previous, calendar,
                     [source(1), source(2)],
                     (close + timedelta(minutes=20)).isoformat())


class AllSourcePublishedCalendarTests(unittest.TestCase):
    def assert_censored(self, result, issue):
        self.assertIn(issue, result["issues"])
        self.assertEqual(result["retained_report_count"], 2)
        self.assertTrue(result["all_supplied_rows_indexed"])
        self.assertEqual(result["structural_status"], "BLOCKED_CENSORED")
        self.assertFalse(result["official_regular_close_verified"])
        self.assertFalse(result["eligible_for_frozen_scoring"])
        self.assertIsNone(result["verified_20pct_prediction_success"])

    def test_skipped_open_day_is_not_consistent(self):
        self.assert_censored(
            claimed_packet(date(2026, 10, 28), date(2026, 10, 26)),
            "PREVIOUS_SESSION_NOT_ADJACENT_ON_PUBLISHED_2026_CALENDAR")

    def test_published_holiday_and_weekend_censored(self):
        for session, previous in (
            (date(2026, 11, 26), date(2026, 11, 25)),
            (date(2026, 11, 29), date(2026, 11, 27)),
        ):
            with self.subTest(session=session):
                self.assert_censored(
                    claimed_packet(session, previous),
                    "CLOSED_OR_UNVERIFIED_PUBLISHED_2026_SESSION")

    def test_forged_normal_close_on_published_early_close(self):
        result = claimed_packet(date(2026, 11, 27), date(2026, 11, 25))
        self.assert_censored(
            result, "EARLY_CLOSE_REQUIRES_SEPARATE_1300_ET_SOURCE_CONTRACT")
        self.assertIn("PUBLISHED_EARLY_CLOSE_CALENDAR_FLAG_MISMATCH",
                      result["issues"])

    def test_previous_early_close_reference_is_not_normal_close(self):
        self.assert_censored(
            claimed_packet(date(2026, 11, 30), date(2026, 11, 27)),
            "EARLY_CLOSE_REQUIRES_SEPARATE_1300_ET_SOURCE_CONTRACT")

    def test_out_of_scope_year_not_accepted(self):
        self.assert_censored(
            claimed_packet(date(2027, 1, 4), date(2026, 12, 31)),
            "CLOSED_OR_UNVERIFIED_PUBLISHED_2026_SESSION")

    def test_holiday_gap_and_adjacent_normal_days_remain_diagnostic_only(self):
        for session, previous in (
            (date(2026, 9, 8), date(2026, 9, 4)),
            (date(2026, 10, 28), date(2026, 10, 27)),
        ):
            with self.subTest(session=session):
                result = claimed_packet(session, previous)
                self.assertEqual(
                    result["structural_status"],
                    "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING")
                self.assertFalse(result["official_regular_close_verified"])
                self.assertFalse(result["eligible_for_frozen_scoring"])


if __name__ == "__main__":
    unittest.main()
