"""Immutable, fail-closed 2026+ OBSIDIAN research journal; NO orders/alerts.

Requires independent as-of evidence supplied by an external scanner. This
module neither discovers securities nor establishes executable SMG fills.
Every screened candidate, including rejected/unknown ones, is preserved.
"""
import argparse
import json
import math
import re
from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo

POLICY_ID = "OBSIDIAN_PROSPECTIVE_V1_FROZEN_20261026"
CENTRAL = ZoneInfo("America/Chicago")
FROZEN_EARLY_THRESHOLD = -0.02  # Diagnostic only; never tuned on 2023-25.


def timestamp(value, field):
    if not isinstance(value, str):
        raise ValueError(f"INVALID_{field.upper()}")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"INVALID_{field.upper()}") from exc
    if result.utcoffset() is None:
        raise ValueError(f"NAIVE_{field.upper()}")
    return result


def positive(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def audit(row):
    if not isinstance(row, dict) or not re.fullmatch(r"[A-Z]{1,5}", str(row.get("ticker", ""))):
        raise ValueError("INVALID_CANDIDATE_OR_TICKER")
    if row.get("direction") not in ("SHORT", "LONG") or row.get("category") not in ("A", "B", "C"):
        raise ValueError("INVALID_DIRECTION_OR_CATEGORY")
    if not isinstance(row.get("screen_id"), str) or not row["screen_id"]:
        raise ValueError("MISSING_SCREEN_ID")
    decision = timestamp(row.get("decision_at"), "decision_at")
    local = decision.astimezone(CENTRAL)
    if local.year < 2026 or row.get("session_date") != local.date().isoformat():
        raise ValueError("INVALID_PROSPECTIVE_CENTRAL_SESSION")
    blockers = []
    if not time(14, 45) <= local.time().replace(tzinfo=None) <= time(14, 58):
        blockers.append("OUTSIDE_CENTRAL_EXECUTION_WINDOW")
    evidence = ["screen", "quote", "previous_close", "shares", "listing", "corporate_actions"]
    evidence += ["borrow", "smg_short"] if row["direction"] == "SHORT" else ["smg_long"]
    for name in evidence:
        when, url = row.get(name + "_at"), row.get(name + "_url")
        if row.get(name + "_verified") is not True or not isinstance(url, str) or not url.startswith("https://") or when is None:
            blockers.append("UNVERIFIED_" + name.upper())
            continue
        at = timestamp(when, name + "_at")
        if at > decision:
            raise ValueError("FUTURE_" + name.upper() + "_EVIDENCE")
        if name in ("quote", "borrow", "smg_short", "smg_long") and decision - at > timedelta(minutes=5):
            blockers.append("STALE_" + name.upper() + "_EVIDENCE")
        if name == "previous_close" and at.astimezone(CENTRAL).date() >= local.date():
            raise ValueError("PREVIOUS_CLOSE_NOT_PREVIOUS_SESSION")
    if row.get("exchange") not in ("NASDAQ", "NYSE") or row.get("security_type") != "COMMON_STOCK":
        blockers.append("NOT_VERIFIED_US_LISTED_COMMON_STOCK")
    if row.get("halted") is not False or row.get("corporate_actions_clear") is not True:
        blockers.append("HALT_OR_CORPORATE_ACTIONS_UNRESOLVED")
    price, previous, shares = row.get("decision_price"), row.get("previous_close"), row.get("shares_outstanding")
    if not positive(price) or price < 3 or not positive(previous) or previous < 3:
        blockers.append("PRICE_GATE_UNKNOWN_OR_BELOW_3")
    cap = round(price * shares, 2) if positive(price) and positive(shares) else None
    if cap is None or cap < 25_000_000:
        blockers.append("MARKET_CAP_UNKNOWN_OR_BELOW_25M")
    if row["direction"] == "SHORT" and (row.get("borrow_available") is not True or row.get("smg_short_available") is not True):
        blockers.append("BORROW_OR_SMG_SHORT_UNKNOWN")
    if row["direction"] == "LONG" and row.get("smg_long_available") is not True:
        blockers.append("SMG_LONG_UNKNOWN")
    if row.get("cutoff_at") is None or row.get("last_complete_at") is None:
        blockers.append("MISSING_DATA_CUTOFF")
    else:
        cutoff, observed = timestamp(row["cutoff_at"], "cutoff_at"), timestamp(row["last_complete_at"], "last_complete_at")
        if not observed <= cutoff < decision:
            raise ValueError("FUTURE_OR_INVALID_CUTOFF")
    change = price / previous - 1 if positive(price) and positive(previous) else None
    return {
        "policy_id": POLICY_ID, "research_only": True, "trade_authorized": False,
        "decision_at_central": local.isoformat(), "market_cap_proxy": cap,
        "prior_close_change": change, "blockers": sorted(set(blockers)),
        "status": "RESEARCH_ELIGIBLE_NOT_EXECUTABLE" if not blockers else "BLOCKED",
        "frozen_minus_2pct_short_diagnostic": bool(not blockers and row["direction"] == "SHORT" and change is not None and change <= FROZEN_EARLY_THRESHOLD),
    }


def write_journal(source, destination):
    """All-or-nothing validation; destination must not exist (write-once)."""
    rows, keys = [], set()
    for line_no, line in enumerate(Path(source).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        result = audit(raw)
        key = (raw["screen_id"], raw["ticker"], raw["direction"], raw["decision_at"])
        if key in keys:
            raise ValueError(f"DUPLICATE_SCREEN_ROW_{line_no}")
        keys.add(key)
        rows.append({"as_screened": raw, "audit": result})
    if not rows:
        raise ValueError("EMPTY_SCREEN")
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    return {"policy_id": POLICY_ID, "preserved": len(rows), "blocked": sum(r["audit"]["status"] == "BLOCKED" for r in rows)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, help="JSONL from independent as-of scanner")
    p.add_argument("--output", required=True, help="new write-once JSONL journal")
    args = p.parse_args()
    print(json.dumps(write_journal(args.input, args.output), sort_keys=True))
