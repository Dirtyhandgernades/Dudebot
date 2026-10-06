"""Conservative point-in-time research execution evidence, not an order API.

A current broker indication is not a historical locate, an SMG acceptance,
or a promise of a fill. Absent facts never become passing facts.
"""
import math
import re
from datetime import datetime, timezone
from .game_rules import is_excluded_symbol, APPROVED_EXCHANGES


REQUIRED=('security','market_cap','halt','borrow','smg_membership')


def stamp(value):
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (TypeError,ValueError,AttributeError):return None


def latest_known(rows,kind,ticker,decision,max_age_seconds=None):
    eligible=[]
    for row in rows:
        if row.get('kind')!=kind or row.get('subject')!=ticker:continue
        observed=stamp(row.get('observed_at'));published=stamp(row.get('published_at',row.get('observed_at')))
        if observed is None or published is None or max(observed,published)>decision:continue
        if max_age_seconds is not None and (decision-observed).total_seconds()>max_age_seconds:continue
        # Do not resurrect a prior passing observation after a later failure.
        eligible.append((observed,published,row))
    return max(eligible,key=lambda x:x[:2])[2] if eligible else None


def execution_evidence(ticker,decision_at,price,observations=()):
    decision=stamp(decision_at)
    if decision is None:raise ValueError('Decision requires an aware timestamp')
    rejected=[];missing=[];sources={}
    if is_excluded_symbol(ticker):rejected.append('SMG_EXCLUDED_SYMBOL')
    if re.fullmatch('[A-Z]{5}',ticker.upper()):rejected.append('FIVE_LETTER_TICKER')
    if not isinstance(price,(int,float)) or isinstance(price,bool) or not math.isfinite(price):missing.append('PRICE_UNAVAILABLE')
    elif price<=3:rejected.append('PRICE_NOT_ABOVE_3')
    facts={}
    for kind in REQUIRED:
        row=latest_known(observations,kind,ticker,decision,26*3600 if kind in {'market_cap','security','smg_membership'} else 3600)
        value=(row or {}).get('value',{})
        sources[kind]={'status':value.get('status','UNAVAILABLE'),'source':(row or {}).get('source'),
                       'observed_at':(row or {}).get('observed_at')}
        if not row or not row.get('source') or value.get('status')!='VERIFIED':
            missing.append(kind.upper()+'_UNAVAILABLE');continue
        facts[kind]=value
    security=facts.get('security',{})
    if security:
        if security.get('exchange') not in APPROVED_EXCHANGES:rejected.append('EXCHANGE_OUTSIDE_SCOPE')
        if security.get('is_acquisition_corp') is True:rejected.append('ACQUISITION_CORPORATION')
        elif security.get('is_acquisition_corp') is not False:missing.append('ISSUER_CLASSIFICATION_UNAVAILABLE')
        if security.get('security_type') not in {'CS','ADRC','ADS','COMMON_STOCK'}:rejected.append('NOT_VERIFIED_COMMON_EQUITY')
    cap=facts.get('market_cap',{}).get('market_cap')
    if 'market_cap' in facts:
        if not isinstance(cap,(int,float)) or isinstance(cap,bool) or not math.isfinite(cap):missing.append('MARKET_CAP_INVALID')
        elif cap<25_000_000:rejected.append('MARKET_CAP_BELOW_25M')
    halt=facts.get('halt',{}).get('halt_status')
    if 'halt' in facts:
        if halt=='HALTED':rejected.append('HALTED')
        elif halt!='CLEAR':missing.append('HALT_STATE_UNAVAILABLE')
    borrow=facts.get('borrow',{})
    if borrow:
        if any(k not in borrow for k in ('tradable','shortable','borrow_status')) or borrow['borrow_status'] is None:missing.append('BORROW_FIELDS_UNAVAILABLE')
        elif borrow['tradable'] is not True or borrow['shortable'] is not True or borrow['borrow_status']!='easy_to_borrow':rejected.append('BORROW_NOT_EXECUTABLE')
    membership=facts.get('smg_membership',{}).get('allowed')
    if 'smg_membership' in facts:
        if membership is False:rejected.append('SMG_SECURITY_NOT_ALLOWED')
        elif membership is not True:missing.append('SMG_MEMBERSHIP_UNKNOWN')
    return {'status':'REJECTED' if rejected else 'UNAVAILABLE' if missing else 'EXECUTABLE_INDICATION',
            'rejected':rejected,'missing':missing,'sources':sources,
            'locate_reserved':False,'borrow_cost_known':borrow.get('annual_rate') is not None,
            'limitation':'Evidence indication only; not a reserved locate or guaranteed SMG fill'}
