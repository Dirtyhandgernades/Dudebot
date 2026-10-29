"""Synthetic full-denominator research coverage audit; not market evidence."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_iex_research_discovery import collect, persist
from backtest.obsidian_forward_horizon_coverage_shadow import audit
from backtest.obsidian_iex_corporate_actions import ACTION_FLAGS

AT = datetime(2026, 10, 28, 14, 15, tzinfo=timezone.utc)
DAYS = ["2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02"]
PREVIOUS = ["2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"]


def close_stamp(day):
    return day + ("T16:00:00-05:00" if day.endswith("11-02") else "T16:00:00-04:00")


def publication(day):
    return day + ("T21:08:00Z" if day.endswith("11-02") else "T20:08:00Z")


def calendar():
    return [
        {"session_date": day, "previous_regular_session": prior,
         "session_open": True, "independently_checked": True,
         "regular_close_at": close_stamp(day),
         "source_url": "https://www.nyse.com/trade/hours-calendars",
         "source_checked_at": "2026-10-28T14:00:00Z"}
        for day, prior in zip(DAYS, PREVIOUS)
    ]


def eod(symbol, horizon, prior, close):
    day, previous = DAYS[horizon], PREVIOUS[horizon]
    record = {
        "ticker": symbol, "session_date": day, "previous_session_date": previous,
        "verified": True, "regular_session": True, "provider_conflict": False,
        "corporate_actions_clear": True, "previous_regular_close": prior,
        "regular_close": close, "close_at": close_stamp(day),
        "collected_at": publication(day), "source_url": "https://first.example/close",
        "corporate_action_review": {
            "status": "NO_ACTIONS_CONFIRMED", "verified": True,
            "reviewed_sessions": [previous, day], "checked_at": publication(day),
            "source_url": "https://actions.example/issuer-check",
            "prior_symbol": symbol, "current_symbol": symbol,
            "prior_security_id": symbol + "-id",
            "current_security_id": symbol + "-id",
            "action_flags": {flag: False for flag in ACTION_FLAGS},
        },
    }
    record["independent_eod_sources"] = [
        {"source_id": group, "provider_group": group,
         "url": "https://" + host + "/eod", "symbol": symbol,
         "session_date": day, "previous_session_date": previous,
         "kind": "regular_close", "session_complete": True,
         "regular_close_asof": close_stamp(day),
         "observed_at": publication(day), "verified": True,
         "regular_close": close, "previous_regular_close": prior}
        for group, host in [("independent_a", "a.example"),
                            ("independent_b", "b.example")]
    ]
    return record


class Provider:
    def assets(self):
        return [{"symbol": symbol, "exchange": "NASDAQ", "status": "active"}
                for symbol in ("AAAA", "BBBB", "CCCC")]

    def snapshots(self, symbols):
        prices = {"AAAA": 9.3, "BBBB": 9.0, "CCCC": 10.1}
        return {
            symbol: {
                "latestTrade": {"p": prices[symbol], "t": "2026-10-28T14:14:00Z"},
                "prevDailyBar": {"c": 10, "t": "2026-10-27T19:59:00Z"},
            } for symbol in symbols
        }


class CoverageTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.capture = Path(folder.name) / "capture"
        persist(*collect(Provider(), clock=lambda: AT), self.capture)

    def four(self, ticker, values):
        prior = 10
        rows = []
        for index, close in enumerate(values):
            rows.append(eod(ticker, index, prior, close))
            prior = close
        return rows

    def test_every_original_symbol_has_four_slots_even_with_no_outcomes(self):
        report = audit(self.capture, calendar(), [])
        self.assertEqual(report["original_universe_count"], 3)
        self.assertEqual(report["total_expected_symbol_session_slots"], 12)
        self.assertEqual([x["missing_source_row"] for x in report["per_horizon"]], [3]*4)
        self.assertEqual(len(report["rows"]), 3)
        self.assertTrue(all(len(x["horizons"]) == 4 for x in report["rows"]))
        self.assertIsNone(report["verified_hits"])

    def test_missing_earlier_day_does_not_hide_later_missingness(self):
        rows = self.four("AAAA", [9.5, 9.1, 8.8, 7.2])
        rows = [x for x in rows if x["session_date"] in (DAYS[1], DAYS[3])]
        report = audit(self.capture, calendar(), rows)
        self.assertEqual([x["missing_source_row"] for x in report["per_horizon"]], [3, 2, 3, 2])
        self.assertEqual(report["per_horizon"][1]["structurally_consistent_source_row"], 1)
        row = next(x for x in report["rows"] if x["ticker"] == "AAAA")
        self.assertEqual(row["horizons"][1]["chain_evidence"], "PRIOR_HORIZON_CENSORED")
        self.assertEqual(row["horizons"][3]["chain_evidence"], "PRIOR_HORIZON_CENSORED")

    def test_all_synthetic_rows_still_censored_and_never_success(self):
        report = audit(self.capture, calendar(), self.four("AAAA", [9.5, 9.1, 8.7, 7.1]))
        self.assertEqual(report["per_horizon"][3]["complete_prefix_unauthenticated"], 1)
        self.assertFalse(report["calendar_and_provider_assertions_independently_authenticated"])
        self.assertIsNone(report["verified_precision"])
        self.assertIsNone(report["verified_false_positives"])
        self.assertFalse(report["actual_smg_trade_authorized"])

    def test_price_chain_mismatch_quarantines_later_prefix(self):
        rows = self.four("AAAA", [9.5, 9.1, 8.7, 7.1])
        rows[1]["previous_regular_close"] = 8.5
        for provider in rows[1]["independent_eod_sources"]:
            provider["previous_regular_close"] = 8.5
        report = audit(self.capture, calendar(), rows)
        row = next(x for x in report["rows"] if x["ticker"] == "AAAA")
        self.assertEqual(row["horizons"][1]["chain_evidence"], "CROSS_SESSION_PRICE_CHAIN_MISMATCH")
        self.assertEqual(row["horizons"][2]["chain_evidence"], "PRIOR_HORIZON_CENSORED")
        self.assertEqual(report["per_horizon"][3]["structurally_consistent_source_row"], 1)

    def test_blocked_provider_keeps_all_later_slots(self):
        rows = self.four("AAAA", [9.5, 9.1, 8.7, 7.1])
        rows[1]["provider_conflict"] = True
        report = audit(self.capture, calendar(), rows)
        row = next(x for x in report["rows"] if x["ticker"] == "AAAA")
        self.assertEqual(row["horizons"][1]["source_evidence"], "SUPPLIED_EOD_EVIDENCE_BLOCKED")
        self.assertEqual(row["horizons"][3]["chain_evidence"], "PRIOR_HORIZON_CENSORED")

    def test_duplicate_and_outside_rows_fail_closed(self):
        first = eod("AAAA", 0, 10, 9.5)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OUTSIDE"):
            audit(self.capture, calendar(), [first, first])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OUTSIDE"):
            audit(self.capture, calendar(), [eod("ZZZZ", 0, 10, 9.5)])


if __name__ == "__main__":
    unittest.main()
