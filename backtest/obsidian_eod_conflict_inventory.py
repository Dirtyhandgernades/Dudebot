"""Complete indexed, fail-closed EOD source/conflict inventory. Research only.

This is an OFFLINE audit of supplied claims, not a market-data fetch or a
certificate of provider ownership, official closes, calendar, identity, or
corporate actions. It retains all supplied row positions, auditable claim
fields, and canonical per-row digests, but is NOT a raw source archive.
Never feed its results directly into frozen scoring.
"""
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

POLICY = "OBSIDIAN_EOD_ALL_SOURCE_CONFLICT_LEDGER_V1_2026_10_29"
MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
ET = ZoneInfo("America/New_York")
CENT = Decimal("0.005")


def instant(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def positive(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() and number > 0 else None


def host(value):
    try:
        parsed = urlsplit(value) if isinstance(value, str) else None
        return parsed.hostname if parsed and parsed.scheme == "https" else None
    except ValueError:
        return None


def report_digest(report):
    """Fingerprint the complete supplied JSON row without echoing URL secrets.

    Non-JSON Python objects are censored; a separate secure source archive is
    still required for independently reproducible provenance.
    """
    try:
        canonical = json.dumps(report, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        return None
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def claim(value):
    """Retain an auditable scalar claim without propagating complex objects."""
    return value if isinstance(value, str) else (
        str(value) if type(value) in (int, float, Decimal) else None)


def inventory(symbol, session, previous, calendar, reports, collected_at):
    """Keep EVERY supplied report, including rejected and contradictory ones.

    `calendar` and provider organizations are supplied assertions. An
    independent external source retrieval, source-ownership check, exchange
    calendar verification, issuer-ID and action review are still mandatory.
    """
    if not isinstance(symbol, str) or not symbol or not isinstance(reports, list):
        raise ValueError("SYMBOL_AND_COMPLETE_REPORT_LIST_REQUIRED")
    if not isinstance(session, date) or isinstance(session, datetime) or not isinstance(previous, date) or isinstance(previous, datetime) or previous >= session:
        raise ValueError("VALID_TRADING_SESSION_PAIR_REQUIRED")
    observed = instant(collected_at)
    if observed is None:
        raise ValueError("AWARE_COLLECTION_TIME_REQUIRED")
    issues = set()
    cal = calendar if isinstance(calendar, dict) else {}
    end = instant(cal.get("regular_close_at"))
    prior_end = instant(cal.get("previous_regular_close_at"))
    early = cal.get("early_close") is True
    if (cal.get("session_date") != session.isoformat()
            or cal.get("previous_session_date") != previous.isoformat()
            or cal.get("session_open") is not True
            or not host(cal.get("exchange_calendar_url"))
            or end is None or prior_end is None
            or end.astimezone(ET).date() != session
            or prior_end.astimezone(ET).date() != previous
            or end >= observed or prior_end >= end):
        issues.add("UNVERIFIED_OR_INVALID_EXCHANGE_SESSION_CHAIN")
    if end is not None:
        et = end.astimezone(ET)
        if (et.hour, et.minute, et.second, et.microsecond) != ((13, 0, 0, 0) if early else (16, 0, 0, 0)):
            issues.add("EXCHANGE_CLOSE_TIME_CONFLICT")
    if early:
        issues.add("EARLY_CLOSE_REQUIRES_SEPARATE_NONFROZEN_PROTOCOL")
    if not reports:
        issues.add("NO_EOD_SOURCE_REPORTS")
    seen_ids, groups, hosts = set(), set(), set()
    valid = []
    rows = []
    for index, report in enumerate(reports):
        faults = set()
        r = report if isinstance(report, dict) else {}
        digest = report_digest(report)
        if not isinstance(report, dict):
            faults.add("MALFORMED_SOURCE_RECORD")
        if digest is None:
            faults.add("NON_JSON_SOURCE_RECORD_NOT_REPRODUCIBLY_HASHABLE")
        source = r.get("source_id")
        group = r.get("provider_organization")
        domain = host(r.get("source_url"))
        if not isinstance(source, str) or not source or not isinstance(group, str) or not group or not domain:
            faults.add("SOURCE_OWNERSHIP_OR_URL_MISSING")
        if not isinstance(source, str) or not source or source in seen_ids:
            faults.add("DUPLICATE_OR_MISSING_SOURCE_ID")
        if isinstance(source, str) and source:
            seen_ids.add(source)
        if (r.get("symbol") != symbol or r.get("session_date") != session.isoformat()
                or r.get("previous_session_date") != previous.isoformat()
                or r.get("kind") != "regular_close" or r.get("session_complete") is not True):
            faults.add("WRONG_SECURITY_SESSION_OR_PRICE_KIND")
        security_id = r.get("security_id")
        if not isinstance(security_id, str) or not security_id or r.get("previous_security_id") != security_id:
            faults.add("SECURITY_IDENTITY_NOT_MATCHED")
        close = positive(r.get("regular_close"))
        prior = positive(r.get("previous_regular_close"))
        if close is None or prior is None:
            faults.add("INVALID_CLOSE_OR_PRIOR_PRICE")
        asof = instant(r.get("regular_close_asof"))
        prev_asof = instant(r.get("previous_regular_close_asof"))
        stamp = instant(r.get("observed_at"))
        if end is None or asof != end or prior_end is None or prev_asof != prior_end:
            faults.add("CLOSE_ASOF_NOT_EXACT_EXCHANGE_SESSION_END")
        if stamp is None or end is None or not end <= stamp <= observed:
            faults.add("SOURCE_OBSERVATION_NOT_POSTCLOSE_OR_FUTURE")
        if faults:
            issues.update(faults)
        else:
            groups.add(group)
            hosts.add(domain)
            valid.append((index, group, domain, close, prior))
        rows.append({
            "index": index,
            "source_id": source if isinstance(source, str) else None,
            "provider_organization_claim": group if isinstance(group, str) else None,
            "source_host": domain,
            "supplied_report_sha256": digest,
            "source_claims": {
                "symbol": claim(r.get("symbol")),
                "session_date": claim(r.get("session_date")),
                "previous_session_date": claim(r.get("previous_session_date")),
                "security_id": claim(r.get("security_id")),
                "previous_security_id": claim(r.get("previous_security_id")),
                "kind": claim(r.get("kind")),
                "session_complete": r.get("session_complete") if type(r.get("session_complete")) is bool else None,
                "regular_close": claim(r.get("regular_close")),
                "previous_regular_close": claim(r.get("previous_regular_close")),
                "regular_close_asof": claim(r.get("regular_close_asof")),
                "previous_regular_close_asof": claim(r.get("previous_regular_close_asof")),
                "observed_at": claim(r.get("observed_at")),
            },
            "status": "STRUCTURALLY_VALID_UNAUTHENTICATED" if not faults else "REJECTED_CENSORED",
            "issues": sorted(faults),
        })
    if len(groups) < 2 or len(hosts) < 2:
        issues.add("TWO_DISTINCT_PROVIDER_ORGANIZATIONS_AND_HOSTS_NOT_ESTABLISHED")
    # Every distinct close/prior pair is represented, including agreement
    # groups and contradictory third-party claims. This is not a verdict.
    price_groups = {}
    for index, group, domain, close, prior in valid:
        price_groups.setdefault((close, prior), []).append(index)
    price_claim_groups = [
        {"regular_close": str(close), "previous_regular_close": str(prior),
         "source_indices": indices,
         "claimed_20pct_drop": close <= prior * Decimal("0.8")}
        for (close, prior), indices in sorted(price_groups.items())
    ]
    if len({g["claimed_20pct_drop"] for g in price_claim_groups}) > 1:
        issues.add("SOURCE_CLAIM_20PCT_CLASSIFICATION_DISAGREEMENT")
    if valid:
        closes = [x[3] for x in valid]
        priors = [x[4] for x in valid]
        if max(closes) - min(closes) > CENT:
            issues.add("ALL_SOURCE_REGULAR_CLOSE_CONFLICT")
        if max(priors) - min(priors) > CENT:
            issues.add("ALL_SOURCE_PREVIOUS_CLOSE_CONFLICT")
        # Even within half a cent, a 20% boundary conflict is material.
        if min(priors) != max(priors):
            issues.add("THRESHOLD_REFERENCE_PREVIOUS_CLOSE_DISAGREEMENT")
        elif min(closes) <= priors[0] * Decimal("0.8") < max(closes):
            issues.add("TWENTY_PERCENT_THRESHOLD_STRADDLED")
    return {
        "mode": MODE, "policy": POLICY, "symbol": symbol,
        "session_date": session.isoformat(), "previous_session_date": previous.isoformat(),
        "collected_at": collected_at, "supplied_report_count": len(reports),
        "retained_report_count": len(rows), "structurally_valid_report_count": len(valid),
        "distinct_claimed_provider_organizations": len(groups),
        "source_rows": rows, "price_claim_groups": price_claim_groups,
        "all_supplied_rows_indexed": len(rows) == len(reports),
        "raw_source_packets_archived_by_module": False,
        "issues": sorted(issues),
        "structural_status": "BLOCKED_CENSORED" if issues else "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING",
        "exchange_calendar_independently_authenticated": False,
        "provider_organization_ownership_authenticated": False,
        "security_identity_and_corporate_actions_authenticated": False,
        "official_regular_close_verified": False,
        "eligible_for_frozen_scoring": False, "verified_20pct_prediction_success": None,
        "smg_trade_authorized": False, "outcome_censored_pending_external_evidence": True,
    }
