import json

from smg.execution_service import cycle
from tests.test_execution_controller import facts, NOW, Adapter


def fixture(tmp_path, enabled=True):
    decision, account, authority = facts()
    authority['enabled'] = enabled
    for name, value in [('authority', authority), ('account', account), ('management', {})]:
        (tmp_path/f'{name}.json').write_text(json.dumps(value))
    queue = tmp_path/'queue';queue.mkdir()
    (queue/'decision.json').write_text(json.dumps(dict(decision=decision)))
    return dict(private_directory=str(tmp_path/'private'), authority_file=str(tmp_path/'authority.json'),
                account_file=str(tmp_path/'account.json'), management_policies_file=str(tmp_path/'management.json'),
                decisions_directory=str(queue), owner_id='synthetic-owner', account_scope='synthetic-account')


def test_disarmed_cycle_does_no_browser_work(tmp_path):
    class NeverCall:
        def wallet_balance(self):raise AssertionError('No network expected')
    result=cycle(fixture(tmp_path, False), NeverCall(), NOW)
    assert result['status']=='ACTIVATION_BLOCKED'
    assert result['orders_submitted']==0


def test_unfunded_browser_never_claims_or_submits(tmp_path):
    class EmptyWallet(Adapter):
        def wallet_balance(self):return 0
    adapter=EmptyWallet()
    result=cycle(fixture(tmp_path),adapter,NOW)
    assert result['status']=='BROWSER_UNFUNDED'
    assert adapter.calls==0


def test_repeat_cycle_reconciles_without_resubmitting_same_intent(tmp_path):
    class Funded(Adapter):
        def wallet_balance(self):return 10
    adapter=Funded();config=fixture(tmp_path)
    first=cycle(config,adapter,NOW)
    assert first['orders_submitted']==1
    second=cycle(config,adapter,NOW)
    assert second['orders_submitted']==0
    assert adapter.calls==1


def test_existing_lock_is_not_automatically_removed(tmp_path):
    config=fixture(tmp_path)
    from pathlib import Path
    root=Path(config['private_directory']);root.mkdir()
    (root/'cycle.lock').write_text('synthetic prior process or crash')
    assert cycle(config,None,NOW)['status']=='EXISTING_CYCLE_LOCK_REQUIRES_INSPECTION'
    assert (root/'cycle.lock').exists()


def test_ambiguous_submit_is_not_reported_as_zero_orders(tmp_path):
    class Ambiguous(Adapter):
        fail=True
        def wallet_balance(self):return 10
    result=cycle(fixture(tmp_path),Ambiguous(),NOW)
    assert result['orders_submitted'] is None
    assert result['submission_attempts']==1
