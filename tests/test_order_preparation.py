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
