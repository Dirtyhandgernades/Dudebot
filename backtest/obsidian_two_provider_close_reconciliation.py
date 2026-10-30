"""Bounded research vendor corroboration; never frozen official-close evidence."""
import datetime as dt
import hashlib
import json
import os
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib import request, parse, error

SYMBOLS = ("AAPL", "MSFT")
SESSIONS = ("2026-10-27", "2026-10-28")
OUT = Path("outputs/backtest/obsidian-two-provider-close-reconciliation.json")
TOLERANCE = Decimal("0.005")


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


def get(url, params, token):
    """Never log URLs, exceptions or provider messages that could echo credentials."""
    req = request.Request(url + "?" + parse.urlencode(params),
                          headers={"User-Agent": "OBSIDIAN-research-only/2.0"})
    try:
        try:
            response = _open_no_redirect(req)
        except error.HTTPError as exc:
            response = exc
        with response:
            body = response.read(150001)
            status = response.code
            # Keep only bounded numeric quota headers. Arbitrary vendor header
            # strings (including echoed query tokens) are unsafe to archive.
            headers = {k.lower(): v.strip() for k, v in response.headers.items()
                       if k.lower() in {"retry-after", "x-ratelimit-remaining", "x-ratelimit-reset"}
                       and isinstance(v, str) and re.fullmatch(r"[0-9]{1,16}", v.strip())}
        payload = json.loads(body) if len(body) <= 150000 else None
    except (ValueError, UnicodeDecodeError):
        payload = None
    except Exception:
        return {"http_status": None, "error": "NETWORK_UNAVAILABLE", "payload": None,
                "retrieved_at": utcnow(), "body_sha256": None, "headers": {}}
    # Raw provider bodies and arbitrary error text must never reach the public
    # GitHub Actions artifact: a vendor may echo URL query credentials verbatim.
    return {"http_status": status, "body_sha256": hashlib.sha256(body).hexdigest(),
            "payload": payload, "retrieved_at": utcnow(), "headers": headers}


def category(receipt):
    status = receipt.get("http_status")
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
    return None


@dataclass
class Budget:
    maximum: int
    used: int = 0
    stopped: str | None = None

    def fetch(self, url, params, token):
        if not token:
            return {"error": "SECRET_ABSENT"}
        if self.stopped or self.used >= self.maximum:
            return {"error": self.stopped or "REQUEST_BUDGET_EXHAUSTED"}
        self.used += 1
        receipt = get(url, params, token)
        failure = category(receipt)
        if failure in {"RATE_LIMIT", "AUTHENTICATION", "ENTITLEMENT_OR_ACCESS"}:
            self.stopped = failure
        if receipt.get("headers", {}).get("x-ratelimit-remaining") == "0":
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


def observation(provider, symbol, day, receipt):
    result = {"provider_organization": provider, "ticker": symbol, "session_date": day,
              "security_identity": None, "identity_verified": False, "exchange": None,
              "price": None, "price_type": "VENDOR_DAILY_OHLC_CLOSE", "adjustment_basis": "UNKNOWN",
              "source_timestamp": None, "retrieval_timestamp": receipt.get("retrieved_at"),
              "http_status": receipt.get("http_status"), "provider_error_category": category(receipt),
              "raw_response_hash": receipt.get("body_sha256"), "validation_status": "BLOCKED",
              "provenance": "https://api.massive.com/v1/open-close" if provider == "MASSIVE"
                            else "https://api.twelvedata.com/time_series",
              "rate_limit_headers": receipt.get("headers", {}),
              "raw_body_retained": False}
    if result["provider_error_category"]:
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
        result["source_timestamp"] = day if payload.get("from") == day else None
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
        result["exchange"] = exchange if exchange in {"NASDAQ", "NYSE"} else None
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
        result["source_timestamp"] = bar.get("datetime")
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
    """External reviewed identity/action evidence is mandatory for comparable pairs."""
    if any(x["validation_status"] != "VALID_VENDOR_BAR" for x in (a, b)):
        return "UNAVAILABLE", None
    if a["ticker"] != b["ticker"] or a["session_date"] != b["session_date"]:
        return "IDENTITY_OR_SESSION_MISMATCH", None
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
    return ("AGREE" if difference <= TOLERANCE else "DISAGREE"), str(difference)


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
    return sessions[0], sessions[-1]


def reconcile(symbols=SYMBOLS, sessions=SESSIONS):
    start_date, end_date = _bounded_request_window(symbols, sessions)
    massive, twelve = Budget(4), Budget(2)
    result = {"mode": "RESEARCH_ONLY_NOT_AN_ORDER", "model_version": "vendor-corroboration-v2",
              "captured_at_utc": utcnow(), "sessions": list(sessions), "symbols": list(symbols),
              "comparison_tolerance_usd": str(TOLERANCE), "rows": [],
              "official_exchange_close_verified": False, "outcome_scoring_eligible": False,
              "independent_underlying_exchange_feed_verified": False, "trade_authorized": False,
              "vendor_redirect_policy": "DENY_ALL_REDIRECTS"}
    for symbol in symbols:
        t = twelve.fetch("https://api.twelvedata.com/time_series",
                         {"symbol": symbol, "interval": "1day", "start_date": start_date,
                          "end_date": end_date, "adjust": "none",
                          "apikey": os.environ.get("TWELVE_DATA_API_KEY", "")},
                         os.environ.get("TWELVE_DATA_API_KEY", ""))
        for day in sessions:
            m = massive.fetch("https://api.massive.com/v1/open-close/" + parse.quote(symbol, safe="") + "/" + day,
                              {"adjusted": "false", "apiKey": os.environ.get("MASSIVE_API_KEY", "")},
                              os.environ.get("MASSIVE_API_KEY", ""))
            a, b = observation("MASSIVE", symbol, day, m), observation("TWELVE_DATA", symbol, day, t)
            status, difference = compare(a, b)
            both = all(x["validation_status"] == "VALID_VENDOR_BAR" for x in (a, b))
            result["rows"].append({"symbol": symbol, "session": day, "providers": {"MASSIVE": a, "TWELVE_DATA": b},
                                   "both_bars_present": both, "comparison_status": status,
                                   "absolute_difference_usd": difference, "within_tolerance":
                                   True if status == "AGREE" else False if status == "DISAGREE" else None,
                                   "eligible_official_close": False,
                                   "diagnostic_numeric_agreement_only":
                                   abs(Decimal(a["price"]) - Decimal(b["price"])) <= TOLERANCE if both else None})
    rows = result["rows"]
    result.update(total_ticker_dates=len(rows), both_bar_count=sum(r["both_bars_present"] for r in rows),
                  valid_same_session_pairs=sum(r["comparison_status"] in {"AGREE", "DISAGREE"} for r in rows),
                  matching_bar_count=sum(r["comparison_status"] == "AGREE" for r in rows),
                  conflict_count=sum(r["comparison_status"] == "DISAGREE" for r in rows),
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
