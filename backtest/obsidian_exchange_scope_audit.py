"""Offline, research-only exchange denominator audit for a frozen IEX capture.

Never changes a captured universe. An asset response obtained at a different
moment cannot establish why a symbol was absent from an earlier capture.
No prices, eligibility, borrow, orders, network access, or performance claims.
"""
from collections import Counter
from datetime import datetime

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
CAPTURE_EXCHANGES = frozenset(("NASDAQ", "NYSE"))


def _aware(value):
    if not isinstance(value, str):
        raise ValueError("MISSING_ASOF_TIMESTAMP")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_ASOF_TIMESTAMP") from exc
    if parsed.utcoffset() is None:
        raise ValueError("NAIVE_ASOF_TIMESTAMP")
    return parsed


def _symbols(values, label):
    if not isinstance(values, (list, tuple)):
        raise ValueError("INVALID_" + label)
    if any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in values):
        raise ValueError("INVALID_" + label)
    if len(values) != len(set(values)):
        raise ValueError("DUPLICATE_" + label)
    return set(values)


def audit(assets, captured_symbols, historical_symbols, *,
          capture_started_at, capture_finished_at, assets_observed_at):
    """Audit requested coverage, without rewriting or backfilling any capture.

    `assets` must be the *complete raw* provider asset response, not the
    already-filtered rows from a captured IEX universe. If it was collected
    outside the immutable capture interval, exclusions are only hypothetical.
    """
    start = _aware(capture_started_at)
    finish = _aware(capture_finished_at)
    observed = _aware(assets_observed_at)
    if finish < start:
        raise ValueError("INVALID_CAPTURE_INTERVAL")
    captured = _symbols(captured_symbols, "CAPTURE_SYMBOLS")
    historical = _symbols(historical_symbols, "HISTORICAL_SYMBOLS")
    if not isinstance(assets, list) or not assets:
        raise ValueError("EMPTY_OR_INVALID_PROVIDER_ASSETS")
    by_symbol = {}
    for item in assets:
        if not isinstance(item, dict):
            raise ValueError("INVALID_PROVIDER_ASSET_ROW")
        symbol = item.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip() or symbol != symbol.strip():
            raise ValueError("INVALID_PROVIDER_ASSET_SYMBOL")
        if symbol in by_symbol:
            raise ValueError("DUPLICATE_PROVIDER_ASSET_SYMBOL")
        by_symbol[symbol] = item
    same_capture = start <= observed <= finish
    selected = {ticker for ticker, asset in by_symbol.items()
                if asset.get("status") == "active"
                and asset.get("exchange") in CAPTURE_EXCHANGES}
    # Time alignment alone is not cryptographic authentication; caller must
    # separately verify the full original provider-response provenance.
    if same_capture and selected != captured:
        raise ValueError("CONTEMPORANEOUS_SELECTED_UNIVERSE_MISMATCH")
    rows = []
    for ticker in sorted(historical):
        item = by_symbol.get(ticker)
        if ticker in captured:
            state = "CAPTURE_REQUESTED_NOT_NECESSARILY_USABLE"
        elif not same_capture:
            state = "MISSING_FROM_CAPTURE_ASYNC_METADATA_CANNOT_EXPLAIN"
        elif item is None:
            state = "MISSING_FROM_PROVIDER_RESPONSE_NOT_PROOF_OF_DELISTING"
        elif item.get("status") != "active":
            state = "EXCLUDED_INACTIVE_PROVIDER_METADATA_NOT_DELISTING_PROOF"
        elif item.get("exchange") not in CAPTURE_EXCHANGES:
            state = "EXCLUDED_EXCHANGE_SCOPE_NOT_SMG_INELIGIBILITY"
        else:
            raise ValueError("UNRECONCILED_SELECTED_HISTORICAL_SYMBOL")
        rows.append({"ticker": ticker, "status": state,
                     "provider_exchange_asof": item.get("exchange") if item else None,
                     "provider_status_asof": item.get("status") if item else None,
                     "provider_metadata_time_aligned": same_capture})
    exchange_counts = Counter(str(a.get("exchange", "UNKNOWN")) for a in assets)
    status_counts = Counter(str(a.get("status", "UNKNOWN")) for a in assets)
    return {
        "mode": MODE, "capture_modified": False,
        "provider_metadata_time_aligned": same_capture,
        "provider_response_authenticated_by_audit": False,
        "provider_assets_count": len(assets),
        "selected_nyse_nasdaq_active_count": len(selected),
        "captured_requested_count": len(captured),
        "historical_retained_count": len(historical),
        "historical_captured_count": len(historical & captured),
        "historical_missing_count": len(historical - captured),
        "provider_exchange_counts": dict(sorted(exchange_counts.items())),
        "provider_status_counts": dict(sorted(status_counts.items())),
        "historical_status_counts": dict(sorted(Counter(r["status"] for r in rows).items())),
        "rows": rows,
        "limitations": [
            "Full original provider-response provenance and hash require independent verification.",
            "Provider metadata does not establish SMG eligibility, common stock, borrow, or liquidity.",
            "No missing ticker is presumed delisted or screened ineligible.",
            "Only the original immutable capture proves an authenticated requested symbol.",
            "Asynchronous provider metadata cannot retroactively explain a frozen capture exclusion.",
            "No price, closing outcome, or predictive performance is scored.",
        ],
    }
