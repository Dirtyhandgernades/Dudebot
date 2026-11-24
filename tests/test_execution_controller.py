from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from smg.execution_controller import ExecutionController, AUTHORITY_GATES, digest, management_queue
from smg.order_intents import IntentJournal
from smg.order_preparation import assess_reduction

NOW = datetime(2026, 11, 24, 19, 30, tzinfo=timezone.utc)


def facts():
    account = dict(account_scope='synthetic-account', observed_at=NOW.isoformat(), source_record='synthetic-live-read',
                   holdings_complete=True, pending_reconciled=True, pending_orders=[],
                   positions=[dict(ticker='TEST', side='short', shares=100, status='open',
                                   instrument_type='STOCK', corporate_actions_clear=True, halt_clear=True)])
    rules = dict(allowed_sides=['COVER', 'SELL'], allowed_reason_kinds=['TEST_EXIT'],
                 max_shares_per_order=100, max_estimated_notional=1000)
    authority = dict(enabled=True, account_scope='synthetic-account', owner_id='synthetic-owner',
                     expires_at=(NOW+timedelta(hours=1)).isoformat(), approved_policies={'synthetic-policy': digest(rules)})
    authority.update({gate: dict(verified=True, verified_at=NOW.isoformat(), source_record='synthetic-permission')
                      for gate in AUTHORITY_GATES})
    decision = dict(decision_id='test-intent', created_at=NOW.isoformat(),
                    expires_at=(NOW+timedelta(minutes=10)).isoformat(), source_record='synthetic-decision',
                    reason_kind='TEST_EXIT', reason_source_record='synthetic-exit-evidence',
                    quote_source_at=NOW.isoformat(), quote_source_record='synthetic-quote',
                    action=dict(ticker='TEST', side='COVER', shares=10, reference_price=2),
                    account_snapshot_sha256=digest(account),
                    policy=dict(id='synthetic-policy', execution_approved=True, source_record='synthetic-standing-policy',
                                rules=rules, policy_sha256=digest(rules)))
    return decision, account, authority


class Adapter:
    calls = 0
    fail = False

    def submit(self, action, intent, deadline):
        self.calls += 1
        if self.fail:
            raise TimeoutError('synthetic ambiguous timeout')
        return self.response(action)

    def response(self, action, status='PENDING', reference='synthetic-confirmation'):
        return dict(request={'run_id': 'synthetic-run'}, result=dict(
            ticker=action['ticker'], side=action['side'], shares=action['shares'],
            status=status, confirmation_id=reference, platform_status='Pending', record_text='synthetic exact pending row',
            source_url='https://www.stockmarketgame.org/po.html', observed_at=NOW.isoformat(),
            filled_shares=0, remaining_shares=action['shares'], executed_price=''))

    def reconcile(self, action, intent, reference):
        result = self.response(action, 'CONFIRMED', reference)
        result['result'].update(platform_status='Order Executed', filled_shares=action['shares'], remaining_shares=0,
                                executed_price='2.01', source_url='https://www.stockmarketgame.org/tnotes.html')
        return result


def controller(tmp_path, adapter=None):
    journal = IntentJournal(tmp_path/'intents.sqlite')
    return ExecutionController(journal, adapter or Adapter(), 'synthetic-owner', 'synthetic-account', lambda: NOW)


def test_actual_call_is_once_pending_is_not_filled_then_exact_note_confirms(tmp_path):
    decision, account, authority = facts()
    ctl = controller(tmp_path)
    assert ctl.prepare(decision, account, {}, [], authority)['status'] == 'PREPARED'
    assert ctl.submit('test-intent', authority)['state'] == 'PENDING'
    assert ctl.submit('test-intent', authority)['status'] == 'RECONCILIATION_REQUIRED'
    assert ctl.adapter.calls == 1
    assert ctl.reconcile('test-intent')['state'] == 'CONFIRMED'


@pytest.mark.parametrize('gate', AUTHORITY_GATES)
def test_each_missing_permission_blocks_before_any_submission(tmp_path, gate):
    decision, account, authority = facts()
    authority[gate]['verified'] = False
    ctl = controller(tmp_path)
    result = ctl.prepare(decision, account, {}, [], authority)
    assert result['status'] == 'BLOCKED'
    assert gate.upper()+'_UNVERIFIED' in result['blockers']
    assert ctl.adapter.calls == 0


