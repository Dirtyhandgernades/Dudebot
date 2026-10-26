"""Research-only, frozen v1 discretionary evidence tiers for early-collapse studies.

NO live execution, orders, rank calibration or production integration.
Hard SMG eligibility is distinct from soft pre-collapse confirmation.
A speculative setup is NOT a proven breakdown or a trade instruction.
All evidence must be independently timestamped at/before decision time.
"""
from datetime import datetime, timedelta, timezone
from math import isfinite
from zoneinfo import ZoneInfo
from .obsidian_early_mechanism_audit import price_band

POLICY_ID = "OBSIDIAN_DISCRETIONARY_TIERS_V1_2026_10_26"
MAX_QUOTE_AGE = timedelta(minutes=15)
MAX_INITIAL_EQUITY_FRACTION = 0.05
HARD_FIELDS = (
    "exchange", "security_type", "current_price", "prior_session_price",
    "prior_session_confirmed", "current_shares", "market_cap",
    "halt_clear", "corporate_actions_clear", "liquidity_sufficient",
    "buying_power", "equity", "exposure_within_limits",
)
SHORT_FIELDS = ("smg_short_available", "smg_platform_short_available")
FRESH_EXECUTION_FIELDS = {"current_price", "halt_clear", "corporate_actions_clear",
                          "liquidity_sufficient", "buying_power", "exposure_within_limits",
                          "smg_short_available", "smg_platform_short_available"}
TAPE_SHORT = ("failed_rebound", "support_loss", "selling_volume", "liquidity")
TAPE_LONG = ("failed_breakdown", "support_reclaim", "higher_low", "buying_volume")
CATALYST_SHORT = ("fresh_adverse_disclosure", "verified_saleable_supply")
PLAN_FIELDS = ("thesis", "entry_trigger", "invalidation", "exit_rule")

def _aware(value):
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None

def _positive_number(value):
    return type(value) in (int, float) and isfinite(value) and value > 0

def _proof(row, decision, *, fresh=False):
    if not isinstance(row, dict) or not _aware(decision):
        return False
    observed = row.get("observed_at")
    published = row.get("published_at")
    if not _aware(observed) or observed > decision:
        return False
    if published is not None and (not _aware(published) or published > decision):
        return False
    if not isinstance(row.get("source_id"), str) or not row["source_id"].strip():
        return False
    if fresh and decision - observed > MAX_QUOTE_AGE:
        return False
    return True

def _clock_window(decision):
    if not _aware(decision):
        return False
    local = decision.astimezone(ZoneInfo("America/Chicago"))
    return local.weekday() < 5 and (14, 45) <= (local.hour, local.minute) <= (14, 58)

def _hard_gate(row, direction, decision):
    evidence = row.get("hard") or {}
    issues = []
    for field in HARD_FIELDS + (SHORT_FIELDS if direction == "SHORT" else ()) + (("market_session_open",) if _clock_window(decision) else ()):
        proof = evidence.get(field)
        if not _proof(proof, decision, fresh=field in FRESH_EXECUTION_FIELDS or field == "market_session_open"):
            issues.append("UNVERIFIED_ASOF_" + field.upper())
    def value(field):
        proof = evidence.get(field)
        return proof.get("value") if isinstance(proof, dict) and _proof(proof, decision) else None
    exchange = value("exchange")
    if exchange not in ("NASDAQ", "NYSE"):
        issues.append("NOT_VERIFIED_US_MAJOR_EXCHANGE")
    if value("security_type") != "COMMON_STOCK":
        issues.append("NOT_VERIFIED_COMMON_STOCK")
    for field in ("current_price", "prior_session_price"):
        v = value(field)
        if not _positive_number(v) or v < 3:
            issues.append("PRICE_GATE_" + field.upper())
    if value("prior_session_confirmed") is not True:
        issues.append("PREVIOUS_REGULAR_SESSION_UNVERIFIED")
    if _clock_window(decision) and value("market_session_open") is not True:
        issues.append("MARKET_SESSION_NOT_VERIFIED_OPEN")
    shares, cap, current = value("current_shares"), value("market_cap"), value("current_price")
    if not _positive_number(shares):
        issues.append("SHARES_UNVERIFIED")
    if not _positive_number(cap) or cap < 25_000_000:
        issues.append("MARKET_CAP_GATE")
    if all(_positive_number(x) for x in (shares, cap, current)):
        # For ADS/split mismatches, a cap inconsistent with shares is not proof.
        if abs(shares * current - cap) / cap > 0.1:
            issues.append("SHARES_CAP_PRICE_MISMATCH")
    for field in ("halt_clear", "corporate_actions_clear", "liquidity_sufficient",
                  "exposure_within_limits"):
        if value(field) is not True:
            issues.append("NOT_CLEARED_" + field.upper())
    if direction == "SHORT":
        for field in SHORT_FIELDS:
            if value(field) is not True:
                issues.append("NO_VERIFIED_" + field.upper())
    for field in ("buying_power", "equity"):
        if not _positive_number(value(field)):
            issues.append("NO_VERIFIED_" + field.upper())
    return sorted(set(issues))

