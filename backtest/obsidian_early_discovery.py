"""OBSIDIAN retrospective coverage + prospective early discovery safeguards.

RESEARCH_ONLY_NOT_AN_ORDER. Pure functions; no HTTP calls, credentials, live
alerts, modifications of frozen policies, order entry, or best-future-close data.
No observed retrospective winner is a model-training example.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from math import isfinite
from zoneinfo import ZoneInfo

OUTPUT_MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
SOURCE_KINDS = {
    "CHAT_REFERENCE", "DATED_AUDIT", "PUBLIC_LEADERBOARD",
    "AUTHENTICATED_SCANNER", "WRITE_ONCE_CANDIDATE_JOURNAL",
}
TIMING_SIGNALS = ("failed_rebound", "support_loss", "selling_volume")
NEGATIVE_MECHANISMS = {"ADVERSE_ISSUER_RELEASE", "ADVERSE_SEC_FILING",
                       "VERIFIED_ACTUAL_SALEABLE_SUPPLY", "PUBLIC_MACRO_SHOCK"}


def parse_stamp(value):
    if isinstance(value, datetime):
        d = value
    elif isinstance(value, str):
        try:
            d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return d if d.utcoffset() is not None else None


def _evidence(proof, at, *, max_age=None, verified=True):
    if not isinstance(proof, dict) or (verified and proof.get("verified") is not True):
        return False
    stamp = parse_stamp(proof.get("observed_at"))
    published = parse_stamp(proof.get("published_at")) if "published_at" in proof else None
    source = proof.get("source_id")
    if not stamp or not at or stamp > at or not isinstance(source, str) or not source.strip():
        return False
    if "published_at" in proof and (not published or published > at):
        return False
    return max_age is None or at - stamp <= max_age


def reconcile_coverage(master, supplemental, observations, *,
                       decision_cutoff=None, scan_inventory=None):
    """Preserve historical membership and observed-vs-screened provenance.

    Scan absence is UNKNOWN unless a complete, authenticated, timestamped
    ticker-universe ledger explicitly establishes the symbol was considered.
    Neither retrospective chats nor third-party movers prove an EOD board.
    """
    cutoff = parse_stamp(decision_cutoff) if decision_cutoff is not None else None
    if decision_cutoff is not None and cutoff is None:
        raise ValueError("CUTOFF_MUST_BE_TIMEZONE_AWARE")
    retained = {}
    for label, rows in (("MASTER", master), ("SUPPLEMENTAL", supplemental)):
        for row in rows:
            symbol = row.get("ticker")
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("INVALID_RETAINED_SYMBOL")
            symbol = symbol.strip().upper()
            retained.setdefault(symbol, set()).add(label)
    events = defaultdict(list)
    for entry in observations:
        symbol = entry.get("ticker")
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("INVALID_OBSERVATION_SYMBOL")
        symbol = symbol.strip().upper()
        kind = entry.get("kind")
        if kind not in SOURCE_KINDS or not entry.get("source_ref"):
            raise ValueError("OBSERVATION_PROVENANCE_REQUIRED")
        recorded = parse_stamp(entry.get("observed_at"))
        # A date-only report or chat reference does NOT have a verified first
        # sighting time; an audit's publication hour is not a quote timestamp.
        if entry.get("observed_at") is not None and recorded is None:
            raise ValueError("INVALID_OBSERVATION_TIMESTAMP")
        screen = kind in {"AUTHENTICATED_SCANNER", "WRITE_ONCE_CANDIDATE_JOURNAL"}
        if screen and (not recorded or not entry.get("scan_id")
                       or entry.get("authenticated") is not True):
            raise ValueError("AUTHENTICATED_SCREEN_REQUIRES_ID_AND_ASOF")
        events[symbol].append({
            "kind": kind, "source_ref": entry["source_ref"],
            "observed_at": recorded.isoformat() if recorded else None,
            "date_only": entry.get("observation_date"),
            "scan_id": entry.get("scan_id") if screen else None,
            "confirmed_screen": screen,
            "after_cutoff": bool(cutoff and recorded and recorded > cutoff),
        })
    inventory = scan_inventory or []
    scanned = defaultdict(list)
    for scan in inventory:
        stamp = parse_stamp(scan.get("captured_at"))
        if scan.get("authenticated") is not True or not stamp or not scan.get("scan_id"):
            raise ValueError("INVALID_SCAN_INVENTORY")
        symbols = scan.get("considered_symbols")
        if not isinstance(symbols, list) or not symbols:
            raise ValueError("INVENTORY_REQUIRES_EXPLICIT_CONSIDERED_SYMBOLS")
        if len(set(symbols)) != len(symbols):
            raise ValueError("DUPLICATE_INVENTORY_SYMBOL")
        for symbol in symbols:
            scanned[symbol.upper()].append((stamp, scan["scan_id"]))
    output = []
    for symbol in sorted(set(retained) | set(events) | set(scanned)):
        entries = events[symbol]
        before = [e for e in entries if e["confirmed_screen"] and
                  (cutoff is None or not e["after_cutoff"])]
        considered = [(stamp, scan_id) for stamp, scan_id in scanned[symbol]
                      if cutoff is None or stamp <= cutoff]
        state = ("AUTHENTICATED_CANDIDATE_ROW" if before else
                 "AUTHENTICATED_INVENTORY_CONSIDERED" if considered else
                 "ONLY_AFTER_CUTOFF_SCREEN" if any(e["confirmed_screen"] for e in entries) else
                 "NO_AUTHENTICATED_SCREEN_EVIDENCE")
        output.append({
            "ticker": symbol, "retained_in": sorted(retained.get(symbol, set())),
            "absent_from_retained_manifests": symbol not in retained,
            "observed_elsewhere": bool(entries),
            "actual_screen_evidence": state,
            "screen_proof_ids": sorted(set(e["scan_id"] for e in before) |
                                       set(scan_id for _, scan_id in considered)),
            "observations": entries,
            "eligibility": "UNKNOWN_NOT_AUTOMATICALLY_ELIGIBLE",
            "historical_position": "NOT_INFERRED",
            "execution_status": OUTPUT_MODE,
        })
    return {
        "mode": OUTPUT_MODE,
        "manifest_symbols": len(retained),
        "observed_symbol_union": len(output),
        "off_manifest_observed": sum(e["absent_from_retained_manifests"] and
                                     e["observed_elsewhere"] for e in output),
        "authenticated_screen_evidence_symbols": sum(
            e["actual_screen_evidence"] in {
                "AUTHENTICATED_CANDIDATE_ROW", "AUTHENTICATED_INVENTORY_CONSIDERED"}
            for e in output),
        "no_authenticated_screen_evidence_is_not_never_screened": True,
        "rows": output,
    }


def audit_archive_health(artifact):
    """A success-like status must never mask empty point-in-time coverage."""
    n = artifact.get("market_rows")
    available = artifact.get("asset_available_rows")
    market_ok = type(n) is int and n > 0
    asset_ok = type(available) is int and available > 0
    return {
        "declared_status": artifact.get("status"),
        "usable_market_rows": n if type(n) is int else None,
        "available_asset_rows": available if type(available) is int else None,
        "screen_complete": False,  # no explicit, externally verified denominator
        "provider_coverage": "PARTIAL_ROWS_UNVERIFIED" if market_ok and asset_ok
                             else "EMPTY_OR_UNKNOWN_COVERAGE",
        "may_claim_full_screen": False,
        "execution_status": OUTPUT_MODE,
    }


def prioritize_early_discovery(observation):
    """Rank single-time research observations, never a trade or probability.

    Takes timestamped vendor/source evidence; cannot infer support, selling,
    locate, SMG platform permissions, saleability, or subsequent closing moves.
    A first sighting after 25% repricing is censored as already exhausted.
    """
    at = parse_stamp(observation.get("observed_at"))
    if at is None:
        raise ValueError("AWARE_OBSERVATION_TIME_REQUIRED")
    symbol = observation.get("ticker")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("TICKER_REQUIRED")
    prior = observation.get("prior_regular_close")
    current = observation.get("observed_price")
    def num(v):
        return type(v) in (float, int) and isfinite(v) and v > 0
    quote = observation.get("quote")
    quote_fresh = _evidence(quote, at, max_age=timedelta(minutes=15))
    price_valid = num(prior) and num(current) and quote_fresh
    change_pct = round(100 * (current / prior - 1), 4) if price_valid else None
    proofs = observation.get("tape") or {}
    tape_signs = sorted(k for k in TIMING_SIGNALS
                        if _evidence(proofs.get(k), at, max_age=timedelta(minutes=15)))
    catalyst = observation.get("catalyst") or {}
    mechanism_valid = (catalyst.get("type") in NEGATIVE_MECHANISMS
                       and _evidence(catalyst, at))
    # Registration alone, unexercised warrants, third-party rumors and firm
    # links never imply actual sales or even legal saleability.
    if catalyst.get("type") == "VERIFIED_ACTUAL_SALEABLE_SUPPLY":
        mechanism_valid &= catalyst.get("issued") is True and (
            catalyst.get("legally_saleable") is True)
    phase = observation.get("phase")
    if phase not in ("MORNING", "INTRADAY", "PRECLOSE", "AFTERHOURS"):
        raise ValueError("PHASE_REQUIRED")
    if not price_valid:
        lane, priority = "QUOTE_OR_PRIOR_CLOSE_UNVERIFIED", None
    elif current < 3 or prior < 3:
        lane, priority = "PRICE_HARD_BLOCK", None
    elif change_pct <= -25:
        lane, priority = "EXHAUSTED_NOT_AN_EARLY_CATCH", None
    elif change_pct <= -15:
        lane, priority = "INTERMEDIATE_CONFIRMATION_REQUIRED", 3
    elif mechanism_valid and tape_signs and change_pct <= -2:
        lane, priority = "EARLY_ADVERSE_MECHANISM_AND_TAPE", 1
    elif mechanism_valid and tape_signs:
        lane, priority = "PREBREAKDOWN_MECHANISM_WATCH", 2
    elif change_pct <= -2:
        lane, priority = "EARLY_PRICE_ONLY_WATCH", 4
    else:
        lane, priority = "UNCONFIRMED_PRICE_WATCH", 5
    if phase == "AFTERHOURS" and lane not in (
        "QUOTE_OR_PRIOR_CLOSE_UNVERIFIED", "PRICE_HARD_BLOCK",
        "EXHAUSTED_NOT_AN_EARLY_CATCH"):
        lane = "AFTERHOURS_DISCOVERY_NOT_PRECLOSE_ENTRY"
        priority = None
    if observation.get("corporate_action_unresolved") is True:
        lane, priority = "CORPORATE_ACTION_REVIEW_REQUIRED", None
    local = at.astimezone(ZoneInfo("America/Chicago"))
    window = (phase == "PRECLOSE" and local.weekday() < 5 and
              (14, 45) <= (local.hour, local.minute) <= (14, 58))
    # Clock alone never confirms an actual trading session. Hard-gate evidence
    # belongs to the frozen discretionary evaluation, not this soft discovery.
    return {
        "ticker": symbol.upper(), "observed_at": at.isoformat(),
        "change_from_previous_regular_close_pct": change_pct,
        "lane": lane, "priority_ordinal_not_probability": priority,
        "catalyst_asof_verified": bool(mechanism_valid),
        "verified_fresh_tape_signs": tape_signs,
        "decision_clock_window_only": window,
        "market_session_confirmed": False,
        "hard_eligibility_confirmed": False,
        "potentially_executable": False,
        "future_20pct_close_outcome": "NOT_OBSERVED",
        "prospective_prediction_credited": False,
        "execution_status": OUTPUT_MODE,
    }
