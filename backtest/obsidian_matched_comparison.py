"""Coverage-censored, paired historical challenger diagnostic (research only).

No live orders or alerts. 2023-2025 were inspected repeatedly, so this is
development-set evidence, NOT untouched out-of-sample validation. Missing
short borrow, historical market cap, corporate actions and actual fills prevent
any assertion of executable SMG profitability.
"""
import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from backtest.confirmation_comparison import drop_timing
from backtest.obsidian_data_audit import load_checked
from smg.models import Config
from smg.swing_backtest import simulate

YEARS = (2023, 2024, 2025)
# Preregistered diagnostic threshold, NOT optimized on these reused outcomes.
EARLY_MAX_CHANGE = -0.02
CASES = (("base", 30, 0.10), ("stress", 100, 1.0))


def matched_events(packet, events, records, year):
    """Same point-in-time/coverage gate for both policies, with explicit censoring."""
    sessions = packet["sessions"]
    indices = {day: i for i, day in enumerate(sessions)}
    baseline, early, audit = {}, {}, Counter()
    for day, rows in events.items():
        baseline[day], early[day] = [], []
        if day not in indices or not day.startswith(str(year)):
            raise ValueError("INVALID_SIGNAL_SESSION")
        i = indices[day]
        if i == 0:
            audit["NO_PRIOR_SESSION"] += len(rows)
            continue
        prior_day = sessions[i - 1]
        for event in rows:
            ticker = event["ticker"]
            key = f"{day}|{ticker}"
            record = records.get(key)
            if record is None or record.get("status") != "RECOVERED":
                audit["CENSORED_UNVERIFIED_WINDOW"] += 1
                continue
            if record.get("day") != day or record.get("ticker") != ticker or record.get("year") != year:
                raise ValueError(f"CHECKPOINT_IDENTITY_MISMATCH: {key}")
            decision = datetime.fromisoformat(event["decision_at"])
            cutoff = datetime.fromisoformat(event["data_cutoff"])
            if (decision.tzinfo is None or cutoff.tzinfo is None
                    or not cutoff < decision or decision.date().isoformat() != day):
                raise ValueError(f"INVALID_DECISION_TIMESTAMPS: {key}")
            if event.get("last_complete_at"):
                observed = datetime.fromisoformat(event["last_complete_at"])
                if observed.tzinfo is None or observed > cutoff:
                    raise ValueError(f"LOOKAHEAD_OBSERVATION: {key}")
            raw_today = packet["raw"].get(ticker, {}).get(day)
            split_today = packet["split"].get(ticker, {}).get(day)
            raw_prior = packet["raw"].get(ticker, {}).get(prior_day)
            if not raw_today or not split_today or not raw_prior:
                audit["CENSORED_MISSING_DAILY_BAR"] += 1
                continue
            price = event.get("decision_price")
            if (not isinstance(price, (int, float)) or price <= 3
                    or raw_prior["c"] <= 3 or raw_today["c"] <= 3):
                audit["CENSORED_PRICE_GATE"] += 1
                continue
            # Price-only gate: cap/borrow/security-type verification remains UNKNOWN.
            change = price / raw_prior["c"] - 1
            baseline[day].append(event)
            audit["MATCHED_BASELINE_SIGNALS"] += 1
            if change <= EARLY_MAX_CHANGE:
                early[day].append({**event,
                                   "research_policy": "FIXED_EARLY_WEAKNESS_MINUS_2PCT",
                                   "observed_change_from_prior_raw_close": change})
                audit["EARLY_WEAKNESS_SIGNALS"] += 1
            else:
                audit["EARLY_FILTER_REJECTED"] += 1
    return baseline, early, dict(audit)


