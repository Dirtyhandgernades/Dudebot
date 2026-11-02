"""Bounded research vendor corroboration; never frozen official-close evidence."""
import datetime as dt
import hashlib
import json
import math
import os
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib import request, parse, error
from zoneinfo import ZoneInfo

SYMBOLS = ("AAPL", "MSFT")
SESSIONS = ("2026-10-27", "2026-10-28")
OUT = Path("outputs/backtest/obsidian-two-provider-close-reconciliation.json")
TOLERANCE = Decimal("0.005")

# Vendor OHLC comparisons cannot discharge these official-close obligations.
# Keep every missing proof for every original ticker/session, even when bars agree.
OFFICIAL_CLOSE_PROOF_GAPS = (
    "EXCHANGE_OFFICIAL_REGULAR_CLOSE_NOT_AUTHENTICATED",
    "TWO_INDEPENDENT_UNDERLYING_PROVIDER_FEEDS_NOT_AUTHENTICATED",
    "SECURITY_IDENTITY_ISSUER_CLASS_NOT_VERIFIED",
    "PREVIOUS_SESSION_OFFICIAL_REFERENCE_NOT_AUTHENTICATED",
    "CORPORATE_ACTION_ADJUSTMENT_PARITY_NOT_VERIFIED",
    "ACTUAL_EXCHANGE_SESSION_NOT_AUTHENTICATED",
    "ORIGINAL_EXCHANGE_SOURCE_TIMESTAMP_NOT_AUTHENTICATED",
    "THIRD_SOURCE_CONFLICT_INVENTORY_NOT_COLLECTED",
)


# Conservative scheduled cash-equity calendar for 2026 only. Dates transcribed
# from NYSE Group's published 2026 closure schedule (2025-12-23):
# https://www.nyse.com/trade/hours-calendars
# This static screen cannot prove an unscheduled exchange closure, an issuer
# halt, an actual completed session, or an official auction closing price.
_CLOSED_2026 = frozenset({
    dt.date(2026, 1, 1), dt.date(2026, 1, 19),
    dt.date(2026, 2, 16), dt.date(2026, 4, 3),
    dt.date(2026, 5, 25), dt.date(2026, 6, 19),
    dt.date(2026, 7, 3), dt.date(2026, 9, 7),
    dt.date(2026, 11, 26), dt.date(2026, 12, 25),
})


def _scheduled_cash_session_2026(day):
    """Only a scheduled weekday, not authenticated session/close evidence.

    Out-of-scope years and known full closures fail closed. Early closes
    (Nov 27, Dec 24) are scheduled sessions, but the separate 16:00 ET
    request-start cutoff remains deliberately conservative.
    """
    return (isinstance(day, dt.date) and day.year == 2026
            and day.weekday() < 5 and day not in _CLOSED_2026)


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def redact(text, token):
    if token:
        text = text.replace(token, "[REDACTED]")
    return re.sub(r'(?i)(api[_-]?key|token|authorization|secret)([\"\s:=]+)[^\s,;&\"}]+', r'\1\2[REDACTED]', text)


class _NoRedirectHandler(request.HTTPRedirectHandler):
    """Never follow vendor redirects: a different host is not the claimed source."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_no_redirect(req):
    return request.build_opener(_NoRedirectHandler()).open(req, timeout=18)


def _unique_vendor_json_object(pairs):
    """Reject duplicate keys at every nesting level of untrusted vendor JSON."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_VENDOR_JSON_KEY")
        result[key] = value
    return result


def _reject_vendor_nonfinite(value):
    # Python's default JSON decoder accepts NaN/Infinity despite JSON rules.
    raise ValueError("NONFINITE_VENDOR_JSON_CONSTANT")


def _finite_vendor_float(value):
    """Reject overflow and silent underflow in any vendor JSON numeric field.

    A JSON exponent such as 1e309 normally decodes to float('inf'), while
    1e-400 silently becomes 0. Neither preserves the supplied price/source
    claim, including when it appears in a nested field rather than 'close'.
    """
    try:
        number = float(value)
        if not math.isfinite(number) or (number == 0.0 and Decimal(value) != 0):
            raise ValueError("NONREPRESENTABLE_VENDOR_JSON_FLOAT")
        return number
    except (InvalidOperation, OverflowError) as exc:
        raise ValueError("NONREPRESENTABLE_VENDOR_JSON_FLOAT") from exc


