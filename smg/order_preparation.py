"""Offline preparation assessment using supplied, source-backed account facts."""
from datetime import datetime
from decimal import Decimal, InvalidOperation


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
