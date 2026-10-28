"""Outcome-blind shadow audit of the *source contract* for frozen IEX scoring.

RESEARCH_ONLY_NOT_AN_ORDER. Never modifies the frozen scorer, inputs, or
captures. A source-consistent outcome is NOT an official close, corporate-action
clearance, SMG eligibility, or a verified early prediction.
"""
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from backtest.obsidian_eod_source_preflight import preflight

ET = ZoneInfo("America/New_York")
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
TOLERANCE = Decimal("0.005")


def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() and number > 0 else None


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def _day(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def audit_outcome_source_contract(outcome, session_date):
    """Check independently supplied source-level evidence; never synthesize it.

    The existing frozen evaluator validates different fields from the newer
    EOD source preflight. This shadow report identifies outcomes that could
    otherwise be scored without per-provider price-as-of, provider ownership,
    or source-specific security/session evidence.
    """
    issues = set()
    if not isinstance(outcome, dict):
        return {"mode": MODE, "status": "SHADOW_SOURCE_CONTRACT_BLOCKED",
                "issues": ["MALFORMED_OUTCOME"],
                "eligible_for_frozen_forward_scoring": False,
                "frozen_evaluator_modified": False}
    session = _day(session_date)
    previous = _day(outcome.get("previous_session_date"))
    symbol = outcome.get("ticker")
    if session is None or previous is None or previous >= session:
        issues.add("INVALID_SESSION_DATES")
    if not isinstance(symbol, str) or not symbol.strip():
        issues.add("INVALID_SYMBOL")
    reports = outcome.get("independent_eod_sources")
    if not isinstance(reports, list):
        issues.add("COMPLETE_SOURCE_REPORT_LIST_MISSING")
        reports = []
    close_at = _timestamp(outcome.get("close_at"))
    expected_close = datetime.combine(session, time(16, 0), tzinfo=ET) if session else None
    if close_at is None or close_at.astimezone(ET) != expected_close:
        issues.add("TOP_LEVEL_CLOSE_NOT_EXACT_1600_ET")
    if (outcome.get("regular_session") is not True
            or outcome.get("verified") is not True
            or outcome.get("provider_conflict") is not False):
        issues.add("TOP_LEVEL_OUTCOME_NOT_VERIFIED")
    parent_close = _decimal(outcome.get("regular_close"))
    parent_prior = _decimal(outcome.get("previous_regular_close"))
    if parent_close is None or parent_prior is None:
        issues.add("INVALID_TOP_LEVEL_PRICES")
    for report in reports:
        if not isinstance(report, dict):
            continue
        if report.get("verified") is not True:
            issues.add("SOURCE_NOT_INDEPENDENTLY_VERIFIED")
        if parent_close is not None and parent_prior is not None:
            source_close = _decimal(report.get("regular_close"))
            source_prior = _decimal(report.get("previous_regular_close"))
            if (source_close is None or source_prior is None
                    or abs(source_close - parent_close) > TOLERANCE
                    or abs(source_prior - parent_prior) > TOLERANCE):
                issues.add("SOURCE_TOP_LEVEL_PRICE_MISMATCH")
    source_report = None
    if session and previous and previous < session and isinstance(symbol, str) and symbol.strip():
        source_report = preflight(
            symbol, session, previous, reports, outcome.get("collected_at"))
        issues.update(source_report["issues"])
    else:
        issues.add("SOURCE_PREFLIGHT_NOT_RUN_INVALID_IDENTITY")
    return {
        "mode": MODE,
        "status": ("SHADOW_SOURCE_CONTRACT_BLOCKED" if issues else
                   "SHADOW_SOURCES_CONSISTENT_NOT_OFFICIAL"),
        "symbol": symbol,
        "session_date": session_date,
        "supplied_reports": len(reports),
        "issues": sorted(issues),
        "preflight_status": source_report["status"] if source_report else None,
        "source_inventory_completeness_externally_verified": False,
        "corporate_action_and_security_identity_verified": False,
        "eligible_for_frozen_forward_scoring": False,
        "frozen_evaluator_modified": False,
        "trade_authorized": False,
    }
