import unittest
from backtest.obsidian_watchlist_reconcile import reconcile
class WatchlistTests(unittest.TestCase):
    def test_unscreened_not_mislabeled_rejected(self):
        r=reconcile(["AEHL","SVRN"],[{"ticker":"AEHL","status":"SCREENED_REJECTED","reason":"PRICE"}])
        self.assertEqual([x["status"] for x in r],["SCREENED_REJECTED","NOT_SCREENED"])
        self.assertTrue(all(x["retain_structural_watch"] for x in r))
    def test_missing_bars_preserved(self):
        r=reconcile(["RGC"],[{"ticker":"RGC","status":"MISSING_DATA","reason":"CURRENT_PRICE_WINDOW_UNAVAILABLE"}])
        self.assertEqual(r[0]["status"],"MISSING_DATA")
    def test_rename_requires_explicit_mapping(self):
        r=reconcile(["SWIN"],[{"ticker":"AXG","status":"SCREENED_WATCH"}],{"SWIN":"AXG"})
        self.assertEqual(r[0]["screen_ticker"],"AXG")
        self.assertEqual(r[0]["status"],"SCREENED_WATCH")
    def test_unseen_rename_does_not_claim_screen(self):
        r=reconcile(["BREA"],[],{"BREA":"SLMT"})
        self.assertEqual(r[0]["status"],"RENAMED")
        self.assertIn("NOT_SCREENED",r[0]["reason"])
    def test_no_silent_deduplication(self):
        r=reconcile(["AEHL","AEHL","SECZ"],[])
        self.assertEqual(len(r),2)
    def test_duplicate_scan_is_error(self):
        with self.assertRaises(ValueError):
            reconcile(["AEHL"],[{"ticker":"AEHL","status":"MISSING_DATA"},{"ticker":"AEHL","status":"SCREENED_WATCH"}])
    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            reconcile(["AEHL"],[{"ticker":"AEHL","status":"ENTER"}])
if __name__=="__main__": unittest.main()