def get(url, params, token):
    """Never log URLs, exceptions or provider messages that could echo credentials."""
    req = request.Request(url + "?" + parse.urlencode(params),
                          headers={"User-Agent": "OBSIDIAN-research-only/2.0"})
    # The request START, not response completion, determines whether a daily
    # bar could have been a completed regular-session observation.
    requested_at = utcnow()
    try:
        try:
            response = _open_no_redirect(req)
        except error.HTTPError as exc:
            response = exc
        with response:
            body = response.read(150001)
            status = response.code
            # Message.get() returns only one value even if the server sent
            # duplicate Content-Length headers. A duplicate is ambiguous
            # framing (even if the two declarations happen to agree).
            get_all_lengths = getattr(response.headers, "get_all", None)
            if callable(get_all_lengths):
                length_headers = get_all_lengths("Content-Length") or []
            else:
                single_length = response.headers.get("Content-Length")
                length_headers = [] if single_length is None else [single_length]
            # A JSON-looking body with missing, contradictory or non-JSON
            # Content-Type is not a trustworthy vendor JSON receipt. Inspect
            # every header value: Message.get() silently hides duplicates.
            if callable(get_all_lengths):
                media_headers = get_all_lengths("Content-Type") or []
            else:
                single_media = response.headers.get("Content-Type")
                media_headers = [] if single_media is None else [single_media]
            # A duplicate/invalid remaining-quota header could hide a zero
            # allowance behind a later nonzero value. Do not select one
            # declaration or spend another paid request on ambiguous framing.
            if callable(get_all_lengths):
                quota_values = get_all_lengths("X-RateLimit-Remaining") or []
            else:
                single_quota = response.headers.get("X-RateLimit-Remaining")
                quota_values = [] if single_quota is None else [single_quota]
            quota_header_unverified = (
                not isinstance(quota_values, (list, tuple))
                or len(quota_values) > 1
                or (len(quota_values) == 1 and
                    (not isinstance(quota_values[0], str) or
                     not re.fullmatch(r"[0-9]{1,16}", quota_values[0].strip()))))
            # Keep only bounded numeric quota headers. Arbitrary vendor header
            # strings (including echoed query tokens) are unsafe to archive.
            headers = {k.lower(): v.strip() for k, v in response.headers.items()
                       if k.lower() in {"retry-after", "x-ratelimit-remaining", "x-ratelimit-reset"}
                       and isinstance(v, str) and re.fullmatch(r"[0-9]{1,16}", v.strip())}
            if quota_header_unverified:
                headers.pop("x-ratelimit-remaining", None)
        # A bounded read can return fewer bytes than the declared HTTP body
        # length. Do not hash or parse an incomplete/contradictory receipt,
        # even when the prefix is valid JSON with an apparently usable close.
        # Content-Length is a transport check, NOT proof of official prices.
        body_truncated = len(body) > 150000
        body_length_mismatch = bool(length_headers) and (
            len(length_headers) != 1 or
            not isinstance(length_headers[0], str) or
            not re.fullmatch(r"[0-9]{1,16}", length_headers[0].strip()) or
            int(length_headers[0].strip()) != len(body))
        media_type_unverified = (
            len(media_headers) != 1 or not isinstance(media_headers[0], str)
            or media_headers[0].split(";", 1)[0].strip().lower() != "application/json")
        # Duplicate keys could overwrite an earlier error/status, symbol,
        # session or close. Reject at every nesting level; no last-key-wins
        # price or identity evidence enters even the diagnostic comparison.
        # JSON decode errors are not transport failures. A ValueError thrown
        # by response.read() or header inspection must fail closed as network
        # unavailable, not escape through uninitialized receipt variables.
        payload = None
        if not (body_truncated or body_length_mismatch or media_type_unverified):
            try:
                payload = json.loads(body, object_pairs_hook=_unique_vendor_json_object,
                                     parse_constant=_reject_vendor_nonfinite,
                                     parse_float=_finite_vendor_float)
            except (ValueError, UnicodeDecodeError, RecursionError):
                payload = None
    except Exception:
        return {"http_status": None, "error": "NETWORK_UNAVAILABLE", "payload": None,
                "retrieved_at": utcnow(), "requested_at": requested_at,
                "body_sha256": None, "body_truncated": False,
                "headers": {}, "body_length_mismatch": False,
                "content_type_unverified": None, "quota_header_unverified": None}
    # Raw provider bodies and arbitrary error text must never reach the public
    # GitHub Actions artifact: a vendor may echo URL query credentials verbatim.
    return {"http_status": status,
            "body_sha256": (None if body_truncated or body_length_mismatch
                            else hashlib.sha256(body).hexdigest()),
            "body_truncated": body_truncated,
            "body_length_mismatch": body_length_mismatch,
            "error": ("RESPONSE_BODY_TOO_LARGE" if body_truncated else
                      "RESPONSE_LENGTH_MISMATCH" if body_length_mismatch else
                      "UNVERIFIED_JSON_CONTENT_TYPE" if media_type_unverified else
                      "UNVERIFIED_QUOTA_HEADER" if quota_header_unverified else None),
            "payload": payload, "retrieved_at": utcnow(),
            "requested_at": requested_at, "headers": headers,
            "content_type_unverified": media_type_unverified,
            "quota_header_unverified": quota_header_unverified}


