"""One private execution-queue cycle; disabled unless all authority gates pass.

Consumes explicit approved decisions, not raw ranks. It does not invent
standing exit rules, generate a strategy, or replace the Portfolio Desk.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .execution_controller import ExecutionController, activation_blockers, management_queue
from .order_intents import IntentJournal
from .tinyfish_execution import TinyFishCLI


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def cycle(config, adapter=None, now=None):
    clock = (lambda: now) if now is not None else (lambda: datetime.now(timezone.utc))
    now = clock()
    root = Path(config['private_directory'])
    root.mkdir(parents=True, exist_ok=True)
    lock = root / 'cycle.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return dict(status='EXISTING_CYCLE_LOCK_REQUIRES_INSPECTION', orders_submitted=0)
    os.close(descriptor)
    journal = None
    try:
        authority = load(config['authority_file'])
        account = load(config['account_file'])
        policies = load(config['management_policies_file'])
        result = dict(observed_at=now.isoformat(), orders_submitted=0, submission_attempts=0,
                      management=management_queue(account, policies, now), events=[])
        blockers = activation_blockers(authority, now, config['owner_id'])
        if blockers:
            result.update(status='ACTIVATION_BLOCKED', blockers=blockers)
            return result
        journal = IntentJournal(root/'intents.sqlite')
        adapter = adapter or TinyFishCLI(**load(config['adapter_file']))
        queue = sorted(Path(config['decisions_directory']).glob('*.json'))
        unresolved = journal.unresolved(config['account_scope'])
        if not unresolved and not queue:
            result.update(status='NO_APPROVED_DECISIONS')
            return result
        if adapter.wallet_balance() <= 0:
            result.update(status='BROWSER_UNFUNDED', blockers=['TINYFISH_WALLET_EMPTY'])
            return result
        ctl = ExecutionController(journal, adapter, config['owner_id'], config['account_scope'], clock)
        # Reconcile first. Pending/unknown outcomes remain position-locked;
        # no second submit attempt is made for a previously claimed intent.
        for intent in unresolved:
            try:
                status = ctl.reconcile(intent)['state']
                result['events'].append(dict(intent_id=intent, status=status))
            except Exception as error:
                result['events'].append(dict(intent_id=intent, status='RECONCILIATION_UNRESOLVED',
                                             error_type=type(error).__name__))
        for path in queue:
            envelope = load(path)
            decision = envelope['decision']
            intent = decision['decision_id']
            try:
                existing = journal.get(intent)
            except KeyError:
                existing = None
            if existing:
                result['events'].append(dict(intent_id=intent, status=existing['state'], retried=False))
                continue
            prepared = ctl.prepare(decision, account, envelope.get('game_rule', {}),
                                   envelope.get('observations', []), authority)
            result['events'].append(prepared)
            if prepared['status'] != 'PREPARED':
                continue
            # One new browser submission attempt per cycle. Keep the remaining
            # queue for another fresh decision/account review.
            try:
                state = ctl.submit(intent, authority)['state']
                result['events'].append(dict(intent_id=intent, status=state))
            except Exception as error:
                result['events'].append(dict(intent_id=intent, status='SUBMISSION_UNRESOLVED',
                                             error_type=type(error).__name__))
            state = journal.get(intent)['state']
            result['submission_attempts'] = int(any(e['state']=='SUBMITTING' for e in journal.history(intent)))
            result['orders_submitted'] = (1 if state in ('PENDING', 'CONFIRMED') else
                                          None if state in ('SUBMITTING', 'UNKNOWN') else 0)
            break
        result.update(status='CYCLE_COMPLETED', submission_attempts_may_be_unresolved=True)
        return result
    finally:
        if journal:
            journal.close()
        try:
            if 'result' in locals():
                with (root/'service-history.jsonl').open('a', encoding='utf-8') as output:
                    output.write(json.dumps(result)+'\n')
                temporary = root/'service-status.json.tmp'
                temporary.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
                os.replace(temporary, root/'service-status.json')
        finally:
            lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(cycle(load(args.config))))


if __name__ == '__main__':
    main()
