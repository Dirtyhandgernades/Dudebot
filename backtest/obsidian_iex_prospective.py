"""Independent, read-only IEX prospective discovery capture.

NOT the frozen SIP baseline. IEX is a single-venue feed and cannot establish
consolidated prices, complete market coverage, or SMG eligibility.
Capture only inside the Chicago preclose window; no retrospective backfill.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from backtest.obsidian_prospective_capture import (
    ASSETS_URL, BATCH_SIZE, CENTRAL, EASTERN, asof, in_window, now_utc
)

IEX_SNAPSHOTS = "https://data.alpaca.markets/v2/stocks/snapshots"
IEX_SCOPE = "ALPACA_ACTIVE_NYSE_NASDAQ_ASSETS_IEX_SINGLE_VENUE_NOT_CONSOLIDATED"
MAX_TRADE_AGE = timedelta(minutes=15)


def _canonical(rows):
    return "".join(json.dumps(x, sort_keys=True, allow_nan=False) + "\n" for x in rows).encode()


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _clock(t):
    if not isinstance(t, datetime) or t.utcoffset() is None or not in_window(t):
        raise ValueError("CAPTURE_CLOCK_OUTSIDE_PRE_CLOSE")
    return t


class IEXReadOnly:
    def __init__(self):
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
            "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
        })

    def _get(self, url, params):
        response = self.session.get(url, params=params, timeout=20)
        if response.status_code in (401, 403):
            raise RuntimeError("RESEARCH_IEX_AUTH_OR_ENTITLEMENT_BLOCKED")
        response.raise_for_status()
        return response.json()

    def assets(self):
        return self._get(ASSETS_URL, {"status": "active", "asset_class": "us_equity"})

    def snapshots(self, symbols):
        response = self._get(IEX_SNAPSHOTS, {"symbols": ",".join(symbols), "feed": "iex"})
        if not isinstance(response, dict) or not isinstance(response.get("snapshots"), dict):
            raise ValueError("INVALID_IEX_RESPONSE")
        return response["snapshots"]


def classify(snap, received):
    if snap is None:
        return "MISSING_SNAPSHOT"
    if not isinstance(snap, dict):
        return "MALFORMED_SNAPSHOT"
    trade, previous = snap.get("latestTrade"), snap.get("prevDailyBar")
    if not isinstance(trade, dict) or not isinstance(previous, dict):
        return "MISSING_TRADE_OR_PREVIOUS_BAR"
    price, prior = trade.get("p"), previous.get("c")
    at, previous_at = asof(trade.get("t")), asof(previous.get("t"))
    if (type(price) not in (int, float) or type(prior) not in (int, float)
            or not 0 < price < float("inf") or not 0 < prior < float("inf")):
        return "INVALID_PRICE"
    if at is None or at > received or received - at > MAX_TRADE_AGE:
        return "STALE_OR_FUTURE_IEX_TRADE"
    if previous_at is None or previous_at >= received:
        return "INVALID_PREVIOUS_BAR"
    # A prior IEX bar is single-venue, never an official close.
    session_day = received.astimezone(EASTERN).date()
    expected_prior = session_day - timedelta(days=1)
    while expected_prior.weekday() >= 5:
        expected_prior -= timedelta(days=1)
    if previous_at.astimezone(EASTERN).date() != expected_prior:
        return "UNVERIFIED_PREVIOUS_IEX_SESSION"
    # Prior bar may be IEX-only. Its date is NOT proof of official previous close.
    change = price / prior - 1
    if change <= -.25:
        return "IEX_EXHAUSTED_PRICE_ONLY"
    if -.15 <= change <= -.02:
        return "IEX_EARLY_WEAKNESS_WATCH_ONLY"
    return "IEX_NO_EARLY_PRICE_ONLY_WATCH"


def collect(provider, clock=now_utc, max_requests=150):
    started = _clock(clock())
    assets = provider.assets()
    asset_at = _clock(clock())
    if not isinstance(assets, list) or not assets:
        raise ValueError("INVALID_OR_EMPTY_ASSET_UNIVERSE")
    selected = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("INVALID_ASSET")
        if asset.get("exchange") not in ("NASDAQ", "NYSE") or asset.get("status") != "active":
            continue
        symbol = asset.get("symbol")
        if not isinstance(symbol, str) or not symbol or symbol in selected:
            raise ValueError("DUPLICATE_OR_INVALID_SYMBOL")
        selected[symbol] = asset
    if not selected:
        raise ValueError("NO_SELECTED_ASSETS")
    if (len(selected) + BATCH_SIZE - 1) // BATCH_SIZE > max_requests:
        raise ValueError("REQUEST_BUDGET_EXCEEDED")
    rows = []
    last = asset_at
    for offset in range(0, len(selected), BATCH_SIZE):
        symbols = sorted(selected)[offset:offset + BATCH_SIZE]
        requested = _clock(clock())
        if requested < last:
            raise ValueError("CLOCK_REGRESSION")
        snaps = provider.snapshots(symbols)
        received = _clock(clock())
        if received < requested:
            raise ValueError("CLOCK_REGRESSION")
        if not isinstance(snaps, dict) or set(snaps) - set(symbols):
            raise ValueError("INVALID_SNAPSHOT_SYMBOLS")
        last = received
        for symbol in symbols:
            snap = snaps.get(symbol)
            rows.append({"ticker": symbol, "asset": selected[symbol],
                         "snapshot_present": symbol in snaps, "snapshot": snap,
                         "received_at": received.isoformat(),
                         "screen_status": classify(snap, received)})
    finished = _clock(clock())
    if finished < last:
        raise ValueError("CLOCK_REGRESSION")
    counts = {}
    for row in rows:
        key = row["screen_status"]
        counts[key] = counts.get(key, 0) + 1
    manifest = {
        "status": "IEX_PROSPECTIVE_SINGLE_VENUE_RAW_DISCOVERY_ONLY",
        "research_only": True, "trade_authorized": False,
        "feed": "iex", "provider_scope": IEX_SCOPE,
        "source_assets": ASSETS_URL, "source_snapshots": IEX_SNAPSHOTS,
        "started_at": started.isoformat(), "assets_received_at": asset_at.isoformat(),
        "finished_at": finished.isoformat(),
        "universe_count": len(rows), "asset_api_count": len(assets),
        "status_counts": counts,
        "limitations": ["IEX is a single venue, not SIP or an official consolidated close.",
                        "IEX previous daily bar is not a verified official previous close.",
                        "All candidates are WATCH_ONLY; no frozen baseline or SMG eligibility is inferred.",
                        "No historical Oct26 capture is reconstructed."],
    }
    return rows, manifest


def verify(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    data = (root / "universe.jsonl").read_bytes()
    if _hash(data) != manifest.get("universe_sha256") or not data.endswith(b"\n"):
        raise ValueError("HASH_OR_TRUNCATION")
    rows = [json.loads(x) for x in data.decode().splitlines()]
    if not rows or len(rows) != manifest.get("universe_count"):
        raise ValueError("UNIVERSE_COUNT")
    if manifest.get("feed") != "iex" or manifest.get("provider_scope") != IEX_SCOPE or manifest.get("trade_authorized") is not False:
        raise ValueError("NOT_IEX_RESEARCH")
    started = asof(manifest.get("started_at"))
    assets_at = asof(manifest.get("assets_received_at"))
    finished = asof(manifest.get("finished_at"))
    if any(t is None or not in_window(t) for t in (started, assets_at, finished)) or not started <= assets_at <= finished:
        raise ValueError("INVALID_CAPTURE_CLOCK")
    counts = {}
    previous = assets_at
    symbols = []
    for row in rows:
        symbol = row.get("ticker")
        symbols.append(symbol)
        asset = row.get("asset")
        if not isinstance(asset, dict) or asset.get("symbol") != symbol or asset.get("exchange") not in ("NASDAQ", "NYSE") or asset.get("status") != "active":
            raise ValueError("ASSET_MISMATCH")
        received = asof(row.get("received_at"))
        if received is None or not previous <= received <= finished or not in_window(received):
            raise ValueError("INVALID_ROW_CLOCK")
        previous = received
        if type(row.get("snapshot_present")) is not bool or (not row["snapshot_present"] and row.get("snapshot") is not None):
            raise ValueError("INVALID_SNAPSHOT_PRESENCE")
        expected = classify(row.get("snapshot"), received) if row["snapshot_present"] else "MISSING_SNAPSHOT"
        if expected != row.get("screen_status"):
            raise ValueError("STATUS_REPLAY_MISMATCH")
        counts[expected] = counts.get(expected, 0) + 1
    if symbols != sorted(set(symbols)) or counts != manifest.get("status_counts"):
        raise ValueError("UNIVERSE_OR_STATUS_COUNTS")
    return {"status": "VERIFIED_IEX_SINGLE_VENUE_RESEARCH_CAPTURE",
            "universe_count": len(rows), "watch_count": counts.get("IEX_EARLY_WEAKNESS_WATCH_ONLY", 0),
            "trade_authorized": False}


def persist(rows, manifest, destination):
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("WRITE_ONCE_CAPTURE_ALREADY_EXISTS")
    with TemporaryDirectory(prefix=".iex-stage-", dir=target.parent) as temporary:
        stage = Path(temporary)
        data = _canonical(rows)
        (stage / "universe.jsonl").write_bytes(data)
        full = {**manifest, "universe_sha256": _hash(data)}
        (stage / "manifest.json").write_text(json.dumps(full, indent=2, sort_keys=True))
        verify(stage)
        if target.exists():
            raise FileExistsError("WRITE_ONCE_CAPTURE_ALREADY_EXISTS")
        stage.rename(target)
    return full


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not in_window(now_utc()):
        print(json.dumps({"status": "NO_CAPTURE_OUTSIDE_WINDOW", "research_only": True}))
        return
    manifest = persist(*collect(IEXReadOnly()), args.out)
    print(json.dumps({"status": manifest["status"], "universe_count": manifest["universe_count"],
                      "status_counts": manifest["status_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
