"""Offline, point-in-time OBSIDIAN prospective outcome audit (research only).

Scores an independently captured, immutable preclose universe against later
regular-session closes. This measures PRICE-ONLY discovery, not eligible SMG
trade recall or executable performance. Never backfills missing captures.
"""
import argparse
import json
from collections import Counter
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from backtest.obsidian_prospective_capture import asof, finite_price
from backtest.obsidian_prospective_verify import verify_capture, jsonl

ET = ZoneInfo("America/New_York")
THRESHOLD = -0.20


class InvalidOutcome(ValueError):
    pass


def evaluate(capture_dir, outcome_file):
    verification = verify_capture(capture_dir)
    root = Path(capture_dir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    _, universe = jsonl(root / "universe.jsonl")
    _, candidates = jsonl(root / "candidates.jsonl")
    _, outcomes = jsonl(Path(outcome_file))
    session = asof(manifest["capture_started_at"]).astimezone(ET).date()
    finished = asof(manifest["capture_finished_at"])
    symbols = {row["ticker"] for row in universe}
    watched = {row["ticker"] for row in candidates}
    seen = set()
    outcome_by_symbol = {}
    for row in outcomes:
        symbol = row.get("ticker")
        if symbol not in symbols or symbol in seen:
            raise InvalidOutcome("DUPLICATE_OR_OUT_OF_UNIVERSE_OUTCOME")
        seen.add(symbol)
        outcome_by_symbol[symbol] = row
    counts = Counter()
    details = []
    for item in universe:
        symbol = item["ticker"]
        outcome = outcome_by_symbol.get(symbol)
        status = "OUTCOME_MISSING"
        change = None
        if outcome is not None:
            prior, close = outcome.get("previous_regular_close"), outcome.get("regular_close")
            close_at = asof(outcome.get("close_at"))
            collected = asof(outcome.get("collected_at"))
            previous_day = outcome.get("previous_session_date")
            source = outcome.get("source_url")
            expected_previous = session - timedelta(days=1)
            while expected_previous.weekday() >= 5:
                expected_previous -= timedelta(days=1)
            # Fail closed for unsupported holidays, splits, conflicting providers,
            # unverified prior close or any future/after-hours quote substituted
            # for the regular-session close.
            valid = (outcome.get("verified") is True
                     and outcome.get("regular_session") is True
                     and outcome.get("corporate_actions_clear") is True
                     and outcome.get("provider_conflict") is False
                     and isinstance(source, str) and source.startswith("https://")
                     and finite_price(prior) and finite_price(close)
                     and previous_day == expected_previous.isoformat()
                     and close_at is not None and collected is not None
                     and close_at.astimezone(ET).date() == session
                     and close_at.astimezone(ET).hour == 16
                     and close_at.astimezone(ET).minute == 0
                     and finished < close_at <= collected)
            if valid:
                change = close / prior - 1
                status = "VERIFIED_COLLAPSE_20_PLUS" if change <= THRESHOLD else "VERIFIED_NON_COLLAPSE"
            else:
                status = "OUTCOME_UNVERIFIED_OR_CONFLICTED"
        counts[status] += 1
        if status.startswith("VERIFIED_"):
            counts["VERIFIED_WATCH" if symbol in watched else "VERIFIED_NONWATCH"] += 1
            counts["WATCH_COLLAPSE" if symbol in watched and change <= THRESHOLD else
                   "NONWATCH_COLLAPSE" if change <= THRESHOLD else
                   "WATCH_NONCOLLAPSE" if symbol in watched else "NONWATCH_NONCOLLAPSE"] += 1
        details.append({"ticker": symbol, "preclose_price_only_watch": symbol in watched,
                        "preclose_screen_status": item["screen_status"],
                        "outcome_status": status, "prior_close_return": change})
    verified = counts["VERIFIED_COLLAPSE_20_PLUS"] + counts["VERIFIED_NON_COLLAPSE"]
    collapse = counts["VERIFIED_COLLAPSE_20_PLUS"]
    return {
        "status": "PROSPECTIVE_PRICE_ONLY_DISCOVERY_AUDIT_NOT_TRADE_VALIDATION",
        "research_only": True, "trade_authorized": False,
        "capture_screen_id": verification["screen_id"],
        "capture_finished_at": manifest["capture_finished_at"],
        "universe_count": len(universe), "watch_count": len(watched),
        "outcomes_verified": verified,
        "outcomes_missing_or_censored": len(universe) - verified,
        "verified_collapse_count": collapse,
        "price_only_watch_collapse_count": counts["WATCH_COLLAPSE"],
        "price_only_watch_noncollapse_count": counts["WATCH_NONCOLLAPSE"],
        "unwatched_verified_collapse_count": counts["NONWATCH_COLLAPSE"],
        "price_only_recall_conditional_on_verified_outcomes":
            counts["WATCH_COLLAPSE"] / collapse if collapse else None,
        "price_only_precision_conditional_on_verified_outcomes":
            counts["WATCH_COLLAPSE"] /
            (counts["WATCH_COLLAPSE"] + counts["WATCH_NONCOLLAPSE"])
            if counts["WATCH_COLLAPSE"] + counts["WATCH_NONCOLLAPSE"] else None,
        "counts": dict(counts), "details": details,
        "smg_eligible_recall": None, "verified_lead_time": None,
        "after_cost_pnl": None, "false_positive_rate_full_eligible_universe": None,
        "limitations": [
            "Only symbols present in an authenticated preclose capture are scored.",
            "Price-only watches are blocked research observations, not confirmed setups.",
            "Missing/conflicted outcome bars remain censored, never counted as negatives.",
            "No verified common-stock, borrow, cap, liquidity, halt or SMG eligibility denominator.",
            "No after-cost P&L, fills, lead time, or demonstrated predictive edge.",
            "No outcome data may change frozen preclose candidates or thresholds.",
        ],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--capture", required=True)
    p.add_argument("--outcomes", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as f:
        json.dump(evaluate(args.capture, args.outcomes), f, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
