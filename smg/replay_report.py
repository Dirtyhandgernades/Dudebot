"""Render an evidence-bound comparison of strict and firm-first replay outputs."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_holdout(reference: Path, message: Path):
    with reference.open(encoding="utf-8-sig") as stream:
        expected = [(r["ticker"], r["event_date"], float(r["reported_drop_pct"])) for r in csv.DictReader(stream)]
    observed = []
    for line in message.read_text(encoding="utf-8-sig").splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        month, day, year = (int(v) for v in fields[1].split("/"))
        observed.append((fields[0], f"{year:04d}-{month:02d}-{day:02d}", float(fields[2].rstrip("%"))))
    if observed != expected:
        raise ValueError("message.txt does not exactly match reference_events.csv")
    return expected


def render(replay: Path, reference: Path, message: Path):
    events = verify_holdout(reference, message)
    firm = list(csv.DictReader((replay / "event_comparison.csv").open(encoding="utf-8")))
    strict = load_json(replay / "strict_event_comparison.json")
    firm_summary = load_json(replay / "summary.json")
    strict_summary = load_json(replay / "strict_summary.json")
    if len(firm) != len(events) or len(strict) != len(events):
        raise ValueError("comparison output does not cover every holdout event")
    firm_by_id = {r["event_id"]: r for r in firm}
    strict_by_id = {r["event_id"]: r for r in strict}
    rows = []
    for ticker, event_date, drop in events:
        event_id = next(r["event_id"] for r in firm if r["ticker"] == ticker and r["event_date"] == event_date)
        a, b = firm_by_id[event_id], strict_by_id[event_id]
        rows.append(dict(event_id=event_id, ticker=ticker, event_date=event_date,
            reported_drop_pct=drop, firm_first=a["result"], strict=b["result"],
            firm_first_decisions=int(a["sampled_decisions"]),
            strict_decisions=int(b["evaluated_candidate_decisions"]),
            strict_reasons=b["reasons"]))
    pair_counts = Counter((r["firm_first"], r["strict"]) for r in rows)
    detected = [r for r in rows if r["strict"] == "DETECTED_PRIOR"]
    halt_only = [r for r in rows if r["strict"] == "UNVERIFIED_HALT_MATCH"]
    body = [
        "# Combined three-year replay report", "",
        f"Holdout integrity: all {len(events)} message rows exactly match reference_events.csv.", "",
        "## Results", "",
        f"- Fully verified strict detections: {len(detected)}.",
        f"- Strict matches blocked only by historical halt verification: {len(halt_only)}.",
        f"- Conditional firm-first matches: {firm_summary['comparison_counts'].get('CONDITIONAL_FIRM_AND_PRICE_MATCH', 0)}.",
        f"- Strict transaction candidates: {strict_summary['transaction_candidates']}; evaluated decisions: {strict_summary['evaluated_decisions']}/{strict_summary.get('planned_decisions', 'unknown')}.",
        "- Verified strict misses and a full-universe detection rate remain undefined while universe coverage is incomplete.", "",
        "Conditional firm-first matches are research evidence, not executable alerts. User-supplied drop percentages are holdout labels, not independently reconstructed returns.", "",
        "## Joint outcome counts", "",
        "| Firm-first result | Strict result | Events |", "|---|---|---:|",
    ]
    body += [f"| {a} | {b} | {count} |" for (a, b), count in sorted(pair_counts.items())]
    body += ["", "## Material data gaps", ""]
    body += [f"- {item}" for item in dict.fromkeys(firm_summary["limitations"] + strict_summary["limitations"])]
    body += ["", "The per-event machine-readable comparison is combined_event_comparison.csv.", ""]
    return "\n".join(body), rows


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("replay", type=Path)
    parser.add_argument("--reference", type=Path, default=Path("backtest/reference_events.csv"))
    parser.add_argument("--message", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/combined-replay"))
    args = parser.parse_args(argv)
    text, rows = render(args.replay, args.reference, args.message)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.md").write_text(text, encoding="utf-8")
    with (args.output / "combined_event_comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


if __name__ == "__main__":
    main()
