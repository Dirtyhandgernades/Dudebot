"""Offline source-byte-to-claim binding shadow for OBSIDIAN P0-1.

This intentionally accepts caller-supplied JSON and HTTP receipt assertions.
It does NOT retrieve a provider response, authenticate transport or provider
ownership, certify official closes, or authorize frozen-cohort scoring. The
flat JSON fixture contract is not an actual vendor API schema. Always censor.
Never return URLs, response bodies, headers or credential-bearing fields.
"""
import hashlib
import json
from datetime import date, datetime, time
from decimal import Decimal, DecimalException, InvalidOperation
from zoneinfo import ZoneInfo

from backtest.obsidian_eod_receipt_integrity_shadow import audit_receipts

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_EOD_BODY_CLAIM_BINDING_SHADOW_V1_2026_10_29"
ET = ZoneInfo("America/New_York")
TEXT_FIELDS = (
    "source_id", "provider_organization", "symbol", "session_date", "previous_session_date",
    "security_id", "previous_security_id", "issuer_class",
    "previous_issuer_class", "kind", "regular_close_asof",
    "previous_regular_close_asof", "observed_at",
)
ACTION_FIELDS = ("status", "coverage_start", "coverage_end", "checked_at", "previous_close_basis")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError("NONFINITE_JSON_NUMBER")


