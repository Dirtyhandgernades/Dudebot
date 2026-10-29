"""Offline fake-provider source handling tests; real workflow is separate."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from backtest.obsidian_sip_fallback import replay, persist, verify, digest, POLICY

OBSERVED=datetime(2026,10,28,23,15,tzinfo=timezone.utc)

def fixture(root):
    root.mkdir()
    rows=[{"ticker":s,"asset":{"symbol":s,"exchange":"NASDAQ","status":"active","shortable":False},
           "received_at":"2026-10-28T17:52:34Z","indicative_status":"STALE_OR_FUTURE_IEX_PRINT",
           "snapshot_present":True,
           "snapshot":{"prevDailyBar":{"c":10,"t":"2026-10-27T04:00:00Z"},
                       "latestTrade":{"p":9,"t":"2026-10-28T14:01:00Z"}}}
          for s in ("AAAA","BBBB","CCCC")]
    raw="".join(json.dumps(x,sort_keys=True)+"\n" for x in rows).encode()
    meta={"feed":"iex","trade_authorized":False,"started_at":"2026-10-28T17:52:31Z",
          "finished_at":"2026-10-28T17:52:36Z", "phase":"INTRADAY",
          "universe_sha256":digest(raw),"universe_count":3,
          "status_counts":{"STALE_OR_FUTURE_IEX_PRINT":3}}
    (root/"manifest.json").write_text(json.dumps(meta))
    (root/"universe.jsonl").write_bytes(raw)

class Fake:
    def __init__(self, error=None, paginate=False):
        self.error=error
        self.paginate=paginate
        self.queries=[]
    def bars(self, symbols, start, end, token=None):
        self.queries.append((symbols,start,end,token))
        if self.error=="auth":
            raise RuntimeError("SIP_PROVIDER_HTTP_403")
        if self.error=="ticker":
            return {"bars":{"UNREQUESTED":[{"t":"2026-10-28T17:34:00Z","c":8}]},"next_page_token":None}
        if self.error=="future":
            return {"bars":{s:[{"t":"2026-10-28T17:52:00Z","c":8}] for s in symbols}}
        if self.error=="invalid":
            return {"bars":{s:[{"t":"2026-10-28T17:34:00Z","c":False}] for s in symbols}}
        if self.paginate and not token:
            return {"bars":{symbols[0]:[{"t":"2026-10-28T17:30:00Z","c":8.5}]},
                    "next_page_token":"page2"}
        return {"bars":{s:[{"t":"2026-10-28T17:34:00Z","c":8.1,"v":100}]
                        for s in (symbols[1:] if self.paginate else symbols)},
                "next_page_token":None}

class SIPFallbackTests(unittest.TestCase):
    def setUp(self):
        context=tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        self.root=Path(context.name)
        self.original=self.root/"original"
        fixture(self.original)
        self.clock=lambda:OBSERVED
    def test_actual_asof_and_no_hindsight_promotion(self):
        p=Fake()
        rows,meta=replay(self.original,p,clock=self.clock)
        self.assertEqual(meta["requested_distinct_symbols"],3)
        self.assertEqual(meta["status_counts"],{"HISTORICAL_DELAYED_SIP_BAR_FRESH_AT_ASOF":3})
        self.assertTrue(meta["historical_reconstruction_not_original_point_in_time_capture"])
        self.assertFalse(meta["future_close_predictions_verified"])
        self.assertTrue(all(not r["usable_as_historical_prediction"] and not r["trade_authorized"] for r in rows))
        self.assertAlmostEqual(rows[0]["bar_vs_iex_reference_pct_not_official"],-19.0)
        self.assertLessEqual(p.queries[0][2],datetime(2026,10,28,17,34,36,tzinfo=timezone.utc))
    def test_selection_preserves_full_original(self):
        rows,meta=replay(self.original,Fake(),clock=self.clock,selected_symbols={"BBBB"})
        self.assertEqual(len(rows),3)
        self.assertEqual(meta["not_requested_symbols_retained"],2)
        self.assertEqual(rows[0]["delayed_sip_status"],"NOT_REQUESTED_SEPARATE_SHADOW_SCOPE")
    def test_403_is_data_gap_not_zero_collapse(self):
        _,meta=replay(self.original,Fake(error="auth"),clock=self.clock)
        self.assertEqual(meta["status_counts"],{"SIP_PROVIDER_REQUEST_FAILED":3})
        self.assertEqual(meta["requests"][0]["error"],"SIP_PROVIDER_HTTP_403")
    def test_future_bar_rejected(self):
        _,meta=replay(self.original,Fake(error="future"),clock=self.clock)
        self.assertEqual(meta["status_counts"],{"OUT_OF_WINDOW_OR_INVALID_SIP_BAR":3})
    def test_malformed_bar_rejected(self):
        _,meta=replay(self.original,Fake(error="invalid"),clock=self.clock)
        self.assertEqual(meta["status_counts"],{"OUT_OF_WINDOW_OR_INVALID_SIP_BAR":3})
    def test_unrequested_symbol_rejected(self):
        _,meta=replay(self.original,Fake(error="ticker"),clock=self.clock)
        self.assertEqual(meta["status_counts"],{"SIP_PROVIDER_REQUEST_FAILED":3})
    def test_pagination(self):
        rows,meta=replay(self.original,Fake(paginate=True),clock=self.clock)
        self.assertEqual(meta["requests"][0]["pages"],2)
        self.assertEqual(sum(bool(r["delayed_sip_bar"]) for r in rows),3)
    def test_embargo_enforced(self):
        with self.assertRaisesRegex(ValueError,"HISTORICAL_SIP_EMBARGO_NOT_ELAPSED"):
            replay(self.original,Fake(),clock=lambda:datetime(2026,10,28,17,53,tzinfo=timezone.utc))
    def test_source_hash_checked(self):
        with (self.original/"universe.jsonl").open("ab") as f:
            f.write(b"CORRUPTION")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_RAW_SHA"):
            replay(self.original,Fake(),clock=self.clock)
    def test_unseen_selection_rejected(self):
        with self.assertRaisesRegex(ValueError,"SELECTION_OUTSIDE_ORIGINAL"):
            replay(self.original,Fake(),clock=self.clock,selected_symbols=["JDZG"])
    def test_write_once_and_hash(self):
        rows,meta=replay(self.original,Fake(),clock=self.clock)
        path=self.root/"result"
        persist(rows,meta,path)
        self.assertEqual(verify(path)["rows"],3)
        with self.assertRaises(FileExistsError):
            persist(rows,meta,path)
        with (path/"rescue.jsonl").open("ab") as f:
            f.write(b"CORRUPTION")
        with self.assertRaisesRegex(ValueError,"SIP_REPLAY_SHA"):
            verify(path)
    def test_policy_frozen(self):
        _,meta=replay(self.original,Fake(),clock=self.clock)
        self.assertEqual(meta["policy"],POLICY)
        self.assertFalse(meta["actual_smg_short_eligibility_verified"])

if __name__=="__main__":
    unittest.main()
