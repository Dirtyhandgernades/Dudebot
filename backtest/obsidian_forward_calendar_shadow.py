"""Outcome-blind exchange-calendar assumptions audit for frozen IEX research.

RESEARCH_ONLY_NOT_AN_ORDER. Supplied exchange evidence is not authenticated by
this offline module. No market calls, frozen-policy changes, scores, or orders.
"""
from datetime import date, datetime, time, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"

EXCHANGE_CALENDAR_HOSTS = {"www.nyse.com", "nyse.com", "www.nasdaq.com", "nasdaq.com"}


def trusted_exchange_calendar_host(value):
    """Structural HTTPS provenance guard, never proof of source authenticity.

    Reject credentials in authority, nonstandard ports, fragments, malformed
    authorities and cleartext HTTP. A claimed URL is NOT a retrieved receipt.
    """
    if not isinstance(value, str) or not value or value.strip() != value:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.netloc
                or parsed.username is not None or parsed.password is not None
                or parsed.fragment or parsed.port not in (None, 443)):
            return None
        return parsed.hostname if parsed.hostname in EXCHANGE_CALENDAR_HOSTS else None
    except ValueError:
        return None


def _date(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _instant(value):
    if not isinstance(value, str):
        return None
    try:
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value if value.utcoffset() is not None else None


def _weekday_previous(day):
    prior = day - timedelta(days=1)
    while prior.weekday() >= 5:
        prior -= timedelta(days=1)
    return prior


def audit_calendar_assumptions(session_date, calendar_evidence):
    """Flag dates where the frozen weekday/16:00 assumptions are unsafe.

    The input must be independently gathered, source-dated exchange calendar
    evidence; this function cannot establish that the evidence is genuine.
    """
    issues = set()
    day = _date(session_date)
    evidence = calendar_evidence if isinstance(calendar_evidence, dict) else {}
    prior = _date(evidence.get("previous_regular_session"))
    close_at = _instant(evidence.get("regular_close_at"))
    checked_at = _instant(evidence.get("source_checked_at"))
    host = trusted_exchange_calendar_host(evidence.get("source_url"))
    if (day is None or day.weekday() >= 5 or
            evidence.get("session_date") != session_date or
            evidence.get("session_open") is not True):
        issues.add("SESSION_NOT_CONFIRMED_OPEN")
    if (host is None or checked_at is None
            or evidence.get("independently_checked") is not True):
        issues.add("EXCHANGE_CALENDAR_PROVENANCE_UNVERIFIED")
    if day is None or prior is None or prior >= day or prior.weekday() >= 5:
        issues.add("PREVIOUS_REGULAR_SESSION_EVIDENCE_MISSING")
    elif prior != _weekday_previous(day):
        issues.add("FROZEN_PREVIOUS_WEEKDAY_DIFFERS_FROM_EXCHANGE_SESSION")
    if day is None or close_at is None or close_at.astimezone(ET).date() != day:
        issues.add("SESSION_CLOSE_EVIDENCE_MISSING")
    elif close_at.astimezone(ET) != datetime.combine(day, time(16), tzinfo=ET):
        issues.add("FROZEN_1600_ET_CLOSE_NOT_APPLICABLE")
    return {
        "mode": MODE,
        "session_date": session_date,
        "status": "SHADOW_CALENDAR_BLOCKED" if issues else "SHADOW_CALENDAR_COMPATIBLE_NOT_AUTHENTICATED",
        "issues": sorted(issues),
        "inferred_previous_weekday": _weekday_previous(day).isoformat() if day else None,
        "supplied_previous_regular_session": prior.isoformat() if prior else None,
        "calendar_evidence_authenticated_by_module": False,
        "eligible_for_frozen_forward_scoring": False,
        "frozen_evaluator_modified": False,
        "trade_authorized": False,
    }
