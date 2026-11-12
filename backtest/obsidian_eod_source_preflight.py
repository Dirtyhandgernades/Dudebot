"""Research-only preflight for independently collected EOD evidence.

Does not produce an official-close verdict, change frozen scoring, query a
provider, or authorize a trade. All collected reports must be supplied: do not
select two agreeing reports while silently dropping a contradictory third.
"""
import re
import unicodedata
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from backtest.obsidian_eod_receipt_integrity_shadow import _host_parent_hint, _safe_host
from backtest.obsidian_two_provider_close_reconciliation import _scheduled_cash_session_2026
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MAX_PRICE_DIFFERENCE = Decimal("0.005")
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"


def _aware(value):
    """Fail closed on timestamp precision unsupported by datetime.

    fromisoformat silently truncates seventh-plus fractional digits, which
    could turn 16:00:00.0000001 into a false exact 16:00 ET close. This
    caller-supplied preflight uses the same strict ISO instant contract as
    the byte-binding shadow; neither authenticates an official source.
    """
    if not isinstance(value, str) or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})",
            value) is None:
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
    if (not number.is_finite() or number <= 0
            or not -100 <= number.adjusted() <= 100
            or len(number.as_tuple().digits) > 100):
        return None
    return number


def _exact_spread(values):
    """Exact source-price spread within the 100-significant-digit intake bound."""
    with localcontext() as ctx:
        ctx.prec = 512
        return max(values) - min(values)


def _exact_threshold(prior):
    """Avoid default-context rounding at the 20% claim boundary."""
    with localcontext() as ctx:
        ctx.prec = 512
        return prior * Decimal("0.8")


