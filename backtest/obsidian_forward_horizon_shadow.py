"""New, separately registered 1-to-3 trading-session OBSIDIAN shadow study.

RESEARCH_ONLY_NOT_AN_ORDER. Does NOT alter frozen October 27 same-day scorer,
write-once captures, live production, or orders. All source/calendar attestations
are external input and NOT authenticated by this offline module; outputs remain
provisional even when structurally consistent.
"""
import argparse
from collections import Counter
from datetime import date, datetime, time
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from backtest.obsidian_iex_research_discovery import verify, EARLY_STATES
from backtest.obsidian_forward_source_contract_shadow import audit_outcome_source_contract
from backtest.obsidian_iex_corporate_actions import no_action_comparable
from backtest.obsidian_prospective_capture import asof, finite_price

ET = ZoneInfo("America/New_York")
POLICY = "OBSIDIAN_FORWARD_NEXT_1_2_3_SESSIONS_SHADOW_V1_2026_10_28"
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
TARGET_FRACTION = 0.80
REMAINING_FRACTION = 0.50


def validate_calendar(rows, initial_day):
    """Require explicit four consecutive *reported trading sessions*, not weekdays.

    External calendar source authenticity still requires a human/provider audit.
    Early-close sessions are quarantined in this first fixed-16:00 protocol.
    """
    if not isinstance(rows, list) or len(rows) != 4:
        raise ValueError("EXACTLY_FOUR_SESSION_CALENDAR_ROWS_REQUIRED")
    verified = []
    prior = None
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("CALENDAR_ROW_NOT_OBJECT")
        try:
            session = date.fromisoformat(row["session_date"])
            previous = date.fromisoformat(row["previous_regular_session"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError("CALENDAR_SESSION_DATE_INVALID") from exc
        stamp = asof(row.get("regular_close_at"))
        checked = asof(row.get("source_checked_at"))
        url = row.get("source_url")
        host = urlsplit(url).hostname if isinstance(url, str) else None
        if (row.get("session_open") is not True or
            row.get("independently_checked") is not True or
            host not in {"nasdaq.com", "www.nasdaq.com", "nyse.com", "www.nyse.com"} or
            checked is None or stamp is None or
            stamp.astimezone(ET) != datetime.combine(session, time(16), tzinfo=ET)):
            raise ValueError("CALENDAR_SOURCE_OR_NORMAL_CLOSE_UNVERIFIED")
        if session.weekday() >= 5 or previous >= session or previous.weekday() >= 5:
            raise ValueError("INVALID_EXCHANGE_SESSION_CHAIN")
        if index == 0 and session != initial_day:
            raise ValueError("FIRST_SESSION_NOT_ORIGINAL_CAPTURE")
        if prior is not None and (session <= prior or previous != prior):
            raise ValueError("NONCONSECUTIVE_EXCHANGE_SESSION_CHAIN")
        verified.append((session,previous,stamp,row))
        prior = session
    return verified


def _source_chain_ok(outcome, calendar):
    session, previous, close_at, _ = calendar
    if outcome.get("session_date") != session.isoformat():
        return False
    issues = audit_outcome_source_contract(outcome, session.isoformat())["issues"]
    if issues:
        return False
    if outcome.get("previous_session_date") != previous.isoformat():
        return False
    if outcome.get("corporate_actions_clear") is not True:
        return False
    observed = asof(outcome.get("close_at"))
    collected = asof(outcome.get("collected_at"))
    if observed != close_at or collected is None or collected < close_at:
        return False
    if not no_action_comparable(outcome, previous, session, observed, collected):
        return False
    return finite_price(outcome.get("regular_close")) and finite_price(outcome.get("previous_regular_close"))


def evaluate(capture, calendar_rows, outcome_rows):
    original = verify(capture)  # rehash/replay every originally screened row
    base = Path(capture)
    manifest = json.loads((base/"manifest.json").read_text(encoding="utf-8"))
    if manifest["phase"] not in ("MORNING", "INTRADAY"):
        raise ValueError("AFTERHOURS_OR_PRECLOSE_NOT_THIS_STUDY")
    original_day = asof(manifest["started_at"]).astimezone(ET).date()
    calendar = validate_calendar(calendar_rows, original_day)
    if not isinstance(outcome_rows,list):
        raise ValueError("OUTCOME_LIST_REQUIRED")
    raw = (base/"universe.jsonl").read_bytes()
    universe = [json.loads(x) for x in raw.splitlines()]
    if len(universe) != original["universe_count"]:
        raise ValueError("TAMPERED_SOURCE_UNIVERSE")
    original_symbols = {row["ticker"] for row in universe}
    dates = {c[0].isoformat() for c in calendar}
    mapped = {}
    for row in outcome_rows:
        if not isinstance(row, dict):
            raise ValueError("INVALID_OUTCOME_ROW")
        key = (row.get("ticker"),row.get("session_date"))
        if key in mapped or key[0] not in original_symbols or key[1] not in dates:
            raise ValueError("DUPLICATE_OR_OUTSIDE_ORIGINAL_COHORT")
        mapped[key] = row
    counters = Counter()
    results = []
    for item in universe:
        ticker = item["ticker"]
        flagged = item["indicative_status"] in EARLY_STATES
        counters["original_symbols"] += 1
        counters["original_price_watches"] += int(flagged)
        result = {"ticker":ticker,"original_watch":flagged,
                  "original_status":item["indicative_status"],
                  "first_event_horizon":None,"remaining_fraction":None,
                  "status":"UNSCORED_MISSING_OR_INCOMPLETE_EOD_EVIDENCE",
                  "actual_smg_eligible":None,"actual_short_fill":None,
                  "externally_authenticated_prediction":False}
        prev_close = None
        baseline = None
        chain_complete = True
        for h,c in enumerate(calendar):
            date_key = c[0].isoformat()
            observation = mapped.get((ticker,date_key))
            if observation is None or not _source_chain_ok(observation,c):
                counters["unverified_or_missing_eod_rows"] += 1
                chain_complete = False
                break
            prior, close = observation["previous_regular_close"], observation["regular_close"]
            if prev_close is not None and abs(prior-prev_close) > .005:
                counters["cross_session_price_chain_mismatch"] += 1
                chain_complete = False
                break
            if h == 0:
                baseline = prior
                result["baseline_prior_close_conditional"] = baseline
            prev_close = close
            counters["structurally_consistent_eod_rows"] += 1
            if close > baseline * TARGET_FRACTION:
                continue
            result["first_event_horizon"] = h
            if h == 0:
                result["status"] = "ALREADY_20PCT_AT_SAME_DAY_CLOSE_NOT_FUTURE_CATCH"
                counters["same_day_first_crossings_not_future_credit"] += 1
            else:
                snap = item.get("snapshot")
                trade = snap.get("latestTrade") if isinstance(snap,dict) else None
                price = trade.get("p") if isinstance(trade,dict) else None
                trade_at = asof(trade.get("t")) if isinstance(trade,dict) else None
                received = asof(item.get("received_at"))
                at = asof(manifest["finished_at"])
                usable = (finite_price(price) and trade_at is not None and
                          received is not None and at is not None and
                          trade_at <= received <= at and
                          (received-trade_at).total_seconds() <= 900)
                remaining = (price-close)/(baseline-close) if usable else None
                result["remaining_fraction"] = round(remaining,6) if remaining is not None else None
                if not usable:
                    result["status"] = "FUTURE_CROSSING_BUT_ORIGINAL_TAPE_UNUSABLE"
                elif flagged and remaining >= REMAINING_FRACTION:
                    result["status"] = "PROVISIONAL_EARLY_NEXT_SESSION_WATCH"
                    counters["provisional_early_next_session_watches"] += 1
                elif flagged:
                    result["status"] = "PROVISIONAL_LATE_NEXT_SESSION_WATCH"
                    counters["provisional_late_next_session_watches"] += 1
                else:
                    result["status"] = "PROVISIONAL_FUTURE_COLLAPSE_UNWATCHED"
                    counters["provisional_unwatched_next_session_collapses"] += 1
                counters["provisional_future_first_crossings"] += 1
            break
        if result["first_event_horizon"] is None:
            if chain_complete:
                result["status"] = "COMPLETE_FOUR_SESSIONS_NO_20PCT_CROSSING_CONDITIONAL"
                counters["complete_four_session_no_crossing"] += 1
            else:
                counters["incomplete_outcome_chains"] += 1
        results.append(result)
    return {
        "mode":MODE,"policy":POLICY,
        "source_run_count":1,"source_phase":manifest["phase"],
        "original_capture_sha256":hashlib.sha256(raw).hexdigest(),
        "original_universe_count":len(universe),
        "provided_outcome_rows":len(outcome_rows),
        "calendar_dates":[c[0].isoformat() for c in calendar],
        "target":"FIRST_CROSSING_DOWN_AT_LEAST_20PCT_FROM_ORIGINAL_OFFICIAL_PREVIOUS_CLOSE_AT_H0_H1_H2_H3",
        "future_horizons":[1,2,3],
        "provisional_counts":dict(sorted(counters.items())),
        "verified_future_hits":None, "verified_precision":None,
        "verified_recall":None, "after_cost_returns":None,
        "provider_data_independently_authenticated_by_module":False,
        "official_closes_independently_authenticated_by_module":False,
        "predictive_edge_proven":False,
        "limitations":[
            "This is a separately registered research-only horizon study; frozen original same-day evaluator remains unchanged.",
            "Actual distinct source providers and public exchange calendars require external verification; consistent JSON alone is not official proof.",
            "Every symbol in source capture remains represented; incomplete sequences never assumed no collapse.",
            "No holiday/early-close session guessed; use independently sourced four-session calendar; early-close dates blocked.",
            "A ticker crossing the 20pct threshold on h0 is NOT credited again on h1-h3.",
            "Same ticker from morning/intraday is correlated; do not aggregate as independent attempts.",
            "IEX original trade/previous bar is single venue, not NBBO, real SMG short availability or executable price.",
        ],
        "rows":results,
    }


def main():
    parser = argparse.ArgumentParser(description="Offline 1-3 session shadow forward outcomes")
    parser.add_argument("--capture",required=True)
    parser.add_argument("--calendar",required=True)
    parser.add_argument("--outcomes",required=True)
    parser.add_argument("--output",required=True)
    a = parser.parse_args()
    cal=json.loads(Path(a.calendar).read_text(encoding="utf-8"))
    obs=json.loads(Path(a.outcomes).read_text(encoding="utf-8"))
    report=evaluate(a.capture,cal,obs)
    target=Path(a.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as file:
        json.dump(report,file,indent=2,sort_keys=True)
        file.write("\n")
    print(json.dumps({"policy":POLICY,
                      "original_universe_count":report["original_universe_count"],
                      "provisional_counts":report["provisional_counts"],
                      "verified_future_hits":None},sort_keys=True))


if __name__=="__main__":
    main()
