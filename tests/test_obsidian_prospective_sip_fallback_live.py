"""Future read-only delayed SIP must capture real wall time, never backfill."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from backtest.obsidian_sip_fallback import replay,digest,verify,persist

NOW=datetime(2026,10,28,19,20,tzinfo=timezone.utc) # Oct 28, 14:20 CT

class Provider:
    def bars(self,symbols,start,end,token=None):
        return {"bars":{s:[{"t":"2026-10-28T19:01:00Z",
                            "c":8.2 if s=="AAAA" else 6.8}]
                        for s in symbols},"next_page_token":None}

class FutureTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.path=Path(d.name)
        original=self.path/"original"
        original.mkdir()
        rows=[{"ticker":s,"asset":{"symbol":s,"exchange":"NASDAQ","status":"active"},
               "received_at":"2026-10-28T17:52:34Z",
               "indicative_status":"STALE_OR_FUTURE_IEX_PRINT",
               "snapshot":{"prevDailyBar":{"c":10,"t":"2026-10-27T04:00:00Z"}}}
              for s in ("AAAA","BBBB")]
        raw="".join(json.dumps(r,sort_keys=True)+"\n" for r in rows).encode()
        (original/"universe.jsonl").write_bytes(raw)
        (original/"manifest.json").write_text(json.dumps({
            "feed":"iex","phase":"INTRADAY","trade_authorized":False,
            "started_at":"2026-10-28T17:52:31Z",
            "finished_at":"2026-10-28T17:52:36Z",
            "universe_sha256":digest(raw),"universe_count":2,
            "status_counts":{"STALE_OR_FUTURE_IEX_PRINT":2}}))
        self.original=original
    def test_actual_future_checkpoint_and_censored_early_watches(self):
        rows,meta=replay(self.original,Provider(),clock=lambda:NOW,prospective=True)
        self.assertTrue(meta["prospective_delayed_sip_checkpoint"])
        self.assertFalse(meta["historical_reconstruction_not_original_point_in_time_capture"])
        self.assertEqual(meta["prospective_research_capture_asof"],"2026-10-28T19:20:00Z")
        self.assertEqual(meta["eligible_historical_end_at"],"2026-10-28T19:03:00Z")
        self.assertEqual(rows[0]["prospective_delayed_sip_lane"],"DELAYED_SIP_INTERMEDIATE_PRICE_ONLY_WATCH")
        self.assertEqual(rows[1]["prospective_delayed_sip_lane"],"DELAYED_SIP_EXHAUSTED_NOT_EARLY")
        self.assertTrue(all(not x["trade_authorized"] for x in rows))
        dest=self.path/"report"
        persist(rows,meta,dest)
        self.assertEqual(verify(dest)["rows"],2)
    def test_outside_1420_or_different_day_rejected(self):
        for t in (datetime(2026,10,28,19,10,tzinfo=timezone.utc),
                  datetime(2026,10,28,19,31,tzinfo=timezone.utc),
                  datetime(2026,10,29,19,20,tzinfo=timezone.utc)):
            with self.assertRaisesRegex(ValueError,"PROSPECTIVE_SHADOW_OUTSIDE"):
                replay(self.original,Provider(),clock=lambda t=t:t,prospective=True)
    def test_replayed_yesterday_is_never_automatically_forward(self):
        _,meta=replay(self.original,Provider(),clock=lambda:NOW,prospective=False)
        self.assertTrue(meta["historical_reconstruction_not_original_point_in_time_capture"])
        self.assertFalse(meta["prospective_delayed_sip_checkpoint"])

if __name__=="__main__":
    unittest.main()
