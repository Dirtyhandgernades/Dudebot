"""Research-only as-of Alpaca universe/snapshot capture; never places orders.

Independent of the historical firm cohort. Retains every returned active NYSE/
NASDAQ US-equity asset in a raw universe ledger, including unclassified names,
missing snapshots and ineligible securities. Price-only A/B *watches* feed the
frozen prospective journal; C reversals need independently observed structure.
No source establishes historical shares, SMG borrow or actual executable fills.
"""
import argparse
import hashlib
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone, time
from pathlib import Path
from zoneinfo import ZoneInfo

CENTRAL = ZoneInfo("America/Chicago")
EASTERN = ZoneInfo("America/New_York")
ASSETS_URL = "https://paper-api.alpaca.markets/v2/assets"
ALTERNATE_ASSETS_URL = "https://api.alpaca.markets/v2/assets"
SNAPSHOTS_URL = "https://data.alpaca.markets/v2/stocks/snapshots"
PROVIDER_SCOPE = "ALPACA_ACTIVE_US_EQUITY_NYSE_NASDAQ_NOT_ALL_SMG_SECURITIES"
BATCH_SIZE = 100


def now_utc():
    return datetime.now(timezone.utc)


def asof(value):
    if not isinstance(value, str):
        return None
    try:
        at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return at if at.utcoffset() is not None else None


def finite_price(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def in_window(at):
    # A naive datetime can silently be interpreted in the runner's local timezone.
    if not isinstance(at, datetime) or at.utcoffset() is None:
        return False
    local = at.astimezone(CENTRAL)
    return local.weekday() < 5 and time(14, 45) <= local.time().replace(tzinfo=None) <= time(14, 58)


class ProviderAuthError(RuntimeError):
    pass


class AlpacaReadOnly:
    """Only GETs public-market metadata and SIP snapshots. No trading endpoints."""
    def __init__(self):
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
            "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
        })

    def get(self, url, params):
        response = self.session.get(url, params=params, timeout=30)
        if response.status_code in (401, 403):
            raise ProviderAuthError("ALPACA_READ_ONLY_AUTH_REJECTED")
        response.raise_for_status()
        return response.json()

    def assets(self):
        params = {"status": "active", "asset_class": "us_equity"}
        try:
            data = self.get(ASSETS_URL, params)
            self.assets_url = ASSETS_URL
            return data
        except ProviderAuthError:
            pass
        data = self.get(ALTERNATE_ASSETS_URL, params)
        self.assets_url = ALTERNATE_ASSETS_URL
        return data

    def snapshots(self, tickers):
        result = self.get(SNAPSHOTS_URL, {"symbols": ",".join(tickers), "feed": "sip"})
        if not isinstance(result, dict) or not isinstance(result.get("snapshots"), dict):
            raise ValueError("INVALID_SIP_SNAPSHOT_RESPONSE")
        return result["snapshots"]


def candidate(asset, snap, at, screen_id, asset_at=None, assets_url=ASSETS_URL):
    """Use only fields in the received as-of snapshot; unknowns remain blocked."""
    ticker = asset["symbol"]
    asset_at = asset_at or at
    # Malformed nested provider fields must censor only this security, not
    # crash the full-universe capture and discard unrelated observations.
    fields = [snap.get(name) for name in ("latestTrade", "prevDailyBar", "minuteBar")]
    if any(value is not None and not isinstance(value, dict) for value in fields):
        return None, "MALFORMED_NESTED_SNAPSHOT"
    trade, prior, minute = (value or {} for value in fields)
    price, previous = trade.get("p"), prior.get("c")
    trade_at, previous_at, minute_at = asof(trade.get("t")), asof(prior.get("t")), asof(minute.get("t"))
    if not finite_price(price) or not finite_price(previous):
        return None, "MISSING_OR_INVALID_PRICE"
    if trade_at is None or trade_at > at or at - trade_at > timedelta(minutes=5):
        return None, "STALE_OR_FUTURE_TRADE"
    if previous_at is None or previous_at.astimezone(EASTERN).date() >= at.astimezone(EASTERN).date():
        return None, "INVALID_PREVIOUS_SESSION"
    # A prior bar can be several sessions old for suspended or illiquid names.
    # Allow ordinary weekends and a one-day market holiday; longer gaps are
    # censored rather than misclassified as a fresh day-over-day decline.
    previous_age_days = (at.astimezone(EASTERN).date() - previous_at.astimezone(EASTERN).date()).days
    if previous_age_days > 4:
        return None, "STALE_PREVIOUS_CLOSE_BAR"
    change = price / previous - 1
    if -.15 <= change <= -.02:
        category = "A"
    elif change <= -.25:
        category = "B"
    else:
        return None, "NO_PRICE_ONLY_A_OR_B_SETUP"
    # Last trade is not proof of executable bid/borrow; bar timestamp is bar start.
    cutoff = at - timedelta(microseconds=1)
    last_complete = minute_at + timedelta(minutes=1) if minute_at else None
    if last_complete is None or last_complete > cutoff:
        last_complete = None
    row = {
        "screen_id": screen_id, "ticker": ticker, "direction": "SHORT",
        "category": category, "session_date": at.astimezone(CENTRAL).date().isoformat(),
        "decision_at": at.isoformat(), "exchange": asset.get("exchange"),
        "security_type": "UNKNOWN", "halted": None,
        "corporate_actions_clear": None, "decision_price": price,
        "previous_close": previous, "shares_outstanding": None,
        "borrow_available": None, "smg_short_available": None,
        "cutoff_at": cutoff.isoformat() if last_complete else None,
        "last_complete_at": last_complete.isoformat() if last_complete else None,
        "screen_verified": True, "screen_url": assets_url,
        "screen_at": asset_at.isoformat(),
        "quote_verified": True, "quote_url": SNAPSHOTS_URL,
        "quote_at": trade_at.isoformat(),
        "previous_close_verified": True, "previous_close_url": SNAPSHOTS_URL,
        "previous_close_at": previous_at.isoformat(),
        "listing_verified": asset.get("exchange") in ("NYSE", "NASDAQ"),
        "listing_url": assets_url, "listing_at": asset_at.isoformat(),
        "shares_verified": False, "corporate_actions_verified": False,
        "borrow_verified": False, "smg_short_verified": False,
        "research_setup": "PRICE_ONLY_WATCH_NOT_CONFIRMED_BREAKDOWN",
        "provider_previous_bar_timestamp_semantics": "BAR_START_NOT_CAPTURE_TIME",
    }
    return row, "PRICE_ONLY_WATCH"


