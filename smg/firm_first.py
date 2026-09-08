"""Separate firm-first research profile requested by the user.

Firm association is not a prediction of a fall or a finding of misconduct.
The three exclusions remain hard; unknown evidence remains unknown.
"""
import re
from datetime import timedelta

from .models import Evaluation
from .rules import structural


def firm_structure(candidate,cfg,entities,now):
    strict = structural(candidate,cfg,entities,now)
    reasons = []
    hard = []
    if re.fullmatch('[A-Z]{5}',candidate.ticker.upper()):
        hard.append('FIVE_LETTER_TICKER')
    if candidate.is_acquisition_corp is True:
        hard.append('ACQUISITION_CORPORATION')
    if re.search(r'\bacquisition\s+corp(?:oration)?\b',candidate.name,re.I):
        hard.append('ACQUISITION_CORPORATION_NAME')
    if candidate.exchange not in {'XNAS','NASDAQ'}:
        hard.append('EXCHANGE_OUTSIDE_SCOPE')
    if candidate.is_acquisition_corp is None or 'is_acquisition_corp' not in candidate.evidence:
        reasons.append('UNKNOWN_ISSUER_CLASSIFICATION')
    # Transaction/current relationships are still required. An old IPO
    # underwriter alone cannot establish a later direct-offering relationship.
    matches=entities.match(candidate)
    if not matches:
        reasons.append('NO_VERIFIED_ENTITY_MATCH')
    if candidate.security_type not in {'CS','ADRC','ADS','COMMON_STOCK'}:
        reasons.append('UNVERIFIED_COMMON_EQUITY')
    if candidate.event_date>now.date():
        reasons.append('FUTURE_EVENT')
    if candidate.status=='canceled' and candidate.pipeline!='FIRM_WATCH':
        reasons.append('TRANSACTION_RELATIONSHIP_REVIEW_REQUIRED')
    if any('RELATIONSHIP_CHANGE_REVIEW' in n for n in candidate.notes):
        reasons.append('RELATIONSHIP_CHANGE_REVIEW_REQUIRED')
    if not 0 <= (now-candidate.reviewed_at).total_seconds() <= 26*3600:
        reasons.append('STALE_OR_FUTURE_FILING_REVIEW')
    result=Evaluation(candidate=candidate,status='EXCLUDED' if hard else 'REVIEW_REQUIRED' if reasons else 'STRUCTURAL_MATCH',
                      reasons=hard+reasons,matches=matches)
    if result.status=='STRUCTURAL_MATCH':
        result.reasons=['VERIFIED_LISTED_FIRM_RELATIONSHIP']+['PREFERENCE_GAP:'+x for x in strict.reasons]
    return result


def evaluate_firm_first(candidate,cfg,entities,now,snapshot=None,halt=None):
    result=firm_structure(candidate,cfg,entities,now)
    result.halt=halt
    if halt and halt.status=='HALTED':
        result.status='EXCLUDED';result.reasons.append('CURRENTLY_HALTED');return result
    if result.status!='STRUCTURAL_MATCH':
        return result
    result.snapshot=snapshot
    # Missing/no pump and low RVOL are preferences; a stale/future price or
    # unresolved split/ADS basis must not be reported as reliable market data.
    if snapshot is None:
        result.status='REVIEW_REQUIRED';result.reasons.append('MISSING_MARKET_DATA');return result
    effective=now-timedelta(minutes=cfg.market_data_delay_minutes)
    if snapshot.feed!=cfg.market_feed or snapshot.declared_delay_minutes!=cfg.market_data_delay_minutes:
        result.status='REVIEW_REQUIRED';result.reasons.append('DATA_FEED_MISMATCH');return result
    if any(not 0 <= (effective-t).total_seconds() <= cfg.max_snapshot_age_seconds for t in [snapshot.asof,snapshot.price_time]):
        result.status='REVIEW_REQUIRED';result.reasons.append('STALE_OR_FUTURE_MARKET_DATA');return result
    if 'CORPORATE_ACTION_REVIEW' in snapshot.flags:
        result.status='REVIEW_REQUIRED';result.reasons.append('CORPORATE_ACTION_REVIEW');return result
    if not halt or halt.status!='CLEAR' or not 0 <= (now-halt.checked_at).total_seconds() <= cfg.max_snapshot_age_seconds:
        result.status='MATCH_EXCEPT_UNKNOWN_HALT';result.reasons.append('UNKNOWN_OR_STALE_HALT_STATUS');return result
    result.status='QUALIFIED'
    if snapshot.rvol is None or snapshot.rvol<cfg.rvol_min:
        result.reasons.append('PREFERENCE_GAP:RVOL')
    if snapshot.monthly_return is None:
        result.reasons.append('PREFERENCE_GAP:MONTHLY_HISTORY')
    elif snapshot.monthly_return < (cfg.surge_return_min_pct or 0):
        result.reasons.append('NOT_YET_PUMPED_OR_BELOW_PREFERRED_SURGE')
    elif cfg.ipo_low_priority_surge_max_pct is not None and snapshot.monthly_return<=cfg.ipo_low_priority_surge_max_pct:
        result.reasons.append('LOW_PRIORITY_MONTHLY_SURGE')
    result.reasons.extend('MARKET_CONTEXT:'+flag for flag in snapshot.flags)
    result.rank=[min(m['priority'] for m in result.matches),-len(result.matches),
                 sum(r.startswith('PREFERENCE_GAP:') for r in result.reasons),-(snapshot.monthly_return or 0)]
    return result
