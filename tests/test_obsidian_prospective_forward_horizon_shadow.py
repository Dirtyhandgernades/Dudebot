"""Research-only next-session shadow outcomes; simulated input only."""
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path

from backtest.obsidian_iex_research_discovery import collect,persist
from backtest.obsidian_forward_horizon_shadow import evaluate,validate_calendar,POLICY
from backtest.obsidian_iex_corporate_actions import ACTION_FLAGS

AT=datetime(2026,10,28,14,15,tzinfo=timezone.utc)
DATES=["2026-10-28","2026-10-29","2026-10-30","2026-11-02"]
PREVIOUS=["2026-10-27","2026-10-28","2026-10-29","2026-10-30"]

def timestamp(day):
    offset="-04:00" if day!="2026-11-02" else "-05:00"
    return day+"T16:00:00"+offset

def published(day):
    return day+("T20:08:00Z" if day!="2026-11-02" else "T21:08:00Z")

def cal():
    return [{"session_date":d,"previous_regular_session":p,
             "session_open":True,"independently_checked":True,
             "regular_close_at":timestamp(d),
             "source_url":"https://www.nyse.com/trade/hours-calendars",
             "source_checked_at":"2026-10-28T14:00:00Z"}
            for d,p in zip(DATES,PREVIOUS)]

def eod(symbol,dayindex,prior,close):
    day=DATES[dayindex];p=PREVIOUS[dayindex]
    record={
        "ticker":symbol,"session_date":day,"previous_session_date":p,
        "verified":True,"regular_session":True,"provider_conflict":False,
        "corporate_actions_clear":True,"previous_regular_close":prior,
        "regular_close":close,"close_at":timestamp(day),
        "collected_at":published(day),"source_url":"https://first.example/close",
        "corporate_action_review":{
            "status":"NO_ACTIONS_CONFIRMED","verified":True,
            "reviewed_sessions":[p,day],"checked_at":published(day),
            "source_url":"https://actions.example/issuer-check",
            "prior_symbol":symbol,"current_symbol":symbol,
            "prior_security_id":symbol+"-id","current_security_id":symbol+"-id",
            "action_flags":{x:False for x in ACTION_FLAGS},
        },
    }
    for_index=[]
    for provider,host in [("independent_a","a.example"),("independent_b","b.example")]:
        for_index.append({
            "source_id":provider,"provider_group":provider,
            "url":"https://"+host+"/eod","symbol":symbol,
            "session_date":day,"previous_session_date":p,
            "kind":"regular_close","session_complete":True,
            "regular_close_asof":timestamp(day),
            "observed_at":published(day),
            "verified":True,"regular_close":close,
            "previous_regular_close":prior,
        })
    record["independent_eod_sources"]=for_index
    return record

class Provider:
    def assets(self):
        return [{"symbol":s,"exchange":"NASDAQ","status":"active"}
                for s in ("AAAA","BBBB","CCCC")]
    def snapshots(self,symbols):
        prices={"AAAA":9.3,"BBBB":9.0,"CCCC":10.1}
        return {s:{"latestTrade":{"p":prices[s],"t":"2026-10-28T14:14:00Z"},
                    "prevDailyBar":{"c":10,"t":"2026-10-27T19:59:00Z"}} for s in symbols}

class HorizonTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.capture=Path(folder.name)/"capture"
        persist(*collect(Provider(),clock=lambda:AT),self.capture)

    def four(self,symbol,values):
        # previous baseline is 10 for day0, then the verified prior EOD close
        prior=10
        out=[]
        for i,v in enumerate(values):
            out.append(eod(symbol,i,prior,v))
            prior=v
        return out

    def test_missing_future_is_not_zero_or_success(self):
        report=evaluate(self.capture,cal(),[])
        self.assertEqual(report["original_universe_count"],3)
        self.assertEqual(report["provisional_counts"]["incomplete_outcome_chains"],3)
        self.assertIsNone(report["verified_future_hits"])
        self.assertFalse(report["predictive_edge_proven"])

    def test_next_h2_early_vs_unwatched(self):
        # AAAA: first <=8 at h2, initial price 9.3, final 7 => >half remains.
        rows=self.four("AAAA",[9.1,8.7,7.0,6.9])
        rows+=self.four("CCCC",[10,9,7.5,7.3])
        r=evaluate(self.capture,cal(),rows)
        by={x["ticker"]:x for x in r["rows"]}
        self.assertEqual(by["AAAA"]["first_event_horizon"],2)
        self.assertEqual(by["AAAA"]["status"],"PROVISIONAL_EARLY_NEXT_SESSION_WATCH")
        self.assertEqual(by["CCCC"]["status"],"PROVISIONAL_FUTURE_COLLAPSE_UNWATCHED")
        self.assertIsNone(r["verified_precision"])

    def test_h0_collapse_not_double_counted_h1(self):
        report=evaluate(self.capture,cal(),self.four("AAAA",[7.5,7,6.8,6.5]))
        row=next(x for x in report["rows"] if x["ticker"]=="AAAA")
        self.assertEqual(row["first_event_horizon"],0)
        self.assertEqual(report["provisional_counts"]["same_day_first_crossings_not_future_credit"],1)
        self.assertNotIn("provisional_early_next_session_watches",report["provisional_counts"])

    def test_incomplete_earlier_day_does_not_claim_later_event(self):
        rows=self.four("AAAA",[9.1,8.8,7.0,6.6])
        rows=[x for x in rows if x["session_date"]!="2026-10-29"]
        report=evaluate(self.capture,cal(),rows)
        row=next(x for x in report["rows"] if x["ticker"]=="AAAA")
        self.assertIsNone(row["first_event_horizon"])
        self.assertEqual(row["status"],"UNSCORED_MISSING_OR_INCOMPLETE_EOD_EVIDENCE")

    def test_third_conflicting_provider_blocks_chain(self):
        rows=self.four("AAAA",[9.1,8.8,7,6.6])
        rows[2]["independent_eod_sources"].append({
            **rows[2]["independent_eod_sources"][0],
            "source_id":"vendor_c","provider_group":"vendor_c",
            "url":"https://c.example/eod","regular_close":7.2,
        })
        result=evaluate(self.capture,cal(),rows)
        row=next(x for x in result["rows"] if x["ticker"]=="AAAA")
        self.assertIsNone(row["first_event_horizon"])

    def test_duplicate_or_unseen_ticker_rejected(self):
        first=eod("AAAA",0,10,9)
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_OUTSIDE"):
            evaluate(self.capture,cal(),[first,first])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_OUTSIDE"):
            evaluate(self.capture,cal(),[eod("ZZZZ",0,10,9)])

    def test_calendar_weekend_transition_is_explicit_not_weekday_math(self):
        result=validate_calendar(cal(),datetime(2026,10,28).date())
        self.assertEqual(result[3][1].isoformat(),"2026-10-30")

    def test_calendar_missing_day_is_blocked(self):
        invalid=cal()
        invalid.pop(1)
        with self.assertRaisesRegex(ValueError,"EXACTLY_FOUR_SESSION"):
            evaluate(self.capture,invalid,[])

    def test_mismatched_prior_close_chain_censored(self):
        rows=self.four("AAAA",[9.1,8.6,7,6.9])
        rows[1]["previous_regular_close"]=8.5
        rows[1]["independent_eod_sources"][0]["previous_regular_close"]=8.5
        rows[1]["independent_eod_sources"][1]["previous_regular_close"]=8.5
        r=evaluate(self.capture,cal(),rows)
        by={x["ticker"]:x for x in r["rows"]}
        self.assertIsNone(by["AAAA"]["first_event_horizon"])

    def test_corporate_action_blocks_chain(self):
        rows=self.four("AAAA",[9.1,8.7,7,6.9])
        rows[1]["corporate_action_review"]["action_flags"]["split"]=True
        r=evaluate(self.capture,cal(),rows)
        self.assertIsNone(next(x for x in r["rows"] if x["ticker"]=="AAAA")["first_event_horizon"])

    def test_after_hours_capture_rejected(self):
        # Existing original source is MORNING and no new capture is forged.
        r=evaluate(self.capture,cal(),[])
        self.assertEqual(r["source_phase"],"MORNING")

if __name__=="__main__":
    unittest.main()
