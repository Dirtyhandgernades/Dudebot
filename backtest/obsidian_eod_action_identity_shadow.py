"""Fail-closed corporate-action and security-identity claim audit for EOD sources.

Research-only companion to obsidian_eod_conflict_inventory. This module
NEVER authenticates a source, certifies a close, adjusts a price, or scores
a prediction. Caller must independently retrieve and archive source receipts.
"""
from datetime import date, datetime, time
from backtest.obsidian_eod_source_preflight import _source_host
from backtest.obsidian_eod_receipt_integrity_shadow import _host_parent_hint
from zoneinfo import ZoneInfo

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_EOD_ACTION_IDENTITY_SHADOW_V1_2026_10_29"
ET = ZoneInfo("America/New_York")
ACTIONS = {"NONE", "SPLIT", "REVERSE_SPLIT", "MERGER", "SYMBOL_CHANGE", "OTHER", "UNKNOWN"}
BASES = {"UNADJUSTED", "ADJUSTED", "UNKNOWN"}


def _instant(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.utcoffset() is not None else None


def _host(value):
    """Shared strict URL syntax screen; not provider ownership authentication."""
    return _source_host(value)


def audit_action_identity(symbol, session, previous, reports, collected_at):
    """Index every supplied source; require an explicit action/identity window.

    A structurally consistent pair is still *unauthenticated* and censored.
    No claim of "NONE" proves the absence of a split or a symbol change.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("SYMBOL_REQUIRED")
    if (not isinstance(session, date) or isinstance(session, datetime)
            or not isinstance(previous, date) or isinstance(previous, datetime)
            or previous >= session):
        raise ValueError("VALID_SESSION_CHAIN_REQUIRED")
    if not isinstance(reports, list):
        raise ValueError("COMPLETE_SOURCE_REPORT_LIST_REQUIRED")
    end = datetime.combine(session, time(16), tzinfo=ET)
    collected = _instant(collected_at)
    if collected is None or collected < end:
        raise ValueError("POSTCLOSE_COLLECTION_TIME_REQUIRED")

    rows, issues, valid, claims, seen = [], set(), [], [], set()
    if not reports:
        issues.add("NO_CORPORATE_ACTION_SOURCE_REPORTS")
    for index, report in enumerate(reports):
        r = report if isinstance(report, dict) else {}
        action = r.get("corporate_action_evidence")
        a = action if isinstance(action, dict) else {}
        faults = set()
        if not isinstance(report, dict):
            faults.add("MALFORMED_SOURCE_RECORD")
        source = r.get("source_id")
        group = r.get("provider_organization")
        source_host = _host(r.get("source_url"))
        action_host = _host(a.get("source_url"))
        if not isinstance(source, str) or not source.strip() or source in seen:
            faults.add("DUPLICATE_OR_MISSING_SOURCE_ID")
        else:
            seen.add(source)
        if not isinstance(group, str) or not group.strip() or not source_host:
            faults.add("PROVIDER_OR_SOURCE_URL_NOT_EVIDENCED")
        if not isinstance(action, dict) or not action_host:
            faults.add("ACTION_SOURCE_PROVENANCE_MISSING")
        security = r.get("security_id")
        prior_security = r.get("previous_security_id")
        issuer_class = r.get("issuer_class")
        prior_class = r.get("previous_issuer_class")
        if (not isinstance(security, str) or not security.strip()
                or security != prior_security
                or not isinstance(issuer_class, str) or not issuer_class.strip()
                or issuer_class != prior_class
                or a.get("security_id") != security
                or a.get("previous_security_id") != prior_security
                or a.get("issuer_class") != issuer_class):
            faults.add("SECURITY_OR_ISSUER_CLASS_IDENTITY_NOT_MATCHED")
        if (r.get("symbol") != symbol
                or r.get("session_date") != session.isoformat()
                or r.get("previous_session_date") != previous.isoformat()):
            faults.add("WRONG_SECURITY_OR_SESSION")
        status = a.get("status")
        basis = a.get("previous_close_basis")
        if (not isinstance(status, str) or status not in ACTIONS
                or not isinstance(basis, str) or basis not in BASES):
            faults.add("ACTION_OR_PREVIOUS_CLOSE_BASIS_UNRESOLVED")
        if status != "NONE" or basis != "UNADJUSTED":
            faults.add("ACTION_OR_ADJUSTED_CLOSE_REQUIRES_EXTERNAL_RECONCILIATION")
        if (a.get("coverage_start") != previous.isoformat()
                or a.get("coverage_end") != session.isoformat()):
            faults.add("CORPORATE_ACTION_WINDOW_NOT_COMPLETE")
        checked = _instant(a.get("checked_at"))
        source_observed = _instant(r.get("observed_at"))
        if (checked is None or source_observed is None
                or not end <= checked <= collected
                or not end <= source_observed <= collected):
            faults.add("ACTION_OR_SOURCE_TIMESTAMP_NOT_POSTCLOSE")
        claims.append((index, security, issuer_class, status, basis))
        if faults:
            issues.update(faults)
        else:
            valid.append((index, group, source_host, action_host))
        rows.append({
            "index": index,
            "source_id": source if isinstance(source, str) else None,
            "provider_organization_claim": group if isinstance(group, str) else None,
            "source_host": source_host,
            "action_evidence_host": action_host,
            "security_id_claim": security if isinstance(security, str) else None,
            "issuer_class_claim": issuer_class if isinstance(issuer_class, str) else None,
            "previous_issuer_class_claim": prior_class if isinstance(prior_class, str) else None,
            "action_previous_security_id_claim":
                a.get("previous_security_id") if isinstance(a.get("previous_security_id"), str) else None,
            "action_status_claim": status if isinstance(status, str) else None,
            "previous_close_basis_claim": basis if isinstance(basis, str) else None,
            "coverage_start_claim": a.get("coverage_start") if isinstance(a.get("coverage_start"), str) else None,
            "coverage_end_claim": a.get("coverage_end") if isinstance(a.get("coverage_end"), str) else None,
            "checked_at_claim": a.get("checked_at") if isinstance(a.get("checked_at"), str) else None,
            "status": "STRUCTURALLY_VALID_UNAUTHENTICATED" if not faults else "REJECTED_CENSORED",
            "issues": sorted(faults),
        })
    if len({x[1] for x in valid}) < 2 or len({x[2] for x in valid}) < 2:
        issues.add("TWO_DISTINCT_PROVIDER_ORGANIZATIONS_AND_HOSTS_NOT_ESTABLISHED")
    # Separate price-feed hosts do not establish independent corporate-action
    # evidence when every provider cites the same upstream action source.
    # Only structurally valid action records may establish source diversity;
    # even distinct hosts remain self-attested until externally authenticated.
    if len({x[3] for x in valid}) < 2:
        issues.add("TWO_DISTINCT_CORPORATE_ACTION_SOURCE_HOSTS_NOT_ESTABLISHED")
    # Screen apparent parent-domain aliases for both price and action sources.
    # Even a third distinct provider cannot mask two conflicting group claims
    # on the same parent. This heuristic is not legal-ownership verification.
    for host_index, label in ((2, "PRICE_SOURCE"), (3, "ACTION_SOURCE")):
        parent_groups = {}
        for item in valid:
            parent_groups.setdefault(_host_parent_hint(item[host_index]), set()).add(item[1])
        if len(parent_groups) < 2:
            issues.add("TWO_DISTINCT_" + label + "_PARENT_HINTS_NOT_ESTABLISHED")
        if any(len(groups) > 1 for groups in parent_groups.values()):
            issues.add("CLAIMED_PROVIDER_GROUPS_SHARE_" + label + "_PARENT_HINT")
    for position, code in ((1, "CROSS_SOURCE_SECURITY_IDENTITY_CLAIM_CONFLICT"),
                           (2, "CROSS_SOURCE_ISSUER_CLASS_CLAIM_CONFLICT"),
                           (3, "CROSS_SOURCE_CORPORATE_ACTION_CLAIM_CONFLICT"),
                           (4, "CROSS_SOURCE_PREVIOUS_CLOSE_BASIS_CLAIM_CONFLICT")):
        if len({x[position] for x in claims if isinstance(x[position], str)}) > 1:
            issues.add(code)
    # A rejected third provider may agree on current class/identity but claim
    # a different previous-session share class or action-record prior identity.
    # Index those claims separately, including missing/unparseable claims,
    # without treating rejected evidence as authenticated source truth.
    previous_class_groups = {}
    action_previous_security_groups = {}
    missing_previous_class = []
    missing_action_previous_security = []
    for item in rows:
        index = item["index"]
        destination = ("valid" if item["status"] ==
                       "STRUCTURALLY_VALID_UNAUTHENTICATED" else "rejected")
        for value, groups, missing in (
            (item["previous_issuer_class_claim"], previous_class_groups,
             missing_previous_class),
            (item["action_previous_security_id_claim"],
             action_previous_security_groups, missing_action_previous_security),
        ):
            if not isinstance(value, str) or not value.strip():
                missing.append(index)
                continue
            groups.setdefault(value, {"valid": [], "rejected": []})[destination].append(index)
    if len(previous_class_groups) > 1:
        issues.add("CROSS_SOURCE_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT")
    if len(action_previous_security_groups) > 1:
        issues.add("CROSS_SOURCE_ACTION_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT")
    previous_class_claim_groups = [
        {"previous_issuer_class": value,
         "structurally_valid_source_indices": groups["valid"],
         "rejected_source_indices": groups["rejected"]}
        for value, groups in sorted(previous_class_groups.items())
    ]
    action_previous_security_id_claim_groups = [
        {"action_previous_security_id": value,
         "structurally_valid_source_indices": groups["valid"],
         "rejected_source_indices": groups["rejected"]}
        for value, groups in sorted(action_previous_security_groups.items())
    ]
    return {
        "mode": MODE, "policy": POLICY,
        "symbol": symbol, "session_date": session.isoformat(),
        "previous_session_date": previous.isoformat(),
        "supplied_report_count": len(reports), "retained_report_count": len(rows),
        "structurally_valid_report_count": len(valid),
        "all_source_rows": rows, "issues": sorted(issues),
        "previous_issuer_class_claim_groups": previous_class_claim_groups,
        "action_previous_security_id_claim_groups": action_previous_security_id_claim_groups,
        "unparseable_previous_issuer_class_claim_source_indices": missing_previous_class,
        "unparseable_action_previous_security_id_claim_source_indices":
            missing_action_previous_security,
        "status": "BLOCKED_CENSORED" if issues else "STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING",
        "provider_ownership_authenticated": False,
        "source_packet_authenticity_verified": False,
        "exchange_calendar_authenticated": False,
        "security_identity_and_corporate_actions_authenticated": False,
        "official_close_verified": False, "eligible_for_frozen_scoring": False,
        "verified_20pct_prediction_success": None,
        "outcome_censored_pending_external_evidence": True,
        "smg_trade_authorized": False,
    }
