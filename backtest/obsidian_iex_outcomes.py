"""Independent later-close scoring for immutable IEX-only prospective captures.

Requires externally sourced, independently verified regular-session closes.
Never treats IEX last trades or previous IEX daily bars as official closes.
"""
import argparse
import json
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from backtest.obsidian_iex_prospective import verify
from backtest.obsidian_iex_corporate_actions import no_action_comparable
from backtest.obsidian_prospective_capture import asof, finite_price
from backtest.obsidian_prospective_verify import jsonl

ET = ZoneInfo("America/New_York")

def corroborated(outcome, close_at, collected_at):
    """Require two distinct timestamped EOD sources, not a self-attested flag."""
    sources = outcome.get("independent_eod_sources")
    if not isinstance(sources, list) or len(sources) < 2:
        return False
    distinct_ids, distinct_hosts = set(), set()
    for item in sources:
        if not isinstance(item, dict) or item.get("verified") is not True:
            return False
        source_id, url = item.get("source_id"), item.get("url")
        observed = asof(item.get("observed_at"))
        if not isinstance(source_id, str) or not source_id.strip() or source_id == "ALPACA_IEX":
            return False
        if not isinstance(url, str) or not url.startswith("https://"):
            return False
        host = urlsplit(url).hostname
        if not host or host in distinct_hosts or source_id in distinct_ids:
            return False
        if observed is None or not close_at <= observed <= collected_at:
            return False
        # No smoothing across the 20% threshold: disagreeing EOD prints are censored.
        for key, expected in (("regular_close", outcome.get("regular_close")),
                              ("previous_regular_close", outcome.get("previous_regular_close"))):
            if not finite_price(item.get(key)) or not finite_price(expected):
                return False
            if abs(item[key] - expected) > 0.005:
                return False
        distinct_ids.add(source_id)
        distinct_hosts.add(host)
    return len(distinct_ids) >= 2




def evaluate(capture, outcome_file):
    verify(capture)
    root = Path(capture)
    manifest = json.loads((root / "manifest.json").read_text())
    _, universe = jsonl(root / "universe.jsonl")
    _, outcomes = jsonl(Path(outcome_file))
    session = asof(manifest["started_at"]).astimezone(ET).date()
    finished = asof(manifest["finished_at"])
    previous = session - timedelta(days=1)
    while previous.weekday() >= 5:
        previous -= timedelta(days=1)
    symbols = {r["ticker"] for r in universe}
    mapped = {}
    for row in outcomes:
        symbol = row.get("ticker")
        if symbol not in symbols or symbol in mapped:
            raise ValueError("DUPLICATE_OR_OUTSIDE_CAPTURE_UNIVERSE")
        mapped[symbol] = row
    results = []
    hits = misses = watch_noncollapses = valid_count = 0
    for row in universe:
        symbol = row["ticker"]
        watched = row["screen_status"] == "IEX_EARLY_WEAKNESS_WATCH_ONLY"
        outcome = mapped.get(symbol, {})
        close_at = asof(outcome.get("close_at"))
        collected_at = asof(outcome.get("collected_at"))
        prior, close = outcome.get("previous_regular_close"), outcome.get("regular_close")
        valid = (outcome.get("verified") is True
                 and outcome.get("regular_session") is True
                 and outcome.get("provider_conflict") is False
                 and outcome.get("corporate_actions_clear") is True
                 and outcome.get("previous_session_date") == previous.isoformat()
                 and isinstance(outcome.get("source_url"), str)
                 and outcome["source_url"].startswith("https://")
                 and finite_price(prior) and finite_price(close)
                 and close_at is not None and collected_at is not None
                 and close_at.astimezone(ET).date() == session
                 and (close_at.astimezone(ET).hour, close_at.astimezone(ET).minute) == (16, 0)
                 and finished < close_at <= collected_at
                 and corroborated(outcome, close_at, collected_at)
                 and no_action_comparable(outcome, previous, session, close_at, collected_at))
        change = close / prior - 1 if valid else None
        collapse = valid and change <= -.20
        valid_count += bool(valid)
        hits += bool(collapse and watched)
        misses += bool(collapse and not watched)
        watch_noncollapses += bool(valid and watched and not collapse)
        results.append({"ticker": symbol, "preclose_iex_watch": watched,
                        "outcome_status": ("CENSORED" if not valid else
                                           "COLLAPSE_20_PLUS" if collapse else "NON_COLLAPSE"),
                        "independent_regular_close_return": change})
    collapses = hits + misses
    return {"status": "IEX_PROSPECTIVE_PRICE_ONLY_OUTCOME_AUDIT_NOT_SMG_PERFORMANCE",
            "research_only": True, "trade_authorized": False,
            "universe_count": len(universe), "outcomes_verified": valid_count,
            "outcomes_censored": len(universe) - valid_count,
            "verified_20pct_collapses": collapses, "preclose_iex_watch_hits": hits,
            "unwatched_collapses": misses, "preclose_iex_watch_noncollapses": watch_noncollapses,
            "conditional_recall": hits / collapses if collapses else None,
            "conditional_precision": hits / (hits + watch_noncollapses)
                                     if hits + watch_noncollapses else None,
            "verified_smg_eligible_recall": None, "lead_time": None,
            "after_cost_pnl": None, "actual_fills": None,
            "limitations": ["IEX is single venue, not consolidated SIP.",
                            "Two distinct timestamped EOD source records required; provenance fields still need source inspection.",
                            "No missing or conflicting outcomes are assumed negative.",
                            "Explicit independently reviewable no-action, same-security evidence is required; known spin-offs, distributions and identity changes are censored pending entitlement-adjusted research.",
                            "No SMG borrow, eligibility, fills or predictive edge proven."],
            "rows": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--outcomes", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as f:
        json.dump(evaluate(args.capture, args.outcomes), f, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
