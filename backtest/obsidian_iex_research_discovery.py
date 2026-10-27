"""Read-only, source-limited IEX discovery snapshots outside the EOD capture gate.

Unlike the protected 14:45-14:58 CT prospective capture, these are EARLY
RECONNAISSANCE observations. Alpaca IEX is one venue; the previous IEX daily
bar is NOT an official prior regular-session close. No eligibility, borrow,
fills, technical pattern, catalyst or future return is inferred from a quote.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from backtest.obsidian_iex_prospective import IEXReadOnly, IEX_SNAPSHOTS, IEX_SCOPE
from backtest.obsidian_prospective_capture import (
    ASSETS_URL, BATCH_SIZE, CENTRAL, EASTERN, asof, now_utc, in_window
)
from backtest.obsidian_early_discovery_packet import build_packet

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
FRESH_LIMIT = timedelta(minutes=15)
EARLY_STATES = frozenset(("IEX_INDICATIVE_EARLY_2_TO_15",
                         "IEX_INDICATIVE_INTERMEDIATE_15_TO_25"))


def phase_at(now):
    """Do not use a research scan to evade the immutable preclose gate."""
    if not isinstance(now, datetime) or now.utcoffset() is None:
        return "INVALID_CLOCK"
    local = now.astimezone(CENTRAL)
    if local.weekday() > 4:
        return "OUTSIDE_RESEARCH_DAYS"
    if in_window(now):
        return "RESERVED_FOR_PROSPECTIVE_EOD_CAPTURE"
    hour, minute = local.hour, local.minute
    if 5 <= hour < 12:
        return "MORNING"
    if 12 <= hour < 14 or hour == 14 and minute < 45:
        return "INTRADAY"
    if 15 <= hour <= 22:
        return "AFTERHOURS"
    return "OUTSIDE_RESEARCH_HOURS"


def _price(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def indicative(snap, received):
    """Return a single-venue attention label, NOT a validated price outcome."""
    if snap is None:
        return "MISSING_IEX_SNAPSHOT", None
    if not isinstance(snap, dict):
        return "MALFORMED_IEX_SNAPSHOT", None
    trade, prior = snap.get("latestTrade"), snap.get("prevDailyBar")
    if not isinstance(trade, dict) or not isinstance(prior, dict):
        return "MISSING_IEX_TRADE_OR_PREV_BAR", None
    current, previous = trade.get("p"), prior.get("c")
    observed, previous_at = asof(trade.get("t")), asof(prior.get("t"))
    if not _price(current) or not _price(previous):
        return "INVALID_IEX_REFERENCE_PRICE", None
    if observed is None or observed > received or received - observed > FRESH_LIMIT:
        return "STALE_OR_FUTURE_IEX_PRINT", None
    if previous_at is None or previous_at >= received:
        return "INVALID_IEX_PREVIOUS_REFERENCE", None
    # Weekends handled, exchange holidays NOT assumed. Holiday-adjacent
    # snapshots are censored until separately validated by calendar evidence.
    target = received.astimezone(EASTERN).date() - timedelta(days=1)
    while target.weekday() >= 5:
        target -= timedelta(days=1)
    if previous_at.astimezone(EASTERN).date() != target:
        return "UNVERIFIED_PREVIOUS_IEX_DAY", None
    change = round(100 * (current / previous - 1), 5)
    if current < 3 or previous < 3:
        return "INDICATIVE_PRICE_FLOOR_BLOCK", change
    if change <= -25:
        return "IEX_INDICATIVE_EXHAUSTED", change
    if change < -15:
        return "IEX_INDICATIVE_INTERMEDIATE_15_TO_25", change
    if change <= -2:
        return "IEX_INDICATIVE_EARLY_2_TO_15", change
    return "IEX_INDICATIVE_OTHER", change


def collect(provider, clock=now_utc, max_requests=150):
    started = clock()
    phase = phase_at(started)
    if phase not in ("MORNING", "INTRADAY", "AFTERHOURS"):
        raise ValueError("OUTSIDE_RESEARCH_DISCOVERY_WINDOW_" + phase)
    assets = provider.assets()
    assets_at = clock()
    if phase_at(assets_at) != phase or assets_at < started:
        raise ValueError("DISCOVERY_CLOCK_OR_PHASE_CHANGED")
    if not isinstance(assets, list) or not assets:
        raise ValueError("EMPTY_OR_INVALID_ASSET_UNIVERSE")
    selected = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("MALFORMED_ASSET")
        if asset.get("exchange") not in ("NASDAQ", "NYSE") or asset.get("status") != "active":
            continue
        symbol = asset.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip() or symbol in selected:
            raise ValueError("INVALID_OR_DUPLICATE_ASSET_SYMBOL")
        selected[symbol] = asset
    if not selected:
        raise ValueError("NO_ELIGIBLE_EXCHANGE_ASSET_METADATA")
    symbols = sorted(selected)
    request_count = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
    if request_count > max_requests:
        raise ValueError("REQUEST_BUDGET_EXCEEDED")
    rows = []
    last = assets_at
    for offset in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[offset:offset + BATCH_SIZE]
        requested = clock()
        if requested < last or phase_at(requested) != phase:
            raise ValueError("DISCOVERY_REQUEST_CLOCK_OR_PHASE_CHANGED")
        result = provider.snapshots(batch)
        received = clock()
        if received < requested or phase_at(received) != phase:
            raise ValueError("DISCOVERY_RESPONSE_CLOCK_OR_PHASE_CHANGED")
        if not isinstance(result, dict) or set(result) - set(batch):
            raise ValueError("INVALID_IEX_SNAPSHOT_SYMBOLS")
        last = received
        for symbol in batch:
            present = symbol in result
            raw = result.get(symbol)
            state, change = indicative(raw, received)
            rows.append({
                "ticker": symbol, "asset": selected[symbol],
                "snapshot_present": present, "snapshot": raw,
                "received_at": received.isoformat(),
                "indicative_status": state,
                "iex_reference_change_pct": change,
                "smg_eligible": None,
                "platform_short_available": None,
                "trade_authorized": False,
            })
    finished = clock()
    if finished < last or phase_at(finished) != phase:
        raise ValueError("DISCOVERY_FINISH_CLOCK_OR_PHASE_CHANGED")
    counts = dict(sorted(Counter(x["indicative_status"] for x in rows).items()))
    return rows, {
        "status": "IEX_SINGLE_VENUE_RECONNAISSANCE_NOT_A_PRECLOSE_CAPTURE",
        "mode": MODE, "feed": "iex", "provider_scope": IEX_SCOPE,
        "phase": phase, "started_at": started.isoformat(),
        "assets_received_at": assets_at.isoformat(),
        "finished_at": finished.isoformat(),
        "asset_source": ASSETS_URL, "snapshot_source": IEX_SNAPSHOTS,
        "asset_api_count": len(assets), "universe_count": len(rows),
        "snapshots_requested": len(rows), "api_request_batches": request_count,
        "status_counts": counts, "trading_session_independently_confirmed": False,
        "previous_reference_is_official_close": False,
        "full_market_coverage_confirmed": False, "smg_eligibility_confirmed": False,
        "preclose_prediction_verified": False, "actual_fills": None,
        "future_regular_close_outcomes": None,
        "limitations": [
            "IEX is one venue, not SIP/consolidated regular-session trading.",
            "Previous IEX daily bar is not a validated official prior close.",
            "Single-snapshot changes do not establish failed rebounds, support, sell volume, or liquidity.",
            "Unknown, absent, stale and ineligible data remain in the denominator.",
            "This observation never substitutes for the authorized 14:45-14:58 CT write-once capture.",
        ],
    }


def _bytes(rows):
    return "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
                   for row in rows).encode("utf-8")


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def build_attention_packet(rows, manifest, master=(), supplemental=(), references=()):
    """Connect actual GET snapshots to strict offline triage without inventing EOD proof."""
    snapshots = []
    for item in rows:
        snap = item.get("snapshot")
        trade = snap.get("latestTrade") if isinstance(snap, dict) else None
        prior = snap.get("prevDailyBar") if isinstance(snap, dict) else None
        price = trade.get("p") if isinstance(trade, dict) else None
        iref = prior.get("c") if isinstance(prior, dict) else None
        stamp = asof(trade.get("t")) if isinstance(trade, dict) else None
        row = {
            "ticker": item["ticker"], "phase": manifest["phase"],
            "observed_at": item["received_at"],
            "observed_price": price if _price(price) else None,
            # A single-venue priorDailyBar is kept as a research-only reference.
            # Never mark it as a completed, independently corroborated prior close.
            "iex_previous_daily_reference_only": iref if _price(iref) else None,
            "quote": ({"value": price, "verified": True,
                       "observed_at": stamp.isoformat(),
                       "source_id": "ALPACA_IEX_SINGLE_VENUE"}
                      if stamp is not None and _price(price) else {}),
        }
        snapshots.append(row)
    packet = {
        "snapshots": snapshots,
        "observations": [],
        "decision_cutoff": manifest["finished_at"],
    }
    summary = build_packet(packet, list(master), list(supplemental), list(references))
    summary["single_venue_indicative_attention"] = [
        {"ticker": row["ticker"], "reference_change_pct": row["iex_reference_change_pct"],
         "status": row["indicative_status"], "asof": row["received_at"],
         "not_a_trading_signal": True}
        for row in rows if row["indicative_status"] in EARLY_STATES]
    summary["source_is_read_only_authenticated_provider"] = True
    summary["separately_verified_prior_close"] = False
    summary["complete_eod_screen"] = False
    return summary


def verify(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    universe = (root / "universe.jsonl").read_bytes()
    attention = (root / "attention.json").read_bytes()
    if _digest(universe) != manifest.get("universe_sha256") or _digest(attention) != manifest.get("attention_sha256"):
        raise ValueError("DISCOVERY_ARTIFACT_HASH_MISMATCH")
    if not universe.endswith(b"\n") or not universe:
        raise ValueError("EMPTY_OR_TRUNCATED_UNIVERSE")
    rows = [json.loads(line) for line in universe.splitlines()]
    if not rows or len(rows) != manifest.get("universe_count"):
        raise ValueError("UNIVERSE_DENOMINATOR_MISMATCH")
    status = Counter()
    symbols = []
    previous_at = asof(manifest.get("assets_received_at"))
    finished_at = asof(manifest.get("finished_at"))
    start_at = asof(manifest.get("started_at"))
    if (previous_at is None or finished_at is None or start_at is None or
        not start_at <= previous_at <= finished_at or
        phase_at(start_at) != manifest.get("phase") or
        phase_at(finished_at) != manifest.get("phase")):
        raise ValueError("DISCOVERY_CLOCK_MISMATCH")
    for row in rows:
        symbol = row.get("ticker")
        symbols.append(symbol)
        asset = row.get("asset")
        observed = asof(row.get("received_at"))
        if (not isinstance(asset, dict) or asset.get("symbol") != symbol
                or asset.get("exchange") not in ("NYSE", "NASDAQ")
                or observed is None or not previous_at <= observed <= finished_at
                or phase_at(observed) != manifest["phase"]):
            raise ValueError("DISCOVERY_ASSET_OR_TIMESTAMP_MISMATCH")
        if type(row.get("snapshot_present")) is not bool or (
                row["snapshot_present"] is False and row.get("snapshot") is not None):
            raise ValueError("SNAPSHOT_PRESENCE_MISMATCH")
        value, change = indicative(row.get("snapshot"), observed)
        if value != row.get("indicative_status") or change != row.get("iex_reference_change_pct"):
            raise ValueError("INDICATIVE_CLASSIFICATION_MISMATCH")
        status[value] += 1
        previous_at = observed
    if sorted(set(symbols)) != symbols or dict(sorted(status.items())) != manifest.get("status_counts"):
        raise ValueError("DISCOVERY_STATUS_MISMATCH")
    scored = json.loads(attention)
    if scored.get("snapshots_received") != len(rows) or scored.get("snapshots_preserved") != len(rows):
        raise ValueError("ATTENTION_COVERAGE_MISMATCH")
    if scored.get("full_market_denominator_verified") is not False or scored.get("early_catch_or_edge_demonstrated") is not False:
        raise ValueError("INVALID_RESEARCH_ASSERTIONS")
    return {
        "status": "VERIFIED_WRITE_ONCE_IEX_RESEARCH_ONLY",
        "universe_count": len(rows),
        "attention_indicative_count": len(scored.get("single_venue_indicative_attention", [])),
        "feed": "iex", "official_closes_verified": False, "trade_authorized": False,
    }


def persist(rows, manifest, destination, master=(), supplemental=(), references=()):
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("DISCOVERY_WRITE_ONCE_EXISTS")
    with TemporaryDirectory(prefix=".obsidian-iex-discovery-", dir=target.parent) as tmp:
        stage = Path(tmp)
        attention = build_attention_packet(rows, manifest, master, supplemental, references)
        universe = _bytes(rows)
        meta = {**manifest, "universe_sha256": _digest(universe)}
        raw_attention = json.dumps(attention, sort_keys=True, indent=2,
                                   allow_nan=False).encode("utf-8")
        meta["attention_sha256"] = _digest(raw_attention)
        (stage / "universe.jsonl").write_bytes(universe)
        (stage / "attention.json").write_bytes(raw_attention)
        (stage / "manifest.json").write_text(json.dumps(meta, indent=2, sort_keys=True),
                                              encoding="utf-8")
        verify(stage)
        if target.exists():
            raise FileExistsError("DISCOVERY_WRITE_ONCE_EXISTS")
        stage.rename(target)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--master", default="backtest/obsidian_historical_watchlist_manifest_2026_10_26.json")
    ap.add_argument("--supplemental", default="backtest/obsidian_supplemental_watchlist_2026_10_26.json")
    ap.add_argument("--references", default="backtest/obsidian_oct26_observation_provenance.json")
    args = ap.parse_args()
    current = now_utc()
    if phase_at(current) not in ("MORNING", "INTRADAY", "AFTERHOURS"):
        print(json.dumps({"status":"DISCOVERY_SKIPPED_PROTECTED_OR_OUTSIDE_HOURS",
                          "phase":phase_at(current), "mode":MODE}))
        return
    def rows_from(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))["records"]
    references = json.loads(Path(args.references).read_text(encoding="utf-8"))["observations"]
    result = persist(*collect(IEXReadOnly()), args.out,
                     rows_from(args.master), rows_from(args.supplemental), references)
    print(json.dumps({
        "status": result["status"], "phase":result["phase"],
        "universe_count":result["universe_count"], "status_counts":result["status_counts"],
        "future_outcome_validated": False, "executability_verified": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
