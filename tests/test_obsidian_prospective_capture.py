"""Synthetic, offline tests for independent research-only capture."""
import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from backtest.obsidian_prospective_capture import collect, candidate, in_window, persist, AlpacaReadOnly, ASSETS_URL, ALTERNATE_ASSETS_URL, ProviderAuthError
from backtest.obsidian_prospective_journal import audit

AT = datetime(2026, 10, 26, 19, 50, tzinfo=timezone.utc)


def snap(price, previous=10, trade_at="2026-10-26T19:49:00Z"):
    return {"latestTrade": {"p": price, "t": trade_at},
            "prevDailyBar": {"c": previous, "t": "2026-10-23T04:00:00Z"},
            "minuteBar": {"t": "2026-10-26T19:48:00Z"}}


class Fake:
    def __init__(self, snapshots=None):
        self.called = 0
        self._snapshots = snapshots if snapshots is not None else {
            "AAAA": snap(9.5), "BBBB": snap(7), "CCCC": snap(11), "DDDD": snap(8.5)}

    def assets(self):
        self.called += 1
        return [{"symbol": s, "status": "active", "exchange": "NASDAQ", "class": "us_equity"}
                for s in ("AAAA", "BBBB", "CCCC", "DDDD")]

    def snapshots(self, symbols):
        self.called += 1
        return {s: self._snapshots[s] for s in symbols if s in self._snapshots}


