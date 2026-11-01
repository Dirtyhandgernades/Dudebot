"""Synthetic, outcome-blind calendar adjacency and early-close EOD regressions."""
import unittest
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from backtest.obsidian_eod_source_preflight import preflight

ET = ZoneInfo("America/New_York")


def source(group, session, previous):
    end = datetime.combine(session, time(16), tzinfo=ET)
    prior_end = datetime.combine(previous, time(16), tzinfo=ET)
    return {
        "source_id": group + "_receipt", "provider_group": group,
        "url": "https://" + group + ".example/history",
        "symbol": "ZZZZ", "session_date": session.isoformat(),
        "previous_session_date": previous.isoformat(),
        "kind": "regular_close", "session_complete": True,
        "regular_close": "8.50", "previous_regular_close": "10.00",
        "regular_close_asof": end.isoformat(),
        "previous_regular_close_asof": prior_end.isoformat(),
        "observed_at": (end + timedelta(minutes=10)).isoformat(),
    }


def audit(session, previous):
    end = datetime.combine(session, time(16), tzinfo=ET)
    return preflight("ZZZZ", session, previous,
                     [source("one", session, previous),
                      source("two", session, previous)],
                     (end + timedelta(minutes=20)).isoformat())


class PublishedCalendarContractTests(unittest.TestCase):
    def test_normal_adjacent_dates_remain_only_source_consistent(self):
        r = audit(date(2026, 10, 27), date(2026, 10, 26))
        self.assertEqual(r["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")
        self.assertFalse(r["actual_exchange_session_authenticated"])
        self.assertFalse(r["eligible_for_frozen_forward_scoring"])

    def test_skipped_open_trading_session_is_censored(self):
        r = audit(date(2026, 10, 28), date(2026, 10, 26))
        self.assertIn("PREVIOUS_SESSION_NOT_ADJACENT_ON_PUBLISHED_2026_CALENDAR", r["issues"])
        self.assertEqual(r["status"], "BLOCKED_SOURCE_EVIDENCE")

    def test_published_holiday_gap_is_allowed(self):
        r = audit(date(2026, 9, 8), date(2026, 9, 4))
        self.assertEqual(r["status"], "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE")
        self.assertFalse(r["eligible_for_frozen_forward_scoring"])

    def test_weekend_and_holiday_are_not_sessions(self):
        for session, previous in (
            (date(2026, 11, 29), date(2026, 11, 27)),
            (date(2026, 11, 26), date(2026, 11, 25)),
            (date(2026, 7, 3), date(2026, 7, 2)),
        ):
            with self.subTest(session=session):
                r = audit(session, previous)
                self.assertIn("CLOSED_OR_UNVERIFIED_PUBLISHED_2026_SESSION", r["issues"])
                self.assertEqual(r["status"], "BLOCKED_SOURCE_EVIDENCE")

    def test_fabricated_1600_close_on_1300_early_session_is_blocked(self):
        r = audit(date(2026, 11, 27), date(2026, 11, 25))
        self.assertIn("EARLY_CLOSE_REQUIRES_SEPARATE_1300_ET_SOURCE_CONTRACT", r["issues"])
        self.assertEqual(r["status"], "BLOCKED_SOURCE_EVIDENCE")

    def test_previous_early_close_cannot_masquerade_as_1600(self):
        for session, previous in (
            (date(2026, 11, 30), date(2026, 11, 27)),
            (date(2026, 12, 28), date(2026, 12, 24)),
        ):
            with self.subTest(session=session):
                r = audit(session, previous)
                self.assertIn("EARLY_CLOSE_REQUIRES_SEPARATE_1300_ET_SOURCE_CONTRACT", r["issues"])
                self.assertNotIn("PREVIOUS_SESSION_NOT_ADJACENT_ON_PUBLISHED_2026_CALENDAR", r["issues"])
                self.assertFalse(r["eligible_for_frozen_forward_scoring"])

    def test_out_of_scope_calendar_year_is_not_inferred(self):
        r = audit(date(2027, 1, 4), date(2026, 12, 31))
        self.assertIn("CLOSED_OR_UNVERIFIED_PUBLISHED_2026_SESSION", r["issues"])
        self.assertFalse(r["eligible_for_frozen_forward_scoring"])


if __name__ == "__main__":
    unittest.main()
