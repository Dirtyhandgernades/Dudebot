"""Read-only 17-minute delayed SIP historical recovery and coverage ledger.

The immutable original IEX capture is an INPUT, never changed or relabeled.
Reconstructed post-capture SIP bars cannot be claimed as genuine earlier predictions.
No real-time SIP, official close, SMG eligibility or trading orders.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import zipfile

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
POLICY = "OBSIDIAN_DELAYED_SIP_17MIN_HISTORICAL_RESCUE_V1_2026_10_28"
URL = "https://data.alpaca.markets/v2/stocks/bars"
DELAY = timedelta(minutes=17)
LOOKBACK = timedelta(minutes=60)
BAR_WIDTH = timedelta(minutes=1)
FRESHNESS = timedelta(minutes=12)
BATCH_SIZE = 100
IEX_UNUSABLE = frozenset({
    "STALE_OR_FUTURE_IEX_PRINT", "STALE_OR_FUTURE_IEX_TRADE",
    "MISSING_IEX_SNAPSHOT", "MISSING_SNAPSHOT",
    "MISSING_IEX_TRADE_OR_PREV_BAR", "MISSING_TRADE_OR_PREVIOUS_BAR",
    "UNVERIFIED_PREVIOUS_IEX_DAY", "UNVERIFIED_PREVIOUS_IEX_SESSION",
    "INVALID_IEX_REFERENCE_PRICE", "INVALID_IEX_PREVIOUS_REFERENCE",
})

def stamp(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.utcoffset() is not None else None

def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def digest(value):
    return hashlib.sha256(value).hexdigest()

def price_ok(value):
    return type(value) in (float, int) and math.isfinite(value) and value > 0

def load_original(path):
    path = Path(path)
    if path.is_file() and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            raw = archive.read("universe.jsonl")
            manifest_bytes = archive.read("manifest.json")
    elif path.is_dir():
        raw = (path / "universe.jsonl").read_bytes()
        manifest_bytes = (path / "manifest.json").read_bytes()
    else:
        raise ValueError("ORIGINAL_CAPTURE_NOT_FOUND")
    meta = json.loads(manifest_bytes)
    if digest(raw) != meta.get("universe_sha256") or not raw.endswith(b"\n"):
        raise ValueError("ORIGINAL_RAW_SHA_OR_TRUNCATION_MISMATCH")
    if meta.get("feed") != "iex" or meta.get("trade_authorized") not in (False, None):
        raise ValueError("NOT_AN_IEX_RESEARCH_CAPTURE")
    start, finish = stamp(meta.get("started_at")), stamp(meta.get("finished_at"))
    if start is None or finish is None or finish < start:
        raise ValueError("INVALID_ORIGINAL_CAPTURE_CLOCK")
    rows = [json.loads(line) for line in raw.splitlines()]
    symbols = [x.get("ticker") for x in rows]
    if (len(rows) != meta.get("universe_count") or
            symbols != sorted(set(symbols)) or
            not all(isinstance(s, str) and s for s in symbols)):
        raise ValueError("ORIGINAL_UNIVERSE_MISMATCH")
    counts = Counter(x.get("indicative_status", x.get("screen_status")) for x in rows)
    if dict(counts) != meta.get("status_counts"):
        raise ValueError("ORIGINAL_STATUS_DENOMINATOR_MISMATCH")
    if any(not isinstance(x.get("asset"), dict) or x["asset"].get("symbol") != x["ticker"] for x in rows):
        raise ValueError("ORIGINAL_SECURITY_IDENTITY_MISMATCH")
    return rows, meta, digest(raw), digest(manifest_bytes)

class HistoricalSIP:
    """Only GET historical, raw 1Min SIP bars, never latest snapshots or orders."""
    def __init__(self):
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
            "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
        })
    def bars(self, symbols, start, end, token=None):
        params = {"symbols": ",".join(symbols), "timeframe": "1Min",
                  "start": iso(start), "end": iso(end), "feed": "sip",
                  "adjustment": "raw", "limit": "10000"}
        if token:
            params["page_token"] = token
        for attempt in range(2):
            try:
                response = self.session.get(URL, params=params, timeout=30)
            except Exception:
                raise RuntimeError("SIP_PROVIDER_NETWORK_ERROR") from None
            if response.status_code in (429, 502, 503, 504) and attempt == 0:
                time.sleep(2)
                continue
            if response.status_code != 200:
                raise RuntimeError("SIP_PROVIDER_HTTP_" + str(response.status_code))
            try:
                return response.json()
            except ValueError:
                raise RuntimeError("SIP_PROVIDER_INVALID_JSON") from None
        raise RuntimeError("SIP_PROVIDER_RETRIES_EXHAUSTED")

def request_batch(provider, symbols, start, eligible_end, max_pages=5):
    all_bars = {s: [] for s in symbols}
    token = None
    seen = set()
    pages = 0
    while True:
        if pages >= max_pages:
            raise ValueError("SIP_PAGINATION_BUDGET_EXCEEDED")
        # An interval bar is marked by its START. End the GET one bar before
        # the safe observation cutoff to exclude an incomplete final minute.
        response = provider.bars(symbols, start, eligible_end - BAR_WIDTH, token)
        pages += 1
        if not isinstance(response, dict) or not isinstance(response.get("bars"), dict):
            raise ValueError("SIP_PROVIDER_INVALID_RESPONSE")
        if set(response["bars"]) - set(symbols):
            raise ValueError("SIP_PROVIDER_UNREQUESTED_TICKER")
        for name, bars in response["bars"].items():
            if not isinstance(bars, list):
                raise ValueError("SIP_PROVIDER_INVALID_BAR_LIST")
            all_bars[name].extend(bars)
        token = response.get("next_page_token")
        if not token:
            break
        if not isinstance(token, str) or token in seen:
            raise ValueError("SIP_PROVIDER_PAGINATION_LOOP")
        seen.add(token)
    return all_bars, pages

def classify_bars(bars, start, cutoff):
    if not isinstance(bars, list):
        return "INVALID_PROVIDER_BAR_LIST", None
    if not bars:
        return "NO_CONSOLIDATED_BAR", None
    latest = None
    seen = set()
    for bar in bars:
        if not isinstance(bar, dict):
            return "INVALID_PROVIDER_BAR", None
        at = stamp(bar.get("t"))
        if (at is None or not price_ok(bar.get("c")) or at < start
                or at + BAR_WIDTH > cutoff):
            return "OUT_OF_WINDOW_OR_INVALID_SIP_BAR", None
        if at in seen:
            return "DUPLICATE_SIP_BAR_TIMESTAMP", None
        seen.add(at)
        if latest is None or at > latest[0]:
            latest = (at, bar)
    finished = latest[0] + BAR_WIDTH
    status = ("HISTORICAL_DELAYED_SIP_BAR_FRESH_AT_ASOF"
              if cutoff - finished <= FRESHNESS
              else "HISTORICAL_DELAYED_SIP_BAR_STALE_AT_ASOF")
    return status, {"bar_start": iso(latest[0]), "bar_end": iso(finished),
                    "close": latest[1]["c"], "volume": latest[1].get("v"),
                    "trade_count": latest[1].get("n"),
                    "minutes_behind_asof": round((cutoff-finished).total_seconds()/60, 3)}

def replay(capture, provider, clock=None, selected_symbols=None):
    observed = clock() if clock else datetime.now(timezone.utc)
    if not isinstance(observed, datetime) or observed.utcoffset() is None:
        raise ValueError("NAIVE_COLLECTION_TIME")
    original, original_meta, source_sha, meta_sha = load_original(capture)
    frozen_at = stamp(original_meta["finished_at"])
    if observed < frozen_at + DELAY:
        raise ValueError("HISTORICAL_SIP_EMBARGO_NOT_ELAPSED")
    cutoff, beginning = frozen_at - DELAY, frozen_at - DELAY - LOOKBACK
    original_symbols = {x["ticker"] for x in original}
    if selected_symbols is not None and not isinstance(selected_symbols, (set, list, tuple)):
        raise ValueError("INVALID_SELECTION")
    wanted = original_symbols if selected_symbols is None else set(selected_symbols)
    if not wanted <= original_symbols:
        raise ValueError("SELECTION_OUTSIDE_ORIGINAL_DENOMINATOR")
    found = {}
    batches = []
    for i in range(0, len(original), BATCH_SIZE):
        symbols = [x["ticker"] for x in original[i:i+BATCH_SIZE] if x["ticker"] in wanted]
        if not symbols:
            continue
        attempted = clock() if clock else datetime.now(timezone.utc)
        try:
            values, pages = request_batch(provider, symbols, beginning, cutoff)
            status, reason = "GET_COMPLETED", None
        except (ValueError, RuntimeError) as error:
            values, pages = {}, 0
            status, reason = "GET_FAILED_QUARANTINED", str(error).split(":", 1)[0][:100]
        finished = clock() if clock else datetime.now(timezone.utc)
        if (not isinstance(attempted, datetime) or attempted.utcoffset() is None or
            not isinstance(finished, datetime) or finished.utcoffset() is None or
            finished < attempted or attempted < frozen_at or finished < observed):
            raise ValueError("REPLAY_CLOCK_REGRESSION")
        batches.append({"symbols": symbols, "attempted_at": iso(attempted),
                        "received_at": iso(finished), "status": status,
                        "pages": pages, "error": reason})
        for symbol in symbols:
            found[symbol] = (("SIP_PROVIDER_REQUEST_FAILED", None) if status != "GET_COMPLETED"
                             else classify_bars(values.get(symbol, []), beginning, cutoff))
    output, counts = [], Counter()
    for original_row in original:
        ticker = original_row["ticker"]
        state, bar = (found[ticker] if ticker in wanted
                      else ("NOT_REQUESTED_SEPARATE_SHADOW_SCOPE", None))
        original_status = original_row.get("indicative_status", original_row.get("screen_status"))
        snapshot = original_row.get("snapshot") or {}
        prior = snapshot.get("prevDailyBar") if isinstance(snapshot, dict) else None
        prior = prior if isinstance(prior, dict) else {}
        ref = prior.get("c") if price_ok(prior.get("c")) else None
        comparison = round(100*(bar["close"]/ref - 1), 5) if bar and ref else None
        counts[state] += 1
        output.append({
            "ticker": ticker, "original_iex_status": original_status,
            "original_capture_received_at": original_row["received_at"],
            "original_universe_included": True,
            "fallback_attempted": ticker in wanted,
            "delayed_sip_status": state, "delayed_sip_bar": bar,
            "previous_iex_daily_reference_only": ref,
            "bar_vs_iex_reference_pct_not_official": comparison,
            "original_iex_unusable": original_status in IEX_UNUSABLE,
            "provider_reported_shortable": original_row["asset"].get("shortable"),
            "actual_smg_borrow_verified": False, "official_close_verified": False,
            "usable_as_historical_prediction": False, "trade_authorized": False,
        })
    return output, {
        "mode": MODE, "policy": POLICY, "source": "ALPACA_CONSOLIDATED_HISTORICAL_1MIN_SIP",
        "source_url": URL, "source_is_full_realtime_sip": False,
        "historical_reconstruction_not_original_point_in_time_capture": True,
        "original_capture_at": original_meta["finished_at"],
        "independent_actual_replay_started_at": iso(observed),
        "eligible_historical_end_at": iso(cutoff),
        "historical_window_start_at": iso(beginning),
        "source_minimum_lag_minutes": 17,
        "original_universe_sha256": source_sha,
        "original_manifest_sha256": meta_sha,
        "original_universe_count": len(original),
        "requested_distinct_symbols": len(wanted),
        "not_requested_symbols_retained": len(original)-len(wanted),
        "status_counts": dict(sorted(counts.items())),
        "requests": batches, "original_statuses_modified": False,
        "future_close_predictions_verified": False,
        "full_market_coverage_verified": False,
        "actual_smg_short_eligibility_verified": False,
        "limitations": [
            "Historical SIP bars retrieved after original decision; no retroactive predictions.",
            "SIP 1Min bars not independently verified official exchange closing prices.",
            "Basic SIP historical access may be blocked; preserve HTTP error as missingness.",
            "Future runs have >=17min historical delay, not real-time consolidated prices.",
            "Halted/illiquid names may still have no recent bar.",
            "Previous IEX daily bar not official previous regular close.",
            "No common stock, capitalization, borrow, SMG platform, corporate action or halt clearance.",
        ],
    }

def persist(rows, meta, destination):
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise FileExistsError("WRITE_ONCE_SIP_REPLAY_EXISTS")
    with TemporaryDirectory(dir=dest.parent, prefix=".sip-replay-") as scratch:
        stage = Path(scratch)
        data = "".join(json.dumps(x, sort_keys=True, allow_nan=False)+"\n" for x in rows).encode()
        complete_meta = {**meta, "rescue_rows_sha256": digest(data)}
        (stage/"rescue.jsonl").write_bytes(data)
        (stage/"manifest.json").write_text(json.dumps(complete_meta, sort_keys=True, indent=2))
        verify(stage)
        if dest.exists():
            raise FileExistsError("WRITE_ONCE_SIP_REPLAY_EXISTS")
        stage.rename(dest)
    return complete_meta

def verify(destination):
    root = Path(destination)
    meta = json.loads((root/"manifest.json").read_text())
    raw = (root/"rescue.jsonl").read_bytes()
    if digest(raw) != meta.get("rescue_rows_sha256") or not raw.endswith(b"\n"):
        raise ValueError("SIP_REPLAY_SHA_MISMATCH")
    rows = [json.loads(x) for x in raw.splitlines()]
    if len(rows) != meta.get("original_universe_count") or len({x["ticker"] for x in rows}) != len(rows):
        raise ValueError("ORIGINAL_UNIVERSE_NOT_PRESERVED")
    if dict(Counter(x["delayed_sip_status"] for x in rows)) != meta.get("status_counts"):
        raise ValueError("SIP_STATUS_COUNTS_MISMATCH")
    attempted = {x["ticker"] for x in rows if x["fallback_attempted"]}
    requested = [x for batch in meta["requests"] for x in batch["symbols"]]
    if (len(attempted) != meta.get("requested_distinct_symbols")
        or len(requested) != len(attempted) or set(requested) != attempted):
        raise ValueError("SIP_REQUEST_DENOMINATOR_MISMATCH")
    if any(x["trade_authorized"] or x["usable_as_historical_prediction"] for x in rows):
        raise ValueError("FAKE_EARLY_PREDICTION_OR_ORDER")
    return {"status": "VERIFIED_HISTORICAL_SIP_COVERAGE_AND_HASH",
            "rows": len(rows), "attempted": len(attempted),
            "statuses": dict(sorted(Counter(x["delayed_sip_status"] for x in rows).items()))}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--symbols", help="Optional comma-separated subset, all other original symbols retained")
    args = p.parse_args()
    wanted = args.symbols.split(",") if args.symbols else None
    rows, meta = replay(args.original, HistoricalSIP(), selected_symbols=wanted)
    persist(rows, meta, args.out)
    report = verify(args.out)
    print(json.dumps({**report, "actual_prior_prediction_verified": False}, sort_keys=True))

if __name__ == "__main__":
    main()
