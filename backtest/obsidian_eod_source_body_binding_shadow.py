"""Offline source-byte-to-claim binding shadow for OBSIDIAN P0-1.

This intentionally accepts caller-supplied JSON and HTTP receipt assertions.
It does NOT retrieve a provider response, authenticate transport or provider
ownership, certify official closes, or authorize frozen-cohort scoring. The
flat JSON fixture contract is not an actual vendor API schema. Always censor.
Never return URLs, response bodies, headers or credential-bearing fields.
"""
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from backtest.obsidian_eod_receipt_integrity_shadow import audit_receipts

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_EOD_BODY_CLAIM_BINDING_SHADOW_V1_2026_10_29"
ET = ZoneInfo("America/New_York")
TEXT_FIELDS = (
    "source_id", "symbol", "session_date", "previous_session_date",
    "security_id", "previous_security_id", "issuer_class",
    "previous_issuer_class", "kind", "regular_close_asof",
    "previous_regular_close_asof",
)
ACTION_FIELDS = ("status", "coverage_start", "coverage_end", "checked_at")


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
    return number if number.is_finite() and number > 0 else None


def _instant(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.utcoffset() is not None else None


def audit_body_bindings(session, previous, reports, receipts, collected_at):
    """Audit EVERY original index; never silently select matching providers."""
    if (not isinstance(previous, date) or isinstance(previous, datetime)
            or not isinstance(session, date) or isinstance(session, datetime)
            or previous >= session):
        raise ValueError("VALID_PREVIOUS_AND_CURRENT_SESSION_DATES_REQUIRED")
    receipt_audit = audit_receipts(session, reports, receipts, collected_at)
    rows, issues, prices = [], set(receipt_audit["issues"]), {}
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
            except (UnicodeError, ValueError, TypeError, RecursionError):
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
            for field, expected in (("regular_close_asof", session),
                                    ("previous_regular_close_asof", previous)):
                stamp = _instant(parsed.get(field))
                if stamp is None or stamp.astimezone(ET).date() != expected:
                    faults.add("BODY_CLOSE_ASOF_SESSION_DATE_MISMATCH")
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
            if not isinstance(action, dict) or not isinstance(report_action, dict):
                faults.add("BODY_OR_REPORT_ACTION_EVIDENCE_MISSING")
            else:
                for field in ACTION_FIELDS:
                    if (not isinstance(action.get(field), str)
                            or not action.get(field)
                            or action.get(field) != report_action.get(field)):
                        faults.add("BODY_REPORT_ACTION_MISMATCH_" + field.upper())
                if (action.get("coverage_start") != previous.isoformat()
                        or action.get("coverage_end") != session.isoformat()
                        or action.get("status") != "NONE"):
                    faults.add("ACTION_WINDOW_OR_STATUS_NOT_CLEARED")
                checked = _instant(action.get("checked_at"))
                observed = _instant(collected_at)
                if checked is None or observed is None or checked > observed:
                    faults.add("ACTION_CHECK_TIME_INVALID")
        issues.update(faults)
        rows.append({
            "index": index,
            "raw_body_sha256_computed": hashlib.sha256(body).hexdigest() if isinstance(body, bytes) else None,
            "status": "BODY_FIELDS_MATCH_UNAUTHENTICATED" if not faults else "REJECTED_CENSORED",
            "issues": sorted(faults),
        })
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