def category(receipt):
    status = receipt.get("http_status")
    # HTTP denial is authoritative even when the error body is oversized or
    # malformed. Keep the separate body_truncated flag for receipt integrity;
    # never misclassify a confirmed 401/403/429 as merely a body parse failure.
    if type(status) is int and status in (401, 403, 429):
        return {401: "AUTHENTICATION", 403: "ENTITLEMENT_OR_ACCESS",
                429: "RATE_LIMIT"}[status]
    # A redirect can change the claimed provider origin. Its HTTP status
    # takes precedence over a missing/ambiguous JSON Content-Type or body
    # framing; never let a secondary parse error obscure a 3xx response.
    if type(status) is int and 300 <= status < 400:
        return "UNTRUSTED_REDIRECT"
    if receipt.get("error"):
        return receipt["error"]
    # Only the transport's integer HTTP status is admissible. Malformed
    # injected/legacy receipts must censor, not crash or resemble HTTP 200.
    if type(status) is not int or not 100 <= status <= 599:
        return "MALFORMED_HTTP_STATUS"
    if status != 200:
        if 300 <= status < 400:
            return "UNTRUSTED_REDIRECT"
        return {400: "BAD_REQUEST", 401: "AUTHENTICATION", 403: "ENTITLEMENT_OR_ACCESS",
                429: "RATE_LIMIT"}.get(status, "SERVER_ERROR" if status >= 500 else "HTTP_ERROR")
    payload = receipt.get("payload")
    if not isinstance(payload, dict):
        return "MALFORMED_RESPONSE"
    # Vendor JSON is untrusted. A list/dict in status or error code must
    # not abort the complete request-budget and missingness inventory.
    provider_status = payload.get("status")
    if provider_status is not None and not isinstance(provider_status, str):
        return "MALFORMED_RESPONSE"
    if provider_status in {"error", "ERROR", "NOT_AUTHORIZED"}:
        code = payload.get("code")
        if code is not None and type(code) is not int:
            return "MALFORMED_RESPONSE"
        return {400: "BAD_REQUEST", 401: "AUTHENTICATION", 403: "ENTITLEMENT_OR_ACCESS",
                429: "RATE_LIMIT"}.get(code, "PROVIDER_ERROR")
    # A missing or unknown provider status cannot establish a successful
    # vendor response. Fail closed before spending the remaining request budget.
    if provider_status not in {"OK", "ok"}:
        return "UNEXPECTED_PROVIDER_STATUS"
    return None


