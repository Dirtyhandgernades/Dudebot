"""Regression tests: after-hours ranking disagreement is NOT a trade signal."""
import unittest
from datetime import datetime, timedelta, timezone
from backtest.obsidian_extended_quote_integrity import reconcile_extended_quote as check

T = datetime(2026, 10, 26, 21, 19, tzinfo=timezone.utc)

def quote(source, price, age=0):
    return {"source_id":source,"price":price,"observed_at":T-timedelta(minutes=age)}

class ExtendedQuoteIntegrityTests(unittest.TestCase):
    def test_itgr_ranked_24pct_drop_conflicts_with_individual_quote(self):
        r=check(symbol="ITGR", observed_at=T, ranked_close=126.52,
                ranked_extended=95.56, individual_close=126.52,
                individual_extended=126.00, individual_quote_at=T-timedelta(minutes=23))
        self.assertIn("NON_SYNCHRONOUS_EXTENDED_QUOTE_DIVERGENCE",r["issues"])
        self.assertIn("EXTREME_RANKED_DROP_UNCORROBORATED",r["issues"])
        self.assertIn("INDIVIDUAL_QUOTE_STALE",r["issues"])
        self.assertEqual(r["trade_status"],"NOT_VERIFIED_EXECUTABLE")
        self.assertEqual(r["hypothetical_profit"],None)
    def test_two_pages_same_vendor_not_independent(self):
        r=check(symbol="X",observed_at=T,ranked_close=10,ranked_extended=7,
                individual_close=10,individual_extended=7,individual_quote_at=T,
                independent_quotes=[quote("same_vendor",7),quote("same_vendor",7)],
                corporate_action_clear=True)
        self.assertIn("NO_TWO_INDEPENDENT_FRESH_SOURCES",r["issues"])
    def test_two_distinct_fresh_sources_corrob_when_other_checks_pass(self):
        r=check(symbol="X",observed_at=T,ranked_close=10,ranked_extended=9.8,
                individual_close=10,individual_extended=9.8,individual_quote_at=T,
                independent_quotes=[quote("sip_provider_a",9.80),quote("provider_b",9.81)],
                corporate_action_clear=True)
        self.assertEqual(r["issues"],[])
        self.assertEqual(r["quote_quality"],"CROSS_SOURCE_CORROBORATED_RESEARCH_ONLY")
        self.assertEqual(r["trade_status"],"NOT_VERIFIED_EXECUTABLE")
    def test_cross_source_disagreement_blocks(self):
        r=check(symbol="X",observed_at=T,ranked_close=10,ranked_extended=9.8,
                individual_close=10,individual_extended=9.8,individual_quote_at=T,
                independent_quotes=[quote("a",9.8),quote("b",8.5)],corporate_action_clear=True)
        self.assertIn("INDEPENDENT_SOURCES_DISAGREE",r["issues"])
    def test_corporate_action_uncleared_blocks(self):
        r=check(symbol="LHSW",observed_at=T,ranked_close=4.8,ranked_extended=3.91,
                individual_close=4.8,individual_extended=3.91,individual_quote_at=T,
                independent_quotes=[quote("a",3.91),quote("b",3.92)])
        self.assertIn("CORPORATE_ACTION_NOT_INDEPENDENTLY_CLEARED",r["issues"])
    def test_future_individual_quote_is_not_asof(self):
        r=check(symbol="X",observed_at=T,ranked_close=10,ranked_extended=9,
                individual_close=10,individual_extended=9,individual_quote_at=T+timedelta(seconds=1),
                independent_quotes=[quote("a",9),quote("b",9)],corporate_action_clear=True)
        self.assertIn("INDIVIDUAL_QUOTE_TIME_UNVERIFIED",r["issues"])
    def test_stale_independent_quotes_are_excluded(self):
        r=check(symbol="X",observed_at=T,ranked_close=10,ranked_extended=8,
                individual_close=10,individual_extended=8,individual_quote_at=T,
                independent_quotes=[quote("a",8,16),quote("b",8)],corporate_action_clear=True)
        self.assertIn("NO_TWO_INDEPENDENT_FRESH_SOURCES",r["issues"])
        self.assertIn("EXTREME_RANKED_DROP_UNCORROBORATED",r["issues"])
    def test_bad_numbers_not_used(self):
        r=check(symbol="X",observed_at=T,ranked_close=None,ranked_extended=float("nan"),
                individual_close=10,individual_extended=9,individual_quote_at=T)
        self.assertIsNone(r["ranked_move_pct"])
        self.assertIn("RANKED_PRICE_MISSING",r["issues"])
    def test_naive_observation_rejected(self):
        with self.assertRaises(ValueError):
            check(symbol="X",observed_at=datetime(2026,10,26,16,19))
    def test_independent_quote_must_have_provenance(self):
        with self.assertRaises(ValueError):
            check(symbol="X",observed_at=T,independent_quotes=[{"source_id":"","price":10,"observed_at":T}])
if __name__=="__main__": unittest.main()
