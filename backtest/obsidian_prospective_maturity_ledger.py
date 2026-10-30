"""Prospective, full-denominator maturity ledger (offline, research-only).

This ledger NEVER authenticates an official close. Even a structurally consistent
supplied provider row is censored pending independent source authentication.
The caller must supply an explicit as-of timestamp; there is no hidden clock,
future close leakage, retroactive prediction labeling, or trade authorization.
"""
from collections import Counter
import argparse
import json
from pathlib import Path

from backtest.obsidian_forward_horizon_coverage_shadow import audit
from backtest.obsidian_forward_horizon_shadow import validate_calendar
from backtest.obsidian_prospective_capture import asof, EASTERN

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_PROSPECTIVE_MATURITY_LEDGER_SHADOW_V1_2026_10_30"
CATEGORIES = (
    "VERIFIED", "SOURCE_CONFLICT", "CENSORED_MISSING",
    "CENSORED_UNVERIFIED", "CENSORED_BLOCKED", "NOT_YET_MATURE",
)


def build(capture, calendar_rows, outcome_rows, as_of):
    """Audit every original issuer and all four exchange-session horizons.

    This is a source-coverage ledger, NOT an outcome scorer. Provider attestations
    in JSON cannot make a row VERIFIED; only a separate authenticated evidence
    pipeline could eventually supply that status.
    """
    now = asof(as_of)
    if now is None or now.utcoffset() is None:
        raise ValueError("EXPLICIT_TIMEZONE_AWARE_AS_OF_REQUIRED")
    coverage = audit(capture, calendar_rows, outcome_rows)
    first_day = asof(json.loads((Path(capture) / "manifest.json").read_text(
        encoding="utf-8"))["started_at"]).astimezone(EASTERN).date()
    calendar = validate_calendar(calendar_rows, first_day)
    supplied = {(r["ticker"], r["session_date"]): r for r in outcome_rows}
    rows = []
    per_horizon = [Counter() for _ in range(4)]
    per_watch = [{True: Counter(), False: Counter()} for _ in range(4)]
    for original in coverage["rows"]:
        symbol = original["ticker"]
        watch = original["original_price_only_watch"]
        horizons = []
        for h, (session, _prior, close_at, _meta) in enumerate(calendar):
            day = session.isoformat()
            source = supplied.get((symbol, day))
            evidence = original["horizons"][h]["source_evidence"]
            if now < close_at:
                category = "NOT_YET_MATURE"
                reason = "REGULAR_SESSION_CLOSE_IN_FUTURE"
            elif source is None:
                category = "CENSORED_MISSING"
                reason = "NO_SUPPLIED_OUTCOME_ROW"
            elif source.get("provider_conflict") is True:
                category = "SOURCE_CONFLICT"
                reason = "SUPPLIED_PROVIDER_CONFLICT_UNAUTHENTICATED"
            elif evidence == "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING":
                category = "CENSORED_UNVERIFIED"
                reason = "PROVIDER_IDENTITY_AND_OFFICIAL_CLOSE_AUTH_PENDING"
            else:
                category = "CENSORED_BLOCKED"
                reason = "SUPPLIED_EOD_EVIDENCE_FAILED_STRUCTURAL_GATE"
            per_horizon[h][category] += 1
            per_watch[h][watch][category] += 1
            horizons.append({
                "horizon": h, "session_date": day,
                "regular_close_at": close_at.isoformat(),
                "category": category, "reason": reason,
                "source_evidence": evidence,
                "official_close_authenticated": False,
                "verified_prediction_or_trade": None,
            })
        rows.append({
            "ticker": symbol,
            "original_status": original["original_status"],
            "original_price_only_watch": watch,
            "horizons": horizons,
        })
    n = coverage["original_universe_count"]
    for h in range(4):
        if sum(per_horizon[h].values()) != n:
            raise AssertionError("ORIGINAL_HORIZON_DENOMINATOR_MISMATCH")
        for category in CATEGORIES:
            if sum(per_watch[h][flag][category] for flag in (True, False)) != per_horizon[h][category]:
                raise AssertionError("WATCH_DENOMINATOR_MISMATCH")
    return {
        "mode": MODE, "policy": POLICY,
        "as_of": now.isoformat(),
        "original_capture_universe_sha256": coverage["original_capture_universe_sha256"],
        "original_universe_count": n,
        "expected_issuer_session_slots": n * 4,
        "provided_source_rows": coverage["provided_source_rows"],
        "per_horizon": [
            {"horizon": h, "session_date": calendar[h][0].isoformat(),
             "original_denominator": n,
             "categories": {key: per_horizon[h][key] for key in CATEGORIES},
             "watch_categories": {
                 str(flag).lower(): {key: per_watch[h][flag][key] for key in CATEGORIES}
                 for flag in (True, False)
             }}
            for h in range(4)
        ],
        "independent_official_close_authentication_performed": False,
        "verified_outcomes": 0, "verified_hits": None,
        "verified_false_positives": None, "verified_precision": None,
        "verified_recall": None, "after_cost_returns": None,
        "predictive_edge_proven": False, "actual_smg_trade_authorized": False,
        "frozen_original_labels_modified": False,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Research-only maturity and missingness ledger")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--calendar", required=True)
    parser.add_argument("--outcomes", required=True)
    parser.add_argument("--as-of", required=True, help="Explicit offset-aware ISO timestamp")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build(
        args.capture,
        json.loads(Path(args.calendar).read_text(encoding="utf-8")),
        json.loads(Path(args.outcomes).read_text(encoding="utf-8")),
        args.as_of,
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({
        "policy": POLICY, "original_universe_count": report["original_universe_count"],
        "expected_issuer_session_slots": report["expected_issuer_session_slots"],
        "verified_outcomes": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
