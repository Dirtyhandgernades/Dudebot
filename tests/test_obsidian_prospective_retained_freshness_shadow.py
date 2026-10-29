"""Offline all-retained-ticker freshness queue, no winner-specific rules."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_retained_freshness_shadow import review
from backtest.obsidian_iex_research_discovery import collect, persist

M=datetime(2026,10,28,14,16,32,tzinfo=timezone.utc)
I=datetime(2026,10,28,17,52,34,tzinfo=timezone.utc)

def snap(price, at):
    return {"latestTrade":{"p":price,"t":at},
            "prevDailyBar":{"c":10,"t":"2026-10-27T19:59:00Z"}}

class Fake:
    def __init__(self,phase):
        self.phase=phase
    def assets(self):
        return [{"symbol":s,"exchange":"NASDAQ","status":"active",
                 "shortable":False if s=="STAL" else True,
                 "borrow_status":"hard_to_borrow" if s=="STAL" else "easy"}
                for s in ("STAL","FRES","MISP","BLOC")]
    def snapshots(self,symbols):
        is_m=self.phase=="M"
        d={
            "STAL":snap(9.9,"2026-10-28T12:20:00Z" if is_m else "2026-10-28T15:20:00Z"),
            "FRES":snap(9.0,"2026-10-28T14:15:50Z" if is_m else "2026-10-28T17:51:50Z"),
            "MISP":None,
            "BLOC":snap(2.0,"2026-10-28T14:15:50Z" if is_m else "2026-10-28T17:51:50Z"),
        }
        return {s:d[s] for s in symbols if s!="MISP"}

class RetainedQualityTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.m=Path(d.name)/"morning"
        self.i=Path(d.name)/"intraday"
        persist(*collect(Fake("M"),clock=lambda:M),self.m)
        persist(*collect(Fake("I"),clock=lambda:I),self.i)

    def run_review(self):
        return review(self.m,self.i,[
            {"ticker":"STAL"},{"ticker":"FRES"},{"ticker":"MISP"},
            {"ticker":"BLOC"},{"ticker":"VOID"},{"ticker":"STAL"}])

    def test_deduplicate_and_preserve_missing(self):
        a=self.run_review()
        self.assertEqual(a["retained_unique_symbols"],5)
        self.assertEqual(a["retained_duplicate_inputs"],1)
        self.assertEqual(len(a["rows"]),5)
        self.assertEqual(a["original_capture_denominator"],4)

    def test_persistently_stale_watchlist_queued_earliest_observed(self):
        a={x["ticker"]:x for x in self.run_review()["rows"]}
        s=a["STAL"]
        self.assertEqual(s["status"],"PERSISTENT_DATA_GAP_REQUIRES_FRESH_SECOND_VENUE")
        self.assertEqual(s["first_source_review_no_earlier_than"],M.isoformat())
        self.assertTrue(s["independent_fresh_venue_quote_required"])
        self.assertIs(s["provider_reported_shortable"],False)
        self.assertFalse(s["actual_smg_platform_short_verified"])
        self.assertFalse(s["bearish_prediction_was_made"])

    def test_absent_ticker_not_assumed_delisted_or_seen(self):
        a={x["ticker"]:x for x in self.run_review()["rows"]}
        self.assertEqual(a["VOID"]["status"],"SOURCE_UNIVERSE_ABSENT_BOTH")
        self.assertTrue(a["VOID"]["independent_fresh_venue_quote_required"])

    def test_valid_weakness_is_not_synthetic_collapse_prediction(self):
        a={x["ticker"]:x for x in self.run_review()["rows"]}
        self.assertEqual(a["FRES"]["status"],"ORIGINAL_PRICE_WATCH_NOT_A_TRADE")
        self.assertFalse(a["FRES"]["future_collapse_credit"])
        self.assertFalse(a["FRES"]["trade_authorized"])

    def test_unpriced_retained_name_remains_in_quality_review(self):
        a={x["ticker"]:x for x in self.run_review()["rows"]}
        self.assertEqual(a["MISP"]["status"],"PERSISTENT_DATA_GAP_REQUIRES_FRESH_SECOND_VENUE")

    def test_floor_block_never_becomes_trade(self):
        a={x["ticker"]:x for x in self.run_review()["rows"]}
        self.assertEqual(a["BLOC"]["status"],"BELOW_FLOOR_INDICATIVE_NOT_EXECUTABLE")
        self.assertFalse(a["BLOC"]["trade_authorized"])

    def test_invalid_input_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"RETAINED_WATCHLIST_REQUIRED"):
            review(self.m,self.i,{"ticker":"STAL"})
        with self.assertRaisesRegex(ValueError,"INVALID_RETAINED_TICKER"):
            review(self.m,self.i,[{"ticker":None}])


if __name__=="__main__":
    unittest.main()