def _positive(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    # Provider bytes are untrusted. Extreme JSON exponents can overflow the
    # Decimal 20%-threshold multiplication and abort the entire indexed audit.
    # This broad arithmetic safety envelope is NOT an SMG price eligibility rule.
    if not -100 <= number.adjusted() <= 100:
        return None
    return number


def _instant(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.utcoffset() is not None else None


def audit_body_bindings(session, previous, reports, receipts, collected_at,
                        session_close_at=None, previous_session_close_at=None):
    """Audit EVERY original index; never silently select matching providers."""
    if (not isinstance(previous, date) or isinstance(previous, datetime)
            or not isinstance(session, date) or isinstance(session, datetime)
            or previous >= session):
        raise ValueError("VALID_PREVIOUS_AND_CURRENT_SESSION_DATES_REQUIRED")
    receipt_audit = audit_receipts(
        session, reports, receipts, collected_at,
        session_close_at=session_close_at)
    previous_end = datetime.combine(previous, time(16), tzinfo=ET)
    if previous_session_close_at is not None:
        supplied_prior = _instant(previous_session_close_at)
        if (supplied_prior is None
                or supplied_prior.astimezone(ET).date() != previous
                or supplied_prior.astimezone(ET).timetz().replace(tzinfo=None)
                not in (time(13), time(16))):
            raise ValueError("EXTERNAL_PREVIOUS_SESSION_CLOSE_TIMESTAMP_INVALID")
        previous_end = supplied_prior.astimezone(ET)
    rows, issues, prices = [], set(receipt_audit["issues"]), {}
    identity_claims = {field: {} for field in (
        "symbol", "session_date", "previous_session_date",
        "security_id", "previous_security_id", "issuer_class",
        "previous_issuer_class", "action_coverage_start", "action_coverage_end",
        "action_security_id",
        "action_previous_security_id", "action_issuer_class",
        "action_previous_issuer_class", "corporate_action_status",
        "previous_close_basis")}
    close_end = (_instant(session_close_at).astimezone(ET) if session_close_at is not None
                 else datetime.combine(session, time(16), tzinfo=ET))
    collected = _instant(collected_at)
    count = max(len(reports), len(receipts))
    for index in range(count):
        report = reports[index] if index < len(reports) else None
        receipt = receipts[index] if index < len(receipts) else None
        r = report if isinstance(report, dict) else {}
        t = receipt if isinstance(receipt, dict) else {}
        faults = set(receipt_audit["all_source_rows"][index]["issues"])
        body = t.get("raw_body")
        parsed = None
        if not isinstance(body, bytes):
            faults.add("BODY_NOT_BYTES_OR_ABSENT")
        elif t.get("content_type", "").split(";", 1)[0].strip().lower() != "application/json" if isinstance(t.get("content_type"), str) else True:
            faults.add("NOT_EXPLICIT_APPLICATION_JSON")
        else:
            try:
                parsed = json.loads(
                    body.decode("utf-8", errors="strict"),
                    object_pairs_hook=_unique_pairs,
                    parse_float=Decimal, parse_int=Decimal,
                    parse_constant=_nonfinite,
                )
                if not isinstance(parsed, dict):
                    faults.add("JSON_ROOT_NOT_OBJECT")
                    parsed = None
            except (UnicodeError, ValueError, TypeError, RecursionError, DecimalException):
                faults.add("INVALID_DUPLICATE_OR_NONFINITE_JSON_BODY")
        if parsed is not None:
            for field in TEXT_FIELDS:
                value = parsed.get(field)
                if not isinstance(value, str) or not value or value != r.get(field):
                    faults.add("BODY_REPORT_FIELD_MISMATCH_" + field.upper())
            if parsed.get("kind") != "regular_close":
                faults.add("BODY_NOT_REGULAR_SESSION_CLOSE")
            if type(parsed.get("session_complete")) is not bool or parsed.get("session_complete") is not True or r.get("session_complete") is not True:
                faults.add("BODY_SESSION_NOT_COMPLETE")
            if parsed.get("session_date") != session.isoformat() or parsed.get("previous_session_date") != previous.isoformat():
                faults.add("BODY_WRONG_SESSION_PAIR")
            if (not parsed.get("security_id")
                    or parsed.get("security_id") != parsed.get("previous_security_id")
                    or not parsed.get("issuer_class")
                    or parsed.get("issuer_class") != parsed.get("previous_issuer_class")):
                faults.add("BODY_SECURITY_IDENTITY_NOT_STABLE")
            for field, expected, expected_close, explicit in (
                    ("regular_close_asof", session, close_end, session_close_at is not None),
                    ("previous_regular_close_asof", previous, previous_end,
                     previous_session_close_at is not None)):
                stamp = _instant(parsed.get(field))
                if stamp is None or stamp.astimezone(ET).date() != expected:
                    faults.add("BODY_CLOSE_ASOF_SESSION_DATE_MISMATCH")
                elif stamp != expected_close:
                    # A last trade or afterhours quote is not the official
                    # regular-session close, including 13:00 ET early closes.
                    faults.add("BODY_CLOSE_ASOF_NOT_EXACT_EXCHANGE_SESSION_CLOSE"
                               if explicit else "BODY_CLOSE_ASOF_NOT_EXACT_1600_ET")
            publication = _instant(parsed.get("observed_at"))
            receipt_time = _instant(t.get("retrieved_at"))
            if (publication is None or receipt_time is None or collected is None
                    or not close_end <= publication <= receipt_time <= collected):
                faults.add("BODY_PUBLICATION_RECEIPT_CHRONOLOGY_INVALID")
            for field in ("regular_close", "previous_regular_close"):
                body_price = _positive(parsed.get(field))
                report_price = _positive(r.get(field))
                if body_price is None or report_price is None or body_price != report_price:
                    faults.add("BODY_REPORT_PRICE_MISMATCH_" + field.upper())
            close = _positive(parsed.get("regular_close"))
            prior = _positive(parsed.get("previous_regular_close"))
            if close is not None and prior is not None:
                bucket = prices.setdefault((close, prior), [])
                bucket.append(index)
            action = parsed.get("corporate_action")
            report_action = r.get("corporate_action")
            # Compare every parseable source-body identity/action claim,
            # including rejected rows; never cherry-pick two agreeing ones.
            for field, value in (
                ("symbol", parsed.get("symbol")),
                ("session_date", parsed.get("session_date")),
                ("previous_session_date", parsed.get("previous_session_date")),
                ("action_coverage_start", action.get("coverage_start") if isinstance(action, dict) else None),
                ("action_coverage_end", action.get("coverage_end") if isinstance(action, dict) else None),
                ("security_id", parsed.get("security_id")),
                ("previous_security_id", parsed.get("previous_security_id")),
                ("issuer_class", parsed.get("issuer_class")),
                ("previous_issuer_class", parsed.get("previous_issuer_class")),
                ("action_security_id", action.get("security_id") if isinstance(action, dict) else None),
                ("action_previous_security_id", action.get("previous_security_id") if isinstance(action, dict) else None),
                ("action_issuer_class", action.get("issuer_class") if isinstance(action, dict) else None),
                ("action_previous_issuer_class", action.get("previous_issuer_class") if isinstance(action, dict) else None),
                ("corporate_action_status", action.get("status") if isinstance(action, dict) else None),
                ("previous_close_basis", action.get("previous_close_basis") if isinstance(action, dict) else None),
            ):
                if isinstance(value, str) and value:
                    identity_claims[field].setdefault(value, []).append(index)
            if not isinstance(action, dict) or not isinstance(report_action, dict):
                faults.add("BODY_OR_REPORT_ACTION_EVIDENCE_MISSING")
            else:
                for field in ACTION_FIELDS:
                    if (not isinstance(action.get(field), str)
                            or not action.get(field)
                            or action.get(field) != report_action.get(field)):
                        faults.add("BODY_REPORT_ACTION_MISMATCH_" + field.upper())
                # Some vendors include security/class identifiers inside their
                # action record. When supplied, bind every one to the caller's
                # action claim AND the parsed body identity; a contradictory
                # rejected third source must remain visible in the inventory.
                # Absence is not proof of identity or an authenticated action.
                for field in ("security_id", "previous_security_id",
                              "issuer_class", "previous_issuer_class"):
                    if field in action or field in report_action:
                        value = action.get(field)
                        if (not isinstance(value, str) or not value
                                or value != report_action.get(field)):
                            faults.add("BODY_REPORT_ACTION_MISMATCH_" + field.upper())
                        if (not isinstance(value, str) or not value
                                or value != parsed.get(field)):
                            faults.add("BODY_ACTION_IDENTITY_NOT_STABLE")
                if (action.get("coverage_start") != previous.isoformat()
                        or action.get("coverage_end") != session.isoformat()
                        or action.get("status") != "NONE"
                        or action.get("previous_close_basis") != "UNADJUSTED"):
                    faults.add("ACTION_WINDOW_OR_STATUS_NOT_CLEARED")
                checked = _instant(action.get("checked_at"))
                observed = _instant(collected_at)
                if (checked is None or observed is None or receipt_time is None
                        or not close_end <= checked <= receipt_time <= observed):
                    faults.add("ACTION_CHECK_TIME_INVALID")
                # The action record is embedded in the same source body as
                # its publication claim. An action check occurring *after*
                # that publication cannot have informed the published body,
                # even if both timestamps precede retrieval. Distinct action
                # sources need separate authenticated receipts; this shadow
                # must not silently backdate their evidence.
                if checked is not None and publication is not None and checked > publication:
                    faults.add("EMBEDDED_ACTION_CHECK_POSTDATES_SOURCE_PUBLICATION")
        issues.update(faults)
        rows.append({
            "index": index,
            "raw_body_sha256_computed": hashlib.sha256(body).hexdigest() if isinstance(body, bytes) else None,
            "status": "BODY_FIELDS_MATCH_UNAUTHENTICATED" if not faults else "REJECTED_CENSORED",
            "issues": sorted(faults),
        })
    for field, issue in (
        ("symbol", "PARSED_BODY_SYMBOL_CLAIM_CONFLICT"),
        ("session_date", "PARSED_BODY_SESSION_DATE_CLAIM_CONFLICT"),
        ("previous_session_date", "PARSED_BODY_PREVIOUS_SESSION_DATE_CLAIM_CONFLICT"),
        ("action_coverage_start", "PARSED_BODY_ACTION_COVERAGE_START_CLAIM_CONFLICT"),
        ("action_coverage_end", "PARSED_BODY_ACTION_COVERAGE_END_CLAIM_CONFLICT"),
        ("security_id", "PARSED_BODY_SECURITY_ID_CLAIM_CONFLICT"),
        ("previous_security_id", "PARSED_BODY_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT"),
        ("issuer_class", "PARSED_BODY_ISSUER_CLASS_CLAIM_CONFLICT"),
        ("previous_issuer_class", "PARSED_BODY_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT"),
        ("action_security_id", "PARSED_BODY_ACTION_SECURITY_ID_CLAIM_CONFLICT"),
        ("action_previous_security_id", "PARSED_BODY_ACTION_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT"),
        ("action_issuer_class", "PARSED_BODY_ACTION_ISSUER_CLASS_CLAIM_CONFLICT"),
        ("action_previous_issuer_class", "PARSED_BODY_ACTION_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT"),
        ("corporate_action_status", "PARSED_BODY_CORPORATE_ACTION_CLAIM_CONFLICT"),
        ("previous_close_basis", "PARSED_BODY_PREVIOUS_CLOSE_BASIS_CLAIM_CONFLICT"),
    ):
        if len(identity_claims[field]) > 1:
            issues.add(issue)
    groups = [
        {"regular_close": str(close), "previous_regular_close": str(prior),
         "source_indices": indices,
         "claimed_20pct_drop": close <= prior * Decimal("0.8")}
        for (close, prior), indices in sorted(prices.items())
    ]
    if len(groups) > 1:
        issues.add("PARSED_BODY_PRICE_CLAIM_CONFLICT")
    if len({g["claimed_20pct_drop"] for g in groups}) > 1:
        issues.add("PARSED_BODY_CLAIMS_STRADDLE_20PCT_THRESHOLD")
    return {
        "mode": MODE, "policy": POLICY,
        "session_date": session.isoformat(),
        "previous_session_date": previous.isoformat(),
        "supplied_report_count": len(reports),
        "supplied_receipt_count": len(receipts),
        "indexed_count": len(rows),
        "byte_bound_unauthenticated_count": sum(
            x["status"] == "BODY_FIELDS_MATCH_UNAUTHENTICATED" for x in rows),
        "all_source_rows": rows,
        "all_parseable_body_price_claim_groups": groups,
        "issues": sorted(issues),
        "status": "BLOCKED_CENSORED" if issues else "BODY_CONSISTENT_EXTERNAL_AUTH_PENDING",
        "source_ownership_and_transport_authenticated": False,
        "provider_specific_official_schema_authenticated": False,
        "exchange_calendar_and_corporate_actions_authenticated": False,
        "provider_organization_independence_authenticated": False,
        "official_close_verified": False,
        "eligible_for_frozen_scoring": False,
        "verified_20pct_prediction_success": None,
        "outcome_censored_pending_external_evidence": True,
        "smg_trade_authorized": False,
    }
