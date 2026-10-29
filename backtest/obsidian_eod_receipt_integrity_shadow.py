"""Read-only byte-integrity inventory for *supplied* independent EOD receipts.

P0-1 preparation, not an HTTP collector or official-close verifier. An input
body's matching SHA-256 proves only local byte consistency, NOT that those
bytes came from the claimed provider, that the provider is independent, or
that any price/identity/action claim was parsed from the body. Always censor.
Never echo URLs, query credentials, headers, or raw response bodies.
"""
import hashlib
from datetime import date, datetime, time
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_EOD_RECEIPT_BYTE_INTEGRITY_SHADOW_V1_2026_10_29"
ET = ZoneInfo("America/New_York")
MAX_RECEIPT_BYTES = 5_000_000
ALLOWED_MEDIA = {"application/json", "text/csv", "application/csv",
                 "text/html", "application/xml", "text/xml"}


def _instant(value):
    if not isinstance(value, str):
        return None
    try:
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value if value.utcoffset() is not None else None


def _safe_host(value):
    try:
        p = urlsplit(value) if isinstance(value, str) else None
        if (p is None or p.scheme != "https" or not p.hostname
                or p.username is not None or p.password is not None
                or p.fragment):
            return None
        return p.hostname.lower()
    except ValueError:
        return None


def audit_receipts(session, reports, receipts, collected_at):
    """Index every source by original index; reject omission and cherry-picking.

    ``receipts`` are caller-supplied dictionaries with ``raw_body`` bytes,
    ``body_sha256`` claimed digest, source_id, provider_organization,
    requested_url, response_url, http_status, http_method, content_type and
    retrieved_at. Never infer transport authentication from these fields.
    This does not parse a vendor price or verify a source-owned receipt.
    """
    if not isinstance(session, date) or isinstance(session, datetime):
        raise ValueError("SESSION_DATE_REQUIRED")
    if not isinstance(reports, list) or not isinstance(receipts, list):
        raise ValueError("COMPLETE_REPORT_AND_RECEIPT_LISTS_REQUIRED")
    end = datetime.combine(session, time(16), tzinfo=ET)
    collected = _instant(collected_at)
    if collected is None or collected < end:
        raise ValueError("POSTCLOSE_COLLECTION_TIMESTAMP_REQUIRED")
    issues, rows, valid = set(), [], []
    if len(reports) != len(receipts):
        issues.add("REPORT_RECEIPT_COUNT_MISMATCH_NO_SELECTIVE_OMISSION")
    if not reports:
        issues.add("NO_SOURCE_REPORTS")
    seen_sources = set()
    for index in range(max(len(reports), len(receipts))):
        report = reports[index] if index < len(reports) else None
        receipt = receipts[index] if index < len(receipts) else None
        r = report if isinstance(report, dict) else {}
        t = receipt if isinstance(receipt, dict) else {}
        faults = set()
        if not isinstance(report, dict):
            faults.add("MISSING_OR_MALFORMED_SOURCE_REPORT")
        if not isinstance(receipt, dict):
            faults.add("MISSING_OR_MALFORMED_SOURCE_RECEIPT")
        source_id = r.get("source_id")
        group = r.get("provider_organization")
        source_url = r.get("source_url")
        source_host = _safe_host(source_url)
        request_host = _safe_host(t.get("requested_url"))
        response_host = _safe_host(t.get("response_url"))
        if not isinstance(source_id, str) or not source_id.strip() or source_id in seen_sources:
            faults.add("MISSING_OR_DUPLICATE_SOURCE_ID")
        else:
            seen_sources.add(source_id)
        if (not isinstance(group, str) or not group.strip()
                or not source_host or not request_host or not response_host
                or t.get("source_id") != source_id
                or t.get("provider_organization") != group
                or t.get("requested_url") != source_url
                or t.get("response_url") != source_url):
            faults.add("SOURCE_ORGANIZATION_URL_OR_REDIRECT_MISMATCH")
        if type(t.get("http_status")) is not int or t.get("http_status") != 200 or t.get("http_method") != "GET":
            faults.add("NON_SUCCESSFUL_OR_NON_GET_HTTP_CLAIM")
        media = t.get("content_type")
        if not isinstance(media, str) or media.split(";", 1)[0].strip().lower() not in ALLOWED_MEDIA:
            faults.add("UNSUPPORTED_OR_MISSING_MEDIA_TYPE_CLAIM")
        received = _instant(t.get("retrieved_at"))
        if received is None or not end <= received <= collected:
            faults.add("RECEIPT_TIMESTAMP_OUTSIDE_POSTCLOSE_WINDOW")
        body = t.get("raw_body")
        digest = None
        if not isinstance(body, bytes) or not 0 < len(body) <= MAX_RECEIPT_BYTES:
            faults.add("MISSING_OVERSIZED_OR_NONBYTE_RESPONSE_BODY")
        else:
            digest = hashlib.sha256(body).hexdigest()
            if t.get("body_sha256") != digest:
                faults.add("RESPONSE_BODY_SHA256_MISMATCH")
        if faults:
            issues.update(faults)
        else:
            valid.append((index, source_id, group, source_host, digest))
        rows.append({
            "index": index,
            "source_id_claim": source_id if isinstance(source_id, str) else None,
            "provider_organization_claim": group if isinstance(group, str) else None,
            "source_host": source_host,
            "request_host": request_host,
            "response_host": response_host,
            "retrieved_at_claim": t.get("retrieved_at") if isinstance(t.get("retrieved_at"), str) else None,
            "body_sha256_computed": digest,
            "body_bytes": len(body) if isinstance(body, bytes) else None,
            "status": "BYTE_CONSISTENT_UNAUTHENTICATED" if not faults else "REJECTED_CENSORED",
            "issues": sorted(faults),
        })
    if len({v[2] for v in valid}) < 2 or len({v[3] for v in valid}) < 2:
        issues.add("TWO_DISTINCT_PROVIDER_ORGANIZATIONS_AND_HOSTS_NOT_ESTABLISHED")
    if len({v[4] for v in valid}) != len(valid):
        issues.add("IDENTICAL_RAW_PAYLOAD_ACROSS_SOURCES_INDEPENDENCE_UNPROVEN")
    return {
        "mode": MODE, "policy": POLICY, "session_date": session.isoformat(),
        "supplied_report_count": len(reports), "supplied_receipt_count": len(receipts),
        "indexed_count": len(rows), "byte_consistent_count": len(valid),
        "all_source_rows": rows, "issues": sorted(issues),
        "status": "BLOCKED_RECEIPT_INTEGRITY" if issues else "BYTE_CONSISTENT_EXTERNAL_AUTH_PENDING",
        "raw_provider_bytes_archived_by_module": False,
        "source_ownership_and_transport_authenticated": False,
        "source_owned_publication_timestamp_authenticated": False,
        "provider_organization_independence_authenticated": False,
        "source_price_claim_parsed_and_bound_to_body": False,
        "official_close_and_corporate_actions_authenticated": False,
        "official_close_verified": False, "eligible_for_frozen_scoring": False,
        "verified_20pct_prediction_success": None,
        "outcome_censored_pending_external_evidence": True,
        "smg_trade_authorized": False,
    }
