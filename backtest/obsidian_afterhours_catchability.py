"""Research-only after-hours attribution: prohibit retroactive preclose trades.

This module is independent of OBSIDIAN's frozen prospective strategy. It does
not fetch prices, authorize orders, infer missing fills or alter watchlists.
"""
from datetime import datetime

BOARD_STATES = {"SCREENED_REJECTED", "SCREENED_WATCH", "NOT_SCREENED",
                "MISSING_DATA", "INELIGIBLE", "UNKNOWN_BOARD"}

def _aware(value):
    return isinstance(value, datetime) and value.utcoffset() is not None

def classify_missed_move(*, decision_cutoff, outcome_observed_at,
                         board_state, catalyst_public_at=None,
                         preclose_signal_at=None, quote_asof=None,
                         smg_eligibility_verified=False,
                         smg_platform_borrow_verified=False,
                         preclose_execution_evidence=False):
    """Separate known events from proven *pre-decision* actionable setups.

    All timestamps must be timezone-aware; unknown board or missing quote is
    never evidence of rejection. Even a fully verified as-of signal is not a
    recorded trade without separately established execution evidence.
    """
    if not _aware(decision_cutoff) or not _aware(outcome_observed_at):
        raise ValueError("AWARE_TIMESTAMPS_REQUIRED")
    if board_state not in BOARD_STATES:
        raise ValueError("INVALID_BOARD_STATE")
    for stamp in (catalyst_public_at, preclose_signal_at, quote_asof):
        if stamp is not None and not _aware(stamp):
            raise ValueError("AWARE_TIMESTAMPS_REQUIRED")
    if outcome_observed_at <= decision_cutoff:
        raise ValueError("OUTCOME_MUST_FOLLOW_DECISION")
    if board_state == "MISSING_DATA":
        status = "UNRESOLVED_DATA_GAP"
    elif board_state == "UNKNOWN_BOARD":
        status = "PREDECISION_BOARD_NOT_RECOVERED"
    elif board_state == "NOT_SCREENED":
        status = "DISCOVERY_MISS_NOT_A_PROVEN_TRADE"
    elif board_state == "SCREENED_REJECTED":
        status = "SCREENED_REJECTED_REQUIRES_ORIGINAL_REASON"
    elif board_state == "INELIGIBLE":
        status = "INELIGIBLE_NOT_A_TRADE"
    elif preclose_signal_at is None:
        status = "WATCH_OR_EVENT_ONLY_NO_PREDECISION_SIGNAL"
    elif preclose_signal_at > decision_cutoff:
        status = "SIGNAL_AFTER_CUTOFF_NO_RETROACTIVE_TRADE"
    elif quote_asof is None or quote_asof > decision_cutoff:
        status = "NO_VERIFIED_PRECLOSE_QUOTE"
    elif catalyst_public_at is not None and catalyst_public_at > decision_cutoff:
        status = "CATALYST_AFTER_CUTOFF"
    elif smg_eligibility_verified is not True or smg_platform_borrow_verified is not True:
        status = "SMG_ELIGIBILITY_OR_BORROW_UNVERIFIED"
    elif preclose_execution_evidence is not True:
        status = "PRECLOSE_SIGNAL_BUT_EXECUTION_UNVERIFIED"
    else:
        status = "POTENTIALLY_CATCHABLE_WITH_RECORDED_EVIDENCE"
    return {"board_state": board_state, "catchability": status,
            "hypothetical_profit": None, "actual_trade": False,
            "afterhours_outcome_is_preclose_signal": False}

def ads_equivalent_market_cap(ads_price, underlying_shares, shares_per_ads):
    """Diagnostic only. Underlying ordinary shares must be verified and dated."""
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or x <= 0
           for x in (ads_price, underlying_shares, shares_per_ads)):
        raise ValueError("INVALID_ADS_INPUT")
    return ads_price * underlying_shares / shares_per_ads