def collect(provider, clock=now_utc, max_requests=150):
    started = clock()
    if started.utcoffset() is None or not in_window(started):
        raise RuntimeError("OUTSIDE_1445_1458_CENTRAL_CAPTURE_WINDOW")
    assets = provider.assets()
    assets_received = clock()
    assets_url = getattr(provider, "assets_url", ASSETS_URL)
    if not isinstance(assets_received, datetime) or assets_received.utcoffset() is None or assets_received < started:
        raise ValueError("INVALID_ASSET_CAPTURE_CLOCK")
    if not in_window(assets_received):
        raise RuntimeError("ASSET_RESPONSE_OUTSIDE_CENTRAL_CAPTURE_WINDOW")
    if not isinstance(assets, list) or not assets:
        raise ValueError("EMPTY_OR_INVALID_ASSET_UNIVERSE")
    selected = []
    seen = set()
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("INVALID_ASSET_RECORD")
        if asset.get("exchange") not in ("NYSE", "NASDAQ") or asset.get("status") != "active":
            continue
        ticker = asset.get("symbol")
        if not isinstance(ticker, str) or not ticker or ticker in seen:
            raise ValueError("DUPLICATE_OR_INVALID_ASSET_SYMBOL")
        seen.add(ticker)
        selected.append(asset)
    if not selected:
        raise ValueError("EMPTY_NYSE_NASDAQ_UNIVERSE")
    selected.sort(key=lambda a: a["symbol"])
    if (len(selected) + BATCH_SIZE - 1) // BATCH_SIZE > max_requests:
        raise RuntimeError("SNAPSHOT_REQUEST_BUDGET_EXCEEDED")
    scan_id = "alpaca-sip-" + started.strftime("%Y%m%dT%H%M%S%fZ")
    universe, watches = [], []
    last_observed_clock = assets_received
    for i in range(0, len(selected), BATCH_SIZE):
        batch = selected[i:i+BATCH_SIZE]
        symbols = [a["symbol"] for a in batch]
        # Reject clock regressions: a later request cannot be recorded as earlier
        # than the asset response or the preceding batch's response.
        request_at = clock()
        if not isinstance(request_at, datetime) or request_at.utcoffset() is None or request_at < last_observed_clock:
            raise ValueError("NONMONOTONIC_SNAPSHOT_REQUEST_CLOCK")
        # A scan begun in the window is not permission to query after it closes.
        if not in_window(request_at):
            raise RuntimeError("SNAPSHOT_REQUEST_OUTSIDE_CENTRAL_CAPTURE_WINDOW")
        snaps = provider.snapshots(symbols)
        if set(snaps) - set(symbols):
            raise ValueError("UNREQUESTED_SNAPSHOT_SYMBOL")
        received = clock()
        if not isinstance(received, datetime) or received.utcoffset() is None or received < request_at:
            raise ValueError("NONMONOTONIC_SNAPSHOT_RESPONSE_CLOCK")
        if not in_window(received):
            raise RuntimeError("SNAPSHOT_RESPONSE_OUTSIDE_CENTRAL_CAPTURE_WINDOW")
        last_observed_clock = received
        for asset in batch:
            ticker = asset["symbol"]
            snap = snaps.get(ticker)
            status = "MISSING_SNAPSHOT" if not isinstance(snap, dict) else "UNCLASSIFIED"
            row = None
            if not re.fullmatch(r"[A-Z]{1,5}", ticker):
                status = "UNSUPPORTED_JOURNAL_TICKER_FORMAT"
            elif isinstance(snap, dict):
                row, status = candidate(asset, snap, received, scan_id, assets_received, assets_url)
            universe.append({"ticker": ticker, "asset": asset, "snapshot": snap,
                             "received_at": received.isoformat(), "screen_status": status})
            if row is not None:
                watches.append(row)
    finished = clock()
    if not isinstance(finished, datetime) or finished.utcoffset() is None or finished < last_observed_clock:
        raise ValueError("NONMONOTONIC_FINISH_CLOCK")
    if not in_window(finished):
        raise RuntimeError("CAPTURE_FINISHED_OUTSIDE_CENTRAL_WINDOW")
    counts = {}
    for row in universe:
        status = row["screen_status"]
        counts[status] = counts.get(status, 0) + 1
    return universe, watches, {
        "status": "AS_OF_PROVIDER_UNIVERSE_CAPTURE_NOT_FULL_MARKET_PROOF",
        "research_only": True, "trade_authorized": False,
        "screen_id": scan_id, "provider_scope": PROVIDER_SCOPE,
        "source_assets": assets_url, "source_snapshots": SNAPSHOTS_URL,
        "capture_started_at": started.isoformat(),
        "assets_received_at": assets_received.isoformat(),
        "capture_finished_at": finished.isoformat(),
        "asset_universe_count": len(selected), "asset_api_total_count": len(assets),
        "screened_count": len(universe), "watch_count": len(watches),
        "status_counts": counts, "snapshot_missing_count": counts.get("MISSING_SNAPSHOT", 0),
        "not_verified": ["common_stock_type", "shares_outstanding", "market_cap", "corporate_actions", "halts", "smg_borrow", "smg_order_acceptance", "executable_bid", "next_session_outcomes"],
        "limitations": ["Asset API coverage is not proof of the complete SMG-eligible universe.",
                        "A/B classification is price-only watch; C requires separately verified structure.",
                        "Provider previous-bar timestamp denotes bar start, not collection time.",
                        "Missing snapshots and unsupported ticker formats remain in the denominator."],
    }


