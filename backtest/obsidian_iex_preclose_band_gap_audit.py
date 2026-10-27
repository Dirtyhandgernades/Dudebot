"""Offline shadow audit of the immutable IEX preclose 15%-25% label gap.

RESEARCH_ONLY_NOT_AN_ORDER. NEVER changes the frozen raw capture or
relabels historical predictions. IEX reference changes are not official
closing-price outcomes, SIP, verified shortability or executable orders.
"""
import argparse
import hashlib
import json
from pathlib import Path

from backtest.obsidian_iex_prospective import verify as verify_preclose
from backtest.obsidian_prospective_capture import asof, finite_price, EASTERN

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
LEGACY_NO_WATCH = "IEX_NO_EARLY_PRICE_ONLY_WATCH"
SHADOW_LABEL = "SHADOW_INTERMEDIATE_15_TO_25_LEGACY_NO_WATCH"


def evaluate(capture):
    """Reproduce the original labels first; flag only verifiable label gaps."""
    root = Path(capture)
    checked = verify_preclose(root)
    manifest_bytes = (root / "manifest.json").read_bytes()
    raw = (root / "universe.jsonl").read_bytes()
    manifest = json.loads(manifest_bytes)
    records = [json.loads(line) for line in raw.splitlines()]
    if len(records) != checked["universe_count"]:
        raise ValueError("IMMUTABLE_PRE_CLOSE_DENOMINATOR_MISMATCH")
    started = asof(manifest["started_at"])
    finished = asof(manifest["finished_at"])
    if started is None or finished is None:
        raise ValueError("INVALID_CAPTURE_CLOCK")
    original_counts = manifest["status_counts"]
    gap = []
    for row in records:
        if row["screen_status"] != LEGACY_NO_WATCH:
            continue
        snap = row.get("snapshot")
        if not isinstance(snap, dict):
            continue
        trade = snap.get("latestTrade")
        prior = snap.get("prevDailyBar")
        if not isinstance(trade, dict) or not isinstance(prior, dict):
            continue
        price, reference = trade.get("p"), prior.get("c")
        trade_at = asof(trade.get("t"))
        received = asof(row.get("received_at"))
        if not finite_price(price) or not finite_price(reference) or trade_at is None or received is None:
            continue
        if not (started <= received <= finished and trade_at <= received):
            continue
        if received - trade_at > __import__("datetime").timedelta(minutes=15):
            continue
        # Compare only against IEX's own prior daily reference. This audit
        # NEVER substitutes it for an independently verified official close.
        change = price / reference - 1
        if not (-0.25 < change < -0.15):
            continue
        gap.append({
            "ticker": row["ticker"],
            "original_screen_status": LEGACY_NO_WATCH,
            "shadow_research_status": SHADOW_LABEL,
            "iex_reference_change_pct": round(change * 100, 6),
            "iex_last_trade_price": price,
            "iex_previous_daily_reference": reference,
            "iex_last_trade_at": trade_at.isoformat(),
            "capture_received_at": received.isoformat(),
            "indicative_both_prices_at_least_3": price >= 3 and reference >= 3,
            "verified_smg_eligible": False,
            "trade_authorized": False,
        })
    gap.sort(key=lambda x: x["ticker"])
    return {
        "mode": MODE,
        "audit": "IMMUTABLE_PRECLOSE_IEX_15_TO_25_LEGACY_LABEL_GAP_V1",
        "session_date_et": started.astimezone(EASTERN).date().isoformat(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "universe_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_capture_replay_verified": True,
        "captured_universe": len(records),
        "original_watch_count": original_counts.get("IEX_EARLY_WEAKNESS_WATCH_ONLY", 0),
        "original_no_watch_count": original_counts.get(LEGACY_NO_WATCH, 0),
        "shadow_intermediate_gap_count": len(gap),
        "gap_indicative_both_prices_at_least_3": sum(x["indicative_both_prices_at_least_3"] for x in gap),
        "shadow_only_not_a_retroactive_original_prediction": True,
        "independently_verified_regular_close_outcomes": None,
        "confirmed_future_20pct_early_hits": None,
        "conditional_precision": None,
        "conditional_recall": None,
        "verified_smg_eligible": None,
        "after_cost_pnl": None,
        "limitations": [
            "The preclose capture's frozen classifier watches -2% to -15% and marks <=-25% exhausted, but labels the intervening -15% to -25% range NO WATCH.",
            "This shadow report identifies a deterministic label gap; it never changes or upgrades original frozen predictions.",
            "IEX single-venue prior bar is not the independently corroborated official previous regular-session close.",
            "Fresh IEX prints and both prices >=$3 do not establish market cap, common-share class, borrow, liquidity, corporate actions, or SMG eligibility.",
            "No verified closing outcome, causal catalyst, lead-time advantage, or prediction performance is inferred.",
        ],
        "rows": gap,
    }


def main():
    parser = argparse.ArgumentParser(description="Offline immutable preclose label-gap audit")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as out:
        json.dump(evaluate(args.capture), out, sort_keys=True, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
