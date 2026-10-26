"""Verify an immutable OBSIDIAN prospective capture without provider calls.

Research-only, offline, fail-closed: verifies manifest hashes, full-universe
denominators, candidate provenance, frozen journal and as-of chronology.
A successful verification NEVER establishes SMG eligibility or tradability.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from backtest.obsidian_prospective_capture import asof, candidate, in_window, PROVIDER_SCOPE
from backtest.obsidian_prospective_journal import audit


class InvalidCapture(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidCapture(message)


def jsonl(path):
    require(path.is_file(), "MISSING_" + path.name.upper())
    data = path.read_bytes()
    require(not data or data.endswith(b"\n"), "TRUNCATED_" + path.name.upper())
    try:
        rows = [json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))
                for line in data.decode("utf-8").splitlines()]
    except (ValueError, UnicodeDecodeError) as exc:
        raise InvalidCapture("INVALID_JSONL_" + path.name.upper()) from exc
    require(all(isinstance(row, dict) for row in rows), "INVALID_JSONL_RECORD")
    return data, rows


def verify_capture(directory):
    root = Path(directory)
    require(root.is_dir(), "MISSING_CAPTURE_DIRECTORY")
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InvalidCapture("INVALID_MANIFEST") from exc
    require(isinstance(manifest, dict), "INVALID_MANIFEST_TYPE")
    require(manifest.get("research_only") is True and manifest.get("trade_authorized") is False,
            "NOT_RESEARCH_ONLY")
    require(manifest.get("provider_scope") == PROVIDER_SCOPE, "PROVIDER_SCOPE_CHANGED")
    require(manifest.get("status") == "AS_OF_PROVIDER_UNIVERSE_CAPTURE_NOT_FULL_MARKET_PROOF",
            "UNEXPECTED_CAPTURE_STATUS")
    started = asof(manifest.get("capture_started_at"))
    assets_at = asof(manifest.get("assets_received_at"))
    finished = asof(manifest.get("capture_finished_at"))
    require(started is not None and assets_at is not None and finished is not None
            and started <= assets_at <= finished
            and in_window(started) and in_window(assets_at) and in_window(finished),
            "INVALID_CAPTURE_CHRONOLOGY")
    universe_data, universe = jsonl(root / "universe.jsonl")
    candidate_data, candidates = jsonl(root / "candidates.jsonl")
    require(hashlib.sha256(universe_data).hexdigest() == manifest.get("universe_sha256"),
            "UNIVERSE_HASH_MISMATCH")
    require(hashlib.sha256(candidate_data).hexdigest() == manifest.get("candidate_sha256"),
            "CANDIDATE_HASH_MISMATCH")
    require(len(universe) == manifest.get("screened_count") == manifest.get("asset_universe_count")
            and len(universe) > 0, "UNIVERSE_COUNT_MISMATCH")
    require(len(candidates) == manifest.get("watch_count"), "CANDIDATE_COUNT_MISMATCH")
    symbols = [row.get("ticker") for row in universe]
    require(all(isinstance(s, str) for s in symbols)
            and symbols == sorted(set(symbols)), "INVALID_UNIVERSE_SYMBOLS")
    counts = Counter()
    watch_universe = {}
    last_received = assets_at
    for row in universe:
        symbol, asset = row["ticker"], row.get("asset")
        require(isinstance(asset, dict) and asset.get("symbol") == symbol
                and asset.get("exchange") in ("NYSE", "NASDAQ")
                and asset.get("status") == "active", "INVALID_ASSET_PROVENANCE")
        received = asof(row.get("received_at"))
        require(received is not None and last_received <= received <= finished
                and in_window(received), "INVALID_UNIVERSE_CHRONOLOGY")
        last_received = received
        status = row.get("screen_status")
        require(isinstance(status, str) and bool(status), "INVALID_SCREEN_STATUS")
        counts[status] += 1
        if status == "PRICE_ONLY_WATCH":
            watch_universe[symbol] = row
    require(dict(counts) == manifest.get("status_counts"), "STATUS_COUNTS_MISMATCH")
    require(counts["MISSING_SNAPSHOT"] == manifest.get("snapshot_missing_count"),
            "MISSING_SNAPSHOT_COUNT_MISMATCH")
    require(len(watch_universe) == len(candidates), "UNMATCHED_WATCH_UNIVERSE")
    # Recompute the price-only classifier from every retained raw provider row.
    # Hashes and matching prices alone do not prove that the screening status,
    # A/B category, timestamps or blocked candidate metadata were preserved.
    expected_watches = {}
    for source in universe:
        symbol = source["ticker"]
        snap = source.get("snapshot")
        present = source.get("snapshot_present")
        require(type(present) is bool, "INVALID_SNAPSHOT_PRESENCE")
        require(present or snap is None, "ABSENT_SNAPSHOT_HAS_PAYLOAD")
        received = asof(source["received_at"])
        if not re.fullmatch(r"[A-Z]{1,5}", symbol):
            expected_row, expected_status = None, "UNSUPPORTED_JOURNAL_TICKER_FORMAT"
        elif not present:
            expected_row, expected_status = None, "MISSING_SNAPSHOT"
        elif not isinstance(snap, dict):
            expected_row, expected_status = None, "MALFORMED_SNAPSHOT"
        else:
            expected_row, expected_status = candidate(
                source["asset"], snap, received, manifest["screen_id"],
                assets_at, manifest.get("source_assets")
            )
        require(source["screen_status"] == expected_status,
                "SCREEN_STATUS_NOT_REPRODUCIBLE")
        if expected_row is not None:
            expected_watches[symbol] = expected_row
    require(set(expected_watches) == set(watch_universe),
            "WATCH_SET_NOT_REPRODUCIBLE")
    seen = set()
    for row in candidates:
        symbol = row.get("ticker")
        require(symbol in watch_universe and symbol not in seen,
                "CANDIDATE_NOT_IN_PRICE_ONLY_UNIVERSE")
        seen.add(symbol)
        original = watch_universe[symbol]
        require(row == expected_watches[symbol], "CANDIDATE_REPLAY_MISMATCH")
        require(row.get("screen_id") == manifest.get("screen_id")
                and row.get("decision_at") == original["received_at"]
                and row.get("screen_at") == manifest["assets_received_at"]
                and row.get("decision_price") == original["snapshot"]["latestTrade"]["p"]
                and row.get("previous_close") == original["snapshot"]["prevDailyBar"]["c"],
                "CANDIDATE_PROVENANCE_MISMATCH")
        try:
            decision = audit(row)
        except (ValueError, TypeError, KeyError) as exc:
            raise InvalidCapture("INVALID_FROZEN_CANDIDATE") from exc
        require(decision["status"] == "BLOCKED"
                and decision["trade_authorized"] is False, "UNEXPECTED_ACTIONABLE_CANDIDATE")
    journal_path = root / "journal.jsonl"
    if candidates:
        _, journal = jsonl(journal_path)
        require(len(journal) == len(candidates), "JOURNAL_COUNT_MISMATCH")
        for recorded, candidate_row in zip(journal, candidates):
            require(recorded.get("as_screened") == candidate_row
                    and recorded.get("audit") == audit(candidate_row),
                    "FROZEN_JOURNAL_MISMATCH")
        require(manifest.get("journal_summary", {}).get("preserved") == len(candidates)
                and manifest["journal_summary"].get("blocked") == len(candidates),
                "JOURNAL_SUMMARY_MISMATCH")
    else:
        require(not journal_path.exists(), "UNEXPECTED_EMPTY_JOURNAL")
        require(manifest.get("journal_summary", {}).get("reason") == "NO_CANDIDATES",
                "INVALID_EMPTY_JOURNAL_SUMMARY")
    return {"status": "VERIFIED_RESEARCH_CAPTURE_NOT_EXECUTABLE",
            "research_only": True, "trade_authorized": False,
            "screen_id": manifest["screen_id"],
            "universe_count": len(universe), "watch_count": len(candidates),
            "blocked_count": len(candidates), "missing_snapshot_count": counts["MISSING_SNAPSHOT"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True)
    args = parser.parse_args()
    print(json.dumps(verify_capture(args.capture), sort_keys=True))
