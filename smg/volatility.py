"""Broad volatility lane with stricter market confirmation than firm-first."""
import re
from datetime import timedelta
from .models import Evaluation
from .game_rules import APPROVED_EXCHANGES,eligibility,is_excluded_symbol

def volatility_structure(candidate,cfg,entities,now):
    hard=[];unknown=[]
    if is_excluded_symbol(candidate.ticker):hard.append('SMG_EXCLUDED_SYMBOL')
    if re.fullmatch('[A-Z]{5}',candidate.ticker.upper()):hard.append('FIVE_LETTER_TICKER')
    if candidate.exchange not in APPROVED_EXCHANGES:hard.append('EXCHANGE_OUTSIDE_SCOPE')
    if candidate.is_acquisition_corp is True or re.search(r'\b(?:acquisition|blank check)\b',candidate.name,re.I):hard.append('ACQUISITION_CORPORATION')
    if candidate.is_acquisition_corp is not False or 'is_acquisition_corp' not in candidate.evidence:unknown.append('UNKNOWN_ISSUER_CLASSIFICATION')
    if candidate.security_type not in {'CS','ADRC','ADS','COMMON_STOCK'} or 'security_type' not in candidate.evidence:unknown.append('UNVERIFIED_COMMON_EQUITY')
    if not 0<=(now-candidate.reviewed_at).total_seconds()<=26*3600:unknown.append('STALE_OR_FUTURE_BROAD_REVIEW')
    matches=entities.match(candidate)
    return Evaluation(candidate=candidate,status='EXCLUDED' if hard else 'REVIEW_REQUIRED' if unknown else 'STRUCTURAL_MATCH',
        reasons=hard+unknown+(['LISTED_FIRM_BONUS'] if matches else ['NO_LISTED_FIRM_MATCH']),matches=matches)

def evaluate_volatility(candidate,cfg,entities,now,snapshot=None,halt=None):
    result=volatility_structure(candidate,cfg,entities,now);result.snapshot=snapshot;result.halt=halt
    if halt and halt.status=='HALTED':result.status='EXCLUDED';result.reasons.append('CURRENTLY_HALTED');return result
    if result.status!='STRUCTURAL_MATCH':return result
    if not halt or halt.status!='CLEAR' or not 0<=(now-halt.checked_at).total_seconds()<=cfg.max_snapshot_age_seconds:
        result.status='REVIEW_REQUIRED';result.reasons.append('UNKNOWN_OR_STALE_HALT_STATUS');return result
    if snapshot is None:result.status='REVIEW_REQUIRED';result.reasons.append('MISSING_MARKET_DATA');return result
    effective=now-timedelta(minutes=snapshot.declared_delay_minutes)
    if snapshot.feed!=cfg.market_feed or snapshot.declared_delay_minutes!=cfg.market_data_delay_minutes:
        result.status='REVIEW_REQUIRED';result.reasons.append('DATA_FEED_MISMATCH');return result
    if any(not 0<=(effective-t).total_seconds()<=cfg.max_snapshot_age_seconds for t in [snapshot.asof,snapshot.price_time]):
        result.status='REVIEW_REQUIRED';result.reasons.append('STALE_OR_FUTURE_MARKET_DATA');return result
    if 'CORPORATE_ACTION_REVIEW' in snapshot.flags:
        result.status='REVIEW_REQUIRED';result.reasons.append('CORPORATE_ACTION_REVIEW');return result
    game_status,game_reasons=eligibility(snapshot,cfg,now)
    if game_status:result.status=game_status;result.reasons+=game_reasons;return result
    if snapshot.rvol is None or snapshot.monthly_return is None or snapshot.one_day_return is None:
        result.status='REVIEW_REQUIRED';result.reasons.append('INSUFFICIENT_VOLATILITY_HISTORY');return result
    pump_failure=(snapshot.monthly_return>=cfg.broad_min_monthly_return_pct and snapshot.rvol>=cfg.broad_min_volume_ratio and
                  (snapshot.one_day_return<=-3 or snapshot.drawdown_pct<=-8))
    shock_failure=snapshot.rvol>=1.5 and snapshot.one_day_return<=-8
    if not (pump_failure or shock_failure):
        result.status='MARKET_NOT_CONFIRMED';result.reasons.append('VOLATILITY_REVERSAL_NOT_CONFIRMED');return result
    result.status='QUALIFIED';result.signal_side='SHORT'
    result.reasons.append('PUMP_FAILURE_SHORT' if pump_failure else 'HIGH_VOLATILITY_BREAKDOWN_SHORT')
    firm_priority=min((m['priority'] for m in result.matches),default=9)
    result.rank=[0 if result.matches else 1,firm_priority,-len(result.matches),snapshot.one_day_return,snapshot.drawdown_pct,-snapshot.rvol,-snapshot.monthly_return]
    return result