def persist(universe, watches, report, destination):
    """Atomically publish a complete write-once capture, never partial evidence."""
    from tempfile import TemporaryDirectory
    from backtest.obsidian_prospective_journal import write_journal

    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise FileExistsError(f"CAPTURE_DESTINATION_ALREADY_EXISTS: {dest}")

    # Build and validate everything in a sibling temporary directory. An
    # invalid candidate, malformed provider payload or disk error must never
    # leave a partially uploaded universe that resembles a completed capture.
    with TemporaryDirectory(prefix=f".{dest.name}.partial-", dir=dest.parent) as temporary:
        staged = Path(temporary)
        manifest = dict(report)

        def write_lines(name, rows):
            data = "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows)
            with (staged / name).open("x", encoding="utf-8") as f:
                f.write(data)
            return hashlib.sha256(data.encode()).hexdigest()

        manifest["universe_sha256"] = write_lines("universe.jsonl", universe)
        manifest["candidate_sha256"] = write_lines("candidates.jsonl", watches)
        if watches:
            manifest["journal_summary"] = write_journal(
                staged / "candidates.jsonl", staged / "journal.jsonl"
            )
        else:
            manifest["journal_summary"] = {
                "preserved": 0, "blocked": 0, "reason": "NO_CANDIDATES"
            }
        with (staged / "manifest.json").open("x", encoding="utf-8") as f:
            json.dump(manifest, f, sort_keys=True, indent=2, allow_nan=False)
        if dest.exists():
            raise FileExistsError(f"CAPTURE_DESTINATION_ALREADY_EXISTS: {dest}")
        staged.rename(dest)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True)
    p.add_argument("--max-requests", type=int, default=150)
    args = p.parse_args()
    if args.max_requests < 1:
        p.error("max requests must be positive")
    if not in_window(now_utc()):
        print(json.dumps({"status": "NO_CAPTURE_OUTSIDE_CENTRAL_WINDOW", "research_only": True}))
        return
    provider = AlpacaReadOnly()
    report = persist(*collect(provider, max_requests=args.max_requests), destination=args.out)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
