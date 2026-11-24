"""Retrospective fixed-ledger short squeeze screen, research only.
H01: exclude pre-decision observed gains >= 5% from prior close.
No reallocation, no retuning, no portfolio replay or fresh holdout.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import zipfile
from datetime import datetime
from pathlib import Path

ARCHIVES = {
    "signals": "a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e",
    "hosted": "95f916cdc1d988f752a49f14c38852c1f9876c5ddfd535bb915c19f840ea1ba1",
}
YEARS = (2023, 2024, 2025)
THRESHOLD = .05

def open_verified(path, digest):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
        raise ValueError("archive digest mismatch")
    z = zipfile.ZipFile(path)
    if len(z.namelist()) != len(set(z.namelist())) or z.testzip() is not None:
        raise ValueError("invalid archive")
    return z

def classify(event, prior_close):
    if event is None:
        return "UNKNOWN", None, "MISSING_SIGNAL"
    try:
        decision = datetime.fromisoformat(event["decision_at"])
        observed = datetime.fromisoformat(event["last_complete_at"])
        cutoff = datetime.fromisoformat(event["data_cutoff"])
        price = float(event["decision_price"])
        prior = float(prior_close)
        if not (math.isfinite(price) and math.isfinite(prior) and price > 0 and prior > 0):
            return "UNKNOWN", None, "INVALID_PRICE"
        change = price / prior - 1
        explicit = event.get("observed_change_from_prior_close")
        if explicit is not None and not math.isclose(float(explicit), change, abs_tol=.0001):
            return "UNKNOWN", None, "CHANGE_CONFLICT"
        if not (observed <= cutoff <= decision and math.isfinite(change)):
            return "UNKNOWN", None, "TIME_OR_PRICE_INVALID"
    except (KeyError, ValueError, TypeError):
        return "UNKNOWN", None, "MISSING_OR_INVALID_PRIOR"
    return ("EXCLUDE_STRENGTH" if change >= THRESHOLD else "KEEP", change,
            "EXPLICIT_MATCH" if explicit is not None else "DERIVED_PRIOR_RAW_CLOSE")

def metrics(rows):
    p = [float(r["pnl"]) for r in rows]
    n = sum(float(r["notional"]) for r in rows)
    return {"trades": len(rows), "trade_pnl": round(sum(p), 2),
            "notional": round(n, 2),
            "pnl_per_notional_pct": round(100 * sum(p) / n, 3) if n else None,
            "wins": sum(v > 0 for v in p),
            "losses": sum(v < 0 for v in p),
            "largest_loss": round(min([0.] + p), 2)}

def run(signals, hosted):
    result = {"status": "RETROSPECTIVE_FIXED_LEDGER_NOT_PROMOTABLE",
              "threshold": THRESHOLD, "archives": ARCHIVES, "seasons": [], "rows": []}
    with open_verified(signals, ARCHIVES["signals"]) as s, open_verified(hosted, ARCHIVES["hosted"]) as h:
        packet = json.loads(gzip.decompress(s.read("firm-timing-inputs.json.gz")))
        sessions = packet["sessions"]
        prior = dict(zip(sessions[1:], sessions[:-1]))
        for year in YEARS:
            events = json.loads(s.read(f"{year}-hybrid-signals.json"))
            by_key = {}
            for day, group in events.items():
                for event in group:
                    key = (day, event["ticker"])
                    if key in by_key:
                        raise ValueError(f"duplicate signal {key}")
                    by_key[key] = event
            for case in ("base", "stress"):
                member = f"backtest/target-rank-2026-10-05/{year}-top_half_30pct-50000-{case}-trades.csv"
                rows = list(csv.DictReader(io.StringIO(h.read(member).decode())))
                groups = {"KEEP": [], "EXCLUDE_STRENGTH": [], "UNKNOWN": []}
                for row in rows:
                    event = by_key.get((row["signal_date"], row["ticker"]))
                    day = row["signal_date"]
                    prev = prior.get(day)
                    if prev and (datetime.fromisoformat(day) - datetime.fromisoformat(prev)).days > 4:
                        prev = None
                    prior_close = packet["raw"].get(row["ticker"], {}).get(prev, {}).get("c")
                    status, change, provenance = classify(event, prior_close)
                    groups[status].append(row)
                    result["rows"].append({"year": year, "case": case, "status": status,
                        "ticker": row["ticker"], "signal_date": row["signal_date"],
                        "change": change, "provenance": provenance, "prior_date": prev,
                        "pnl": float(row["pnl"]), "notional": float(row["notional"])})
                result["seasons"].append({"year": year, "case": case, "baseline": metrics(rows),
                                          **{k: metrics(v) for k,v in groups.items()}})
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--signals", required=True)
    p.add_argument("--hosted", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    Path(a.out).write_text(json.dumps(run(a.signals, a.hosted), indent=2) + "\n")
