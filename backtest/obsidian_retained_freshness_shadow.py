"""Point-in-time *data quality* escalation for historically retained watchlists.

Research-only offline shadow. It does NOT imply a negative catalyst, predict
a future breakdown, infer SMG borrow, create alerts, or edit frozen captures.
Historical winner cases must NEVER be promoted into prior-time predictions.
"""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path

from backtest.obsidian_iex_capture_transitions import _load, compare
from backtest.obsidian_iex_research_discovery import EARLY_STATES
from backtest.obsidian_prospective_capture import asof

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "RETAINED_TICKER_MISSING_OR_STALE_SOURCE_REVIEW_V1"
UNUSABLE = frozenset({
    "STALE_OR_FUTURE_IEX_PRINT", "MISSING_IEX_SNAPSHOT",
    "MISSING_IEX_TRADE_OR_PREV_BAR", "UNVERIFIED_PREVIOUS_IEX_DAY",
    "INVALID_IEX_REFERENCE_PRICE", "INVALID_IEX_PREVIOUS_REFERENCE",
    "MALFORMED_IEX_SNAPSHOT",
})
EXHAUSTED = frozenset({"IEX_INDICATIVE_EXHAUSTED"})
FLOOR_BLOCK = frozenset({"INDICATIVE_PRICE_FLOOR_BLOCK"})


def review(morning_root, intraday_root, retained_records):
    """Deterministically queue all retained symbols with inadequate IEX data.

    Only the ORIGINAL as-of source statuses determine the result. This function
    cannot see later market outcomes, news, halt events, or known winners.
    """
    if not isinstance(retained_records, list):
        raise ValueError("RETAINED_WATCHLIST_REQUIRED")
    matched = compare(morning_root, intraday_root)
    mm, early, mm_hash = _load(morning_root)
    im, later, im_hash = _load(intraday_root)
    if (mm_hash != matched["morning_universe_sha256"] or
            im_hash != matched["intraday_universe_sha256"]):
        raise ValueError("ORIGINAL_CAPTURE_HASH_MISMATCH")
    if mm.get("phase") != "MORNING" or im.get("phase") != "INTRADAY":
        raise ValueError("UNEXPECTED_PHASE")
    expected = {entry["ticker"]: entry for entry in matched["full_unselected_union_ledger"]}
    retained = {}
    for item in retained_records:
        if not isinstance(item,dict):
            raise ValueError("INVALID_RETAINED_RECORD")
        ticker = item.get("ticker")
        if not isinstance(ticker,str) or not ticker.strip():
            raise ValueError("INVALID_RETAINED_TICKER")
        ticker=ticker.upper().strip()
        retained.setdefault(ticker,0)
        retained[ticker]+=1
    results=[]
    counts=Counter()
    for ticker in sorted(retained):
        m=early.get(ticker)
        i=later.get(ticker)
        old=expected.get(ticker)
        first=m.get("indicative_status") if m else "NOT_IN_MORNING_UNIVERSE"
        second=i.get("indicative_status") if i else "NOT_IN_INTRADAY_UNIVERSE"
        if old is not None and (old["morning_status"]!=first or old["intraday_status"]!=second):
            raise ValueError("SOURCE_STATUS_CHANGED")
        missing_m=first == "NOT_IN_MORNING_UNIVERSE"
        missing_i=second == "NOT_IN_INTRADAY_UNIVERSE"
        def unusable(status):
            return status in UNUSABLE or status.startswith("NOT_IN_")
        if missing_m and missing_i:
            status="SOURCE_UNIVERSE_ABSENT_BOTH"
        elif first in EXHAUSTED or second in EXHAUSTED:
            status="EXHAUSTED_IEX_REFERENCE_NOT_EARLY_CREDIT"
        elif first in FLOOR_BLOCK or second in FLOOR_BLOCK:
            status="BELOW_FLOOR_INDICATIVE_NOT_EXECUTABLE"
        elif first in EARLY_STATES or second in EARLY_STATES:
            status="ORIGINAL_PRICE_WATCH_NOT_A_TRADE"
        elif unusable(first) and unusable(second):
            status="PERSISTENT_DATA_GAP_REQUIRES_FRESH_SECOND_VENUE"
        elif unusable(first) or unusable(second):
            status="ONE_CHECKPOINT_DATA_GAP_REQUIRES_REVIEW"
        else:
            status="OBSERVED_NO_IEX_PRICE_WATCH"
        review_needed=status in {
            "SOURCE_UNIVERSE_ABSENT_BOTH",
            "PERSISTENT_DATA_GAP_REQUIRES_FRESH_SECOND_VENUE",
            "ONE_CHECKPOINT_DATA_GAP_REQUIRES_REVIEW",
        }
        first_problem=(not missing_m and first in UNUSABLE) or missing_m
        earliest_not_before=(mm["finished_at"] if first_problem else
                             im["finished_at"] if unusable(second) else None)
        raw_asset=(i or m or {}).get("asset") or {}
        def last_trade(row):
            snap=row.get("snapshot") if isinstance(row,dict) else None
            trade=snap.get("latestTrade") if isinstance(snap,dict) else None
            raw=trade.get("t") if isinstance(trade,dict) else None
            seen=asof(raw)
            return seen.isoformat() if seen else None
        counts[status]+=1
        results.append({
            "ticker":ticker,
            "original_morning_status":first,
            "original_intraday_status":second,
            "original_reference_capture_verified":True,
            "first_source_review_no_earlier_than":earliest_not_before,
            "independent_fresh_venue_quote_required":review_needed,
            "original_morning_last_iex_trade_at":last_trade(m),
            "original_intraday_last_iex_trade_at":last_trade(i),
            "provider_reported_shortable":raw_asset.get("shortable"),
            "provider_reported_borrow_status":raw_asset.get("borrow_status"),
            "actual_smg_platform_short_verified":False,
            "trade_authorized":False,
            "bearish_prediction_was_made":False,
            "future_collapse_credit":False,
            "status":status,
        })
    return {
        "policy":POLICY,"mode":MODE,
        "session_date":matched["session_date"],
        "retained_unique_symbols":len(retained),
        "retained_duplicate_inputs":sum(v-1 for v in retained.values()),
        "original_morning_universe_sha256":mm_hash,
        "original_intraday_universe_sha256":im_hash,
        "original_capture_denominator":matched["counts"]["union_symbols"],
        "original_watch_labels_modified":False,
        "review_needed_symbols":sum(x["independent_fresh_venue_quote_required"] for x in results),
        "statuses":dict(sorted(counts.items())),
        "followup_requires_independently_collected_second_venue_asof":True,
        "no_outcomes_or_trades_claimed":True,
        "rows":results,
    }


def main():
    p=argparse.ArgumentParser(description="Stale retained symbols quality queue; no trading")
    p.add_argument("--morning",required=True)
    p.add_argument("--intraday",required=True)
    p.add_argument("--master",required=True)
    p.add_argument("--supplemental",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    master=json.loads(Path(args.master).read_text(encoding="utf-8"))["records"]
    extra=json.loads(Path(args.supplemental).read_text(encoding="utf-8"))["records"]
    report=review(args.morning,args.intraday,master+extra)
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(report,f,sort_keys=True,indent=2)
        f.write("\n")
    print(json.dumps({k:report[k] for k in ("policy","retained_unique_symbols",
                                          "review_needed_symbols","statuses")},sort_keys=True))


if __name__=="__main__":
    main()
