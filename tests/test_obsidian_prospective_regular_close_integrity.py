"""Offline EOD outcome verification; no retroactive forecast claims."""
import unittest
from datetime import date, datetime, timedelta, timezone
from backtest.obsidian_regular_close_integrity import audit_regular_close_outcome as check

D = date(2026, 10, 26)
T = datetime(2026, 10, 26, 22, 47, tzinfo=timezone.utc)

def row(provider, close, *, stamp=T, day=D, complete=True, kind="regular_close"):
    return {"provider_id":provider, "close":close, "captured_at":stamp,
            "session_date":day, "session_complete":complete, "kind":kind}

class RegularCloseIntegrityTests(unittest.TestCase):
    def test_eikn_conflicting_sources_not_verified_20pct_winner(self):
        r=check(symbol="EIKN",session_date=D,previous_close=7.26,observed_at=T,
                reports=[row("stockanalysis",5.54),row("stockanalysis",5.48),
                         row("chartexchange",6.06),row("investing",6.59)])
        self.assertEqual(r["classification"],"OUTCOME_UNVERIFIED")
        self.assertIn("INDEPENDENT_CLOSE_SOURCES_DISAGREE",r["issues"])
        self.assertIn("SOURCES_STRADDLE_20PCT_THRESHOLD",r["issues"])
        self.assertEqual(r["independent_provider_count"],3)
        self.assertIsNone(r["hypothetical_profit"])

    def test_same_vendor_two_pages_not_independent(self):
        r=check(symbol="EIKN",session_date=D,previous_close=7.26,observed_at=T,
                reports=[row("same_vendor",5.48),row("same_vendor",5.54)])
        self.assertEqual(r["classification"],"OUTCOME_UNVERIFIED")
        self.assertIn("INSUFFICIENT_INDEPENDENT_COMPLETED_CLOSE_SOURCES",r["issues"])

    def test_two_independent_consistent_extreme_closes(self):
        r=check(symbol="X",session_date=D,previous_close=10,observed_at=T,
                reports=[row("a",7.95),row("b",7.96)])
        self.assertEqual(r["classification"],"VERIFIED_AT_LEAST_20PCT_CLOSE_DROP")
        self.assertEqual(r["preclose_catchability"],"UNPROVEN_NO_PREDECISION_TAPE")

    def test_two_independent_consistent_nonextreme_closes(self):
        r=check(symbol="X",session_date=D,previous_close=10,observed_at=T,
                reports=[row("a",8.10),row("b",8.12)])
        self.assertEqual(r["classification"],"VERIFIED_BELOW_20PCT_CLOSE_DROP")

    def test_preclose_or_incomplete_reports_excluded(self):
        r=check(symbol="X",session_date=D,previous_close=10,observed_at=T,
                reports=[row("a",7,stamp=datetime(2026,10,26,19,47,tzinfo=timezone.utc)),
                         row("b",7,complete=False)])
        self.assertEqual(r["classification"],"OUTCOME_UNVERIFIED")
        self.assertIn("INCOMPLETE_STALE_OR_WRONG_SESSION_REPORT",r["issues"])

    def test_late_future_or_wrong_session_rejected(self):
        r=check(symbol="X",session_date=D,previous_close=10,observed_at=T,
                reports=[row("a",7,stamp=T+timedelta(seconds=1)),
                         row("b",7,day=date(2026,10,23))])
        self.assertEqual(r["classification"],"OUTCOME_UNVERIFIED")

    def test_provider_internal_conflict_fails_closed(self):
        r=check(symbol="X",session_date=D,previous_close=10,observed_at=T,
                reports=[row("a",7),row("a",8),row("b",7.5)])
        self.assertIn("SAME_PROVIDER_CLOSE_CONFLICT",r["issues"])

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            check(symbol="X",session_date=D,previous_close=0,observed_at=T,reports=[])

if __name__=="__main__":
    unittest.main()
