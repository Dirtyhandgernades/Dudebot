"""Frozen forward study of IEX research watches vs later regular-session closes.

RESEARCH_ONLY_NOT_AN_ORDER. Scoring requires verified write-once raw discovery,
independently corroborated regular-session closing prices, and explicitly
reviewed comparable shareholder entitlements. No API calls or orders.

This is an indicator study of single-venue OBSIDIAN research WATCHES, not
proof of SMG short eligibility, fills, profit or a validated predictive edge.
"""
import argparse
from collections import Counter
from datetime import timedelta
import hashlib
import json
from pathlib import Path

from backtest.obsidian_iex_research_discovery import verify, EARLY_STATES
from backtest.obsidian_iex_outcomes import corroborated
from backtest.obsidian_iex_corporate_actions import no_action_comparable
from backtest.obsidian_prospective_capture import asof, finite_price, EASTERN

POLICY = "OBSIDIAN_IEX_FORWARD_20PCT_EARLY_HALF_REMAINING_V1_2026_10_27"
TARGET_DROP_FRACTION = 0.20
MIN_REMAINING_FRACTION = 0.50
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
VALID_PHASES = frozenset(("MORNING", "INTRADAY"))
NONPREDICTIVE_PHASE = "AFTERHOURS"


def load_outcomes(path):
    """Explicit input rows, no synthetic missing values or automatic sources."""
    if path is None:
        return {}, None
    raw = Path(path).read_bytes()
    rows = {}
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            raise ValueError("EMPTY_OUTCOME_ROW_" + str(lineno))
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError("INVALID_OUTCOME_ROW")
        symbol = item.get("ticker")
        if not isinstance(symbol, str) or not symbol.strip() or symbol in rows:
            raise ValueError("DUPLICATE_OR_INVALID_OUTCOME_SYMBOL")
        rows[symbol] = item
    return rows, hashlib.sha256(raw).hexdigest()


def previous_weekday(session):
    previous = session - timedelta(days=1)
    while previous.weekday() >= 5:
        previous -= timedelta(days=1)
    return previous


def valid_closes(outcome, symbol, previous, session, capture_finished):
    if not isinstance(outcome, dict) or outcome.get("ticker") != symbol:
        return False
    close = outcome.get("regular_close")
    prior = outcome.get("previous_regular_close")
    at = asof(outcome.get("close_at"))
    collected = asof(outcome.get("collected_at"))
    if not finite_price(close) or not finite_price(prior) or at is None or collected is None:
        return False
    if (outcome.get("verified") is not True or
            outcome.get("provider_conflict") is not False or
            outcome.get("regular_session") is not True or
            outcome.get("previous_session_date") != previous.isoformat() or
            outcome.get("corporate_actions_clear") is not True):
        return False
    if not isinstance(outcome.get("source_url"), str) or not outcome["source_url"].startswith("https://"):
        return False
    local = at.astimezone(EASTERN)
    if local.date() != session or (local.hour, local.minute) != (16, 0):
        return False
    if not (capture_finished < at <= collected):
        return False
    if not corroborated(outcome, at, collected):
        return False
    if not no_action_comparable(outcome, previous, session, at, collected):
        return False
    return True


def valid_tape(row, captured_at, close_at):
    """Prospective IEX trade freshness, not an executable or consolidated quote."""
    if row.get("indicative_status") in {
        "STALE_OR_FUTURE_IEX_PRINT", "UNVERIFIED_PREVIOUS_IEX_DAY",
        "MISSING_IEX_SNAPSHOT", "MISSING_IEX_TRADE_OR_PREV_BAR",
        "INVALID_IEX_REFERENCE_PRICE", "INVALID_IEX_PREVIOUS_REFERENCE",
        "MALFORMED_IEX_SNAPSHOT"}:
        return None
    snap = row.get("snapshot")
    trade = snap.get("latestTrade") if isinstance(snap, dict) else None
    if not isinstance(trade, dict):
        return None
    traded_at = asof(trade.get("t"))
    price = trade.get("p")
    received = asof(row.get("received_at"))
    if not finite_price(price) or traded_at is None or received is None:
        return None
    if not (traded_at <= received <= captured_at < close_at):
        return None
    if received - traded_at > timedelta(minutes=15):
        return None
    return price, traded_at


