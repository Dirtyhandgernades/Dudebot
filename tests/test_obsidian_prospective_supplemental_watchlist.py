"""Supplemental historical-watch retention must not fabricate past screens."""
import json
import unittest
from pathlib import Path
from backtest.obsidian_watchlist_reconcile import reconcile
BASE=Path(__file__).resolve().parents[1]/"backtest"
class SupplementalManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((BASE/"obsidian_historical_watchlist_manifest_2026_10_26.json").read_text())
        cls.supp=json.loads((BASE/"obsidian_supplemental_watchlist_2026_10_26.json").read_text())
        cls.a=[r["ticker"] for r in cls.base["records"]]
        cls.b=[r["ticker"] for r in cls.supp["records"]]
    def test_no_duplicate_across_sources(self):
        self.assertEqual(len(self.a)+len(self.b),len(set(self.a+self.b)))
    def test_missing_historical_examples_retained(self):
        self.assertTrue({"AIOK","XRPN","WFF","SDEV","AVTX","TTMI","AIFA","RZAI"}.issubset(set(self.b)))
    def test_new_afterhours_discovery_not_pretended_prior_watch(self):
        apxc=next(r for r in self.supp["records"] if r["ticker"]=="APXC")
        self.assertEqual(apxc["source"],"2026_10_26_AFTERHOURS_NEW_DISCOVERY")
        self.assertIsNone(apxc["verified_preclose_signal_at"])
    def test_all_unknown_eligibility_and_no_invented_holdings(self):
        self.assertTrue(all(r["retained"] and not r["confirmed_holding"] and
                            r["verified_preclose_signal_at"] is None for r in self.supp["records"]))
    def test_union_reconciles_as_unscreened(self):
        out=reconcile(self.a+self.b,[])
        self.assertEqual(len(out),len(self.a)+len(self.b))
        self.assertTrue(all(r["status"]=="NOT_SCREENED" for r in out))
if __name__=="__main__": unittest.main()
