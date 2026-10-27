"""Audit source-limited IEX watch transitions across immutable same-day captures.

RESEARCH_ONLY_NOT_AN_ORDER. A newly observed price-reference watch is NOT a
prospective 20% collapse prediction, a full-market signal or an SMG short.
"""
import argparse
from collections import Counter
from datetime import timedelta
import hashlib
import json
from pathlib import Path

from backtest.obsidian_iex_research_discovery import EARLY_STATES, verify
from backtest.obsidian_prospective_capture import asof, EASTERN

POLICY = "OBSIDIAN_IEX_IMMUTABLE_MORNING_TO_INTRADAY_TRANSITIONS_V1"
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
OTHER = "IEX_INDICATIVE_OTHER"


def _load(root):
    root = Path(root)
    proof = verify(root)
    raw = (root / "universe.jsonl").read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    if len(rows) != proof["universe_count"]:
        raise ValueError("IMMUTABLE_CAPTURE_DENOMINATOR_MISMATCH")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    return manifest, {r["ticker"]: r for r in rows}, hashlib.sha256(raw).hexdigest()


def _prior(row):
    snap = row.get("snapshot")
    bar = snap.get("prevDailyBar") if isinstance(snap, dict) else None
    if not isinstance(bar, dict):
        return None
    value, timestamp = bar.get("c"), bar.get("t")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        return None
    if asof(timestamp) is None:
        return None
    return value, timestamp


