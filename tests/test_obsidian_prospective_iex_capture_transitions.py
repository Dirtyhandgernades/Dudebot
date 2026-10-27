"""Offline, immutable cross-capture IEX provenance tests; no provider calls."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_iex_research_discovery import collect, persist
from backtest.obsidian_iex_capture_transitions import compare

MORNING = datetime(2026,10,27,13,50,tzinfo=timezone.utc)
INTRADAY = datetime(2026,10,27,17,43,tzinfo=timezone.utc)


def snap(price, at, prior=10):
    return {"latestTrade":{"p":price,"t":at},
            "prevDailyBar":{"c":prior,"t":"2026-10-26T04:00:00Z"}}


class Fake:
    def __init__(self, prices, clock):
        self.prices = prices
        self.clock = clock
    def assets(self):
        return [{"symbol":s,"exchange":"NASDAQ","status":"active",
                 "id":"ID-"+s} for s in self.prices]
    def snapshots(self, symbols):
        return {s:self.prices[s] for s in symbols}


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.a = self.base/"morning"
        self.b = self.base/"intraday"

    def make(self, morning, later):
        persist(*collect(Fake(morning, MORNING),clock=lambda:MORNING),self.a)
        persist(*collect(Fake(later, INTRADAY),clock=lambda:INTRADAY),self.b)
        return compare(self.a,self.b)

    def test_new_real_crossing_vs_stale_recovery(self):
        first={
            "AAAA":snap(9.85,"2026-10-27T13:49:00Z"),
            "BBBB":snap(9.0,"2026-10-27T13:49:00Z"),
            "CCCC":snap(9.0,"2026-10-27T13:01:00Z"),
            "DDDD":snap(8.9,"2026-10-27T13:49:00Z"),
            "EEEE":snap(10.0,"2026-10-27T13:49:00Z"),
        }
        second={
            "AAAA":snap(9.1,"2026-10-27T17:42:00Z"),
            "BBBB":snap(8.8,"2026-10-27T17:42:00Z"),
            "CCCC":snap(9.0,"2026-10-27T17:42:00Z"),
            "DDDD":snap(10.0,"2026-10-27T17:42:00Z"),
            "EEEE":snap(9.9,"2026-10-27T17:42:00Z"),
        }
        r=self.make(first,second)
        c=r["counts"]
        self.assertEqual(c["morning_watches"],2)
        self.assertEqual(c["intraday_watches"],3)
        self.assertEqual(c["persistent_watches"],1)
        self.assertEqual(c["new_watch_labels"],2)
        self.assertEqual(c["new_comparable_crossings"],1)
        self.assertEqual(c["newly_visible_after_unusable"],1)
        self.assertEqual(c["dropped_watch_labels"],1)
        self.assertEqual(c["union_symbols"],5)
        self.assertFalse(r["prospective_20pct_collapse_predictions_proven"])
        self.assertIsNone(r["conditional_recall"])
        self.assertTrue(all(not row["smg_executable"] for row in r["full_unselected_union_ledger"]))

    def test_prior_reference_drift_cannot_be_called_new_onset(self):
        r=self.make({"AAAA":snap(9.85,"2026-10-27T13:49:00Z",10)},
                    {"AAAA":snap(9.0,"2026-10-27T17:42:00Z",11)})
        self.assertEqual(r["counts"]["previous_iex_reference_changed"],1)
        self.assertEqual(r["counts"].get("new_comparable_crossings",0),0)
        self.assertEqual(r["full_unselected_union_ledger"][0]["transition"],
                         "PRIOR_IEX_REFERENCE_CHANGED_NOT_COMPARABLE")

    def test_added_symbol_not_retroactive_discovery(self):
        r=self.make({"AAAA":snap(10.0,"2026-10-27T13:49:00Z")},
                    {"AAAA":snap(10.0,"2026-10-27T17:42:00Z"),
                     "BBBB":snap(9.0,"2026-10-27T17:42:00Z")})
        self.assertEqual(r["counts"]["added_symbols"],1)
        self.assertEqual(r["counts"].get("new_comparable_crossings",0),0)

    def test_hash_tamper_rejected(self):
        self.make({"AAAA":snap(10,"2026-10-27T13:49:00Z")},
                  {"AAAA":snap(9,"2026-10-27T17:42:00Z")})
        with (self.a/"universe.jsonl").open("ab") as f:
            f.write(b"CORRUPTION")
        with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):
            compare(self.a,self.b)

    def test_wrong_order_rejected(self):
        self.make({"AAAA":snap(10,"2026-10-27T13:49:00Z")},
                  {"AAAA":snap(9,"2026-10-27T17:42:00Z")})
        with self.assertRaisesRegex(ValueError,"INVALID_OR_OVERLAPPING_SAME_SESSION_PHASES"):
            compare(self.b,self.a)


if __name__ == "__main__":
    unittest.main()
