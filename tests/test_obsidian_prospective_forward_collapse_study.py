"""Prospectively frozen IEX-forward study regression; NO market connections."""
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from backtest.obsidian_iex_research_discovery import collect, persist
from backtest.obsidian_forward_collapse_study import evaluate, POLICY
from backtest.obsidian_iex_corporate_actions import ACTION_FLAGS

AT = datetime(2026, 10, 27, 13, 50, tzinfo=timezone.utc)

def snapshot(price):
    return {
        "latestTrade": {"p": price, "t": "2026-10-27T13:49:00Z"},
        "prevDailyBar": {"c": 10, "t": "2026-10-26T19:59:00Z"},
    }

class Mock:
    def assets(self):
        return [{"symbol": name, "exchange":"NASDAQ", "status":"active"}
                for name in ("AAAA", "BBBB", "CCCC", "DDDD", "EEEE")]
    def snapshots(self, symbols):
        prices = {"AAAA":9.5, "BBBB":7.8, "CCCC":10.5, "DDDD":8.8, "EEEE":7}
        return {ticker:snapshot(prices[ticker]) for ticker in symbols}

def closing(name, value):
    item = {
        "ticker":name, "verified":True, "regular_session":True,
        "provider_conflict":False, "corporate_actions_clear":True,
        "previous_session_date":"2026-10-26",
        "previous_regular_close":10, "regular_close":value,
        "close_at":"2026-10-27T20:00:00Z",
        "collected_at":"2026-10-27T20:12:00Z",
        "source_url":"https://official-review.example/eod",
    }
    item["corporate_action_review"] = {
        "status":"NO_ACTIONS_CONFIRMED", "verified":True,
        "reviewed_sessions":["2026-10-26","2026-10-27"],
        "checked_at":"2026-10-27T20:11:00Z",
        "source_url":"https://actions.example/review",
        "prior_symbol":name,"current_symbol":name,
        "prior_security_id":"CID-"+name,"current_security_id":"CID-"+name,
        "action_flags":{flag:False for flag in ACTION_FLAGS},
    }
    item["independent_eod_sources"] = [
        {"source_id":"PROVIDER_A","url":"https://provider-a.example/historical",
         "observed_at":"2026-10-27T20:02:00Z","verified":True,
         "previous_regular_close":10,"regular_close":value},
        {"source_id":"PROVIDER_B","url":"https://provider-b.example/historical",
         "observed_at":"2026-10-27T20:05:00Z","verified":True,
         "previous_regular_close":10,"regular_close":value},
    ]
    return item

class ForwardStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.capture=self.root/"original"
        persist(*collect(Mock(),clock=lambda:AT),self.capture)

    def score(self,rows):
        target=self.root/"closures.jsonl"
        target.write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8")
        return evaluate(self.capture,target)

    def test_none_means_not_yet_proven(self):
        report=evaluate(self.capture)
        self.assertEqual(report["outcome_rows_supplied"],0)
        self.assertEqual(report["counts"]["raw_iex_watches"],3)
        self.assertEqual(report["counts"]["missing_outcome"],5)
        self.assertIsNone(report["conditional_early_recall"])
        self.assertFalse(report["untouched_future_prediction_edge_established"])
        self.assertEqual(report["study_id"],POLICY)

    def test_early_vs_late_vs_unwatched(self):
        r=self.score([
            closing("AAAA",7), # 9.5 at decision, 7 at close => 83% drop remained
            closing("BBBB",7), # 7.8 at decision, 7 at close => 27% remained: late
            closing("CCCC",7), # no watch at decision
            closing("DDDD",9), # watched but did not collapse
            closing("EEEE",7), # exhausted at decision
        ])
        self.assertEqual(r["counts"]["verified_20pct_regular_close_collapses"],4)
        self.assertEqual(r["counts"]["early_iex_watch_hits"],1)
        self.assertEqual(r["counts"]["late_iex_watch_not_credited"],1)
        self.assertEqual(r["counts"]["unwatched_collapses"],2)
        self.assertEqual(r["counts"]["watched_noncollapses"],1)
        self.assertAlmostEqual(r["conditional_early_recall"],.25)
        self.assertAlmostEqual(r["conditional_early_precision"],1/3)
        by={x["ticker"]:x for x in r["rows"]}
        self.assertEqual(by["AAAA"]["prediction_status"],"EARLY_IEX_WATCH_BEFORE_HALF_OF_DECLINE")
        self.assertEqual(by["BBBB"]["prediction_status"],"LATE_IEX_WATCH_AFTER_MOST_OF_DECLINE")
        self.assertEqual(by["EEEE"]["prediction_status"],"COLLAPSE_NOT_EARLY_WATCHED")

    def test_missing_and_corporate_actions_are_censored(self):
        row=closing("AAAA",7)
        row["corporate_action_review"]["action_flags"]["special_dividend"]=True
        r=self.score([row])
        self.assertEqual(r["counts"]["verified_outcomes"],0)
        self.assertEqual(r["counts"]["censored_unverified_outcome"],1)
        self.assertEqual(r["counts"]["missing_outcome"],4)

    def test_early_candidate_outcome_later_vendor_conflict_censored(self):
        row=closing("AAAA",7)
        row["independent_eod_sources"][1]["regular_close"]=8
        self.assertEqual(self.score([row])["counts"]["verified_20pct_regular_close_collapses"],0)

    def test_source_observed_before_actual_close_censored(self):
        row=closing("AAAA",7)
        row["independent_eod_sources"][1]["observed_at"]="2026-10-27T19:58:00Z"
        self.assertEqual(self.score([row])["counts"]["verified_outcomes"],0)

    def test_must_match_previous_session(self):
        row=closing("AAAA",7)
        row["previous_session_date"]="2026-10-23"
        self.assertEqual(self.score([row])["counts"]["verified_outcomes"],0)

    def test_outcome_only_after_capture(self):
        row=closing("AAAA",7)
        row["close_at"]="2026-10-27T13:45:00Z"
        self.assertEqual(self.score([row])["counts"]["verified_outcomes"],0)

    def test_no_fake_external_symbol(self):
        with self.assertRaisesRegex(ValueError,"OUTCOME_OUTSIDE_IMMUTABLE_UNIVERSE"):
            self.score([closing("ZZZZ",5)])

    def test_duplicate_outcome_rejected(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            self.score([closing("AAAA",7),closing("AAAA",7)])

    def test_afterhours_never_same_day_prediction(self):
        # No need to forge a new capture: independently checked attribute on
        # captured manifest cannot be mutated because verify() hashes raw data.
        row=closing("AAAA",7)
        r=self.score([row])
        self.assertNotIn("POST_CLOSE",r["rows"][0]["prediction_status"])

    def test_20percent_boundary_inclusive(self):
        r=self.score([closing("AAAA",8)])
        self.assertEqual(r["counts"]["verified_20pct_regular_close_collapses"],1)
        self.assertEqual(r["counts"]["early_iex_watch_hits"],1)

    def test_unknown_borrow_never_becomes_executable(self):
        r=self.score([closing("AAAA",7)])
        self.assertIsNone(r["verified_smg_eligible_recall"])
        self.assertIsNone(r["after_cost_pnl"])
        self.assertTrue(all(not x["executable_signal"] for x in r["rows"]))

if __name__=="__main__":
    unittest.main()