def run(source, recovery, out):
    source, recovery, out = Path(source), Path(recovery), Path(out)
    packet, integrity = load_checked(source)
    checkpoint = json.loads((recovery / "checkpoint.json").read_text())
    progress = json.loads((recovery / "recovery.json").read_text())
    if checkpoint.get("source_sha256") != integrity["packet_sha256"]:
        raise ValueError("CHECKPOINT_SOURCE_HASH_MISMATCH")
    if progress.get("source_sha256") != integrity["packet_sha256"]:
        raise ValueError("RECOVERY_SOURCE_HASH_MISMATCH")
    if progress["remaining_unchecked"] or progress["retryable_pending"] or progress["retry_exhausted"]:
        raise ValueError("RECOVERY_NOT_COMPLETE")
    records = checkpoint["records"]
    if (len(records) != progress["total_candidate_windows"]
            or len(records) != progress["windows_checked_cumulative"]
            or sum(progress["counts"].values()) != len(records)):
        raise ValueError("RECOVERY_COUNT_MISMATCH")
    out.mkdir(parents=True, exist_ok=True)
    cfg = Config(**packet["config"])
    results = []
    coverage = {}
    for year in YEARS:
        events = json.loads((source / f"{year}-hybrid-signals.json").read_text())
        baseline, early, audit = matched_events(packet, events, records, year)
        coverage[str(year)] = audit
        for label, signal_set in (("existing_hybrid", baseline), ("fixed_early_weakness", early)):
            for cost_name, cost_bps, borrow_rate in CASES:
                end = f"{year}-12-05"
                result = simulate(
                    packet["raw"], packet["split"],
                    packet["cohorts"][f"{year}-09-08"]["short"],
                    packet["sessions"], start=f"{year}-09-08", end=end,
                    hold=3, strategy="FIRM_HYBRID_EXHAUSTION_RESEARCH",
                    cost_bps=cost_bps, borrow_rate=borrow_rate,
                    position_target=30000, buying_power=150000,
                    firm_dates=packet["firm_dates"], firm_cfg=cfg,
                    risk_controls=True, signal_share_sizing=True,
                    intraday_signals=signal_set, smg_cash_interest=True,
                )
                name = f"{year}-{label}-{cost_name}"
                fields = ("ticker", "signal_date", "entry_date", "exit_date",
                          "shares", "notional", "pnl", "exit_reason")
                with (out / f"{name}-trades.csv").open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(result["trades"])
                results.append({
                    "year": year, "policy": label, "cost_case": cost_name,
                    "signal_count_after_coverage_gate": sum(map(len, signal_set.values())),
                    "net_profit_model_only": result["net_profit"],
                    "cash_interest_pnl_model_only": result["interest_pnl"],
                    "net_profit_excluding_cash_interest_model_only": (
                        round(result["net_profit"] - result["interest_pnl"], 2)
                        if result["net_profit"] is not None else None
                    ),
                    "realized_trade_pnl_model_only": result["realized_profit"],
                    "unresolved_open_positions": result["unresolved_open_positions"],
                    "financial_status": result["financial_status"],
                    "closed_trades": result["closed_trades"],
                    "max_observed_drawdown_pct": result["max_observed_drawdown_pct"],
                    "account_insolvent": result["account_insolvent"],
                    "model_data_gaps": result.get("data_gaps", result.get("gaps")),
                    "drop_timing": drop_timing(result, packet, end),
                })
    report = {
        "status": "REUSED_YEARS_CONDITIONAL_DIAGNOSTIC_NOT_OOS",
        "source_sha256": integrity["packet_sha256"],
        "coverage": coverage,
        "original_candidate_windows": progress["total_candidate_windows"],
        "usable_provider_windows": progress["counts"].get("RECOVERED", 0),
        "censored_provider_windows": progress["counts"].get("PROVIDER_EMPTY_OR_STALE", 0),
        "early_threshold_prior_close_return": EARLY_MAX_CHANGE,
        "results": results,
        "edge_demonstrated": False,
        "live_enabled": False,
        "limitations": [
            "This filters previously discovered hybrid signals; no independent new-security discovery or full-market recall.",
            "All 2023-2025 years were previously inspected, not untouched chronological out-of-sample.",
            "Recovery windows with missing/stale bars are censored, not assumed profitable or flat.",
            "Missingness can correlate with volatility, halts, or poor liquidity; results are selection-biased.",
            "No historical verified SMG market cap, security type, short borrow/locates, actual order fills or exact slippage.",
            "Simulated same-day closing fills and modeled exits are hypothetical, not executed trades.",
            "Net profit includes modeled interest on cash; zero-trade positive interest is NOT strategy alpha.",
            "The threshold is a fixed diagnostic, not an optimized winner or a production-ready strategy.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": report["status"], "coverage": coverage,
                      "results": [{k: row[k] for k in ("year", "policy", "cost_case",
                                  "net_profit_model_only", "realized_trade_pnl_model_only", "closed_trades",
                                  "max_observed_drawdown_pct")} for row in results]},
                     indent=2), flush=True)
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="outputs/backtest/hybrid-37386241124")
    p.add_argument("--recovery", default="outputs/backtest/obsidian-recovery")
    p.add_argument("--out", default="outputs/backtest/obsidian-matched-comparison")
    args = p.parse_args()
    run(args.source, args.recovery, args.out)
