import re
from datetime import date, datetime, timedelta
from .models import Config, Candidate, Evaluation, Snapshot, HaltCheck

def years_ago(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year-years)
    except ValueError:
        return day.replace(year=day.year-years, day=28)

def normalize_name(name):
    tokens = re.findall(r'[a-z0-9]+', name.lower().replace('&', ' and '))
    while tokens and tokens[-1] in {'llp','llc','inc','limited','ltd','corp'}:
        tokens.pop()
    return ''.join(tokens)

class EntityList:
    def __init__(self, data):
        self.entries = {}
        for role, groups in data.items():
            for category, names in groups.items():
                priority = -1 if category.startswith('SUPER ') else 0 if category in {'High-Suspicion Focus Group','High-Suspicion Parties'} else 1 if category.startswith('Additional') else 2
                for name in names:
                    self.entries[(role, normalize_name(name))] = dict(name=name, role=role, category=category, priority=priority)

    def match(self, candidate):
        found = {}
        for item in candidate.matches:
            role = 'underwriter' if item.role == 'placement_agent' else item.role
            entry = self.entries.get((role, normalize_name(item.name)))
            if not entry:
                continue
            if candidate.pipeline == 'DIRECT_OFFERING':
                valid = item.relationship == 'transaction' or (item.relationship == 'current' and role in {'auditor','counsel'})
            else:
                valid = item.relationship == 'transaction' or (item.relationship == 'current' and role in {'auditor','counsel'})
            if valid:
                found[(entry['name'],role)] = dict(entry, evidence=item.evidence.model_dump(mode='json'), relationship=item.relationship)
        return list(found.values())

def structural(c: Candidate, cfg: Config, entities: EntityList, now: datetime) -> Evaluation:
    excluded, unknown = [], []
    if re.fullmatch('[A-Z]{5}', c.ticker.upper()): excluded.append('FIVE_LETTER_TICKER')
    if c.exchange not in {'XNAS','NASDAQ'}: excluded.append('EXCHANGE_OUTSIDE_SCOPE')
    if c.is_acquisition_corp is True: excluded.append('ACQUISITION_CORPORATION')
    if c.is_acquisition_corp is None: unknown.append('UNKNOWN_ISSUER_CLASSIFICATION')
    if c.security_type not in {'CS','ADRC','ADS','COMMON_STOCK'}: unknown.append('UNVERIFIED_COMMON_EQUITY')
    if c.status == 'canceled': excluded.append('OFFERING_CANCELED')
    if c.status == 'unknown': unknown.append('UNKNOWN_TRANSACTION_STATUS')
    if not c.terms_unambiguous: unknown.append('AMBIGUOUS_OFFERING_TERMS')
    if c.currency != 'USD': unknown.append('UNVERIFIED_USD_TERMS')
    if c.event_date > now.date(): unknown.append('FUTURE_EVENT')
    for key, val, lo, hi in [('price',c.offer_price,cfg.offer_price_usd_min,cfg.offer_price_usd_max),('gross',c.offer_gross,cfg.offer_gross_usd_min,cfg.offer_gross_usd_max)]:
        if val is None: unknown.append('MISSING_OFFER_'+key.upper())
        elif not lo <= val <= hi: excluded.append('OFFER_'+key.upper()+'_OUT_OF_RANGE')
    required = {'operations_country','offer_price','offer_gross','is_acquisition_corp','security_type','status'}
    if c.pipeline == 'RECENT_IPO':
        required.add('ipo_date')
        if not c.ipo_date: unknown.append('MISSING_IPO_DATE')
        elif c.ipo_date < years_ago(now.date(),cfg.ipo_max_age_years): excluded.append('IPO_TOO_OLD')
        elif c.ipo_date > now.date(): excluded.append('NOT_YET_LISTED')
        if not c.operations_country: unknown.append('UNKNOWN_OPERATIONS')
        elif c.operations_country not in cfg.ipo_operations_countries: excluded.append('IPO_GEOGRAPHY')
    elif not c.operations_country:
        unknown.append('UNKNOWN_OPERATIONS')
    for key in sorted(required - set(c.evidence)): unknown.append('MISSING_EVIDENCE:'+key)
    matched = entities.match(c)
    if len(matched) < cfg.entity_match_min: unknown.append('NO_VERIFIED_ENTITY_MATCH')
    # A recent direct-offering event still needs status refresh; discovery manages this.
    if (now-c.reviewed_at).total_seconds() > 26*3600: unknown.append('STALE_FILING_REVIEW')
    if (now-c.reviewed_at).total_seconds() < -60: unknown.append('FUTURE_REVIEW_TIMESTAMP')
    return Evaluation(candidate=c, status='EXCLUDED' if excluded else 'REVIEW_REQUIRED' if unknown else 'STRUCTURAL_MATCH', reasons=excluded+unknown, matches=matched)