class CaptureTests(unittest.TestCase):
    def test_early_and_exhausted_only_without_c_inference(self):
        universe, watches, report = collect(Fake(), clock=lambda: AT)
        self.assertEqual(len(universe), 4)
        self.assertEqual([(w["ticker"], w["category"]) for w in watches], [("AAAA", "A"), ("BBBB", "B")])
        self.assertEqual(report["watch_count"], 2)
        self.assertTrue(all(w["shares_outstanding"] is None and w["borrow_available"] is None for w in watches))
        self.assertTrue(all(w["security_type"] == "UNKNOWN" for w in watches))

    def test_missing_snapshot_retained_in_universe(self):
        provider = Fake({"AAAA": snap(9.5)})
        universe, watches, report = collect(provider, clock=lambda: AT)
        self.assertEqual(len(universe), 4)
        self.assertEqual(report["snapshot_missing_count"], 3)
        self.assertEqual(len(watches), 1)

    def test_malformed_nested_provider_fields_censor_one_asset_only(self):
        for field in ("latestTrade", "prevDailyBar", "minuteBar"):
            with self.subTest(field=field):
                provider = Fake()
                provider._snapshots["AAAA"][field] = ["invalid provider shape"]
                universe, watches, report = collect(provider, clock=lambda: AT)
                self.assertEqual(len(universe), 4)
                self.assertEqual(universe[0]["screen_status"], "MALFORMED_NESTED_SNAPSHOT")
                self.assertEqual(report["status_counts"]["MALFORMED_NESTED_SNAPSHOT"], 1)
                self.assertEqual([(w["ticker"], w["category"]) for w in watches], [("BBBB", "B")])
                self.assertEqual(audit(watches[0])["status"], "BLOCKED")

    def test_stale_trade_does_not_become_candidate(self):
        row, status = candidate({"symbol": "AAAA", "exchange": "NASDAQ"}, snap(9.5, trade_at="2026-10-26T19:40:00Z"), AT, "id")
        self.assertIsNone(row)
        self.assertEqual(status, "STALE_OR_FUTURE_TRADE")

    def test_future_trade_does_not_become_candidate(self):
        row, status = candidate({"symbol": "AAAA", "exchange": "NASDAQ"}, snap(9.5, trade_at="2026-10-26T20:00:00Z"), AT, "id")
        self.assertIsNone(row)
        self.assertEqual(status, "STALE_OR_FUTURE_TRADE")

    def test_off_hours_fail_before_network(self):
        provider = Fake()
        with self.assertRaisesRegex(RuntimeError, "OUTSIDE"):
            collect(provider, clock=lambda: datetime(2026, 10, 26, 21, 0, tzinfo=timezone.utc))
        self.assertEqual(provider.called, 0)

    def test_window_timezone(self):
        self.assertTrue(in_window(AT))
        self.assertFalse(in_window(datetime(2026, 10, 26, 19, 58, 1, tzinfo=timezone.utc)))
        self.assertFalse(in_window(datetime(2026, 10, 25, 19, 50, tzinfo=timezone.utc)))

    def test_invalid_previous_bar_date(self):
        s = snap(9.5); s["prevDailyBar"]["t"] = "2026-10-26T04:00:00Z"
        self.assertEqual(candidate({"symbol": "AAAA"}, s, AT, "id")[1], "INVALID_PREVIOUS_SESSION")

    def test_stale_previous_bar_censored_instead_of_early_signal(self):
        s = snap(9.5); s["prevDailyBar"]["t"] = "2026-10-19T04:00:00Z"
        row, status = candidate({"symbol": "AAAA"}, s, AT, "id")
        self.assertIsNone(row)
        self.assertEqual(status, "STALE_PREVIOUS_CLOSE_BAR")

    def test_four_day_holiday_gap_keeps_watch_but_not_verified_trade(self):
        s = snap(9.5); s["prevDailyBar"]["t"] = "2026-10-22T04:00:00Z"
        row, status = candidate({"symbol": "AAAA"}, s, AT, "id")
        self.assertEqual(status, "PRICE_ONLY_WATCH")
        self.assertEqual(row["security_type"], "UNKNOWN")

    def test_naive_clock_never_opens_capture_window(self):
        self.assertFalse(in_window(datetime(2026, 10, 26, 14, 50)))
        provider = Fake()
        with self.assertRaisesRegex(RuntimeError, "OUTSIDE"):
            collect(provider, clock=lambda: datetime(2026, 10, 26, 14, 50))
        self.assertEqual(provider.called, 0)

    def test_snapshot_error_fails_closed(self):
        class Bad(Fake):
            def snapshots(self, symbols):
                return {"UNREQUESTED": snap(9.5)}
        with self.assertRaisesRegex(ValueError, "UNREQUESTED"):
            collect(Bad(), clock=lambda: AT)

    def test_journal_integration_blocks_all_unverified_borrow_and_cap(self):
        universe, watches, report = collect(Fake(), clock=lambda: AT)
        self.assertTrue(watches)
        self.assertTrue(all(audit(w)["status"] == "BLOCKED" for w in watches))
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "capture"
            manifest = persist(universe, watches, report, dest)
            self.assertEqual(manifest["journal_summary"]["preserved"], 2)
            self.assertEqual(manifest["journal_summary"]["blocked"], 2)
            self.assertEqual(len((dest / "universe.jsonl").read_text().splitlines()), 4)
            self.assertEqual(len((dest / "journal.jsonl").read_text().splitlines()), 2)
            self.assertEqual(json.loads((dest / "manifest.json").read_text())["screened_count"], 4)
            with self.assertRaises(FileExistsError):
                persist(universe, watches, report, dest)

    def test_paper_key_auth_fallback_is_read_only(self):
        client = object.__new__(AlpacaReadOnly)
        calls = []
        def get(url, params):
            calls.append(url)
            if url == ASSETS_URL:
                raise ProviderAuthError("paper unauthorized")
            return [{"symbol": "AAAA"}]
        client.get = get
        self.assertEqual(client.assets(), [{"symbol": "AAAA"}])
        self.assertEqual(calls, [ASSETS_URL, ALTERNATE_ASSETS_URL])
        self.assertEqual(client.assets_url, ALTERNATE_ASSETS_URL)

    def test_asset_response_after_cutoff_fails_before_snapshots(self):
        provider = Fake()
        times = iter((AT, datetime(2026, 10, 26, 19, 59, tzinfo=timezone.utc)))
        with self.assertRaisesRegex(RuntimeError, "ASSET_RESPONSE_OUTSIDE"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 1)

    def test_snapshot_request_after_cutoff_never_calls_provider(self):
        provider = Fake()
        times = iter((AT, AT, datetime(2026, 10, 26, 19, 59, tzinfo=timezone.utc)))
        with self.assertRaisesRegex(RuntimeError, "SNAPSHOT_REQUEST_OUTSIDE"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 1)

    def test_snapshot_response_after_cutoff_is_rejected(self):
        provider = Fake()
        times = iter((AT, AT, AT, datetime(2026, 10, 26, 19, 59, tzinfo=timezone.utc)))
        with self.assertRaisesRegex(RuntimeError, "SNAPSHOT_RESPONSE_OUTSIDE"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 2)

    def test_finished_capture_after_cutoff_is_rejected(self):
        provider = Fake()
        times = iter((AT, AT, AT, AT, datetime(2026, 10, 26, 19, 59, tzinfo=timezone.utc)))
        with self.assertRaisesRegex(RuntimeError, "CAPTURE_FINISHED_OUTSIDE"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 2)

    def test_asset_response_naive_clock_is_rejected(self):
        provider = Fake()
        times = iter((AT, datetime(2026, 10, 26, 14, 50)))
        with self.assertRaisesRegex(ValueError, "INVALID_ASSET_CAPTURE_CLOCK"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 1)

    def test_snapshot_request_clock_regression_is_rejected_before_network(self):
        provider = Fake()
        times = iter((AT, AT.replace(second=2), AT.replace(second=1)))
        with self.assertRaisesRegex(ValueError, "NONMONOTONIC_SNAPSHOT_REQUEST_CLOCK"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 1)

    def test_snapshot_response_clock_regression_is_rejected(self):
        provider = Fake()
        times = iter((AT, AT.replace(second=1), AT.replace(second=3), AT.replace(second=2)))
        with self.assertRaisesRegex(ValueError, "NONMONOTONIC_SNAPSHOT_RESPONSE_CLOCK"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 2)

    def test_finished_capture_clock_regression_is_rejected(self):
        provider = Fake()
        times = iter((AT, AT.replace(second=1), AT.replace(second=2),
                      AT.replace(second=3), AT.replace(second=2)))
        with self.assertRaisesRegex(ValueError, "NONMONOTONIC_FINISH_CLOCK"):
            collect(provider, clock=lambda: next(times))
        self.assertEqual(provider.called, 2)

    def test_request_budget_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "BUDGET"):
            collect(Fake(), clock=lambda: AT, max_requests=0)


if __name__ == "__main__":
    unittest.main()
