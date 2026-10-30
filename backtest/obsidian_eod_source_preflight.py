"""Research-only preflight for independently collected EOD evidence.

Does not produce an official-close verdict, change frozen scoring, query a
provider, or authorize a trade. All collected reports must be supplied: do not
select two agreeing reports while silently dropping a contradictory third.
"""
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit
from backtest.obsidian_eod_receipt_integrity_shadow import _host_parent_hint
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MAX_PRICE_DIFFERENCE = Decimal("0.005")
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"


def _aware(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.utcoffset() is not None else None


def _positive(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, OverflowError):
        return None
    # Untrusted vendor claims can be finite but carry exponents so large that
    # a later 20%-threshold multiplication raises decimal.Overflow and aborts
    # the entire complete-source audit. Keep them as rejected/censored rows.
    # This is a generous arithmetic guard, NOT an SMG price eligibility rule.
    if not number.is_finite() or number <= 0 or not -100 <= number.adjusted() <= 100:
        return None
    return number


def _source_host(value):
    """Conservative URL syntax guard; does NOT authenticate provider ownership."""
    if (not isinstance(value, str)
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.netloc
                or parsed.username is not None or parsed.password is not None
                or parsed.fragment or parsed.port not in (None, 443)):
            return None
        host = parsed.hostname
        if not host or host.endswith(".") or any(ch.isspace() for ch in host):
            return None
        return host.lower()
    except ValueError:
        return None


def preflight(symbol, session_date, previous_session_date, reports, collected_at):
    """Fail closed on *any* supplied conflict, stale record or provider alias.

    A consistent result is only a candidate for subsequent independent
    security-identity/corporate-action and official-close verification.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("SYMBOL_REQUIRED")
    if not isinstance(session_date, date) or isinstance(session_date, datetime):
        raise ValueError("SESSION_DATE_REQUIRED")
    if not isinstance(previous_session_date, date) or isinstance(previous_session_date, datetime) or previous_session_date >= session_date:
        raise ValueError("PREVIOUS_SESSION_DATE_REQUIRED")
    if not isinstance(reports, list):
        raise ValueError("COMPLETE_COLLECTED_REPORT_LIST_REQUIRED")
    end = datetime.combine(session_date, time(16, 0), tzinfo=ET)
    # The previous-session reference must itself be an exact regular close.
    # Previous early closes require a separate registered calendar protocol;
    # this normal-session shadow preflight censors them rather than guessing.
    previous_end = datetime.combine(previous_session_date, time(16, 0), tzinfo=ET)
    collection_time = _aware(collected_at)
    if collection_time is None or collection_time < end:
        raise ValueError("POST_CLOSE_COLLECTION_TIMESTAMP_REQUIRED")
    issues, accepted = set(), []
    seen_source_ids = set()
    for report in reports:
        if not isinstance(report, dict):
            issues.add("MALFORMED_SOURCE_RECORD")
            continue
        source = report.get("source_id")
        # A repeated source receipt cannot be counted as two independent reports,
        # even if its self-attested provider name and URL have changed.
        if isinstance(source, str) and source.strip():
            if source in seen_source_ids:
                issues.add("DUPLICATE_SOURCE_ID")
            seen_source_ids.add(source)
        group = report.get("provider_group")
        url = report.get("url")
        host = _source_host(url)
        observed = _aware(report.get("observed_at"))
        close_asof = _aware(report.get("regular_close_asof"))
        previous_close_asof = _aware(report.get("previous_regular_close_asof"))
        close = _positive(report.get("regular_close"))
        prior = _positive(report.get("previous_regular_close"))
        if (not isinstance(source, str) or not source.strip()
                or not isinstance(group, str) or not group.strip()
                or not host or close is None or prior is None):
            issues.add("INVALID_SOURCE_PROVENANCE_OR_PRICE")
            continue
        if (report.get("symbol") != symbol
                or report.get("session_date") != session_date.isoformat()
                or report.get("previous_session_date") != previous_session_date.isoformat()
                or report.get("kind") != "regular_close"
                or report.get("session_complete") is not True):
            issues.add("WRONG_SECURITY_SESSION_OR_PRICE_KIND")
            continue
        # Source publication/collection time is not the time of its price.
        # A 15:59:35 last trade, even on a page labeled "At Close",
        # is not independently evidenced as the 16:00 ET regular close.
        if close_asof is None or close_asof.astimezone(ET) != end:
            issues.add("NON_1600_ET_REGULAR_CLOSE_SOURCE")
            continue
        if (previous_close_asof is None
                or previous_close_asof.astimezone(ET) != previous_end):
            issues.add("PREVIOUS_CLOSE_NOT_EXACT_1600_ET_SOURCE")
            continue
        if observed is None or not end <= observed <= collection_time:
            issues.add("STALE_OR_UNTIMED_SOURCE")
            continue
        accepted.append((source, group, host, close, prior))
    if len(accepted) < 2 or len({x[1] for x in accepted}) < 2 or len({x[2] for x in accepted}) < 2:
        issues.add("INSUFFICIENT_DISTINCT_HOST_AND_PROVIDER_EVIDENCE")
    # Different subdomains may share one vendor organization. A third source
    # must not conceal conflicting claimed organizations on that same parent.
    # This is only an alias-screening hint, never proof of legal independence.
    parent_groups = {}
    for _, group, host, _, _ in accepted:
        parent_groups.setdefault(_host_parent_hint(host), set()).add(group)
    if len(parent_groups) < 2:
        issues.add("INSUFFICIENT_DISTINCT_PROVIDER_PARENT_HOST_EVIDENCE")
    if any(len(groups) > 1 for groups in parent_groups.values()):
        issues.add("CLAIMED_PROVIDER_GROUPS_SHARE_SOURCE_HOST_PARENT_HINT")
    if accepted:
        closes = [x[3] for x in accepted]
        priors = [x[4] for x in accepted]
        if max(closes) - min(closes) > MAX_PRICE_DIFFERENCE:
            issues.add("CONFLICTING_REGULAR_CLOSE_REPORTS")
        if max(priors) - min(priors) > MAX_PRICE_DIFFERENCE:
            issues.add("CONFLICTING_PREVIOUS_CLOSE_REPORTS")
    # Numerical half-cent agreement can still straddle the exact 20% event
    # boundary. Never silently turn an ambiguous classification into a hit.
    # A distinct prior-close claim also changes the reference denominator,
    # even when its difference is smaller than the price tolerance.
    if len(accepted) >= 2:
        if len(set(priors)) > 1:
            issues.add("THRESHOLD_REFERENCE_PREVIOUS_CLOSE_DISAGREEMENT")
        elif min(closes) <= priors[0] * Decimal("0.8") < max(closes):
            issues.add("TWENTY_PERCENT_THRESHOLD_STRADDLED")
    return {
        "mode": MODE,
        "symbol": symbol,
        "session_date": session_date.isoformat(),
        "supplied_reports": len(reports),
        "accepted_reports": len(accepted),
        "distinct_provider_groups": len({x[1] for x in accepted}),
        "distinct_hosts": len({x[2] for x in accepted}),
        "status": "BLOCKED_SOURCE_EVIDENCE" if issues else "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE",
        "issues": sorted(issues),
        "corporate_action_and_security_identity_verified": False,
        "eligible_for_frozen_forward_scoring": False,
        "early_hit_or_profit_verified": False,
    }
