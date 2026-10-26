"""Research-only prospective setup taxonomy; NEVER an executable trade gate.

This independent diagnostic deliberately does not change the frozen journal or
production scanner. Each decision requires pre-decision evidence and preserves
all price bands; issuer relationships alone never establish a breakdown.
"""
from datetime import datetime

def _known(x):
    return x is True

def _asof(observed, decision):
    if not isinstance(observed, datetime) or not isinstance(decision, datetime):
        return False
    return (observed.utcoffset() is not None and decision.utcoffset() is not None
            and observed <= decision)

def price_band(change_pct):
    if change_pct is None:
        return "UNKNOWN_PRICE"
    if change_pct <= -25:
        return "EXHAUSTED_25_PLUS"
    if change_pct < -15:
        return "INTERMEDIATE_15_TO_25"
    if change_pct <= -2:
        return "EARLY_2_TO_15"
    return "OTHER_PRICE"

def classify(observation):
    """Return research watch with evidence/rejection reasons, never ENTER.

    Required evidence booleans must have independently verified as-of stamps.
    C is a *long-reversal research watch* only when a failed breakdown,
    support reclaim, higher low and verified buying volume coincide.
    """
    decision = observation.get("decision_at")
    band = price_band(observation.get("change_pct"))
    evidence = observation.get("evidence") or {}
    def ok(key):
        row = evidence.get(key) or {}
        return _known(row.get("verified")) and _asof(row.get("observed_at"), decision)
    breakdown = all(ok(k) for k in ("failed_rebound", "support_loss", "selling_volume", "liquidity"))
    reversal = all(ok(k) for k in ("failed_breakdown", "support_reclaim", "higher_low", "buying_volume"))
    adverse = ok("fresh_adverse_disclosure") or ok("verified_saleable_supply")
    reasons = []
    if not isinstance(decision, datetime) or decision.utcoffset() is None:
        reasons.append("UNKNOWN_DECISION_TIME")
    if band == "UNKNOWN_PRICE":
        reasons.append("MISSING_PRICE_CHANGE")
    if reversal:
        category,setup = "C", "EVIDENCE_BASED_FAILED_BREAKDOWN_LONG_WATCH"
    elif band == "EXHAUSTED_25_PLUS":
        category,setup = "B", "EXHAUSTED_COLLAPSE_NO_FRESH_ENTRY"
    elif band == "INTERMEDIATE_15_TO_25":
        category,setup = "INTERMEDIATE", "INTERMEDIATE_DECLINE_REVIEW_REQUIRED"
    elif band == "EARLY_2_TO_15":
        category,setup = "A", ("MECHANISM_AND_TAPE_CONFIRMED_RESEARCH_WATCH"
                              if breakdown and adverse else "PRICE_ONLY_EARLY_WATCH")
    else:
        category,setup = "UNCLASSIFIED", "NO_EVIDENCE_BASED_SETUP"
    if category == "A" and not breakdown:
        reasons.append("NO_CONFIRMED_BREAKDOWN_TAPE")
    if category == "A" and not adverse:
        reasons.append("NO_VERIFIED_ADVERSE_MECHANISM")
    if category == "INTERMEDIATE":
        reasons.append("PRICE_BAND_REQUIRES_INDEPENDENT_MECHANISM_REVIEW")
    if not reversal and observation.get("claims_reversal"):
        reasons.append("CATEGORY_C_EVIDENCE_INCOMPLETE")
    for field in ("security_type_verified", "market_cap_verified", "prior_price_verified",
                  "current_price_verified", "halt_clear_verified", "corporate_actions_clear_verified",
                  "smg_borrow_verified", "smg_platform_short_verified"):
        if observation.get(field) is not True:
            reasons.append("UNKNOWN_" + field.upper())
    return {"ticker": observation.get("ticker"), "decision_at": decision.isoformat() if
            isinstance(decision, datetime) and decision.utcoffset() is not None else None,
            "price_band": band, "category": category, "research_setup": setup,
            "breakdown_mechanism_confirmed": breakdown and adverse,
            "reversal_confirmed": reversal, "trade_status": "BLOCKED_RESEARCH_ONLY",
            "reasons": reasons}
