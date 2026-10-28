"""Read-only matched original IEX cohort ledger; never a performance scorer.

RESEARCH_ONLY_NOT_AN_ORDER. Original morning/intraday raw captures are
independently hash-verified by the existing transition audit. Every union
symbol is retained once, including stale, unselected and absent observations.
A newly visible IEX watch is NOT necessarily a new price breakdown.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from backtest.obsidian_iex_capture_transitions import compare
from backtest.obsidian_iex_research_discovery import EARLY_STATES
from backtest.obsidian_prospective_capture import asof

POLICY = "OBSIDIAN_MATCHED_UNTOUCHED_IEX_COHORT_LOCK_V1_2026_10_28"
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"


def lock(morning_root, intraday_root):
    transition = compare(morning_root, intraday_root)
    morning = json.loads((Path(morning_root) / "manifest.json").read_text())
    intraday = json.loads((Path(intraday_root) / "manifest.json").read_text())
    m_finished = asof(morning.get("finished_at"))
    i_finished = asof(intraday.get("finished_at"))
    if m_finished is None or i_finished is None or m_finished >= i_finished:
        raise ValueError("INVALID_CAPTURE_DECISION_TIMESTAMPS")
    if (morning.get("phase"), intraday.get("phase")) != ("MORNING", "INTRADAY"):
        raise ValueError("INVALID_CAPTURE_PHASES")
    original = transition["full_unselected_union_ledger"]
    if len(original) != transition["counts"]["union_symbols"]:
        raise ValueError("UNION_DENOMINATOR_MISMATCH")
    seen = set()
    counts = Counter()
    rows = []
    for item in original:
        ticker = item["ticker"]
        if not isinstance(ticker, str) or not ticker or ticker in seen:
            raise ValueError("DUPLICATE_OR_INVALID_ORIGINAL_TICKER")
        seen.add(ticker)
        m_status, i_status = item["morning_status"], item["intraday_status"]
        m_present = m_status != "NOT_IN_MORNING_UNIVERSE"
        i_present = i_status != "NOT_IN_INTRADAY_UNIVERSE"
        m_watch, i_watch = m_status in EARLY_STATES, i_status in EARLY_STATES
        counts["union_symbols"] += 1
        counts["morning_present"] += int(m_present)
        counts["intraday_present"] += int(i_present)
        counts["morning_watches"] += int(m_watch)
        counts["intraday_watches"] += int(i_watch)
        if not m_present or not i_present:
            matching = "UNMATCHED_CAPTURE_UNIVERSE"
        elif item["same_asset_id"] is not True:
            matching = "QUARANTINED_SECURITY_IDENTITY_CHANGE"
        elif item["same_iex_previous_bar"] is not True:
            matching = "QUARANTINED_REFERENCE_CHANGE_OR_MISSING"
        else:
            matching = "SAME_IEX_ASSET_AND_REFERENCE_ONLY"
        counts[matching] += 1
        phase = "MORNING" if m_watch else "INTRADAY" if i_watch else None
        if phase is None:
            onset = "NOT_WATCHED"
        elif phase == "MORNING":
            onset = "MORNING_PRICE_ONLY_WATCH"
        elif item["transition"] == "NEW_COMPARABLE_IEX_THRESHOLD_CROSSING":
            onset = "NEW_COMPARABLE_INTRADAY_IEX_THRESHOLD_CROSSING"
        else:
            onset = "INTRADAY_VISIBLE_ONSET_NOT_ESTABLISHED"
        counts["any_original_price_watch"] += int(phase is not None)
        counts["first_morning_price_watch"] += int(phase == "MORNING")
        counts["first_intraday_price_watch"] += int(phase == "INTRADAY")
        decision_at = (m_finished if phase == "MORNING" else
                       i_finished if phase == "INTRADAY" else None)
        rows.append({
            "ticker": ticker,
            "morning_original_status": m_status,
            "intraday_original_status": i_status,
            "source_transition": item["transition"],
            "matched_source_status": matching,
            "first_original_watch_phase": phase,
            "first_original_watch_decision_not_before": (
                decision_at.isoformat() if decision_at else None),
            "watch_onset_interpretation": onset,
            "official_prior_close_verified": False,
            "official_future_regular_close_verified": False,
            "actual_smg_short_eligibility_verified": False,
            "automatically_scoreable": False,
            "trade_authorized": False,
        })
    if (counts["morning_watches"] != transition["counts"]["morning_watches"]
            or counts["intraday_watches"] != transition["counts"]["intraday_watches"]
            or counts["union_symbols"] != transition["counts"]["union_symbols"]):
        raise ValueError("ORIGINAL_CAPTURE_WATCH_COUNTS_CHANGED")
    return {
        "policy": POLICY, "mode": MODE,
        "session_date": transition["session_date"],
        "morning_original_universe_sha256": transition["morning_universe_sha256"],
        "intraday_original_universe_sha256": transition["intraday_universe_sha256"],
        "morning_decision_not_before": m_finished.isoformat(),
        "intraday_decision_not_before": i_finished.isoformat(),
        "counts": dict(sorted(counts.items())),
        "original_union_denominator_retained": True,
        "correlated_scans_counted_as_independent_events": False,
        "externally_verified_outcome_rows": 0,
        "precision": None, "recall": None, "after_cost_pnl": None,
        "matched_outcome_scoring_enabled": False,
        "limitations": [
            "IEX single-venue previous bar and last print are not official exchange closes.",
            "No authentic independently sourced post-close and corporate-action proof was supplied.",
            "Original watch labels are not reclassified or tuned after observing outcomes.",
            "Different IEX asset IDs or prior bars prohibit comparable same-security onset claims.",
            "Missing or stale source observations remain in the original union denominator.",
            "No actual SMG platform borrow, fills, execution, predictive edge or trades verified.",
        ],
        "full_original_union_rows": rows,
    }


def main():
    ap = argparse.ArgumentParser(description="Immutable matched IEX cohort lock, research only")
    ap.add_argument("--morning", required=True)
    ap.add_argument("--intraday", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as f:
        json.dump(lock(args.morning, args.intraday), f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
