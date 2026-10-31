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



def _audit_preclose(capture, calendar_rows, outcome_rows, manifest):
    """Separately audit original protected IEX preclose rows without relabeling.

    The existing morning/intraday frozen forward cohort is untouched. This
    adapter replays the distinct preclose manifest, hashes and statuses before
    creating four strictly non-scoring outcome-coverage slots per original row.
    """
    import hashlib
    from backtest.obsidian_iex_prospective import verify as verify_preclose
    from backtest.obsidian_forward_horizon_shadow import _source_chain_ok

    verified = verify_preclose(capture)
    base = Path(capture)
    started = asof(manifest.get("started_at"))
    if started is None:
        raise ValueError("PRECLOSE_START_TIME_UNVERIFIED")
    calendar = validate_calendar(calendar_rows, started.astimezone(EASTERN).date())
    if not isinstance(outcome_rows, list):
        raise ValueError("OUTCOME_ROWS_MUST_BE_LIST")
    raw = (base / "universe.jsonl").read_bytes()
    originals = [json.loads(line) for line in raw.splitlines()]
    if len(originals) != verified["universe_count"]:
        raise ValueError("PRECLOSE_ORIGINAL_DENOMINATOR_MISMATCH")
    allowed = {row["ticker"] for row in originals}
    sessions = {item[0].isoformat() for item in calendar}
    mapped = {}
    for row in outcome_rows:
        if not isinstance(row, dict):
            raise ValueError("INVALID_OUTCOME_ROW")
        key = (row.get("ticker"), row.get("session_date"))
        if key[0] not in allowed or key[1] not in sessions or key in mapped:
            raise ValueError("DUPLICATE_OR_OUTSIDE_ORIGINAL_COHORT")
        mapped[key] = row

    rows = []
    for original in originals:
        ticker = original["ticker"]
        prefix_ok = True
        previous_close = None
        horizons = []
        for session in calendar:
            day = session[0].isoformat()
            source = mapped.get((ticker, day))
            if source is None:
                evidence = "MISSING_EOD_SOURCE_ROW"
                chain = "PREFIX_CENSORED_MISSING_OR_BLOCKED"
                prefix_ok = False
            elif not _source_chain_ok(source, session):
                evidence = "SUPPLIED_EOD_EVIDENCE_BLOCKED"
                chain = "PREFIX_CENSORED_MISSING_OR_BLOCKED"
                prefix_ok = False
            else:
                evidence = "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING"
                if not prefix_ok:
                    chain = "PRIOR_HORIZON_CENSORED"
                elif previous_close is not None and abs(
                        source["previous_regular_close"] - previous_close) > 0.005:
                    chain = "CROSS_SESSION_PRICE_CHAIN_MISMATCH"
                    prefix_ok = False
                else:
                    chain = "COMPLETE_PREFIX_UNAUTHENTICATED"
                    previous_close = source["regular_close"]
            horizons.append({"source_evidence": evidence, "chain_evidence": chain})
        rows.append({
            "ticker": ticker, "original_status": original["screen_status"],
            "original_price_only_watch":
                original["screen_status"] == "IEX_EARLY_WEAKNESS_WATCH_ONLY",
            "horizons": horizons,
        })
    return {
        "original_capture_universe_sha256": hashlib.sha256(raw).hexdigest(),
        "original_universe_count": len(originals),
        "provided_source_rows": len(outcome_rows),
        "rows": rows,
    }


def build(capture, calendar_rows, outcome_rows, as_of):
    """Audit every original issuer and all four exchange-session horizons.

    This is a source-coverage ledger, NOT an outcome scorer. Provider attestations
    in JSON cannot make a row VERIFIED; only a separate authenticated evidence
    pipeline could eventually supply that status.
    """
    now = asof(as_of)
    if now is None or now.utcoffset() is None:
        raise ValueError("EXPLICIT_TIMEZONE_AWARE_AS_OF_REQUIRED")
    manifest = json.loads((Path(capture) / "manifest.json").read_text(encoding="utf-8"))
    finished = asof(manifest.get("finished_at"))
    if finished is None or now < finished:
        raise ValueError("AS_OF_PRECEDES_ORIGINAL_CAPTURE_COMPLETION")
    preclose = manifest.get("status") == "IEX_PROSPECTIVE_SINGLE_VENUE_RAW_DISCOVERY_ONLY"
    coverage = (_audit_preclose(capture, calendar_rows, outcome_rows, manifest)
                if preclose else audit(capture, calendar_rows, outcome_rows))
    first_day = asof(manifest["started_at"]).astimezone(EASTERN).date()
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
            # A future or untimed source must never alter a historical as-of
            # inventory, including by leaking a future provider conflict.
            receipt_at = asof(source.get("collected_at")) if source is not None else None
            if now < close_at:
                category = "NOT_YET_MATURE"
                reason = "REGULAR_SESSION_CLOSE_IN_FUTURE"
            elif source is None:
                category = "CENSORED_MISSING"
                reason = "NO_SUPPLIED_OUTCOME_ROW"
            elif receipt_at is None or receipt_at > now:
                category = "CENSORED_BLOCKED"
                reason = "SOURCE_RECEIPT_MISSING_OR_AFTER_AS_OF"
            elif source.get("provider_conflict") is True:
                category = "SOURCE_CONFLICT"
                reason = "SUPPLIED_PROVIDER_CONFLICT_UNAUTHENTICATED"
            elif evidence == "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING":
                chain = original["horizons"][h].get("chain_evidence")
                if chain != "COMPLETE_PREFIX_UNAUTHENTICATED":
                    category = "CENSORED_BLOCKED"
                    reason = chain or "OUTCOME_PREFIX_NOT_VERIFIED"
                else:
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
        "capture_phase": "PRECLOSE" if preclose else manifest["phase"],
        "preclose_is_separate_unmatched_cohort": preclose,
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
