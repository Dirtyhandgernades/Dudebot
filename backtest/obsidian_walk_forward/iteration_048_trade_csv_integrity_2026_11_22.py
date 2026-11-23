"""Iteration 048: read-only trade-ledger reconciliation supplement.
Checks original-ranker CSV output against its corresponding portfolio JSON.
Does not execute, mutate, or infer executable SMG fills.
"""
import csv
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python iteration_048_trade_csv_integrity_2026_11_22.py OUTPUT_DIRECTORY")
    candidate = Path(sys.argv[1])
    if candidate.is_symlink():
        raise SystemExit("BLOCKED: output path is symlink")
    root = candidate.resolve(strict=True)
    if root.name != "target-rank-2026-10-05" or not root.is_dir():
        raise SystemExit("BLOCKED: wrong output directory")
    expected_fields = ["ticker", "signal_date", "entry_date", "exit_date", "exit_reason",
                       "shares", "entry_price", "notional", "pnl", "return_pct"]
    failures = []
    checked = 0
    for year in (2023, 2024, 2025):
        for policy in ("top_half", "top_quartile", "top_decile", "confirmed_top_quartile", "top_half_30pct"):
            for target in ((50000,) if policy == "top_half_30pct" else (30000, 50000)):
                for case in ("base", "stress"):
                    stem = f"{year}-{policy}-{target}-{case}"
                    j, c = root / (stem + ".json"), root / (stem + "-trades.csv")
                    if not j.is_file() or not c.is_file() or j.is_symlink() or c.is_symlink():
                        failures.append(f"{stem}: missing/symlink file")
                        continue
                    try:
                        portfolio = json.loads(j.read_text(encoding="utf-8"))
                        with c.open(newline="", encoding="utf-8") as f:
                            reader = csv.DictReader(f)
                            fields = reader.fieldnames
                            trades = list(reader)
                        original = portfolio["trades"]
                        if fields != expected_fields:
                            failures.append(f"{stem}: CSV field mismatch")
                        if len(trades) != len(original) or len(trades) != portfolio["closed_trades"]:
                            failures.append(f"{stem}: trade count CSV={len(trades)} JSON={len(original)} closed={portfolio['closed_trades']}")
                        for idx, (row, trade) in enumerate(zip(trades, original)):
                            for field in expected_fields:
                                # The ranker's csv.DictWriter uses Python's str() on JSON values.
                                if row.get(field) != str(trade.get(field, "")):
                                    failures.append(f"{stem}: trade {idx} {field} mismatch")
                                    break
                        checked += 1
                    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
                        failures.append(f"{stem}: parsing/reconciliation error {type(exc).__name__}")
    print(json.dumps({"status": "PASS" if checked == 54 and not failures else "BLOCKED",
                      "checked_configurations": checked, "expected": 54,
                      "failures": failures[:30], "failure_count": len(failures)}, indent=2))
    if checked != 54 or failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
