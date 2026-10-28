"""Synthetic regression for frozen weekday/16:00 exchange-calendar assumptions."""
import unittest
from backtest.obsidian_forward_calendar_shadow import audit_calendar_assumptions
from backtest.obsidian_forward_collapse_study import previous_weekday
from datetime import date


def evidence(day, prior, close, **updates):
    row = {
        "session_date": day, "previous_regular_session": prior,
        "regular_close_at": close, "session_open": True,
        "source_url": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
        "source_checked_at": "2026-10-27T12:00:00-04:00",
        "independently_checked": True,
    }
    row.update(updates)
    return row


class ForwardCalendarShadowTests(unittest.TestCase):
    def test_regular_oct27_does_not_claim_proof_or_authorize_trades(self):
        result = audit_calendar_assumptions("2026-10-27", evidence(
            "2026-10-27", "2026-10-26", "2026-10-27T16:00:00-04:00"))
        self.assertEqual(result["status"], "SHADOW_CALENDAR_COMPATIBLE_NOT_AUTHENTICATED")
        self.assertFalse(result["eligible_for_frozen_forward_scoring"])
        self.assertFalse(result["trade_authorized"])
        self.assertFalse(result["calendar_evidence_authenticated_by_module"])

    def test_nov27_thanksgiving_previous_session_and_early_close(self):
        self.assertEqual(previous_weekday(date(2026, 11, 27)), date(2026, 11, 26))
        result = audit_calendar_assumptions("2026-11-27", evidence(
            "2026-11-27", "2026-11-25", "2026-11-27T13:00:00-05:00"))
        self.assertIn("FROZEN_PREVIOUS_WEEKDAY_DIFFERS_FROM_EXCHANGE_SESSION", result["issues"])
        self.assertIn("FROZEN_1600_ET_CLOSE_NOT_APPLICABLE", result["issues"])

    def test_dec28_after_christmas_holiday_is_full_session_but_prior_mismatch(self):
        self.assertEqual(previous_weekday(date(2026, 12, 28)), date(2026, 12, 25))
        result = audit_calendar_assumptions("2026-12-28", evidence(
            "2026-12-28", "2026-12-24", "2026-12-28T16:00:00-05:00"))
        self.assertEqual(result["issues"], ["FROZEN_PREVIOUS_WEEKDAY_DIFFERS_FROM_EXCHANGE_SESSION"])

    def test_missing_calendar_evidence_fails_closed(self):
        result = audit_calendar_assumptions("2026-10-27", None)
        self.assertEqual(result["status"], "SHADOW_CALENDAR_BLOCKED")
        self.assertIn("EXCHANGE_CALENDAR_PROVENANCE_UNVERIFIED", result["issues"])

    def test_market_holiday_not_promoted_to_regular_session(self):
        result = audit_calendar_assumptions("2026-11-26", evidence(
            "2026-11-26", "2026-11-25", "2026-11-26T16:00:00-05:00",
            session_open=False))
        self.assertIn("SESSION_NOT_CONFIRMED_OPEN", result["issues"])

    def test_unverified_source_and_naive_close_are_blocked(self):
        result = audit_calendar_assumptions("2026-10-27", evidence(
            "2026-10-27", "2026-10-26", "2026-10-27T16:00:00",
            source_url="https://untrusted.example/calendar", independently_checked=False))
        self.assertIn("EXCHANGE_CALENDAR_PROVENANCE_UNVERIFIED", result["issues"])
        self.assertIn("SESSION_CLOSE_EVIDENCE_MISSING", result["issues"])


if __name__ == "__main__":
    unittest.main()
