"""Offline source-byte-to-claim binding shadow for OBSIDIAN P0-1.

This intentionally accepts caller-supplied JSON and HTTP receipt assertions.
It does NOT retrieve a provider response, authenticate transport or provider
ownership, certify official closes, or authorize frozen-cohort scoring. The
flat JSON fixture contract is not an actual vendor API schema. Always censor.
Never return URLs, response bodies, headers or credential-bearing fields.
"""
import hashlib
import json
import re
from datetime import date, datetime, time
from decimal import Decimal, DecimalException, InvalidOperation, localcontext
from zoneinfo import ZoneInfo

from backtest.obsidian_eod_receipt_integrity_shadow import audit_receipts, MAX_RECEIPT_BYTES
from backtest.obsidian_eod_source_preflight import _published_2026_calendar_issues
from backtest.obsidian_eod_action_identity_shadow import ACTIONS, BASES

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


class _UnboundedJsonNumber(ValueError):
    """A vendor JSON numeric token exceeds the evidence precision envelope."""


def _bounded_json_number(token):
    """Reject extreme JSON numbers anywhere in the source body, not just prices.

    An unrelated vendor sideband with 5 MB of digits or an enormous exponent
    must not be silently accepted as part of a byte-bound close receipt.
    This is a parser resource/integrity guard, not a market-price eligibility
    rule; source rows remain indexed and censored on rejection.
    """
    if len(token) > 128:
        raise _UnboundedJsonNumber("OVERSIZE_JSON_NUMERIC_TOKEN")
    try:
        number = Decimal(token)
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise _UnboundedJsonNumber("UNREPRESENTABLE_JSON_NUMERIC_TOKEN") from exc
    if (not number.is_finite() or not -100 <= number.adjusted() <= 100
            or len(number.as_tuple().digits) > 100):
        raise _UnboundedJsonNumber("UNBOUNDED_JSON_NUMERIC_TOKEN")
    return number


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
    if not -100 <= number.adjusted() <= 100 or len(number.as_tuple().digits) > 100:
        return None
    return number


def _exact_20pct_threshold(prior):
    """Compare original source claims without 28-digit Decimal rounding."""
    with localcontext() as ctx:
        ctx.prec = 512
        return prior * Decimal("0.8")


def _instant(value):
    """Parse exact source timestamps without silently truncating nanoseconds.

    datetime.fromisoformat accepts 7+ fractional digits but discards digits
    beyond microseconds. That could turn 16:00:00.0000001 into a false exact
    16:00:00 official-close claim. Fail closed on unsupported precision or
    noncanonical offset syntax rather than rounding an untrusted timestamp.
    """
    if not isinstance(value, str) or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})",
            value) is None:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.utcoffset() is not None else None


def _asof_claim_key(value):
    """Compare untrusted as-of claims by instant, not textual UTC offset.

    Invalid nonempty timestamps remain distinct inventory claims; they never
    become admissible exchange-close evidence or appear in the public output.
    """
    if not isinstance(value, str) or not value:
        return None
    stamp = _instant(value)
    return stamp.astimezone(ZoneInfo("UTC")).isoformat() if stamp else "INVALID:" + value



