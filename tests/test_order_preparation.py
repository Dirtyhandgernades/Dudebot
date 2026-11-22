from datetime import datetime, timezone

from smg.order_preparation import assess_short, assess_preparation


def test_existing_and_pending_exposure_count_toward_limit():
    now = datetime(2026, 11, 23, 20, 30, tzinfo=timezone.utc)
    action = dict(ticker='TEST', side='SHORT', shares=100, reference_price=10)
    account = dict(source_record='fixture', observed_at=now.isoformat(), pending_reconciled=True,
                   rule_buying_power=100000, security_exposure={'TEST': 18000},
                   pending_open_exposure={'TEST': 1500})
    rule = dict(source_record='fixture-rule', buying_power_basis_verified=True,
                single_security_fraction='.20')
    result = assess_short(action, account, rule, now, 60)
    assert result['projected_exposure'] == '20500'
    assert 'SINGLE_SECURITY_LIMIT_EXCEEDED' in result['blockers']
    account['pending_open_exposure']['TEST'] = 1000
    assert assess_short(action, account, rule, now, 60)['status'] == 'PREPARATION_CHECK_PASSED'
    assert not result['submission_authorized']


def test_missing_pending_and_unverified_denominator_block():
    now = datetime(2026, 11, 23, 20, 30, tzinfo=timezone.utc)
    result = assess_short(dict(ticker='TEST', side='SHORT', shares=10, reference_price=10),
                          dict(observed_at=now.isoformat()), {}, now, 60)
    assert 'PENDING_ACTIVITY_UNRECONCILED' in result['blockers']
    assert 'LIMIT_DENOMINATOR_UNVERIFIED' in result['blockers']
    assert 'PENDING_UNKNOWN_OR_INVALID' in result['blockers']


def test_recent_receipt_cannot_refresh_stale_quote_source():
    now = datetime(2026, 11, 23, 20, 30, tzinfo=timezone.utc)
    rows = [dict(kind='quote', subject='TEST', source='fixture', observed_at=now.isoformat(),
                 value=dict(status='VERIFIED', price=10, source_timestamp='2026-11-23T20:00:00Z'))]
    result = assess_preparation(dict(ticker='TEST', side='SHORT', shares=10, reference_price=10),
                                {}, {}, now, 60, rows)
    assert 'QUOTE_SOURCE_STALE_OR_FUTURE' in result['blockers']
    assert 'SMG_SHORT_PERMISSION_EVIDENCE_MISSING' in result['blockers']
    assert not result['submission_authorized']


def test_prior_close_uses_exchange_holiday_and_source_session():
    now = datetime(2026, 11, 27, 17, 30, tzinfo=timezone.utc)
    row = dict(kind='prior_close', subject='TEST', source='fixture', observed_at=now.isoformat(),
               value=dict(status='VERIFIED', price=10, session_date='2026-11-25',
                          close_at='2026-11-25T21:00:00Z'))
    action = dict(ticker='TEST', side='SHORT', shares=10, reference_price=10)
    result = assess_preparation(action, {}, {}, now, 60, [row])
    assert 'PRIOR_SESSION_PRICE_UNVERIFIED_OR_INELIGIBLE' not in result['blockers']
    row['value']['session_date'] = '2026-11-26'
    result = assess_preparation(action, {}, {}, now, 60, [row])
    assert 'PRIOR_SESSION_PRICE_UNVERIFIED_OR_INELIGIBLE' in result['blockers']


def test_preparation_blocks_after_short_session_close():
    now = datetime(2026, 11, 27, 19, 0, tzinfo=timezone.utc)
    result = assess_preparation(dict(ticker='TEST', side='SHORT', shares=10, reference_price=10),
                                {}, {}, now, 60, [])
    assert 'OUTSIDE_REGULAR_DECISION_SESSION' in result['blockers']


def test_complete_synthetic_preparation_still_requires_submission_authorization():
    now = datetime(2026, 11, 23, 20, 30, tzinfo=timezone.utc)
    facts = dict(
        security=dict(exchange='NASDAQ', is_acquisition_corp=False, security_type='CS'),
        market_cap=dict(market_cap=50_000_000), halt=dict(halt_status='CLEAR'),
        borrow=dict(tradable=True, shortable=True, borrow_status='easy_to_borrow'),
        smg_membership=dict(allowed=True), smg_short_permission=dict(allowed=True),
        corporate_actions=dict(clear=True), quote=dict(price=10, source_timestamp=now.isoformat()),
        prior_close=dict(price=10, session_date='2026-11-20', close_at='2026-11-20T21:00:00Z'))
    rows = [dict(kind=kind, subject='TEST', source='synthetic-fixture',
                 observed_at=now.isoformat(), value=dict(status='VERIFIED', **value))
            for kind, value in facts.items()]
    account = dict(source_record='synthetic-account', observed_at=now.isoformat(),
                   pending_reconciled=True, rule_buying_power=100000,
                   security_exposure={'TEST': 0}, pending_open_exposure={'TEST': 0})
    rule = dict(source_record='synthetic-rule', buying_power_basis_verified=True,
                single_security_fraction='.20')
    result = assess_preparation(dict(ticker='TEST', side='SHORT', shares=10, reference_price=10),
                                account, rule, now, 60, rows)
    assert result['blockers'] == []
    assert result['status'] == 'PREPARATION_CHECK_PASSED'
    assert result['submission_authorized'] is False