@dataclass
class Budget:
    maximum: int
    used: int = 0
    stopped: str | None = None

    def fetch(self, url, params, token, expected_status=None):
        if not token:
            return {"error": "SECRET_ABSENT"}
        if self.stopped or self.used >= self.maximum:
            return {"error": self.stopped or "REQUEST_BUDGET_EXHAUSTED"}
        self.used += 1
        receipt = get(url, params, token)
        failure = category(receipt)
        # The generic HTTP-200 classifier recognizes both OK and ok, but
        # vendor success contracts differ. Stop the budget immediately on a
        # provider-specific mismatch, before spending another paid request.
        if expected_status is not None and failure is None:
            if receipt["payload"].get("status") != expected_status:
                receipt["error"] = "UNEXPECTED_PROVIDER_STATUS"
                failure = "UNEXPECTED_PROVIDER_STATUS"
        # Preserve quota safety even when a malformed/oversized body obscures
        # an authoritative HTTP 401/403/429 status in the error category.
        http_status = receipt.get("http_status")
        if type(http_status) is int and http_status in (401, 403, 429):
            self.stopped = {401: "AUTHENTICATION", 403: "ENTITLEMENT_OR_ACCESS",
                            429: "RATE_LIMIT"}[http_status]
        elif failure in {"RATE_LIMIT", "AUTHENTICATION", "ENTITLEMENT_OR_ACCESS"}:
            self.stopped = failure
        elif failure == "BAD_REQUEST":
            # A rejected query/parameter contract is not evidence that
            # another paid request to this same endpoint will succeed.
            # Keep the first HTTP 400 receipt intact, stop this provider
            # within the bounded diagnostic, and preserve all original
            # symbol/session slots as censored rather than spending quota.
            self.stopped = "BAD_REQUEST"
        elif failure == "SERVER_ERROR":
            # A 5xx indicates provider-side failure, not a missing symbol.
            # Stop this provider within this bounded run instead of making
            # repeated billable calls against the same unavailable service.
            # A later independently scheduled run has a fresh budget.
            self.stopped = "SERVER_ERROR"
        elif failure in {"NETWORK_UNAVAILABLE", "UNTRUSTED_REDIRECT"}:
            # A provider endpoint with broken transport or an untrusted
            # redirect cannot support source-origin evidence. Stop this
            # provider for the bounded checkpoint (not future checkpoints),
            # preserving its exact failure category in all remaining slots.
            # No automatic same-run retry or additional paid requests.
            self.stopped = failure
        elif failure in {"MALFORMED_RESPONSE", "UNEXPECTED_PROVIDER_STATUS",
                         "PROVIDER_ERROR", "RESPONSE_BODY_TOO_LARGE",
                         "RESPONSE_LENGTH_MISMATCH", "UNVERIFIED_JSON_CONTENT_TYPE",
                         "UNVERIFIED_QUOTA_HEADER", "MALFORMED_HTTP_STATUS"}:
            # Ambiguous vendor errors may conceal a quota or entitlement
            # denial. Preserve the first receipt, but do not spend another
            # paid request on this provider in the same bounded checkpoint.
            self.stopped = "UNVERIFIABLE_PROVIDER_RESPONSE"
        remaining = receipt.get("headers", {}).get("x-ratelimit-remaining")
        if isinstance(remaining, str) and re.fullmatch(r"[0-9]{1,16}", remaining) and int(remaining) == 0:
            # Numeric quota exhaustion includes zero-padded forms like "000".
            self.stopped = "RATE_LIMIT"
        # No automatic retries: preserve Retry-After/reset evidence and stop, never burn quota.
        return receipt


def price(value):
    if isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
        # Finite vendor exponents can still overflow Decimal subtraction
        # during the diagnostic pair comparison. Censor, never score them.
        return result if result.is_finite() and result > 0 and -100 <= result.adjusted() <= 100 else None
    except (InvalidOperation, ValueError, OverflowError):
        return None


def _request_after_regular_close(day, requested_at):
    """Conservative 16:00 New York wall-clock cutoff, NOT exchange-calendar proof.

    A daily OHLC response requested before the session ends can represent a
    partial, mutable bar. The request-start timestamp is local instrumentation,
    not vendor self-attestation. Closed holidays/early-close exceptions and
    official auction provenance remain independently unverified.
    """
    try:
        session = dt.date.fromisoformat(day)
        if not isinstance(requested_at, str):
            return False
        started = dt.datetime.fromisoformat(requested_at)
        if started.tzinfo is None or started.utcoffset() is None:
            return False
        cutoff = dt.datetime.combine(session, dt.time(16, 0),
                                     tzinfo=ZoneInfo("America/New_York"))
        return started > cutoff
    except (ValueError, TypeError, OverflowError):
        return False


