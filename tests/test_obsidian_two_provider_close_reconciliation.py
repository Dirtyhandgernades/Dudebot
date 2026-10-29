import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from backtest import obsidian_two_provider_close_reconciliation as module

class ReconciliationBudgetTests(unittest.TestCase):
    def test_bounded_requests_and_exact_date_matching(self):
        calls=[]
        def fake_get(url,params,token):
            calls.append((url,dict(params)))
            if "twelvedata" in url:
                return {"http_status":200,"body_sha256":"a",
                        "payload":{"status":"ok","values":[
                            {"datetime":"2026-10-28","close":"100.00"},
                            {"datetime":"2026-10-27","close":"101.00"},
                            {"datetime":"2026-10-26","close":"999.00"}]}}
            day=url.rsplit("/",1)[-1]
            return {"http_status":200,"body_sha256":"b",
                    "payload":{"status":"OK","close":100.0 if day=="2026-10-28" else 101.0}}
        with tempfile.TemporaryDirectory() as d,patch.object(module,"get",side_effect=fake_get),patch.object(module,"OUT",Path(d)/"result.json"),patch.dict("os.environ",{"MASSIVE_API_KEY":"fake","TWELVE_DATA_API_KEY":"fake"}):
            module.main()
            result=json.loads((Path(d)/"result.json").read_text())
        self.assertEqual(sum("twelvedata" in x[0] for x in calls),2)
        self.assertEqual(sum("massive" in x[0] for x in calls),4)
        self.assertEqual(result["both_bar_count"],4)
        self.assertEqual(result["matching_bar_count"],4)
        self.assertFalse(result["outcome_scoring_eligible"])
        self.assertFalse(result["official_exchange_close_verified"])
    def test_missing_vendor_sessions_are_censored(self):
        def fake_get(url,params,token):
            if "twelvedata" in url:
                return {"http_status":200,"body_sha256":"a","payload":{"status":"ok","values":[]}}
            return {"http_status":429,"body_sha256":"b","payload":{"status":"ERROR"}}
        with tempfile.TemporaryDirectory() as d,patch.object(module,"get",side_effect=fake_get),patch.object(module,"OUT",Path(d)/"result.json"),patch.dict("os.environ",{"MASSIVE_API_KEY":"fake","TWELVE_DATA_API_KEY":"fake"}):
            module.main()
            result=json.loads((Path(d)/"result.json").read_text())
        self.assertEqual(result["missing_pair_count"],4)
        self.assertEqual(result["both_bar_count"],0)
        self.assertEqual(result["matching_bar_count"],0)
        self.assertTrue(all(not row["eligible_official_close"] for row in result["rows"]))
if __name__=="__main__": unittest.main()
