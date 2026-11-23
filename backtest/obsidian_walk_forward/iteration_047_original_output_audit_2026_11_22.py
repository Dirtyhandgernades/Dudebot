"""Research-only, read-only structural audit of original 54-configuration output.
Run only AFTER the unchanged original ranker finishes in a disposable checkout.
Does not calculate returns, execute the ranker, or modify any file.
"""
import json
import sys
from pathlib import Path

POLICIES = ("top_half", "top_quartile", "top_decile", "confirmed_top_quartile", "top_half_30pct")
CASES = ("base", "stress")
YEARS = (2023, 2024, 2025)
EXPECTED = {
    (2023, "top_half_30pct", 50000, "base"): 18658.11,
    (2024, "top_half_30pct", 50000, "base"): 39124.52,
    (2025, "top_half_30pct", 50000, "base"): 103258.54,
    (2025, "top_half_30pct", 50000, "stress"): 64020.56,
    (2025, "top_half", 30000, "base"): 73815.54,
    (2025, "top_half", 30000, "stress"): 48528.08,
}

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python iteration_047_original_output_audit_2026_11_22.py OUTPUT_DIRECTORY")
    root = Path(sys.argv[1]).resolve(strict=True)
    if not root.is_dir() or root.is_symlink() or root.name != "target-rank-2026-10-05":
        raise SystemExit("BLOCKED: unexpected original-ranker output directory")
    expected = {"summary.json"} | {f"{year}-model.json" for year in YEARS}
    keys = []
    for year in YEARS:
        for policy in POLICIES:
            for target in ((50000,) if policy == "top_half_30pct" else (30000, 50000)):
                for case in CASES:
                    stem = f"{year}-{policy}-{target}-{case}"
                    expected.update((stem + ".json", stem + "-trades.csv"))
                    keys.append((year, policy, target, case, stem))
    actual = {p.name for p in root.iterdir() if p.is_file()}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    failures = []
    if missing: failures.append(f"missing {len(missing)} expected files: {missing[:8]}")
    if extra: failures.append(f"unexpected {len(extra)} files: {extra[:8]}")
    if len(keys) != 54: failures.append(f"wrong matrix count {len(keys)}")
    if not missing:
        summary = json.loads((root / "summary.json").read_text())
        rows = summary.get("results", [])
        if len(rows) != 54: failures.append(f"summary has {len(rows)} rows, expected 54")
        indexed = {}
        for row in rows:
            k = (row.get("year"), row.get("policy"), row.get("position_target"), row.get("cost_case"))
            if k in indexed: failures.append(f"duplicate summary key {k}")
            indexed[k] = row
        for year, policy, target, case, stem in keys:
            k = (year, policy, target, case)
            row = indexed.get(k)
            if row is None:
                failures.append(f"missing summary key {k}")
                continue
            result = json.loads((root / (stem + ".json")).read_text())
            for field in ("net_profit", "ending_balance", "closed_trades", "max_observed_drawdown_pct"):
                if field not in result or field not in row or result[field] != row[field]:
                    failures.append(f"summary/result mismatch {stem}: {field}")
            if k in EXPECTED and abs(float(result["net_profit"]) - EXPECTED[k]) > .011:
                failures.append(f"archived report P&L mismatch {stem}: {result['net_profit']} vs {EXPECTED[k]}")
    print(json.dumps({"status": "PASS_STRUCTURE_AND_SIX_REPORT_SPOT_CHECKS" if not failures else "BLOCKED",
                      "expected_configurations": len(keys), "expected_files": len(expected),
                      "failures": failures}, indent=2))
    if failures: raise SystemExit(1)

if __name__ == "__main__":
    main()
