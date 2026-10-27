"""Research-only validation of delayed Alpaca SIP bar response provenance.

A successful HTTP request is not evidence of nonempty, trustworthy bars.
Never use delayed bars as an as-of preclose observation or executable quote.
"""
from datetime import datetime, timedelta, timezone
from math import isfinite


def _time(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc) if dt.utcoffset() is not None else None


def inspect_delayed_sip(payload, symbol, start, end, received_at):
    """Validate content, timestamps, OHLC and volume; no price outcome claims."""
    result = {"status": "UNVERIFIED", "valid_bars": 0,
              "research_only": "RESEARCH_ONLY_NOT_AN_ORDER"}
    if any(not isinstance(t, datetime) or t.utcoffset() is None
           for t in (start, end, received_at)):
        result["status"] = "INVALID_REQUEST_CLOCK"
        return result
    if not (start < end <= received_at - timedelta(minutes=15)):
        result["status"] = "NOT_DELAYED_ASOF"
        return result
    if not isinstance(payload, dict) or not isinstance(payload.get("bars"), dict):
        result["status"] = "INVALID_RESPONSE_SHAPE"
        return result
    bars = payload["bars"].get(symbol)
    if bars is None or bars == []:
        result["status"] = "NO_BARS_RETURNED"
        return result
    if not isinstance(bars, list):
        result["status"] = "INVALID_BAR_LIST"
        return result
    seen = set()
    excluded_boundary = 0
    for bar in bars:
        if not isinstance(bar, dict):
            result["status"] = "INVALID_BAR"
            return result
        t = _time(bar.get("t"))
        if t is None or not (start <= t <= end) or t >= received_at or t in seen:
            result["status"] = "INVALID_OR_DUPLICATE_BAR_TIMESTAMP"
            return result
        seen.add(t)
        # Alpaca's bars endpoint can include the exact requested end
        # timestamp. That minute is outside the half-open study interval.
        if t == end:
            excluded_boundary += 1
            continue
        prices = [bar.get(k) for k in ("o", "h", "l", "c")]
        if any(type(x) not in (float, int) or not isfinite(x) or x <= 0 for x in prices):
            result["status"] = "INVALID_OHLC"
            return result
        o, h, l, c = prices
        if not (l <= min(o, c) <= max(o, c) <= h):
            result["status"] = "INCONSISTENT_OHLC"
            return result
        volume = bar.get("v")
        if type(volume) not in (float, int) or not isfinite(volume) or volume < 0:
            result["status"] = "INVALID_VOLUME"
            return result
    result["boundary_bars_excluded"] = excluded_boundary
    result["valid_bars"] = len(bars) - excluded_boundary
    result["status"] = ("DELAYED_SIP_BAR_CONTENT_VALIDATED_NOT_OFFICIAL_CLOSE"
                        if result["valid_bars"] else "NO_IN_WINDOW_BARS")
    return result