def evaluate(c, cfg, entities, now, snapshot=None, halt=None):
    result = structural(c,cfg,entities,now)
    result.halt = halt
    if halt and halt.status == 'HALTED':
        result.status='EXCLUDED'; result.reasons.append('CURRENTLY_HALTED'); return result
    if result.status != 'STRUCTURAL_MATCH': return result
    if not halt or halt.status != 'CLEAR' or not 0 <= (now-halt.checked_at).total_seconds() <= cfg.max_snapshot_age_seconds:
        result.status='REVIEW_REQUIRED'; result.reasons.append('UNKNOWN_OR_STALE_HALT_STATUS'); return result
    return market_confirmation(result,cfg,now,snapshot)

def market_confirmation(result,cfg,now,snapshot):
    """Market rules alone; caller must retain structural and halt gating."""
    c=result.candidate
    if snapshot is None:
        result.status='REVIEW_REQUIRED'; result.reasons.append('MISSING_MARKET_DATA'); return result
    result.snapshot=snapshot
    effective_now=now-timedelta(minutes=snapshot.declared_delay_minutes)
    if snapshot.feed != 'synthetic' and (snapshot.feed!=cfg.market_feed or snapshot.declared_delay_minutes!=cfg.market_data_delay_minutes):
        result.status='REVIEW_REQUIRED'; result.reasons.append('DATA_FEED_MISMATCH'); return result
    age=(effective_now-snapshot.price_time).total_seconds()
    if not 0 <= age <= cfg.max_snapshot_age_seconds or not 0 <= (effective_now-snapshot.asof).total_seconds() <= cfg.max_snapshot_age_seconds:
        result.status='REVIEW_REQUIRED'; result.reasons.append('STALE_OR_FUTURE_MARKET_DATA'); return result
    fatal = [f for f in snapshot.flags if f in {'MISSING_SESSION_DATA','CORPORATE_ACTION_REVIEW','MARKET_CLOSED'}]
    if fatal or snapshot.rvol is None or snapshot.baseline_sessions < cfg.rvol_min_sessions:
        result.status='REVIEW_REQUIRED'; result.reasons += fatal or ['INSUFFICIENT_VOLUME_HISTORY']; return result
    if snapshot.rvol < cfg.rvol_min:
        result.status='MARKET_NOT_CONFIRMED'; result.reasons.append('RVOL_BELOW_ONE'); return result
    surge_needed = c.pipeline == 'RECENT_IPO' or cfg.direct_offering_require_monthly_surge
    if surge_needed:
        if cfg.surge_return_min_pct is None:
            result.status='CONFIG_REQUIRED'; result.reasons.append('SURGE_THRESHOLD_NOT_SET'); return result
        if snapshot.monthly_return is None:
            result.status='REVIEW_REQUIRED'; result.reasons.append('SHORT_MONTHLY_HISTORY'); return result
        if snapshot.monthly_return < cfg.surge_return_min_pct:
            result.status='MARKET_NOT_CONFIRMED'; result.reasons.append('SURGE_THRESHOLD_NOT_MET'); return result
    result.status='QUALIFIED'
    result.reasons=['IPO_SURGE_CONFIRMED' if c.pipeline=='RECENT_IPO' else 'DIRECT_OFFERING_REVIEW']
    age_days=(now.date()-c.ipo_date).days if c.ipo_date else 99999
    if c.pipeline=='RECENT_IPO':
        primary=0 if cfg.ipo_focus_days[0]<=age_days<=cfg.ipo_focus_days[1] else 1 if c.ipo_date >= years_ago(now.date(),cfg.ipo_preferred_age_years) else 2
    else: primary=1 if c.operations_country in {'US','CA'} else 0
    result.rank=[primary,min(m['priority'] for m in result.matches),-len(result.matches),-(snapshot.monthly_return or 0),-snapshot.rvol]
    if c.pipeline=='RECENT_IPO' and cfg.ipo_low_priority_surge_max_pct is not None:
        low_priority=snapshot.monthly_return <= cfg.ipo_low_priority_surge_max_pct
        # Retain existing age/entity ranking within each surge priority band.
        result.rank=[int(low_priority)]+result.rank
        if low_priority: result.reasons.append('LOW_PRIORITY_MONTHLY_SURGE')
    return result
