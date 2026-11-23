"""Iteration 052: regression test for silent omission of required JSON trade keys.

Research-only synthetic fixture. This test intentionally fails against iteration 049
until a new append-only checker version rejects absent required trade fields.
No ranker execution, historical outcome calculation, or SMG access.
Run:
python -m unittest discover -s backtest/obsidian_walk_forward -p 'test_iteration_052_missing_trade_field.py' -v
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


class MissingTradeFieldTests(unittest.TestCase):
    def test_missing_required_json_field_must_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
                            trade = dict(sample)
                            if stem == "2025-top_half-30000-base":
                                del trade["exit_reason"]
                            (root / f"{stem}.json").write_text(
                                json.dumps({"trades": [trade], "closed_trades": 1}),
                                encoding="utf-8",
                            )
                            with (root / f"{stem}-trades.csv").open(
                                "w", newline="", encoding="utf-8"
                            ) as stream:
                                writer = csv.DictWriter(stream, fieldnames=checker.FIELDS)
                                writer.writeheader()
                                writer.writerow(trade)
            result = checker.check(root)
            self.assertEqual(
                result["status"], "BLOCKED",
                "Missing required JSON trade field was silently accepted",
            )


if __name__ == "__main__":
    unittest.main()
