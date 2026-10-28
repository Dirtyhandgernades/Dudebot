"""OBSIDIAN independent-EOD intake gate, RESEARCH_ONLY_NOT_AN_ORDER.

This is a SHADOW evidence structure gate, not a price feed, exchange calendar,
authentication system, executable trading signal, or official close verifier.
It never edits immutable captures or the October 27 frozen forward scorer.
"""
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path

from backtest.obsidian_forward_calendar_shadow import audit_calendar_assumptions
from backtest.obsidian_forward_source_contract_shadow import audit_outcome_source_contract
from backtest.obsidian_iex_corporate_actions import no_action_comparable
from backtest.obsidian_prospective_capture import asof

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_SHADOW_STRICT_EOD_INTAKE_V1_2026_10_28"


def assess(outcome, calendar):
    """Audit source/date/identity provenance without claiming it is authentic."""
    issues = set()
    if not isinstance(outcome, dict):
        outcome = {}
        issues.add("MALFORMED_EOD_OUTCOME")
    if not isinstance(calendar, dict):
        calendar = {}
        issues.add("MISSING_EXTERNAL_CALENDAR_EVIDENCE")
    day = calendar.get("session_date")
    if not isinstance(day, str):
        issues.add("SESSION_DATE_MISSING")
        day = ""
    calendar_check = audit_calendar_assumptions(day, calendar)
    issues.update(calendar_check["issues"])
    source_check = audit_outcome_source_contract(outcome, day)
    issues.update(source_check["issues"])
    if outcome.get("previous_session_date") != calendar.get("previous_regular_session"):
        issues.add("PREVIOUS_SESSION_CHAIN_MISMATCH")
    if outcome.get("ticker") is None:
        issues.add("TICKER_MISSING")
    close_at = asof(outcome.get("close_at"))
    collected_at = asof(outcome.get("collected_at"))
    try:
        previous = date.fromisoformat(outcome["previous_session_date"])
        current = date.fromisoformat(day)
    except (KeyError, ValueError, TypeError):
        previous = current = None
        issues.add("INVALID_SESSION_DATE_PAIR")
    if previous is not None and current is not None:
        if not no_action_comparable(outcome, previous, current, close_at, collected_at):
            issues.add("SECURITY_OR_CORPORATE_ACTION_NOT_INDEPENDENTLY_CLEARED")
    # Source-group metadata, signed-off external calendar notes, and even
    # 'verified': true fields are supplied assertions, not an authenticated
    # market-data retrieval by this offline module.
    status = ("STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING" if not issues
              else "BLOCKED_EOD_EVIDENCE")
    return {
        "mode": MODE, "policy": POLICY, "ticker": outcome.get("ticker"),
        "session_date": day, "status": status,
        "issues": sorted(issues),
        "structural_checks_passed": not issues,
        "actual_source_independence_authenticated": False,
        "official_close_verified_by_module": False,
        "usable_for_automatic_frozen_forward_scoring": False,
        "actual_smg_trade_authorized": False,
    }


def audit_packet(outcomes, calendar_rows):
    if not isinstance(outcomes, list) or not isinstance(calendar_rows, list):
        raise ValueError("OUTCOMES_AND_CALENDAR_LISTS_REQUIRED")
    calendars = {}
    for entry in calendar_rows:
        if not isinstance(entry, dict) or not isinstance(entry.get("session_date"), str):
            raise ValueError("CALENDAR_ROW_INVALID")
        key = entry["session_date"]
        if key in calendars:
            raise ValueError("DUPLICATE_CALENDAR_SESSION")
        calendars[key] = entry
    seen = set()
    results = []
    for entry in outcomes:
        if not isinstance(entry, dict):
            raise ValueError("INVALID_OUTCOME_ROW")
        key = (entry.get("ticker"), entry.get("session_date"))
        if key in seen:
            raise ValueError("DUPLICATE_TICKER_SESSION")
        seen.add(key)
        results.append(assess(entry, calendars.get(entry.get("session_date"))))
    counts = Counter(x["status"] for x in results)
    return {
        "mode": MODE, "policy": POLICY,
        "input_outcomes": len(outcomes), "outcomes_retained": len(results),
        "status_counts": dict(sorted(counts.items())),
        "externally_verified_completed_outcomes": 0,
        "performance_metrics": None,
        "is_authenticated_data_ingestion": False,
        "rows": results,
    }


def _load_list(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("JSON_LIST_REQUIRED")
    return value


def main():
    parser = argparse.ArgumentParser(description="Offline EOD evidence intake (not scoring)")
    parser.add_argument("--outcomes-json", required=True)
    parser.add_argument("--calendar-json", required=True)
    parser.add_argument("--output", required=True)
    a = parser.parse_args()
    output = audit_packet(_load_list(a.outcomes_json), _load_list(a.calendar_json))
    raw = json.dumps(output, sort_keys=True, indent=2) + "\n"
    target = Path(a.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(raw)
    print(json.dumps({"policy": POLICY, "rows": output["outcomes_retained"],
                      "status_counts": output["status_counts"],
                      "performance_metrics": None}, sort_keys=True))


if __name__ == "__main__":
    main()