def evaluate(capture, outcomes_file=None):
    checked = verify(capture)  # replays hashes, all 8K+ rows, timestamps
    root = Path(capture)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    phase = manifest["phase"]
    if phase not in VALID_PHASES | {NONPREDICTIVE_PHASE}:
        raise ValueError("INVALID_RESEARCH_PHASE")
    universe_bytes = (root / "universe.jsonl").read_bytes()
    records = [json.loads(x) for x in universe_bytes.splitlines()]
    if len(records) != checked["universe_count"]:
        raise ValueError("UNIVERSE_REPLAY_MISMATCH")
    outcomes, outcomes_sha = load_outcomes(outcomes_file)
    universe = {row["ticker"] for row in records}
    if set(outcomes) - universe:
        raise ValueError("OUTCOME_OUTSIDE_IMMUTABLE_UNIVERSE")
    start = asof(manifest["started_at"])
    finish = asof(manifest["finished_at"])
    session = start.astimezone(EASTERN).date()
    previous = previous_weekday(session)
    close_at = start.astimezone(EASTERN).replace(hour=16, minute=0, second=0, microsecond=0)
    if phase in VALID_PHASES and finish >= close_at:
        raise ValueError("CAPTURE_NOT_BEFORE_REGULAR_CLOSE")
    counters = Counter()
    output = []
    for row in records:
        symbol = row["ticker"]
        status = row["indicative_status"]
        flagged = status in EARLY_STATES
        outcome = outcomes.get(symbol)
        result = {
            "ticker": symbol, "source_lane": status,
            "captured_phase": phase, "iex_research_watch": flagged,
            "official_regular_close_return_pct": None,
            "fraction_of_final_drop_remaining_at_capture": None,
            "prediction_status": "UNSCORED_NO_INDEPENDENT_OUTCOME",
            "smg_platform_short_verified": False,
            "executable_signal": False,
        }
        counters["scanned_symbols"] += 1
        counters["raw_iex_watches"] += int(flagged)
        if phase == NONPREDICTIVE_PHASE:
            result["prediction_status"] = "POST_CLOSE_OBSERVATION_CANNOT_PREDICT_SAME_DAY"
            counters["excluded_post_close"] += 1
            output.append(result)
            continue
        if outcome is None:
            counters["missing_outcome"] += 1
            output.append(result)
            continue
        if not valid_closes(outcome, symbol, previous, session, finish):
            result["prediction_status"] = "CENSORED_UNVERIFIED_CLOSE_OR_CORPORATE_ACTION"
            counters["censored_unverified_outcome"] += 1
            output.append(result)
            continue
        prior, close = outcome["previous_regular_close"], outcome["regular_close"]
        pct = 100 * (close / prior - 1)
        event = close <= prior * (1 - TARGET_DROP_FRACTION)
        result["official_regular_close_return_pct"] = round(pct, 6)
        result["prediction_status"] = "NON_COLLAPSE" if not event else "COLLAPSE_OUTCOME_VERIFIED"
        counters["verified_outcomes"] += 1
        tape = valid_tape(row, finish, close_at)
        if tape is None:
            counters["unusable_preclose_tape"] += 1
            if event:
                counters["collapses_without_usable_tape"] += 1
                result["prediction_status"] = "COLLAPSE_BUT_TIMING_TAPE_UNAVAILABLE"
            output.append(result)
            continue
        tape_price, tape_at = tape
        result["iex_last_trade_at"] = tape_at.isoformat()
        result["iex_last_trade_price"] = tape_price
        counters["verified_outcomes_with_usable_tape"] += 1
        if not event:
            counters["watched_noncollapses"] += int(flagged)
            output.append(result)
            continue
        counters["verified_20pct_regular_close_collapses"] += 1
        full_drop = prior - close
        remaining = (tape_price - close) / full_drop
        result["fraction_of_final_drop_remaining_at_capture"] = round(remaining, 6)
        if flagged and remaining >= MIN_REMAINING_FRACTION:
            result["prediction_status"] = "EARLY_IEX_WATCH_BEFORE_HALF_OF_DECLINE"
            counters["early_iex_watch_hits"] += 1
        elif flagged:
            result["prediction_status"] = "LATE_IEX_WATCH_AFTER_MOST_OF_DECLINE"
            counters["late_iex_watch_not_credited"] += 1
        else:
            result["prediction_status"] = "COLLAPSE_NOT_EARLY_WATCHED"
            counters["unwatched_collapses"] += 1
        output.append(result)
    verified = counters["verified_outcomes_with_usable_tape"]
    collapses = counters["verified_20pct_regular_close_collapses"]
    watches_scored = (counters["early_iex_watch_hits"] +
                      counters["late_iex_watch_not_credited"] +
                      counters["watched_noncollapses"])
    complete = len(outcomes) > 0 and phase in VALID_PHASES
    return {
        "study_id": POLICY,
        "mode": MODE,
        "capture_sha256": hashlib.sha256(universe_bytes).hexdigest(),
        "raw_capture_manifest_sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
        "outcomes_input_sha256": outcomes_sha,
        "session_date": session.isoformat(), "phase": phase,
        "source": "IEX_SINGLE_VENUE_NOT_SIP_OR_OFFICIAL_CLOSE",
        "target": "SAME_SESSION_REGULAR_1600_ET_CLOSE_DOWN_AT_LEAST_20PCT_FROM_PREVIOUS_REGULAR_CLOSE",
        "early_rule": "RAW_IEX_EARLY_OR_INTERMEDIATE_WATCH_AND_AT_LEAST_HALF_OF_FINAL_DROP_STILL_REMAINED",
        "fraction_remaining_required": MIN_REMAINING_FRACTION,
        "outcome_rows_supplied": len(outcomes),
        "counts": {key: counters[key] for key in (
            "scanned_symbols", "raw_iex_watches", "excluded_post_close",
            "missing_outcome", "censored_unverified_outcome",
            "verified_outcomes", "verified_outcomes_with_usable_tape",
            "unusable_preclose_tape", "collapses_without_usable_tape",
            "verified_20pct_regular_close_collapses", "early_iex_watch_hits",
            "late_iex_watch_not_credited", "unwatched_collapses",
            "watched_noncollapses")},
        "conditional_early_recall": (counters["early_iex_watch_hits"] / collapses
                                     if complete and collapses else None),
        "conditional_early_precision": (counters["early_iex_watch_hits"] / watches_scored
                                        if complete and watches_scored else None),
        "verified_smg_eligible_recall": None,
        "after_cost_pnl": None, "actual_trades": None,
        "no_outcome_yet_is_not_strategy_failure": True,
        "unverified_outcomes_are_never_assumed_noncollapses": True,
        "untouched_future_prediction_edge_established": False,
        "limitations": [
            "Watch is a frozen price-only IEX-reference label, not a vetted mechanism/tape/borrow short.",
            "Previous IEX daily price is not an official previous regular-session close.",
            "Half-drop-remaining is a prospective timing definition, not a tested or optimized profit threshold.",
            "Morning and intraday reports are correlated if they cover the same issuer/session; do not count as independent cases.",
            "Post-close snapshots cannot score same-day predictions.",
            "Only independently verified corporate-action-comparable official closes are scored.",
            "Censored and missing bar outcomes remain in denominator accounting.",
            "Common stock, market cap, platform borrow, liquidity, execution and costs remain unverified.",
            "No proof of positive predictive advantage or usable trade exists without forward verified outcomes.",
        ],
        "rows": output,
    }


def main():
    parser = argparse.ArgumentParser(description="Offline forward research study, not a trade system")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--outcomes", help="Independent completed-session JSONL; omit until available")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Write once so repeated scoring cannot quietly overwrite existing study.
    with destination.open("x", encoding="utf-8") as f:
        json.dump(evaluate(args.capture, args.outcomes), f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
