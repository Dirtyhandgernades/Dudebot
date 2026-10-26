"""Fail-closed regression checks for recovered historical watchlist manifest."""
import json
import unittest
from pathlib import Path
from backtest.obsidian_watchlist_reconcile import reconcile

MANIFEST=Path(__file__).resolve().parents[1]/"backtest/obsidian_historical_watchlist_manifest_2026_10_26.json"
EXPLICIT=set("AEHL SVRN RGC JDZG SECZ AVBP CPIX MELI TNGX".split())
class HistoricalManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(MANIFEST.read_text())
        cls.rows=cls.data["records"]
    def test_all_explicit_structural_watches_retained(self):
        self.assertTrue(EXPLICIT.issubset({r["ticker"] for r in self.rows}))
    def test_no_silent_duplicates_or_empty_symbols(self):
        tickers=[r["ticker"] for r in self.rows]
        self.assertEqual(len(tickers),len(set(tickers)))
        self.assertTrue(all(ticker and ticker==ticker.upper() for ticker in tickers))
    def test_unscreened_does_not_imply_rejection(self):
        self.assertEqual(self.data["screened_count"],0)
        self.assertEqual(self.data["unverified_count"],len(self.rows))
        self.assertTrue(all(r["audit_status"]=="NOT_SCREENED" and
                            r["latest_scan_id"] is None and
                            r["structural_watch_retained"] for r in self.rows))
    def test_source_provenance_and_unverified_prices(self):
        self.assertTrue(all(r["source_groups"] for r in self.rows))
        self.assertTrue(all(r["last_verified_price_at"] is None and
                            r["last_verified_eligibility_at"] is None for r in self.rows))
    def test_reconciliation_preserves_every_historical_watch(self):
        reconciled=reconcile([r["ticker"] for r in self.rows],[])
        self.assertEqual(len(reconciled),len(self.rows))
        self.assertTrue(all(r["status"]=="NOT_SCREENED" for r in reconciled))
if __name__=="__main__": unittest.main()