def _soft_proof(row, decision):
    return isinstance(row, dict) and row.get("verified") is True and _proof(row, decision)

def evaluate(observation):
    """Return HARD_BLOCKED/WATCH_ONLY/SPECULATIVE_SETUP/CONFIRMED_SETUP.

    Even CONFIRMED_SETUP is a RESEARCH classification, not an executable order.
    Never use future prices, outcome labels, social claims or unvalidated scores
    to create a verified mechanism. Output keeps underlying soft classification
    when eligibility is blocked so research discovery is not silently lost.
    """
    decision = observation.get("decision_at")
    direction = observation.get("direction")
    if direction not in ("SHORT", "LONG"):
        raise ValueError("DIRECTION_MUST_BE_SHORT_OR_LONG")
    soft = observation.get("soft") or {}
    known = {key for key, proof in soft.items() if _soft_proof(proof, decision)}
    band = price_band(observation.get("change_pct"))
    short_catalyst = any(k in known for k in CATALYST_SHORT)
    short_tape = set(TAPE_SHORT) & known
    long_tape = set(TAPE_LONG) & known
    full_short = short_catalyst and len(short_tape) == len(TAPE_SHORT)
    full_long = len(long_tape) == len(TAPE_LONG)
    partial_short = short_catalyst and bool(short_tape)
    partial_long = "failed_breakdown" in known and bool(
        long_tape & {"support_reclaim", "higher_low", "buying_volume"})
    plan = observation.get("plan") or {}
    plan_missing = [f for f in PLAN_FIELDS if not isinstance(plan.get(f), str)
                    or not plan[f].strip()]
    if direction == "SHORT":
        # Exhausted losses do not qualify as fresh speculative entries.
        if band == "EXHAUSTED_25_PLUS":
            soft_tier = "WATCH_ONLY"
        elif full_short:
            soft_tier = "CONFIRMED_SETUP"
        elif partial_short:
            soft_tier = "SPECULATIVE_SETUP"
        else:
            soft_tier = "WATCH_ONLY"
        category = ("B" if band == "EXHAUSTED_25_PLUS" else
                    "A" if band == "EARLY_2_TO_15" else
                    "INTERMEDIATE" if band == "INTERMEDIATE_15_TO_25" else "UNCLASSIFIED")
        missing_soft = sorted(set(TAPE_SHORT) - known)
        if not short_catalyst:
            missing_soft.append("NO_VERIFIED_ADVERSE_MECHANISM")
    else:
        soft_tier = ("CONFIRMED_SETUP" if full_long else
                     "SPECULATIVE_SETUP" if partial_long else "WATCH_ONLY")
        category = "C" if full_long else "C_CANDIDATE" if partial_long else "UNCLASSIFIED"
        missing_soft = sorted(set(TAPE_LONG) - known)
    if plan_missing and soft_tier != "WATCH_ONLY":
        soft_tier = "WATCH_ONLY"
    hard_reasons = _hard_gate(observation, direction, decision)
    if not _aware(decision):
        hard_reasons.append("INVALID_DECISION_TIME")
    if observation.get("change_pct") is None:
        # Price band itself is soft, but do not pretend a current tape exists.
        missing_soft.append("MISSING_PRICE_CHANGE")
    tier = "HARD_BLOCKED" if hard_reasons else soft_tier
    hard = observation.get("hard") or {}
    def amount(field):
        proof = hard.get(field) or {}
        return proof.get("value") if _proof(proof, decision) else None
    bp, equity = amount("buying_power"), amount("equity")
    max_initial = (round(MAX_INITIAL_EQUITY_FRACTION * min(bp, equity), 2)
                   if not hard_reasons and soft_tier == "SPECULATIVE_SETUP"
                   and _positive_number(bp) and _positive_number(equity) else None)
    return {
        "policy_id": POLICY_ID, "ticker": observation.get("ticker"),
        "decision_at": decision.isoformat() if _aware(decision) else None,
        "direction": direction, "price_band": band, "category": category,
        "tier": tier, "underlying_soft_tier": soft_tier,
        "hard_gates_passed": not hard_reasons, "hard_blockers": sorted(set(hard_reasons)),
        "missing_soft_evidence": sorted(set(missing_soft)),
        "missing_plan": plan_missing,
        "confirmed_mechanism": full_short if direction == "SHORT" else full_long,
        "speculative_initial_size_ceiling_usd": max_initial,
        "initial_size_ceiling_policy": "AT_MOST_5_PERCENT_OF_LESSER_VERIFIED_EQUITY_OR_BUYING_POWER",
        "execution_status": "RESEARCH_ONLY_NOT_AN_ORDER",
        "entry_trigger": plan.get("entry_trigger"),
        "invalidation": plan.get("invalidation"),
        "exit_rule": plan.get("exit_rule"),
        "thesis": plan.get("thesis"),
        "decision_window_open": _clock_window(decision) and not any(
            reason in hard_reasons for reason in
            ("UNVERIFIED_ASOF_MARKET_SESSION_OPEN", "MARKET_SESSION_NOT_VERIFIED_OPEN")),
    }
