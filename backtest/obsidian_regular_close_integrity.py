"""Legacy offline regular-close CLAIM audit; never certifies market outcomes.

A postclose vendor display, provider_id string, and caller-supplied previous
close cannot authenticate exchange closes, security identity, corporate actions
or independence. This isolated research helper ALWAYS censors official outcomes.
No orders, live alerts, or changes to frozen strategy/denominator.
"""
from datetime import date, datetime, time
from math import isfinite
from zoneinfo import ZoneInfo

MAX_CLOSE_DIVERGENCE = 0.02
EXTREME_DROP = 0.20
NY = ZoneInfo("America/New_York")


def _price(x):
    # Avoid float overflow/underflow in ratios, provider means and threshold
    # diagnostics. This is NOT a market/SMG price-eligibility threshold.
    return type(x) in (float, int) and isfinite(x) and 1e-100 <= x <= 1e100


def _aware(x):
    return isinstance(x, datetime) and x.utcoffset() is not None


def audit_regular_close_outcome(*, symbol, session_date, previous_close,
                                reports, observed_at):
    """Inspect only untrusted price claims, never a forecast or trade.

    reports: claimed provider_id, session_date (date), close, captured_at
    (aware datetime), session_complete (literal True), kind='regular_close'.
    Post-4pm capture is necessary but NOT proof of the 4pm auction price.
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
    structural_consensus = not issues
    # This legacy helper has no authenticated transport receipts, legal
    # provider-ownership mapping, official close auction source, previous-close
    # provenance, exchange calendar or corporate-action/security-ID proof.
    # Two agreeing self-attested provider IDs are NEVER a verified outcome.
    issues.append("OFFICIAL_CLOSE_AND_REFERENCE_NOT_AUTHENTICATED")
    classification = "OUTCOME_UNVERIFIED"
    return {
        "symbol": symbol,
        "session_date": session_date.isoformat(),
        "classification": classification,
        "issues": sorted(set(issues)),
        "independent_provider_count": 0,
        "claimed_provider_id_count": len(accepted),
        "structural_consensus_only": structural_consensus,
        "official_close_verified": False,
        "previous_close_authenticated": False,
        "provider_independence_authenticated": False,
        "corporate_action_and_security_identity_authenticated": False,
        "eligible_for_frozen_forward_scoring": False,
        "verified_20pct_prediction_success": None,
        "outcome_censored_pending_external_evidence": True,
        "observed_close_range": [min(provider_prices), max(provider_prices)] if provider_prices else None,
        "preclose_catchability": "UNPROVEN_NO_PREDECISION_TAPE",
        "trade_status": "RESEARCH_ONLY_NOT_AN_ORDER",
        "hypothetical_profit": None,
    }