def _canonical_iso_date(value):
    """Date claims must be exact YYYY-MM-DD, not Python's lenient variants."""
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _has_unpaired_surrogate(value):
    """Reject unpaired UTF-16 escapes anywhere in a decoded provider packet.

    Python's JSON decoder accepts an isolated \\ud800 escape as a string, but
    it cannot be encoded as a valid UTF-8 Unicode scalar. Such a field could
    crash the later source-index SHA256 grouping or hide malformed vendor
    sideband evidence. Traverse iteratively and reject the entire source row;
    never normalize or silently discard an untrusted claim.
    """
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            if any(0xD800 <= ord(char) <= 0xDFFF for char in item):
                return True
        elif isinstance(item, dict):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return False


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
    # Matching source bytes cannot override the published session calendar
    # or invent an adjacent previous trading day. Static screen only; the
    # raw provider packet and every source row remain unauthenticated.
    issues.update(_published_2026_calendar_issues(session, previous))
    # Index each parseable price independently, even when a rejected third
    # source supplies only one side of the close/prior-close pair. A complete
    # pair-only ledger could otherwise conceal an explicit contradiction.
    close_claims, prior_claims = {}, {}
    # Publication/action-check times are not expected to match across vendors.
    # Inventory each exact source claim without treating different legitimate
    # retrieval/publication clocks as a price or identity conflict.
    timing_claims = {field: {} for field in ("source_publication_at", "action_checked_at")}
    # A present malformed timing value is different from a field omitted in
    # an otherwise parseable body. Neither can authenticate a closing price.
    present_invalid_timing_indices = {field: set() for field in timing_claims}
    explicitly_absent_timing_indices = {field: set() for field in timing_claims}
    identity_claims = {field: {} for field in (
        "symbol", "session_date", "previous_session_date",
        "regular_close_asof", "previous_regular_close_asof",
        "security_id", "previous_security_id", "issuer_class",
        "previous_issuer_class", "action_coverage_start", "action_coverage_end",
        "action_security_id",
        "action_previous_security_id", "action_issuer_class",
        "action_previous_issuer_class", "corporate_action_status",
        "previous_close_basis")}
    # Explicit malformed values must not be silently indistinguishable from
    # omitted fields. Keep the existing unparseable-index contract unchanged.
    invalid_identity_claim_indices = {field: set() for field in identity_claims}
    close_end = (_instant(session_close_at).astimezone(ET) if session_close_at is not None
                 else datetime.combine(session, time(16), tzinfo=ET))
    # This shadow follows the frozen normal 16:00 ET source contract.
    # An explicit 13:00 ET close needs separate registered evaluation.
    if close_end.timetz().replace(tzinfo=None) != time(16):
        issues.add("NONSTANDARD_CURRENT_CLOSE_REQUIRES_SEPARATE_SESSION_CONTRACT")
    if previous_end.timetz().replace(tzinfo=None) != time(16):
        issues.add("NONSTANDARD_PREVIOUS_CLOSE_REQUIRES_SEPARATE_SESSION_CONTRACT")
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
        elif not 0 < len(body) <= MAX_RECEIPT_BYTES:
            # The receipt layer rejects bodies outside this bound. Do not
            # parse them anyway: a rejected multi-megabyte JSON payload could
            # exhaust memory/CPU and prevent other source rows being indexed.
            faults.add("BODY_EMPTY_OR_OVERSIZED_NO_PARSE")
        elif t.get("content_type", "").split(";", 1)[0].strip().lower() != "application/json" if isinstance(t.get("content_type"), str) else True:
            faults.add("NOT_EXPLICIT_APPLICATION_JSON")
        else:
            try:
                parsed = json.loads(
                    body.decode("utf-8", errors="strict"),
                    object_pairs_hook=_unique_pairs,
                    parse_float=_bounded_json_number,
                    parse_int=_bounded_json_number,
                    parse_constant=_nonfinite,
                )
                if not isinstance(parsed, dict):
                    faults.add("JSON_ROOT_NOT_OBJECT")
                    parsed = None
                elif _has_unpaired_surrogate(parsed):
                    # JSON can parse an escaped lone surrogate even though
                    # the resulting string cannot be safely UTF-8 hashed.
                    # Censor the entire malformed source, not the other rows.
                    faults.add("INVALID_UNICODE_SCALAR_IN_JSON_BODY_CENSORED")
                    parsed = None
            except _UnboundedJsonNumber:
                faults.add("UNBOUNDED_JSON_NUMERIC_TOKEN_CENSORED")
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
            if close is not None:
                close_claims.setdefault(close, []).append(index)
            if prior is not None:
                prior_claims.setdefault(prior, []).append(index)
            if close is not None and prior is not None:
                bucket = prices.setdefault((close, prior), [])
                bucket.append(index)
            action = parsed.get("corporate_action")
            report_action = r.get("corporate_action")
            for field, value in (
                    ("source_publication_at", parsed.get("observed_at")),
                    ("action_checked_at", action.get("checked_at") if isinstance(action, dict) else None)):
                claim = _asof_claim_key(value)
                if claim is not None:
                    timing_claims[field].setdefault(claim, []).append(index)
            for field, owner, key in (
                    ("source_publication_at", parsed, "observed_at"),
                    ("action_checked_at", action, "checked_at")):
                if isinstance(owner, dict):
                    if key not in owner:
                        explicitly_absent_timing_indices[field].add(index)
                    elif _instant(owner[key]) is None:
                        present_invalid_timing_indices[field].add(index)
                elif field == "action_checked_at" and "corporate_action" in parsed:
                    # An explicit null/list/string action container is not
                    # evidence that the checked_at claim was simply omitted.
                    present_invalid_timing_indices[field].add(index)
                else:
                    explicitly_absent_timing_indices[field].add(index)
            # Compare every parseable source-body identity/action claim,
            # including rejected rows; never cherry-pick two agreeing ones.
            for field, value in (
                ("symbol", parsed.get("symbol")),
                ("session_date", parsed.get("session_date")),
                ("previous_session_date", parsed.get("previous_session_date")),
                ("regular_close_asof", _asof_claim_key(parsed.get("regular_close_asof"))),
                ("previous_regular_close_asof", _asof_claim_key(parsed.get("previous_regular_close_asof"))),
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
            # A present null, array, object, number or empty string is not an
            # absent claim. Preserve its original index without echoing data.
            # Malformed entire JSON bodies remain unparseable, not "invalid".
            for field, owner, key in (
                    ("symbol", parsed, "symbol"),
                    ("session_date", parsed, "session_date"),
                    ("previous_session_date", parsed, "previous_session_date"),
                    ("regular_close_asof", parsed, "regular_close_asof"),
                    ("previous_regular_close_asof", parsed, "previous_regular_close_asof"),
                    ("security_id", parsed, "security_id"),
                    ("previous_security_id", parsed, "previous_security_id"),
                    ("issuer_class", parsed, "issuer_class"),
                    ("previous_issuer_class", parsed, "previous_issuer_class"),
                    ("action_coverage_start", action, "coverage_start"),
                    ("action_coverage_end", action, "coverage_end"),
                    ("action_security_id", action, "security_id"),
                    ("action_previous_security_id", action, "previous_security_id"),
                    ("action_issuer_class", action, "issuer_class"),
                    ("action_previous_issuer_class", action, "previous_issuer_class"),
                    ("corporate_action_status", action, "status"),
                    ("previous_close_basis", action, "previous_close_basis")):
                if isinstance(owner, dict) and key in owner:
                    raw = owner[key]
                    if (not isinstance(raw, str) or not raw
                            or (field in ("regular_close_asof", "previous_regular_close_asof")
                                and _instant(raw) is None)
                            or (field in ("session_date", "previous_session_date",
                                          "action_coverage_start", "action_coverage_end")
                                and not _canonical_iso_date(raw))
                            or (field == "corporate_action_status" and raw not in ACTIONS)
                            or (field == "previous_close_basis" and raw not in BASES)):
                        # Retain hashed contradictory string claims, but flag
                        # syntactically invalid timestamps, dates and action
                        # enums separately from genuinely omitted fields.
                        invalid_identity_claim_indices[field].add(index)
                elif (not isinstance(owner, dict)
                      and (field.startswith("action_") or field in
                           ("corporate_action_status", "previous_close_basis"))
                      and "corporate_action" in parsed):
                    # An explicitly present but malformed action container
                    # (null, list, number, string) invalidates EVERY nested
                    # action/identity claim. Do not misclassify it as merely
                    # omitted; retain the original source index without
                    # copying any untrusted body value into the audit.
                    invalid_identity_claim_indices[field].add(index)
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
            "raw_body_sha256_computed": (
                hashlib.sha256(body).hexdigest()
                if isinstance(body, bytes) and 0 < len(body) <= MAX_RECEIPT_BYTES else None),
            "status": "BODY_FIELDS_MATCH_UNAUTHENTICATED" if not faults else "REJECTED_CENSORED",
            "issues": sorted(faults),
        })
    for field, issue in (
        ("symbol", "PARSED_BODY_SYMBOL_CLAIM_CONFLICT"),
        ("session_date", "PARSED_BODY_SESSION_DATE_CLAIM_CONFLICT"),
        ("previous_session_date", "PARSED_BODY_PREVIOUS_SESSION_DATE_CLAIM_CONFLICT"),
        ("regular_close_asof", "PARSED_BODY_REGULAR_CLOSE_ASOF_CLAIM_CONFLICT"),
        ("previous_regular_close_asof", "PARSED_BODY_PREVIOUS_CLOSE_ASOF_CLAIM_CONFLICT"),
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
    # Preserve exact source-index provenance for every parseable body
    # identity/action/as-of claim, including rejected third sources. The
    # existing conflict flags alone do not show which source disagreed.
    # Hash claim values rather than echoing arbitrary untrusted strings:
    # a vendor field could contain a credential, URL or sensitive text.
    # These digests are local grouping fingerprints, NOT source authenticity.
    identity_claim_groups = {}
    missing_identity_claim_indices = {}
    for field, claims in identity_claims.items():
        groups_for_field = []
        covered_indices = set()
        for value, indices in sorted(claims.items()):
            covered_indices.update(indices)
            groups_for_field.append({
                "claim_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                "structurally_valid_source_indices": [
                    i for i in indices if rows[i]["status"] == "BODY_FIELDS_MATCH_UNAUTHENTICATED"
                ],
                "rejected_source_indices": [
                    i for i in indices if rows[i]["status"] != "BODY_FIELDS_MATCH_UNAUTHENTICATED"
                ],
            })
        identity_claim_groups[field] = groups_for_field
        missing_identity_claim_indices[field] = [
            i for i in range(count) if i not in covered_indices
        ]
    # Preserve every source-body publication/action-check assertion, including
    # rejected and unsupported-precision timestamps. UTC-equivalent offsets
    # group together; distinct valid publication times are NOT conflicts.
    # Only hashed claim keys are exposed, never untrusted timestamp text.
    timing_claim_groups = {}
    missing_timing_claim_indices = {}
    invalid_timing_claim_indices = {}
    for field, claims in timing_claims.items():
        groups_for_field = []
        covered_indices, invalid_indices = set(), set()
        for value, indices in sorted(claims.items()):
            covered_indices.update(indices)
            if value.startswith("INVALID:"):
                invalid_indices.update(indices)
            groups_for_field.append({
                "claim_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                "structurally_valid_source_indices": [
                    i for i in indices if rows[i]["status"] == "BODY_FIELDS_MATCH_UNAUTHENTICATED"
                ],
                "rejected_source_indices": [
                    i for i in indices if rows[i]["status"] != "BODY_FIELDS_MATCH_UNAUTHENTICATED"
                ],
            })
        timing_claim_groups[field] = groups_for_field
        missing_timing_claim_indices[field] = [
            i for i in range(count) if i not in covered_indices
        ]
        invalid_timing_claim_indices[field] = sorted(
            invalid_indices | present_invalid_timing_indices[field])
    # Every parseable price claim retains its original source index even if
    # the source fails receipt, identity, action or chronology validation.
    # Distinguish structurally matching rows from rejected third-source claims;
    # otherwise a diagnostic 20% threshold could look like corroboration.
    def indexed_price_group(indices):
        return {
            "source_indices": indices,
            "structurally_valid_source_indices": [
                i for i in indices if rows[i]["status"] == "BODY_FIELDS_MATCH_UNAUTHENTICATED"
            ],
            "rejected_source_indices": [
                i for i in indices if rows[i]["status"] != "BODY_FIELDS_MATCH_UNAUTHENTICATED"
            ],
        }

    groups = [
        {"regular_close": str(close), "previous_regular_close": str(prior),
         **indexed_price_group(indices),
         "claimed_20pct_drop": close <= _exact_20pct_threshold(prior)}
        for (close, prior), indices in sorted(prices.items())
    ]
    current_groups = [
        {"regular_close": str(value), **indexed_price_group(indices)}
        for value, indices in sorted(close_claims.items())
    ]
    previous_groups = [
        {"previous_regular_close": str(value), **indexed_price_group(indices)}
        for value, indices in sorted(prior_claims.items())
    ]
    current_covered = {i for indices in close_claims.values() for i in indices}
    previous_covered = {i for indices in prior_claims.values() for i in indices}
    paired_covered = {i for indices in prices.values() for i in indices}
    if len(current_groups) > 1:
        issues.add("PARSED_BODY_REGULAR_CLOSE_CLAIM_CONFLICT")
    if len(previous_groups) > 1:
        issues.add("PARSED_BODY_PREVIOUS_CLOSE_CLAIM_CONFLICT")
    if len(groups) > 1 or len(current_groups) > 1 or len(previous_groups) > 1:
        issues.add("PARSED_BODY_PRICE_CLAIM_CONFLICT")
    if len({g["claimed_20pct_drop"] for g in groups}) > 1:
        issues.add("PARSED_BODY_CLAIMS_STRADDLE_20PCT_THRESHOLD")
    # A rejected third body can contain only a current or only a prior close.
    # Cross-check all independently parseable claims, not just complete pairs.
    # This is an UNTRUSTED claim-conflict inventory, never an official outcome.
    if current_groups and previous_groups:
        thresholds = [_exact_20pct_threshold(prior) for prior in prior_claims]
        if min(close_claims) <= max(thresholds) and max(close_claims) > min(thresholds):
            issues.add("PARSED_BODY_ALL_CLAIMS_STRADDLE_20PCT_THRESHOLD")
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
        "all_parseable_body_current_close_claim_groups": current_groups,
        "all_parseable_body_previous_close_claim_groups": previous_groups,
        "missing_body_current_close_claim_source_indices": [
            i for i in range(count) if i not in current_covered
        ],
        "missing_body_previous_close_claim_source_indices": [
            i for i in range(count) if i not in previous_covered
        ],
        "incomplete_body_price_pair_source_indices": [
            i for i in range(count) if i not in paired_covered
        ],
        "all_parseable_body_identity_claim_groups": identity_claim_groups,
        "unparseable_body_identity_claim_source_indices": missing_identity_claim_indices,
        "invalid_body_identity_claim_source_indices": {
            field: sorted(indices) for field, indices in invalid_identity_claim_indices.items()
        },
        "all_body_timing_claim_groups": timing_claim_groups,
        "missing_body_timing_claim_source_indices": missing_timing_claim_indices,
        "invalid_body_timing_claim_source_indices": invalid_timing_claim_indices,
        "explicitly_absent_body_timing_claim_source_indices": {
            field: sorted(indices) for field, indices in explicitly_absent_timing_indices.items()
        },
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
