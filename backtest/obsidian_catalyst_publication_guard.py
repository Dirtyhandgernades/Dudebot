"""Offline as-of guard for public catalysts; research only.

A private board approval or adverse event is not public market evidence.
Do not turn a post-decision press release into a prior-day prediction.
This guard does NOT determine whether a symbol was screened, eligible or
predictable using other information.
"""
from backtest.obsidian_prospective_capture import asof


def catalyst_asof_status(decision_at, public_at, observed_at, internal_at=None):
    """Return evidence-timing status without deriving any trading signal."""
    decision = asof(decision_at)
    public = asof(public_at)
    observed = asof(observed_at)
    if any(t is None for t in (decision, public, observed)):
        return "MISSING_OR_INVALID_PUBLICATION_CLOCK"
    if decision > observed or public > observed:
        return "INCONSISTENT_FUTURE_OBSERVATION"
    if internal_at is not None and asof(internal_at) is None:
        return "INVALID_INTERNAL_CLOCK"
    # internal_at is intentionally NOT used to establish public knowledge.
    if public > decision:
        return "POST_DECISION_PUBLICATION_NOT_PRIOR_PUBLIC_SIGNAL"
    return "PUBLIC_AT_DECISION_NOT_PROOF_SCREENED_OR_ACTIONABLE"
