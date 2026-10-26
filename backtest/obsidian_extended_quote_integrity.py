"""OBSIDIAN research-only extended-hours quote reconciliation (no orders).

A ranked mover table and an individual quote from the SAME data vendor are
not independent confirmation. Rankings often lack a trade timestamp, and
after-hours prices can move sharply between observations. Divergent displays
are UNRESOLVED, not evidence that either trade was fabricated or executable.
This module does not change the frozen strategy, execution gate or provider.
"""
from datetime import datetime, timedelta
from math import isfinite
from zoneinfo import ZoneInfo

MAX_QUOTE_AGE = timedelta(minutes=15)
MAX_VIEW_DIVERGENCE = 0.05
MAX_INDEPENDENT_DIVERGENCE = 0.02
EXTREME_MOVE = 0.20

def _aware(dt):
    return isinstance(dt, datetime) and dt.utcoffset() is not None

def _price(x):
    return type(x) in (int, float) and isfinite(x) and x > 0

def _fraction(a, b):
    return abs(a - b) / b

def reconcile_extended_quote(*, symbol, observed_at, ranked_close=None,
                             ranked_extended=None, individual_close=None,
                             individual_extended=None, individual_quote_at=None,
                             independent_quotes=(), corporate_action_clear=False):
    """Return a fail-closed *research data quality* result.

    independent_quotes: records with unique source_id, price, observed_at.
    Two displays from one vendor never constitute independent corroboration.
    An uncorroborated ranking must not become a claimed trade opportunity.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("SYMBOL_REQUIRED")
    if not _aware(observed_at):
        raise ValueError("AWARE_OBSERVATION_REQUIRED")
    issues = []
    if not (_price(ranked_close) and _price(ranked_extended)):
        issues.append("RANKED_PRICE_MISSING")
    if not (_price(individual_close) and _price(individual_extended)):
        issues.append("INDIVIDUAL_PRICE_MISSING")
    if not _aware(individual_quote_at) or individual_quote_at > observed_at:
        issues.append("INDIVIDUAL_QUOTE_TIME_UNVERIFIED")
    elif observed_at - individual_quote_at > MAX_QUOTE_AGE:
        issues.append("INDIVIDUAL_QUOTE_STALE")
    elif individual_quote_at.astimezone(ZoneInfo("America/New_York")).date() != observed_at.astimezone(ZoneInfo("America/New_York")).date():
        issues.append("INDIVIDUAL_QUOTE_WRONG_SESSION")
    if _price(ranked_close) and _price(individual_close) and _fraction(ranked_close, individual_close) > 0.01:
        issues.append("REGULAR_CLOSE_CROSS_VIEW_CONFLICT")
    if _price(ranked_extended) and _price(individual_extended) and _fraction(ranked_extended, individual_extended) > MAX_VIEW_DIVERGENCE:
        issues.append("NON_SYNCHRONOUS_EXTENDED_QUOTE_DIVERGENCE")
    if corporate_action_clear is not True:
        issues.append("CORPORATE_ACTION_NOT_INDEPENDENTLY_CLEARED")
    accepted = {}
    for row in independent_quotes:
        if not isinstance(row, dict):
            raise ValueError("INVALID_INDEPENDENT_QUOTE")
        source, price, stamp = row.get("source_id"), row.get("price"), row.get("observed_at")
        if not isinstance(source, str) or not source.strip() or not _price(price) or not _aware(stamp):
            raise ValueError("INVALID_INDEPENDENT_QUOTE")
        if stamp > observed_at or observed_at - stamp > MAX_QUOTE_AGE:
            continue
        if stamp.astimezone(ZoneInfo("America/New_York")).date() != observed_at.astimezone(ZoneInfo("America/New_York")).date():
            continue
        accepted[source] = price
    if len(accepted) < 2:
        issues.append("NO_TWO_INDEPENDENT_FRESH_SOURCES")
    elif max(accepted.values()) / min(accepted.values()) - 1 > MAX_INDEPENDENT_DIVERGENCE:
        issues.append("INDEPENDENT_SOURCES_DISAGREE")
    if _price(ranked_close) and _price(ranked_extended) and ranked_extended <= ranked_close * (1 - EXTREME_MOVE):
        if "NO_TWO_INDEPENDENT_FRESH_SOURCES" in issues or "INDEPENDENT_SOURCES_DISAGREE" in issues:
            issues.append("EXTREME_RANKED_DROP_UNCORROBORATED")
    if _price(individual_close) and _price(individual_extended) and individual_extended <= individual_close * (1 - EXTREME_MOVE):
        if "NO_TWO_INDEPENDENT_FRESH_SOURCES" in issues or "INDEPENDENT_SOURCES_DISAGREE" in issues:
            issues.append("EXTREME_INDIVIDUAL_DROP_UNCORROBORATED")
    # Even clean quotes are NOT proof of actual SMG eligibility or borrow.
    return {
        "symbol": symbol, "observed_at": observed_at.isoformat(),
        "ranked_move_pct": round(100 * (ranked_extended / ranked_close - 1), 2)
            if _price(ranked_close) and _price(ranked_extended) else None,
        "individual_move_pct": round(100 * (individual_extended / individual_close - 1), 2)
            if _price(individual_close) and _price(individual_extended) else None,
        "issues": sorted(set(issues)),
        "quote_quality": "UNVERIFIED_CONFLICT_OR_MISSINGNESS" if issues else "CROSS_SOURCE_CORROBORATED_RESEARCH_ONLY",
        "trade_status": "NOT_VERIFIED_EXECUTABLE",
        "preclose_catchability": "UNPROVEN_NO_PREDECISION_TAPE",
        "hypothetical_profit": None,
    }