def _canonical_label(value):
    """Conservative case/whitespace comparison key for supplied labels.

    Mirrors the complete-source inventory's alias screen. This does not
    authenticate legal provider ownership or alter source receipts.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    # NFKC folds canonically equivalent and compatibility spellings. Invisible
    # format controls (e.g. zero-width and bidi markers) must not manufacture
    # an apparently independent provider or source receipt.
    normalized = unicodedata.normalize("NFKC", value)
    if any(unicodedata.category(char) == "Cf" for char in normalized):
        return None
    return " ".join(normalized.split()).casefold() or None


def _source_host(value):
    """Reuse the strict external HTTPS receipt host syntax guard.

    This rejects local/IP-literal and malformed hosts, but does not establish
    ownership, transport authenticity or legal provider independence.
    """
    return _safe_host(value)



# NYSE's published 2026 cash-equity calendar lists 13:00 ET early closes
# on Nov 27 and Dec 24. These cannot satisfy this normal-session-only
# 16:00 ET source contract; do not relabel the frozen scoring calendar.
# https://www.nyse.com/trade/hours-calendars
_PUBLISHED_EARLY_CLOSES_2026 = frozenset({
    date(2026, 11, 27), date(2026, 12, 24),
})


def _published_2026_calendar_issues(session_date, previous_session_date):
    """Static NYSE schedule screen, NOT authenticated actual-session evidence.

    Reject a non-adjacent prior trading date, scheduled closures, out-of-scope
    years and early-close 13:00 ET auctions. An unexpected exchange closure,
    security halt or provider-specific calendar remains externally unverified.
    """
    issues = set()
    current_scheduled = _scheduled_cash_session_2026(session_date)
    previous_scheduled = _scheduled_cash_session_2026(previous_session_date)
    if not current_scheduled or not previous_scheduled:
        issues.add("CLOSED_OR_UNVERIFIED_PUBLISHED_2026_SESSION")
    if (session_date in _PUBLISHED_EARLY_CLOSES_2026
            or previous_session_date in _PUBLISHED_EARLY_CLOSES_2026):
        issues.add("EARLY_CLOSE_REQUIRES_SEPARATE_1300_ET_SOURCE_CONTRACT")
    if current_scheduled and previous_scheduled:
        preceding = session_date - timedelta(days=1)
        while preceding.year == 2026 and not _scheduled_cash_session_2026(preceding):
            preceding -= timedelta(days=1)
        if preceding != previous_session_date:
            issues.add("PREVIOUS_SESSION_NOT_ADJACENT_ON_PUBLISHED_2026_CALENDAR")
    return issues


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
    issues, accepted = _published_2026_calendar_issues(session_date, previous_session_date), []
    # Inventory every parseable *claim*, including rejected/late/wrong-symbol
    # third sources. Such claims are not authenticated prices and cannot be
    # used as outcomes; they must not silently disappear from conflict review.
    all_close_claims, all_prior_claims = {}, {}
    seen_source_ids = set()
    for report_index, report in enumerate(reports):
        if not isinstance(report, dict):
            issues.add("MALFORMED_SOURCE_RECORD")
            continue
        for field, bucket in (("regular_close", all_close_claims),
                              ("previous_regular_close", all_prior_claims)):
            claim = _positive(report.get(field))
            if claim is not None:
                bucket.setdefault(claim, []).append(report_index)
        source = report.get("source_id")
        # A repeated source receipt cannot be counted as two independent reports,
        # even if its self-attested provider name and URL have changed.
        source_key = _canonical_label(source)
        if source_key is not None:
            if source_key in seen_source_ids:
                issues.add("DUPLICATE_SOURCE_ID")
            seen_source_ids.add(source_key)
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
                or source_key is None or _canonical_label(group) is None
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
        # Raw source/provider spellings are caller claims, not independent
        # organizations. Normalize only the comparison keys, preserving the
        # full supplied report and never promoting it to official evidence.
        accepted.append((source_key, _canonical_label(group), host, close, prior))
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
        if _exact_spread(closes) > MAX_PRICE_DIFFERENCE:
            issues.add("CONFLICTING_REGULAR_CLOSE_REPORTS")
        if _exact_spread(priors) > MAX_PRICE_DIFFERENCE:
            issues.add("CONFLICTING_PREVIOUS_CLOSE_REPORTS")
    # Numerical half-cent agreement can still straddle the exact 20% event
    # boundary. Never silently turn an ambiguous classification into a hit.
    # A distinct prior-close claim also changes the reference denominator,
    # even when its difference is smaller than the price tolerance.
    if len(accepted) >= 2:
        if len(set(priors)) > 1:
            issues.add("THRESHOLD_REFERENCE_PREVIOUS_CLOSE_DISAGREEMENT")
        elif min(closes) <= _exact_threshold(priors[0]) < max(closes):
            issues.add("TWENTY_PERCENT_THRESHOLD_STRADDLED")
    # Accepted-source tolerances alone miss contradictory third-source claims
    # rejected for wrong security, stale timing, or malformed provenance.
    # Report these as untrusted CLAIM conflicts, never as official closes.
    if (len(all_close_claims) > 1 and
            _exact_spread(list(all_close_claims)) > MAX_PRICE_DIFFERENCE):
        issues.add("ALL_SUPPLIED_REGULAR_CLOSE_CLAIM_CONFLICT")
    if len(all_prior_claims) > 1:
        issues.add("ALL_SUPPLIED_PREVIOUS_CLOSE_REFERENCE_DISAGREEMENT")
    # Multiple *untrusted* previous-close claims can move the 20% boundary
    # across even one identical current-close claim. Inventory the entire
    # claimed close/prior cross-product without promoting any claim to an
    # authenticated outcome. A boundary-equal close counts as <=20% down.
    if all_prior_claims and all_close_claims:
        thresholds = [_exact_threshold(prior) for prior in all_prior_claims]
        if (min(all_close_claims) <= max(thresholds)
                and max(all_close_claims) > min(thresholds)):
            issues.add("ALL_SUPPLIED_CLAIMS_STRADDLE_20PCT_THRESHOLD")
    return {
        "mode": MODE,
        "symbol": symbol,
        "session_date": session_date.isoformat(),
        "supplied_reports": len(reports),
        "accepted_reports": len(accepted),
        "all_parseable_regular_close_claim_groups": [
            {"claimed_regular_close": str(price), "source_indices": indices}
            for price, indices in sorted(all_close_claims.items())],
        "all_parseable_previous_close_claim_groups": [
            {"claimed_previous_regular_close": str(price), "source_indices": indices}
            for price, indices in sorted(all_prior_claims.items())],
        "untrusted_claim_inventory_not_official": True,
        "distinct_provider_groups": len({x[1] for x in accepted}),
        "distinct_hosts": len({x[2] for x in accepted}),
        "status": "BLOCKED_SOURCE_EVIDENCE" if issues else "CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE",
        "issues": sorted(issues),
        "published_2026_calendar_screen_only": True,
        "actual_exchange_session_authenticated": False,
        "corporate_action_and_security_identity_verified": False,
        "eligible_for_frozen_forward_scoring": False,
        "early_hit_or_profit_verified": False,
    }
