"""Offline regression tests for delayed SIP response validation."""
import unittest
from datetime import datetime, timedelta, timezone
from backtest.obsidian_delayed_sip_integrity import inspect_delayed_sip

NOW = datetime(2026, 10, 27, 1, 0, tzinfo=timezone.utc)
START = NOW - timedelta(minutes=45)
END = NOW - timedelta(minutes=30)


def sample(t=None):
    return {"bars": {"SPY": [{"t": (t or START).isoformat(), "o": 100.0,
                              "h": 102.0, "l": 99.0, "c": 101.0, "v": 1200}]}}


def check(payload, start=START, end=END, received=NOW):
    return inspect_delayed_sip(payload, "SPY", start, end, received)


class DelayedSipIntegrityTests(unittest.TestCase):
    def test_valid_bars_not_official_close(self):
        r = check(sample())
        self.assertEqual(r["status"], "DELAYED_SIP_BAR_CONTENT_VALIDATED_NOT_OFFICIAL_CLOSE")
        self.assertEqual(r["valid_bars"], 1)
    def test_http_200_empty_not_validated(self):
        self.assertEqual(check({"bars": {"SPY": []}})["status"], "NO_BARS_RETURNED")
    def test_http_200_missing_bars_not_validated(self):
        self.assertEqual(check({"message": "ok"})["status"], "INVALID_RESPONSE_SHAPE")
    def test_future_bar_rejected(self):
        self.assertEqual(check(sample(NOW))["status"], "INVALID_OR_DUPLICATE_BAR_TIMESTAMP")
    def test_inclusive_end_bar_excluded(self):
        p = sample()
        p["bars"]["SPY"].append(dict(p["bars"]["SPY"][0], t=END.isoformat()))
        r = check(p)
        self.assertEqual(r["status"], "DELAYED_SIP_BAR_CONTENT_VALIDATED_NOT_OFFICIAL_CLOSE")
        self.assertEqual(r["valid_bars"], 1)
        self.assertEqual(r["boundary_bars_excluded"], 1)
    def test_only_boundary_bar_is_not_evidence(self):
        self.assertEqual(check(sample(END))["status"], "NO_IN_WINDOW_BARS")
    def test_after_end_rejected(self):
        self.assertEqual(check(sample(END + timedelta(minutes=1)))["status"],
                         "INVALID_OR_DUPLICATE_BAR_TIMESTAMP")
    def test_duplicate_timestamp_rejected(self):
        p = sample()
        p["bars"]["SPY"].append(dict(p["bars"]["SPY"][0]))
        self.assertEqual(check(p)["status"], "INVALID_OR_DUPLICATE_BAR_TIMESTAMP")
    def test_recent_window_rejected(self):
        self.assertEqual(check(sample(), end=NOW - timedelta(minutes=14))["status"], "NOT_DELAYED_ASOF")
    def test_inconsistent_ohlc_rejected(self):
        p = sample()
        p["bars"]["SPY"][0]["h"] = 100
        self.assertEqual(check(p)["status"], "INCONSISTENT_OHLC")
    def test_nan_rejected(self):
        p = sample()
        p["bars"]["SPY"][0]["c"] = float("nan")
        self.assertEqual(check(p)["status"], "INVALID_OHLC")
    def test_negative_volume_rejected(self):
        p = sample()
        p["bars"]["SPY"][0]["v"] = -1
        self.assertEqual(check(p)["status"], "INVALID_VOLUME")
    def test_naive_clock_rejected(self):
        self.assertEqual(check(sample(), received=NOW.replace(tzinfo=None))["status"], "INVALID_REQUEST_CLOCK")


if __name__ == "__main__":
    unittest.main()
