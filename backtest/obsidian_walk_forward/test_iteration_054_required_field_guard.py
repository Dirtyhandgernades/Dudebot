"""Iteration 054: regression of the hardened 053 checker against omitted required fields.
Synthetic fixtures only; no ranker, SMG, or historical P&L.
Run: python -m unittest discover -s backtest/obsidian_walk_forward -p 'test_iteration_054_required_field_guard.py' -v
"""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "obsidian_csv_integrity_053",
    HERE / "iteration_053_trade_csv_integrity_required_fields_2026_11_23.py",
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

class RequiredFieldGuardTests(unittest.TestCase):
    def fixture(self, root, omission=False):
        sample = dict(ticker="TEST", signal_date="2025-09-08",
                      entry_date="2025-09-08", exit_date="2025-09-09",
                      exit_reason=None, shares=10, entry_price=4.0,
                      notional=40.0, pnl=0.0, return_pct=0.0)
        for year in (2023, 2024, 2025):
            for policy in checker.POLICIES:
                targets = (50000,) if policy == "top_half_30pct" else (30000, 50000)
                for target in targets:
                    for case in ("base", "stress"):
                        stem = f"{year}-{policy}-{target}-{case}"
                        trade = dict(sample)
                        if omission and stem == "2025-top_half-30000-base":
                            del trade["exit_reason"]
                        (root / (stem + ".json")).write_text(
                            json.dumps({"trades": [trade], "closed_trades": 1}),
                            encoding="utf-8")
                        with (root / (stem + "-trades.csv")).open(
                            "w", newline="", encoding="utf-8") as handle:
                            writer = csv.DictWriter(handle, fieldnames=checker.FIELDS)
                            writer.writeheader()
                            writer.writerow(trade)

    def test_complete_54_configuration_fixture_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            result = checker.check(root)
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["checked_configurations"], 54)

    def test_missing_required_key_blocks_even_if_csv_cell_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, omission=True)
            result = checker.check(root)
            self.assertEqual(result["status"], "BLOCKED", result)
            self.assertTrue(any("missing required JSON trade field" in x
                                for x in result["failures"]), result)

    def test_null_is_not_missing(self):
        self.assertEqual(checker.csv_cell(None), "")

if __name__ == "__main__":
    unittest.main()
