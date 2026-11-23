"""Iteration 053: required-field-hardened read-only reconciliation of original ranker CSVs.
No ranker execution, trade placement, or baseline modification.
"""
import csv
import json
import sys
from pathlib import Path

FIELDS = ("ticker", "signal_date", "entry_date", "exit_date", "exit_reason",
          "shares", "entry_price", "notional", "pnl", "return_pct")
POLICIES = ("top_half", "top_quartile", "top_decile",
            "confirmed_top_quartile", "top_half_30pct")

def csv_cell(value):
    # csv.DictWriter writes None as empty text, unlike str(None).
    return "" if value is None else str(value)

def check(root):
    failures = []
    checked = 0
    for year in (2023, 2024, 2025):
        for policy in POLICIES:
            for target in ((50000,) if policy == "top_half_30pct" else (30000, 50000)):
                for case in ("base", "stress"):
                    stem = f"{year}-{policy}-{target}-{case}"
                    j, c = root / (stem + ".json"), root / (stem + "-trades.csv")
                    if not j.is_file() or not c.is_file() or j.is_symlink() or c.is_symlink():
                        failures.append(f"{stem}: missing or symlink input")
                        continue
                    try:
                        portfolio = json.loads(j.read_text(encoding="utf-8"))
                        with c.open(newline="", encoding="utf-8") as stream:
                            reader = csv.DictReader(stream)
                            header = reader.fieldnames
                            rows = list(reader)
                        originals = portfolio["trades"]
                        if header != list(FIELDS):
                            failures.append(f"{stem}: CSV header mismatch")
                        if len(rows) != len(originals) or len(rows) != portfolio["closed_trades"]:
                            failures.append(f"{stem}: trade count mismatch")
                        for idx, (row, trade) in enumerate(zip(rows, originals)):
                            if not isinstance(trade, dict) or any(field not in trade for field in FIELDS):
                                failures.append(f"{stem}: row {idx} missing required JSON trade field")
                                continue
                            if any(row.get(field) != csv_cell(trade[field])
                                   for field in FIELDS):
                                failures.append(f"{stem}: row {idx} value mismatch")
                        checked += 1
                    except (ValueError, KeyError, TypeError, OSError) as exc:
                        failures.append(f"{stem}: {type(exc).__name__}: {exc}")
    return {"status": "PASS" if checked == 54 and not failures else "BLOCKED",
            "checked_configurations": checked, "expected": 54,
            "failure_count": len(failures), "failures": failures[:30]}

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python iteration_053_trade_csv_integrity_required_fields_2026_11_23.py OUTPUT_DIRECTORY")
    candidate = Path(sys.argv[1])
    if candidate.is_symlink():
        raise SystemExit("BLOCKED: symlink output directory")
    root = candidate.resolve(strict=True)
    if not root.is_dir() or root.name != "target-rank-2026-10-05":
        raise SystemExit("BLOCKED: incorrect output directory")
    result = check(root)
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
