"""Fail-closed corporate-action comparability for IEX prospective outcomes.

Two agreeing unadjusted closing prices are NOT enough when a split, spin-off,
distribution, merger or ticker/identity change alters the shareholder entitlement.
This module does not calculate adjusted returns or authorize trades.
"""
from urllib.parse import urlsplit

from backtest.obsidian_prospective_capture import asof

ACTION_FLAGS = frozenset({
    "split", "reverse_split", "spin_off", "special_dividend",
    "merger", "rights_distribution", "symbol_change",
    "share_class_conversion", "adr_ratio_change",
})


def no_action_comparable(outcome, previous_session, session, close_at, collected_at):
    """Accept only explicit, independently reviewable same-entitlement evidence.

    Known/possible corporate actions are CENSORED pending a separate
    independently verified total-entitlement return, not automatically
    classified as a price collapse. A 'clear' boolean alone is insufficient.
    """
    if outcome.get("corporate_actions_clear") is not True:
        return False
    review = outcome.get("corporate_action_review")
    if not isinstance(review, dict):
        return False
    if review.get("status") != "NO_ACTIONS_CONFIRMED" or review.get("verified") is not True:
        return False
    if review.get("reviewed_sessions") != [previous_session.isoformat(), session.isoformat()]:
        return False
    observed = asof(review.get("checked_at"))
    if (observed is None or close_at is None or collected_at is None
            or not close_at <= observed <= collected_at):
        return False
    source = review.get("source_url")
    if not isinstance(source, str):
        return False
    parsed = urlsplit(source)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    symbol = outcome.get("ticker")
    before = review.get("prior_symbol")
    after = review.get("current_symbol")
    if not isinstance(symbol, str) or not symbol or before != symbol or after != symbol:
        return False
    prior_id = review.get("prior_security_id")
    current_id = review.get("current_security_id")
    if not isinstance(prior_id, str) or not prior_id.strip() or current_id != prior_id:
        return False
    flags = review.get("action_flags")
    if not isinstance(flags, dict) or set(flags) != ACTION_FLAGS:
        return False
    return all(flag is False for flag in flags.values())