def compare(morning_root, intraday_root):
    before, morning, morning_sha = _load(morning_root)
    after, intraday, intraday_sha = _load(intraday_root)
    t0, t1 = asof(before.get("started_at")), asof(after.get("started_at"))
    e0, e1 = asof(before.get("finished_at")), asof(after.get("finished_at"))
    if (t0 is None or t1 is None or e0 is None or e1 is None
            or before.get("phase") != "MORNING" or after.get("phase") != "INTRADAY"
            or not t0 <= e0 < t1 <= e1
            or t0.astimezone(EASTERN).date() != t1.astimezone(EASTERN).date()):
        raise ValueError("INVALID_OR_OVERLAPPING_SAME_SESSION_PHASES")
    for key in ("feed", "provider_scope", "snapshot_source", "asset_source"):
        if before.get(key) != after.get(key):
            raise ValueError("MISMATCHED_CAPTURE_SOURCE_" + key)
    if before.get("feed") != "iex":
        raise ValueError("NOT_SINGLE_VENUE_IEX")
    if before.get("full_market_coverage_confirmed") is not False or after.get("full_market_coverage_confirmed") is not False:
        raise ValueError("INVALID_FULL_MARKET_COVERAGE_CLAIM")

    counts = Counter()
    transitions = []
    for symbol in sorted(set(morning) | set(intraday)):
        old = morning.get(symbol)
        new = intraday.get(symbol)
        old_state = old.get("indicative_status") if old else "NOT_IN_MORNING_UNIVERSE"
        new_state = new.get("indicative_status") if new else "NOT_IN_INTRADAY_UNIVERSE"
        old_watch = old_state in EARLY_STATES
        new_watch = new_state in EARLY_STATES
        counts["union_symbols"] += 1
        counts["morning_watches"] += int(old_watch)
        counts["intraday_watches"] += int(new_watch)
        counts["added_symbols"] += int(old is None)
        counts["removed_symbols"] += int(new is None)

        identity_same = (old is not None and new is not None
                         and old["asset"].get("id") is not None
                         and old["asset"].get("id") == new["asset"].get("id"))
        ref0 = _prior(old) if old else None
        ref1 = _prior(new) if new else None
        reference_same = ref0 is not None and ref1 is not None and ref0 == ref1
        if old and new and ref0 is not None and ref1 is not None and not reference_same:
            counts["previous_iex_reference_changed"] += 1
        if old and new and not identity_same:
            counts["security_identity_changed"] += 1

        if old_watch and new_watch:
            category = "PERSISTENT_PRICE_ONLY_WATCH" if identity_same and reference_same else "PERSISTENT_BUT_SOURCE_NOT_COMPARABLE"
            counts["persistent_watches"] += 1
        elif not old_watch and new_watch:
            if old is None:
                category = "ADDED_TO_UNIVERSE_NOT_PROVEN_NEW_SIGNAL"
            elif not identity_same:
                category = "CHANGED_SECURITY_IDENTITY_NOT_COMPARABLE"
            elif old_state == OTHER and reference_same:
                category = "NEW_COMPARABLE_IEX_THRESHOLD_CROSSING"
                counts["new_comparable_crossings"] += 1
            elif old_state == OTHER:
                category = "PRIOR_IEX_REFERENCE_CHANGED_NOT_COMPARABLE"
            else:
                category = "PREVIOUSLY_UNUSABLE_OR_BLOCKED_NOT_NEW_ONSET"
                counts["newly_visible_after_unusable"] += 1
            counts["new_watch_labels"] += 1
        elif old_watch and not new_watch:
            category = "WATCH_DROPPED_OR_UNOBSERVABLE"
            counts["dropped_watch_labels"] += 1
            counts["dropped_to_other"] += int(new_state == OTHER)
            counts["dropped_to_stale"] += int(new_state == "STALE_OR_FUTURE_IEX_PRINT")
            counts["dropped_to_exhausted"] += int(new_state == "IEX_INDICATIVE_EXHAUSTED")
        else:
            category = "NOT_A_WATCH_AT_EITHER_CAPTURE"
        counts[category] += 1
        transitions.append({
            "ticker": symbol,
            "morning_status": old_state,
            "intraday_status": new_state,
            "morning_iex_reference_change_pct": old.get("iex_reference_change_pct") if old else None,
            "intraday_iex_reference_change_pct": new.get("iex_reference_change_pct") if new else None,
            "same_asset_id": identity_same if old and new else None,
            "same_iex_previous_bar": reference_same if old and new else None,
            "transition": category,
            "iex_only_not_official_close": True,
            "smg_executable": False,
        })
    if counts["morning_watches"] != sum(before["status_counts"].get(s, 0) for s in EARLY_STATES):
        raise ValueError("MORNING_WATCH_LEDGER_MISMATCH")
    if counts["intraday_watches"] != sum(after["status_counts"].get(s, 0) for s in EARLY_STATES):
        raise ValueError("INTRADAY_WATCH_LEDGER_MISMATCH")
    if counts["intraday_watches"] != counts["persistent_watches"] + counts["new_watch_labels"]:
        raise ValueError("INTRADAY_TRANSITION_RECONCILIATION_FAILED")
    if counts["morning_watches"] != counts["persistent_watches"] + counts["dropped_watch_labels"]:
        raise ValueError("MORNING_TRANSITION_RECONCILIATION_FAILED")
    return {
        "policy": POLICY, "mode": MODE,
        "morning_universe_sha256": morning_sha, "intraday_universe_sha256": intraday_sha,
        "morning_capture_at": before["started_at"], "intraday_capture_at": after["started_at"],
        "session_date": t0.astimezone(EASTERN).date().isoformat(),
        "counts": dict(sorted(counts.items())),
        "full_unselected_union_ledger": transitions,
        "verified_regular_close_outcomes": None,
        "prospective_20pct_collapse_predictions_proven": False,
        "conditional_recall": None, "conditional_precision": None,
        "after_cost_pnl": None, "smg_eligible_trades": None,
        "limitations": [
            "Threshold crossings are IEX single-venue price-reference movements, not independently confirmed official regular-session declines.",
            "Previously stale or missing observations are never relabeled as a newly discovered deterioration.",
            "Changing IEX previous bars or asset identities blocks comparable transition claims.",
            "All source captures remain immutable and their full attempted-universe denominators are preserved.",
            "No 20% future collapse, market-wide recall, borrow availability, trade or positive edge is established.",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description="Offline immutable research-only IEX transition audit")
    ap.add_argument("--morning", required=True)
    ap.add_argument("--intraday", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8") as handle:
        json.dump(compare(args.morning, args.intraday), handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
