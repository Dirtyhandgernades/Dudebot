"""Full-denominator, non-scoring 0/+1/+2/+3 outcome-coverage audit.

RESEARCH_ONLY_NOT_AN_ORDER. Separately registered shadow, not a change to
frozen forward labels or source captures. Offline supplied provider/calendar
assertions are NEVER independently authenticated here. All four horizons for
EVERY original symbol are inventoried, even after an earlier missing row.
"""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

from backtest.obsidian_iex_research_discovery import verify, EARLY_STATES
from backtest.obsidian_forward_horizon_shadow import validate_calendar, _source_chain_ok
from backtest.obsidian_prospective_capture import asof, EASTERN

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_FORWARD_FULL_DENOMINATOR_COVERAGE_SHADOW_V1_2026_10_29"


def audit(capture, calendar_rows, outcome_rows):
    """No prediction scoring: retain 4*N evidence slots, including all misses."""
    original = verify(capture)
    base = Path(capture)
    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("phase") not in ("MORNING", "INTRADAY"):
        raise ValueError("ONLY_ORIGINAL_PREDECISION_RESEARCH_CAPTURE_ALLOWED")
    started = asof(manifest.get("started_at"))
    if started is None:
        raise ValueError("CAPTURE_START_TIME_UNVERIFIED")
    original_day = started.astimezone(EASTERN).date()
    calendar = validate_calendar(calendar_rows, original_day)
    if not isinstance(outcome_rows, list):
        raise ValueError("OUTCOME_ROWS_MUST_BE_LIST")
    raw = (base / "universe.jsonl").read_bytes()
    records = [json.loads(line) for line in raw.splitlines()]
    if len(records) != original["universe_count"]:
        raise ValueError("ORIGINAL_UNIVERSE_DENOMINATOR_MISMATCH")
    symbols = [row.get("ticker") for row in records]
    if any(not isinstance(s, str) or not s for s in symbols) or len(set(symbols)) != len(symbols):
        raise ValueError("ORIGINAL_UNIVERSE_IDENTITY_INVALID")
    allowed = set(symbols)
    days = {entry[0].isoformat() for entry in calendar}
    mapped = {}
    for row in outcome_rows:
        if not isinstance(row, dict):
            raise ValueError("INVALID_OUTCOME_ROW")
        key = (row.get("ticker"), row.get("session_date"))
        if key[0] not in allowed or key[1] not in days or key in mapped:
            raise ValueError("DUPLICATE_OR_OUTSIDE_ORIGINAL_COHORT")
        mapped[key] = row

    per_horizon = [Counter(original_denominator=len(records)) for _ in range(4)]
    rows = []
    for source in records:
        ticker = source["ticker"]
        statuses = []
        prefix_ok = True
        previous_close = None
        for horizon, calendar_entry in enumerate(calendar):
            day = calendar_entry[0].isoformat()
            supplied = mapped.get((ticker, day))
            counts = per_horizon[horizon]
            if supplied is None:
                evidence = "MISSING_EOD_SOURCE_ROW"
                counts["missing_source_row"] += 1
                structurally_ok = False
            elif not _source_chain_ok(supplied, calendar_entry):
                evidence = "SUPPLIED_EOD_EVIDENCE_BLOCKED"
                counts["blocked_source_row"] += 1
                structurally_ok = False
            else:
                evidence = "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING"
                counts["structurally_consistent_source_row"] += 1
                structurally_ok = True
            if not structurally_ok:
                chain = "PREFIX_CENSORED_MISSING_OR_BLOCKED"
                prefix_ok = False
                counts["prefix_censored"] += 1
            elif not prefix_ok:
                chain = "PRIOR_HORIZON_CENSORED"
                counts["prior_horizon_censored"] += 1
            elif (horizon > 0 and previous_close is not None and
                  abs(supplied["previous_regular_close"] - previous_close) > 0.005):
                chain = "CROSS_SESSION_PRICE_CHAIN_MISMATCH"
                prefix_ok = False
                counts["price_chain_mismatch"] += 1
            else:
                chain = "COMPLETE_PREFIX_UNAUTHENTICATED"
                previous_close = supplied["regular_close"]
                counts["complete_prefix_unauthenticated"] += 1
            statuses.append({
                "horizon": horizon, "session_date": day,
                "source_evidence": evidence, "chain_evidence": chain,
                "official_close_authenticated": False,
                "outcome_censored_for_verified_scoring": True,
            })
        rows.append({
            "ticker": ticker, "original_status": source.get("indicative_status"),
            "original_price_only_watch": source.get("indicative_status") in EARLY_STATES,
            "horizons": statuses,
            "verified_prediction_or_trade": None,
        })
    for counter in per_horizon:
        if (counter["missing_source_row"] + counter["blocked_source_row"] +
                counter["structurally_consistent_source_row"] != len(records)):
            raise AssertionError("HORIZON_DENOMINATOR_PARTITION_FAILED")
    return {
        "mode": MODE, "policy": POLICY,
        "original_capture_universe_sha256": hashlib.sha256(raw).hexdigest(),
        "original_universe_count": len(records),
        "horizons": [0, 1, 2, 3],
        "total_expected_symbol_session_slots": 4 * len(records),
        "provided_source_rows": len(outcome_rows),
        "per_horizon": [
            {"horizon": index, "session_date": calendar[index][0].isoformat(),
             **dict(sorted(counts.items()))}
            for index, counts in enumerate(per_horizon)
        ],
        "calendar_and_provider_assertions_independently_authenticated": False,
        "verified_outcomes": None, "verified_hits": None,
        "verified_false_positives": None, "verified_precision": None,
        "verified_recall": None, "after_cost_returns": None,
        "multiple_scans_of_same_issuer_counted_as_independent": False,
        "frozen_baselines_or_denominators_modified": False,
        "actual_smg_trade_authorized": False,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Research-only forward missingness audit")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--calendar", required=True)
    parser.add_argument("--outcomes", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = audit(args.capture,
                   json.loads(Path(args.calendar).read_text(encoding="utf-8")),
                   json.loads(Path(args.outcomes).read_text(encoding="utf-8")))
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({
        "policy": POLICY,
        "original_universe_count": report["original_universe_count"],
        "total_expected_symbol_session_slots": report["total_expected_symbol_session_slots"],
        "verified_hits": None,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
