"""Offline preparation assessment using supplied, source-backed account facts."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .decision_evidence import execution_evidence, latest_known, stamp
from .market import calendar, session_bounds
from zoneinfo import ZoneInfo


def assess_short(action, account, rule, now, max_age_seconds):
    blockers = []
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError('Aware assessment time required')
    if type(max_age_seconds) is not int or max_age_seconds <= 0:
        raise ValueError('Explicit positive freshness limit required')
    for item, label in ((account, 'ACCOUNT'), (rule, 'RULE')):
        if not item.get('source_record'):
            blockers.append(label + '_SOURCE_MISSING')
    observed = account.get('observed_at')
    try:
        at = datetime.fromisoformat(observed)
        age = (now - at).total_seconds()
        if at.utcoffset() is None or not 0 <= age <= max_age_seconds:
            blockers.append('ACCOUNT_STALE_OR_FUTURE')
    except (TypeError, ValueError):
        blockers.append('ACCOUNT_TIME_UNKNOWN')
    if account.get('pending_reconciled') is not True:
        blockers.append('PENDING_ACTIVITY_UNRECONCILED')
    if rule.get('buying_power_basis_verified') is not True:
        blockers.append('LIMIT_DENOMINATOR_UNVERIFIED')
    if action.get('side') != 'SHORT' or type(action.get('shares')) is not int or action['shares'] < 10:
        blockers.append('INVALID_SHORT_OPEN_QUANTITY')
    ticker = action.get('ticker')
    if not isinstance(ticker, str) or not ticker.strip():
        blockers.append('SECURITY_UNKNOWN')
    else:
        ticker = ticker.strip().upper()
    values = {}
    for name, value in (
        ('price', action.get('reference_price')),
        ('buying_power', account.get('rule_buying_power')),
        ('existing', account.get('security_exposure', {}).get(ticker)),
        ('pending', account.get('pending_open_exposure', {}).get(ticker)),
        ('limit', rule.get('single_security_fraction')),
    ):
        try:
            if isinstance(value, bool):
                raise ValueError()
            number = Decimal(str(value))
            if not number.is_finite() or number < 0:
                raise ValueError()
            values[name] = number
        except (InvalidOperation, ValueError):
            blockers.append(name.upper() + '_UNKNOWN_OR_INVALID')
    ceiling = projected = None
    if len(values) == 5:
        if values['price'] < 3 or values['buying_power'] <= 0 or not 0 < values['limit'] <= 1:
            blockers.append('INVALID_PRICE_OR_LIMIT_BASIS')
        elif 'INVALID_SHORT_OPEN_QUANTITY' not in blockers:
            ceiling = values['buying_power'] * values['limit']
            projected = values['existing'] + values['pending'] + values['price'] * action['shares']
            if projected > ceiling:
                blockers.append('SINGLE_SECURITY_LIMIT_EXCEEDED')
    return dict(status='BLOCKED' if blockers else 'PREPARATION_CHECK_PASSED',
                blockers=sorted(set(blockers)),
                projected_exposure=str(projected) if projected is not None else None,
                ceiling=str(ceiling) if ceiling is not None else None,
                submission_authorized=False)


def assess_preparation(action, account, rule, now, max_age_seconds, observations):
    result = assess_short(action, account, rule, now, max_age_seconds)
    ticker = action.get('ticker')
    if not isinstance(ticker, str) or not ticker.strip():
        return result
    ticker = ticker.strip().upper()
    indication = execution_evidence(ticker, now.isoformat(), action.get('reference_price'), observations)
    result['blockers'].extend(indication['rejected'] + indication['missing'])
    session = now.astimezone(ZoneInfo('America/New_York')).date()
    bounds = session_bounds(session)
    if bounds is None or not bounds[0] <= now < bounds[1]:
        result['blockers'].append('OUTSIDE_REGULAR_DECISION_SESSION')
    if bounds:
        previous = calendar(session.year).previous_session(session.isoformat()).date()
        prior = latest_known(observations, 'prior_close', ticker, now)
        value = (prior or {}).get('value', {})
        try:
            price = Decimal(str(value.get('price')))
            valid_price = price.is_finite() and price >= 3 and not isinstance(value.get('price'), bool)
        except InvalidOperation:
            valid_price = False
        expected_close = session_bounds(previous)[1]
        if (not prior or not prior.get('source') or value.get('status') != 'VERIFIED'
                or value.get('session_date') != previous.isoformat()
                or stamp(value.get('close_at')) != expected_close or not valid_price):
            result['blockers'].append('PRIOR_SESSION_PRICE_UNVERIFIED_OR_INELIGIBLE')
    for kind in ('quote', 'smg_short_permission', 'corporate_actions'):
        row = latest_known(observations, kind, ticker, now, max_age_seconds)
        value = (row or {}).get('value', {})
        if not row or not row.get('source') or value.get('status') != 'VERIFIED':
            result['blockers'].append(kind.upper() + '_EVIDENCE_MISSING')
            continue
        if kind == 'quote':
            source_at = stamp(value.get('source_timestamp'))
            if source_at is None or not 0 <= (now-source_at).total_seconds() <= max_age_seconds:
                result['blockers'].append('QUOTE_SOURCE_STALE_OR_FUTURE')
            try:
                equal = Decimal(str(value.get('price'))) == Decimal(str(action.get('reference_price')))
            except InvalidOperation:
                equal = False
            if not equal:
                result['blockers'].append('QUOTE_REFERENCE_MISMATCH')
        elif value.get('allowed' if kind == 'smg_short_permission' else 'clear') is not True:
            result['blockers'].append(kind.upper() + '_UNRESOLVED')
    result['blockers'] = sorted(set(result['blockers']))
    result['status'] = 'BLOCKED' if result['blockers'] else 'PREPARATION_CHECK_PASSED'
    result['execution_indication'] = indication
    return result