@pytest.mark.parametrize('fault', ['scope', 'stale', 'pending', 'overclose', 'policy', 'notional', 'self_authorized'])
def test_account_position_and_policy_failures_cannot_create_a_ticket(tmp_path, fault):
    decision, account, authority = facts()
    if fault == 'scope':
        account['account_scope'] = 'another-account'
    elif fault == 'stale':
        account['observed_at'] = (NOW-timedelta(minutes=6)).isoformat()
    elif fault == 'pending':
        account['pending_orders'] = [dict(ticker='TEST')]
    elif fault == 'overclose':
        decision['action']['shares'] = 101
    elif fault == 'policy':
        decision['policy']['source_record'] = ''
    elif fault == 'notional':
        decision['action']['reference_price'] = 1000
    else:
        authority['approved_policies'] = {}
    decision['account_snapshot_sha256'] = digest(account)
    ctl = controller(tmp_path)
    assert ctl.prepare(decision, account, {}, [], authority)['status'] == 'BLOCKED'
    assert ctl.adapter.calls == 0


def test_timeout_keeps_position_locked_across_new_intent_ids(tmp_path):
    decision, account, authority = facts()
    adapter = Adapter(); adapter.fail = True
    ctl = controller(tmp_path, adapter)
    ctl.prepare(decision, account, {}, [], authority)
    with pytest.raises(TimeoutError):
        ctl.submit('test-intent', authority)
    assert ctl.journal.get('test-intent')['state'] == 'UNKNOWN'
    second = deepcopy(decision); second['decision_id'] = 'second-intent'
    ctl.prepare(second, account, {}, [], authority)
    assert ctl.submit('second-intent', authority)['status'] == 'RECONCILIATION_REQUIRED'
    assert adapter.calls == 1


def test_changed_authority_or_stale_preparation_requires_new_review(tmp_path):
    decision, account, authority = facts()
    ctl = controller(tmp_path)
    ctl.prepare(decision, account, {}, [], authority)
    ctl.clock = lambda: NOW+timedelta(seconds=31)
    with pytest.raises(ValueError, match='PREPARATION_EXPIRED'):
        ctl.submit('test-intent', authority)
    assert ctl.adapter.calls == 0


@pytest.mark.parametrize('fault', ['reference', 'partial', 'price', 'page', 'status'])
def test_bad_execution_receipt_keeps_pending_lock(tmp_path, fault):
    decision, account, authority = facts()
    ctl = controller(tmp_path); ctl.prepare(decision, account, {}, [], authority)
    ctl.submit('test-intent', authority)
    result = ctl.adapter.reconcile(decision['action'], 'test-intent', 'synthetic-confirmation')
    row = result['result']
    if fault == 'reference': row['confirmation_id'] = 'some-old-order'
    elif fault == 'partial': row.update(filled_shares=5, remaining_shares=5)
    elif fault == 'price': row['executed_price'] = ''
    elif fault == 'page': row['source_url'] = 'https://www.stockmarketgame.org/po.html'
    else: row['platform_status'] = 'button clicked'
    with pytest.raises(ValueError): ctl._apply('test-intent', result, 'synthetic-confirmation')
    assert ctl.journal.get('test-intent')['state'] == 'PENDING'


def test_sub_three_dollar_and_less_than_ten_share_reductions_are_valid_but_bonds_are_not():
    decision, account, _ = facts()
    action = dict(ticker='TEST', side='COVER', shares=1, reference_price=1)
    assert assess_reduction(action, account, NOW, 300)['status'] == 'PREPARATION_CHECK_PASSED'
    account['positions'][0].update(instrument_type='BOND', shares=None)
    assert assess_reduction(action, account, NOW, 300)['status'] == 'BLOCKED'


def test_every_position_gets_review_status_without_inventing_exit_rules():
    _, account, _ = facts()
    result = management_queue(account, {}, NOW)
    assert result['positions'][0]['status'] == 'EXIT_POLICY_REQUIRED'
    assert not result['positions'][0]['automatic_order_created']


def test_new_queue_generation_does_not_refresh_old_account_observations():
    _, account, _ = facts()
    account['observed_at']=(NOW-timedelta(hours=4)).isoformat()
    result=management_queue(account,{},NOW)
    assert not result['account_current']
    assert result['account_observed_at']==account['observed_at']
    assert result['account_age_seconds']==14400


def test_unbound_old_executed_note_cannot_confirm_new_submission(tmp_path):
    decision, account, authority=facts()
    class OldNote(Adapter):
        def submit(self,action,intent,deadline):return self.reconcile(action,intent,'old-confirmation')
    ctl=controller(tmp_path,OldNote());ctl.prepare(decision,account,{},[],authority)
    with pytest.raises(ValueError,match='PREVIOUSLY_BOUND'):
        ctl.submit('test-intent',authority)
    assert ctl.journal.get('test-intent')['state']=='UNKNOWN'