def _receipt_timestamps_ordered(receipt):
    """Require monotonic local request/response times, not vendor assertions.

    This checks internal receipt consistency only; it cannot authenticate an
    exchange close, a provider's underlying feed, or a security's identity.
    """
    try:
        requested = receipt.get("requested_at")
        retrieved = receipt.get("retrieved_at")
        if not isinstance(requested, str) or not isinstance(retrieved, str):
            return False
        start = dt.datetime.fromisoformat(requested.replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(retrieved.replace("Z", "+00:00"))
        return (start.utcoffset() is not None and end.utcoffset() is not None
                and end >= start)
    except (ValueError, TypeError, OverflowError):
        return False


def observation(provider, symbol, day, receipt):
    result = {"provider_organization": provider, "ticker": symbol, "session_date": day,
              "security_identity": None, "identity_verified": False, "exchange": None,
              "price": None, "price_type": "VENDOR_DAILY_OHLC_CLOSE", "adjustment_basis": "UNKNOWN",
              "source_timestamp": None, "vendor_session_label": None,
              "source_timestamp_evidence_status": "NOT_PROVIDED_BY_VENDOR_DAILY_BAR",
              "retrieval_timestamp": receipt.get("retrieved_at"),
              "request_started_at": receipt.get("requested_at"),
              "http_status": receipt.get("http_status"), "provider_error_category": category(receipt),
              "raw_response_hash": (None if receipt.get("body_truncated") is True
                                    or receipt.get("body_length_mismatch") is True
                                    else receipt.get("body_sha256")),
              "response_body_truncated": receipt.get("body_truncated") is True,
              "response_length_mismatch": receipt.get("body_length_mismatch") is True,
              "response_content_type_unverified": receipt.get("content_type_unverified") is True,
              "response_quota_header_unverified": receipt.get("quota_header_unverified") is True,
              "validation_status": "BLOCKED",
              "provenance": "https://api.massive.com/v1/open-close" if provider == "MASSIVE"
                            else "https://api.twelvedata.com/time_series",
              "rate_limit_headers": receipt.get("headers", {}),
              "raw_body_retained": False}
    if result["provider_error_category"]:
        return result
    # A vendor daily bar on a known non-session date is not a completed
    # regular-session close. This is a STATIC 2026 calendar screen, not proof
    # that a scheduled session actually traded or that an auction was official.
    try:
        scheduled = _scheduled_cash_session_2026(dt.date.fromisoformat(day))
    except (ValueError, TypeError):
        scheduled = False
    if not scheduled:
        result["provider_error_category"] = "CLOSED_OR_UNVERIFIED_EXCHANGE_SESSION"
        return result
    # Keep the existing fail-closed session cutoff as the first gate so
    # malformed/missing request starts retain their original classification.
    if not _request_after_regular_close(day, receipt.get("requested_at")):
        result["provider_error_category"] = "SESSION_NOT_COMPLETE_AT_REQUEST_OR_TIMESTAMP_UNVERIFIED"
        return result
    # A response timestamp before its request (or without a usable timezone)
    # cannot support even a vendor-bar diagnostic. Never substitute a vendor
    # payload timestamp for local retrieval instrumentation.
    if not _receipt_timestamps_ordered(receipt):
        result["provider_error_category"] = "RECEIPT_TIMESTAMP_ORDER_UNVERIFIED"
        return result
    payload = receipt["payload"]
    # Provider-specific success status is required before a numeric bar may
    # enter even the diagnostic count. An unknown/partial status is not proof
    # that the vendor returned a completed daily close.
    expected_status = {"MASSIVE": "OK", "TWELVE_DATA": "ok"}.get(provider)
    if expected_status is None or payload.get("status") != expected_status:
        result["provider_error_category"] = "UNEXPECTED_PROVIDER_STATUS"
        return result
    if provider == "MASSIVE":
        bar = payload
        valid_identity = payload.get("symbol") == symbol
        valid_session = payload.get("from") == day
        result["vendor_session_label"] = day if payload.get("from") == day else None
        result["adjustment_basis"] = "UNADJUSTED_REQUESTED"
    else:
        meta = payload.get("meta", {})
        if not isinstance(meta, dict):
            result["provider_error_category"] = "MALFORMED_METADATA"
            return result
        valid_identity = meta.get("symbol") == symbol
        exchange = meta.get("exchange")
        if exchange is not None and not isinstance(exchange, str):
            result["provider_error_category"] = "MALFORMED_METADATA"
            return result
        # A ticker echo does not establish an eligible listed security.
        # Unknown/OTC/NYSE American venues cannot be silently counted as
        # Nasdaq/NYSE diagnostic bars. NYSE American needs a separately
        # preregistered universe; do not rewrite the frozen cohort.
        if exchange not in {"NASDAQ", "NYSE"}:
            result["provider_error_category"] = "EXCHANGE_UNVERIFIED_OR_OUT_OF_SCOPE"
            return result
        result["exchange"] = exchange
        result["adjustment_basis"] = "UNADJUSTED_REQUESTED"
        bars = payload.get("values", [])
        if not isinstance(bars, list) or any(not isinstance(b, dict) for b in bars):
            result["provider_error_category"] = "MALFORMED_BARS"
            return result
        matches = [b for b in bars if b.get("datetime") == day]
        if len(matches) != 1:
            result["provider_error_category"] = "DUPLICATE_SESSION" if matches else "SESSION_MISSING"
            return result
        bar = matches[0]
        result["vendor_session_label"] = bar.get("datetime")
        valid_session = True
    if not valid_identity or not valid_session:
        result["provider_error_category"] = "IDENTITY_MISMATCH" if not valid_identity else "SESSION_MISMATCH"
        return result
    value = price(bar.get("close"))
    if value is None:
        result["provider_error_category"] = "INVALID_PRICE"
        return result
    result.update(price=str(value), validation_status="VALID_VENDOR_BAR")
    # Echoed ticker is not verified legal/security identity or corporate-action continuity.
    return result


def compare(a, b, identity=None):
    """Diagnostic vendor comparison only; caller-supplied identity flags are not official proof."""
    if any(x["validation_status"] != "VALID_VENDOR_BAR" for x in (a, b)):
        return "UNAVAILABLE", None
    if a["ticker"] != b["ticker"] or a["session_date"] != b["session_date"]:
        return "IDENTITY_OR_SESSION_MISMATCH", None
    # Distinct *declared* vendor organizations are a necessary diagnostic
    # condition, never proof of independent underlying exchange feeds or
    # exchange-official auction closes. Fail closed on aliases, blanks, and
    # same-organization copies before any numerical agreement is reported.
    if {a.get("provider_organization"), b.get("provider_organization")} != {"MASSIVE", "TWELVE_DATA"}:
        return "PROVIDER_ORGANIZATION_NOT_DISTINCT_OR_UNRECOGNIZED", None
    if a["price_type"] != b["price_type"] or a["adjustment_basis"] != b["adjustment_basis"]:
        return "PRICE_BASIS_MISMATCH", None
    if not identity or identity.get("identity_verified") is not True or identity.get("exchange_verified") is not True:
        return "IDENTITY_UNVERIFIED", None
    if identity.get("corporate_actions_verified") is not True or identity.get("corporate_action_changed") is not False:
        return "CORPORATE_ACTION_AMBIGUITY", None
    if identity.get("ticker") != a["ticker"] or identity.get("session_date") != a["session_date"]:
        return "IDENTITY_OR_SESSION_MISMATCH", None
    if not identity.get("security_id") or not identity.get("source_receipts"):
        return "IDENTITY_UNVERIFIED", None
    difference = abs(Decimal(a["price"]) - Decimal(b["price"]))
    # A caller-supplied identity mapping, even with review flags and receipt
    # strings, is not independently authenticated exchange-official evidence.
    # Never return bare AGREE/DISAGREE: those labels could be mistaken for
    # eligible official-close corroboration by downstream reporting.
    return ("VENDOR_BAR_AGREEMENT_NOT_OFFICIAL" if difference <= TOLERANCE
            else "VENDOR_BAR_CONFLICT_NOT_OFFICIAL"), str(difference)


def _bounded_request_window(symbols, sessions):
    """Validate the entire fixed diagnostic cohort BEFORE any paid API request.

    The Twelve Data date filter must be explicit: outputsize=10 alone drifts
    away from the requested historical sessions as newer bars accumulate.
    This is not an exchange-calendar or official-close verification.
    """
    if (not isinstance(symbols, (list, tuple)) or not symbols
            or len(symbols) > 2 or len(set(symbols)) != len(symbols)
            or any(not isinstance(s, str) or not re.fullmatch(r"[A-Z]{1,6}", s)
                   for s in symbols)):
        raise ValueError("BOUNDED_UNIQUE_SYMBOLS_REQUIRED")
    if (not isinstance(sessions, (list, tuple)) or not sessions
            or len(sessions) > 4 or len(symbols) * len(sessions) > 4
            or any(not isinstance(s, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s)
                   for s in sessions)):
        raise ValueError("BOUNDED_SESSION_DATES_REQUIRED")
    try:
        days = [dt.date.fromisoformat(s) for s in sessions]
    except ValueError as exc:
        raise ValueError("BOUNDED_SESSION_DATES_REQUIRED") from exc
    if len(set(days)) != len(days) or days != sorted(days) or (days[-1] - days[0]).days > 31:
        raise ValueError("UNIQUE_ASCENDING_MAX_31_DAY_WINDOW_REQUIRED")
    # Validate every requested date BEFORE any potentially billable request.
    # Do not silently turn a weekend, published holiday or out-of-scope year
    # into a fabricated completed cash-equity trading session.
    if not all(_scheduled_cash_session_2026(day) for day in days):
        raise ValueError("CLOSED_OR_UNVERIFIED_EXCHANGE_SESSION")
    return sessions[0], sessions[-1]


def reconcile(symbols=SYMBOLS, sessions=SESSIONS):
    start_date, end_date = _bounded_request_window(symbols, sessions)
    # A published scheduled session is not necessarily a completed session.
    # Reject the ENTIRE diagnostic window before any billable request when
    # any target session is still future/in progress. Never fetch a mutable
    # current-day bar and misreport it as a completed vendor close. This
    # conservative 16:00 ET gate is not official auction authentication.
    started_at_utc = utcnow()
    if not all(_request_after_regular_close(day, started_at_utc) for day in sessions):
        raise ValueError("SESSION_NOT_COMPLETE_AT_DIAGNOSTIC_START")
    massive, twelve = Budget(4), Budget(2)
    result = {"mode": "RESEARCH_ONLY_NOT_AN_ORDER", "model_version": "vendor-corroboration-v2",
              "captured_at_utc": started_at_utc, "sessions": list(sessions), "symbols": list(symbols),
              "comparison_tolerance_usd": str(TOLERANCE), "rows": [],
              "official_exchange_close_verified": False, "outcome_scoring_eligible": False,
              "independent_underlying_exchange_feed_verified": False, "trade_authorized": False,
              "vendor_redirect_policy": "DENY_ALL_REDIRECTS",
              "vendor_daily_bar_cutoff": "REQUEST_START_AFTER_16_ET_CONSERVATIVE_NOT_CALENDAR_PROOF",
              "vendor_calendar_screen": "STATIC_NYSE_2026_SCHEDULE_ONLY_NOT_SESSION_AUTHENTICATION",
              "official_close_proof_requirements": list(OFFICIAL_CLOSE_PROOF_GAPS),
              "third_source_conflict_inventory_status": "NOT_COLLECTED"}
    for symbol in symbols:
        t = twelve.fetch("https://api.twelvedata.com/time_series",
                         {"symbol": symbol, "interval": "1day", "start_date": start_date,
                          "end_date": end_date, "adjust": "none",
                          "apikey": os.environ.get("TWELVE_DATA_API_KEY", "")},
                         os.environ.get("TWELVE_DATA_API_KEY", ""), expected_status="ok")
        for day in sessions:
            m = massive.fetch("https://api.massive.com/v1/open-close/" + parse.quote(symbol, safe="") + "/" + day,
                              {"adjusted": "false", "apiKey": os.environ.get("MASSIVE_API_KEY", "")},
                              os.environ.get("MASSIVE_API_KEY", ""), expected_status="OK")
            a, b = observation("MASSIVE", symbol, day, m), observation("TWELVE_DATA", symbol, day, t)
            status, difference = compare(a, b)
            both = all(x["validation_status"] == "VALID_VENDOR_BAR" for x in (a, b))
            # A withheld identity review must NOT hide numeric disagreement
            # between available vendor bars. Preserve this diagnostic conflict
            # separately from authenticated official-close source conflicts.
            vendor_difference = (abs(Decimal(a["price"]) - Decimal(b["price"]))
                                 if both else None)
            result["rows"].append({"symbol": symbol, "session": day, "providers": {"MASSIVE": a, "TWELVE_DATA": b},
                                   "both_bars_present": both, "comparison_status": status,
                                   "absolute_difference_usd": difference, "within_tolerance":
                                   True if status == "VENDOR_BAR_AGREEMENT_NOT_OFFICIAL"
                                   else False if status == "VENDOR_BAR_CONFLICT_NOT_OFFICIAL" else None,
                                   "eligible_official_close": False,
                                   "official_close_evidence_status": "CENSORED_UNVERIFIED",
                                   "missing_official_close_proofs": list(OFFICIAL_CLOSE_PROOF_GAPS),
                                   "third_source_conflict_status": "NOT_COLLECTED",
                                   "vendor_bar_numeric_difference_usd_unverified_identity":
                                   str(vendor_difference) if vendor_difference is not None else None,
                                   "vendor_bar_numeric_conflict_unverified_identity":
                                   vendor_difference > TOLERANCE if vendor_difference is not None else None,
                                   "diagnostic_numeric_agreement_only":
                                   vendor_difference <= TOLERANCE if vendor_difference is not None else None})
    rows = result["rows"]
    result.update(total_ticker_dates=len(rows), official_close_censored_count=len(rows),
                  official_close_eligible_count=0, third_source_conflict_inventory_count=0,
                  both_bar_count=sum(r["both_bars_present"] for r in rows),
                  valid_same_session_pairs=sum(r["comparison_status"] in
                      {"VENDOR_BAR_AGREEMENT_NOT_OFFICIAL", "VENDOR_BAR_CONFLICT_NOT_OFFICIAL"} for r in rows),
                  matching_bar_count=sum(r["comparison_status"] == "VENDOR_BAR_AGREEMENT_NOT_OFFICIAL" for r in rows),
                  conflict_count=sum(r["comparison_status"] == "VENDOR_BAR_CONFLICT_NOT_OFFICIAL" for r in rows),
                  vendor_bar_numeric_conflict_unverified_identity_count=sum(
                      r["vendor_bar_numeric_conflict_unverified_identity"] is True for r in rows),
                  vendor_bar_numeric_agreement_unverified_identity_count=sum(
                      r["diagnostic_numeric_agreement_only"] is True for r in rows),
                  missing_pair_count=sum(not r["both_bars_present"] for r in rows),
                  rate_limited_count=sum(any(p["provider_error_category"] == "RATE_LIMIT" for p in r["providers"].values()) for r in rows),
                  corporate_action_blocked_count=sum(r["comparison_status"] == "CORPORATE_ACTION_AMBIGUITY" for r in rows),
                  identity_blocked_count=sum(r["comparison_status"] == "IDENTITY_UNVERIFIED" for r in rows))
    for provider in ("MASSIVE", "TWELVE_DATA"):
        result["valid_" + provider.lower() + "_bars"] = sum(r["providers"][provider]["validation_status"] == "VALID_VENDOR_BAR" for r in rows)
    result["request_budget"] = {"massive_max": 4, "twelve_data_max": 2, "automatic_retries": 0,
                                "massive_used": massive.used, "twelve_data_used": twelve.used}
    return result


def main():
    # Fail before spending API quota if this immutable destination already exists.
    if OUT.exists():
        raise FileExistsError(OUT)
    result = reconcile()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    print(json.dumps({k: v for k, v in result.items() if k not in {"rows"}}, sort_keys=True))


if __name__ == "__main__":
    main()
