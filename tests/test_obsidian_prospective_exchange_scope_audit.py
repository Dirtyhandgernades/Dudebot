"""Offline exchange-scope audit regression tests (never provider/network calls)."""
import unittest
from backtest.obsidian_exchange_scope_audit import audit

START = "2026-10-29T14:16:00Z"
FINISH = "2026-10-29T14:16:45Z"
AT = "2026-10-29T14:16:10Z"
ASSETS = [
    {"symbol": "A", "exchange": "NASDAQ", "status": "active"},
    {"symbol": "B", "exchange": "NYSE", "status": "active"},
    {"symbol": "TP", "exchange": "NYSEMkt", "status": "active"},
    {"symbol": "OLD", "exchange": "NASDAQ", "status": "inactive"},
]


class ExchangeScopeTests(unittest.TestCase):
    def run_audit(self, **changes):
        params = dict(assets=ASSETS, captured_symbols=["A", "B"],
                      historical_symbols=["A", "TP", "OLD", "ABSENT"],
                      capture_started_at=START, capture_finished_at=FINISH,
                      assets_observed_at=AT)
        params.update(changes)
        return audit(**params)

    def test_same_capture_exchange_exclusion_preserves_denominator(self):
        result = self.run_audit()
        self.assertTrue(result["provider_metadata_time_aligned"])
        self.assertFalse(result["provider_response_authenticated_by_audit"])
        self.assertEqual(result["historical_missing_count"], 3)
        self.assertEqual(result["provider_exchange_counts"]["NYSEMkt"], 1)
        statuses = {r["ticker"]: r["status"] for r in result["rows"]}
        self.assertEqual(statuses["TP"], "EXCLUDED_EXCHANGE_SCOPE_NOT_SMG_INELIGIBILITY")
        self.assertEqual(statuses["OLD"], "EXCLUDED_INACTIVE_PROVIDER_METADATA_NOT_DELISTING_PROOF")
        self.assertEqual(statuses["ABSENT"], "MISSING_FROM_PROVIDER_RESPONSE_NOT_PROOF_OF_DELISTING")
        self.assertFalse(result["capture_modified"])

    def test_later_asset_response_cannot_backfill_original_exclusion(self):
        result = self.run_audit(assets_observed_at="2026-10-29T15:00:00Z")
        statuses = {r["ticker"]: r["status"] for r in result["rows"]}
        self.assertEqual(statuses["TP"], "MISSING_FROM_CAPTURE_ASYNC_METADATA_CANNOT_EXPLAIN")
        self.assertEqual(statuses["OLD"], "MISSING_FROM_CAPTURE_ASYNC_METADATA_CANNOT_EXPLAIN")
        self.assertFalse(result["provider_metadata_time_aligned"])

    def test_same_capture_missing_selected_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError, "CONTEMPORANEOUS_SELECTED_UNIVERSE_MISMATCH"):
            self.run_audit(captured_symbols=["A"])

    def test_duplicate_provider_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PROVIDER_ASSET_SYMBOL"):
            self.run_audit(assets=ASSETS + [ASSETS[0]])

    def test_duplicate_historical_watch_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_HISTORICAL_SYMBOLS"):
            self.run_audit(historical_symbols=["TP", "TP"])

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "NAIVE_ASOF_TIMESTAMP"):
            self.run_audit(assets_observed_at="2026-10-29T14:16:10")

    def test_missing_exchange_is_not_eligible(self):
        result = self.run_audit(assets=ASSETS + [{"symbol": "X", "status": "active"}],
                                historical_symbols=["X"])
        self.assertEqual(result["rows"][0]["status"],
                         "EXCLUDED_EXCHANGE_SCOPE_NOT_SMG_INELIGIBILITY")

    def test_original_capture_not_modified_by_audit(self):
        import copy
        raw = copy.deepcopy(ASSETS)
        self.run_audit()
        self.assertEqual(raw, ASSETS)


if __name__ == "__main__":
    unittest.main()
