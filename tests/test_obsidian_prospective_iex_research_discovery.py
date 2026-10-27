"""No-network verification for isolated IEX research discovery."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backtest.obsidian_iex_research_discovery import (
    phase_at, indicative, collect, persist, verify, build_attention_packet
)

AT = datetime(2026, 10, 27, 13, 50, tzinfo=timezone.utc) # Tuesday 08:50 CT


def snap(price, trade_time="2026-10-27T13:49:00Z", prior=10):
    return {"latestTrade": {"p": price, "t": trade_time},
            "prevDailyBar": {"c": prior, "t": "2026-10-26T19:59:00Z"}}


class Fake:
    def __init__(self, row=None):
        self.data = row if row is not None else {
            "AAAA": snap(9.1), "BBBB": snap(7.7), "CCCC": snap(4.9),
            "DDDD": None, "EEEE": snap(10.1),
        }
    def assets(self):
        return [{"symbol": t, "exchange":"NASDAQ", "status":"active"}
                for t in self.data]
    def snapshots(self, symbols):
        return {t:self.data[t] for t in symbols if t in self.data}


class DiscoveryTests(unittest.TestCase):
    def test_phase_masks_preclose_without_mutating_old_gate(self):
        self.assertEqual(phase_at(AT), "MORNING")
        self.assertEqual(phase_at(datetime(2026,10,27,19,50,tzinfo=timezone.utc)),
                         "RESERVED_FOR_PROSPECTIVE_EOD_CAPTURE")
        self.assertEqual(phase_at(datetime(2026,10,27,21,22,tzinfo=timezone.utc)),
                         "AFTERHOURS")

    def test_naive_time_fails_closed(self):
        self.assertEqual(phase_at(datetime(2026,10,27,13,50)), "INVALID_CLOCK")
        with self.assertRaisesRegex(ValueError, "OUTSIDE_RESEARCH_DISCOVERY_WINDOW"):
            collect(Fake(),clock=lambda: datetime(2026,10,27,13,50))

    def test_multiband_and_unknown_retained(self):
        rows, report = collect(Fake(),clock=lambda: AT)
        self.assertEqual(len(rows),5)
        self.assertEqual(report["universe_count"],5)
        statuses={r["ticker"]:r["indicative_status"] for r in rows}
        self.assertEqual(statuses["AAAA"],"IEX_INDICATIVE_EARLY_2_TO_15")
        self.assertEqual(statuses["BBBB"],"IEX_INDICATIVE_INTERMEDIATE_15_TO_25")
        self.assertEqual(statuses["CCCC"],"IEX_INDICATIVE_EXHAUSTED")
        self.assertEqual(statuses["DDDD"],"MISSING_IEX_SNAPSHOT")
        self.assertEqual(statuses["EEEE"],"IEX_INDICATIVE_OTHER")
        self.assertFalse(report["previous_reference_is_official_close"])

    def test_precose_capture_gate_cannot_be_bypassed(self):
        with self.assertRaisesRegex(ValueError,"RESERVED_FOR_PROSPECTIVE_EOD_CAPTURE"):
            collect(Fake(), clock=lambda: datetime(2026,10,27,19,50,tzinfo=timezone.utc))

    def test_stale_and_future_quotes_quarantined(self):
        self.assertEqual(indicative(snap(9,"2026-10-27T13:01:00Z"),AT)[0],
                         "STALE_OR_FUTURE_IEX_PRINT")
        self.assertEqual(indicative(snap(9,"2026-10-27T13:51:00Z"),AT)[0],
                         "STALE_OR_FUTURE_IEX_PRINT")

    def test_absent_symbol_preserved(self):
        p=Fake()
        p.snapshots=lambda symbols:{"AAAA":snap(9.1)}
        rows, report=collect(p, clock=lambda: AT)
        self.assertEqual(report["status_counts"]["MISSING_IEX_SNAPSHOT"],4)

    def test_unknown_symbol_cannot_inject_into_capture(self):
        p=Fake()
        p.snapshots=lambda symbols:{"ZZZZ":snap(9.1)}
        with self.assertRaisesRegex(ValueError,"INVALID_IEX_SNAPSHOT_SYMBOLS"):
            collect(p,clock=lambda:AT)

    def test_packet_has_no_fake_eligible_prior_close(self):
        rows,report=collect(Fake(),clock=lambda:AT)
        x=build_attention_packet(rows,report,[{"ticker":"CPIX"}],[],[])
        self.assertEqual(x["snapshots_preserved"],len(rows))
        self.assertEqual(x["authenticated_provider_symbols_requested"],len(rows))
        self.assertEqual(x["coverage"]["authenticated_screen_evidence_symbols"],len(rows))
        self.assertTrue(x["requested_is_not_usable_or_eligible"])
        self.assertFalse(x["separately_verified_prior_close"])
        self.assertFalse(x["full_market_denominator_verified"])
        self.assertFalse(x["early_catch_or_edge_demonstrated"])
        self.assertEqual(len(x["single_venue_indicative_attention"]),2)
        self.assertTrue(all(y["lane"]=="QUOTE_OR_PRIOR_CLOSE_UNVERIFIED"
                            for y in x["research_priorities_not_orders"]))

    def test_write_once_and_verify_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"scan"
            rows,manifest=collect(Fake(),clock=lambda:AT)
            persist(rows,manifest,target)
            self.assertEqual(verify(target)["universe_count"],5)
            with self.assertRaises(FileExistsError):
                persist(rows,manifest,target)
            with (target/"universe.jsonl").open("ab") as f:
                f.write(b"CORRUPTION")
            with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):
                verify(target)

    def test_paper_assets_not_smg_borrow(self):
        rows,manifest=collect(Fake(),clock=lambda:AT)
        self.assertFalse(manifest["smg_eligibility_confirmed"])
        self.assertIsNone(rows[0]["platform_short_available"])
        self.assertFalse(rows[0]["trade_authorized"])

    def test_wrong_prior_session_is_not_certified(self):
        data=snap(9.1)
        data["prevDailyBar"]["t"]="2026-10-23T19:59:00Z"
        self.assertEqual(indicative(data,AT)[0],"UNVERIFIED_PREVIOUS_IEX_DAY")


if __name__=="__main__":
    unittest.main()
