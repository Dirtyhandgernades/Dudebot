"""Fail-closed regular-session collapse outcome verification; research only.

A postclose vendor display is not an authenticated exchange close. Multiple
pages from the same provider do not constitute independent confirmation.
Do not award retrospective >=20% winners when independent providers disagree.
No orders, live alerts, or frozen strategy changes.
"""
from datetime import date, datetime, time
from math import isfinite
from zoneinfo import ZoneInfo

MAX_CLOSE_DIVERGENCE = 0.02
EXTREME_DROP = 0.20
NY = ZoneInfo("America/New_York")


def _price(x):
    return type(x) in (float, int) and isfinite(x) and x > 0


def _aware(x):
    return isinstance(x, datetime) and x.utcoffset() is not None


def audit_regular_close_outcome(*, symbol, session_date, previous_close,
                                reports, observed_at):
    """Verify only an OUTCOME, never a preclose forecast or executable trade.

    reports: provider_id, session_date (date), close, captured_at (aware
    datetime), session_complete (literal True), kind='regular_close'.
    Only observations captured after 4pm ET on the target session count.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("SYMBOL_REQUIRED")
    if not isinstance(session_date, date) or isinstance(session_date, datetime):
        raise ValueError("SESSION_DATE_REQUIRED")
    if not _aware(observed_at):
        raise ValueError("AWARE_OBSERVATION_REQUIRED")
    if not _price(previous_close):
        raise ValueError("PREVIOUS_CLOSE_REQUIRED")
    if not isinstance(reports, (tuple, list)):
        raise ValueError("REPORTS_REQUIRED")
    issues = []
    accepted = {}
    session_end = datetime.combine(session_date, time(16, 0), NY)
    for report in reports:
        if not isinstance(report, dict):
            raise ValueError("INVALID_REPORT")
        provider = report.get("provider_id")
        close = report.get("close")
        stamp = report.get("captured_at")
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("PROVIDER_ID_REQUIRED")
        if (report.get("session_date") != session_date or
            report.get("kind") != "regular_close" or
            report.get("session_complete") is not True or
            not _price(close) or not _aware(stamp) or
            stamp < session_end or stamp > observed_at):
            issues.append("INCOMPLETE_STALE_OR_WRONG_SESSION_REPORT")
            continue
        accepted.setdefault(provider, []).append(close)
    if len(accepted) < 2:
        issues.append("INSUFFICIENT_INDEPENDENT_COMPLETED_CLOSE_SOURCES")
    # Contradictory pages within one provider cannot be used selectively.
    if any(max(v) / min(v) - 1 > MAX_CLOSE_DIVERGENCE for v in accepted.values()):
        issues.append("SAME_PROVIDER_CLOSE_CONFLICT")
    provider_prices = [sum(v) / len(v) for v in accepted.values()]
    if len(provider_prices) >= 2 and max(provider_prices) / min(provider_prices) - 1 > MAX_CLOSE_DIVERGENCE:
        issues.append("INDEPENDENT_CLOSE_SOURCES_DISAGREE")
    threshold = previous_close * (1 - EXTREME_DROP)
    # Preserve every accepted observation at the decision threshold. Averaging
    # same-provider pages can hide a threshold conflict even when their prices
    # differ by less than the general cross-vendor tolerance.
    all_accepted_prices = [price for prices in accepted.values() for price in prices]
    if (all_accepted_prices and min(all_accepted_prices) <= threshold
            < max(all_accepted_prices)):
        issues.append("SOURCES_STRADDLE_20PCT_THRESHOLD")
    verified = not issues
    if verified:
        classification = ("VERIFIED_AT_LEAST_20PCT_CLOSE_DROP"
                          if max(provider_prices) <= threshold
                          else "VERIFIED_BELOW_20PCT_CLOSE_DROP")
    else:
        classification = "OUTCOME_UNVERIFIED"
    return {
        "symbol": symbol,
        "session_date": session_date.isoformat(),
        "classification": classification,
        "issues": sorted(set(issues)),
        "independent_provider_count": len(accepted),
        "observed_close_range": [min(provider_prices), max(provider_prices)] if provider_prices else None,
        "preclose_catchability": "UNPROVEN_NO_PREDECISION_TAPE",
        "trade_status": "RESEARCH_ONLY_NOT_AN_ORDER",
        "hypothetical_profit": None,
    }
