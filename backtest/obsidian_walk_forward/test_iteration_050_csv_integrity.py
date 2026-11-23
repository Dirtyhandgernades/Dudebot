"""Research-only regression tests for iteration 049 reconciliation; synthetic fixtures only.

No historical data, P&L, ranker invocation, or SMG interaction.
Run from repository root:
python -m unittest discover -s backtest/obsidian_walk_forward -p 'test_iteration_050_csv_integrity.py' -v
"""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "obsidian_csv_integrity_049",
    HERE / "iteration_049_trade_csv_integrity_fixed_2026_11_23.py",
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class CsvIntegrityTests(unittest.TestCase):
    def make_fixture(self, root, *, corrupt=False):
        sample = {
            "ticker": "TEST", "signal_date": "2025-09-08",
            "entry_date": "2025-09-08", "exit_date": "2025-09-09",
            "exit_reason": None, "shares": 10, "entry_price": 4.0,
            "notional": 40.0, "pnl": 0.0, "return_pct": 0.0,
        }
        for year in (2023, 2024, 2025):
            for policy in checker.POLICIES:
                targets = (50000,) if policy == "top_half_30pct" else (30000, 50000)
                for target in targets:
                    for case in ("base", "stress"):
                        stem = f"{year}-{policy}-{target}-{case}"
                        (root / f"{stem}.json").write_text(
                            json.dumps({"trades": [sample], "closed_trades": 1}),
                            encoding="utf-8",
                        )
                        with (root / f"{stem}-trades.csv").open(
                            "w", newline="", encoding="utf-8"
                        ) as stream:
                            writer = csv.DictWriter(stream, fieldnames=checker.FIELDS)
                            writer.writeheader()
                            row = dict(sample)
                            if corrupt and stem == "2025-top_half-30000-base":
                                row["shares"] = 11
                            writer.writerow(row)

    def test_null_csv_cell_matches_original_writer(self):
        self.assertEqual(checker.csv_cell(None), "")
        self.assertEqual(checker.csv_cell(0.0), "0.0")

    def test_all_54_consistent_fixtures_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            result = checker.check(root)
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["checked_configurations"], 54)

    def test_mismatched_share_count_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root, corrupt=True)
            result = checker.check(root)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(any("value mismatch" in x for x in result["failures"]))

    def test_missing_csv_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            (root / "2025-top_half-30000-base-trades.csv").unlink()
            result = checker.check(root)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(any("missing or symlink" in x for x in result["failures"]))


if __name__ == "__main__":
    unittest.main()
