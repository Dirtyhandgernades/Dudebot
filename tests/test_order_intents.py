import sqlite3

import pytest

from smg.order_intents import IntentJournal


def test_restart_ambiguity_and_duplicate_claim(tmp_path):
    path = tmp_path / 'intents.sqlite'
    first = IntentJournal(path)
    first.prepare('unique-1', dict(ticker='TEST', side='SHORT', shares=10))
    second = IntentJournal(path)
    assert first.claim_submission('unique-1', 'test-account')
    assert not second.claim_submission('unique-1', 'test-account')
    first.record_uncertain('unique-1', {'reason': 'timeout'})
    first.close()
    assert second.get('unique-1')['state'] == 'UNKNOWN'
    assert not second.claim_submission('unique-1', 'test-account')
    with pytest.raises(sqlite3.IntegrityError):
        second.prepare('unique-1', dict(ticker='TEST', side='SHORT', shares=10))
    second.reconcile('unique-1', 'PENDING', {'platform_record': 'test-pending-1'})
    second.reconcile('unique-1', 'CONFIRMED', {'platform_record': 'test-fill-1'})
    assert second.get('unique-1')['state'] == 'CONFIRMED'
    assert not second.claim_submission('unique-1', 'test-account')
    second.close()


def test_confirmation_requires_platform_evidence(tmp_path):
    journal = IntentJournal(tmp_path / 'intents.sqlite')
    journal.prepare('id', dict(ticker='TEST', side='COVER', shares=10))
    assert journal.claim_submission('id', 'test-account')
    with pytest.raises(ValueError, match='record'):
        journal.reconcile('id', 'CONFIRMED', {})
    assert journal.get('id')['state'] == 'SUBMITTING'
    journal.close()


def test_different_ids_share_position_lock_until_reconciled(tmp_path):
    path = tmp_path / 'intents.sqlite'
    first = IntentJournal(path)
    second = IntentJournal(path)
    first.prepare('a', dict(ticker='test', side='SHORT', shares=10))
    second.prepare('b', dict(ticker='TEST', side='COVER', shares=10))
    assert first.claim_submission('a', 'same-account')
    assert not second.claim_submission('b', 'same-account')
    first.record_uncertain('a', {'reason': 'connection lost'})
    assert not second.claim_submission('b', 'same-account')
    first.reconcile('a', 'PENDING', {'platform_record': 'pending'})
    assert not second.claim_submission('b', 'same-account')
    first.reconcile('a', 'REJECTED', {'platform_record': 'rejected'})
    assert second.claim_submission('b', 'same-account')
    first.close()
    second.close()


def test_account_scope_required(tmp_path):
    journal = IntentJournal(tmp_path / 'intents.sqlite')
    journal.prepare('id', dict(ticker='TEST', side='SHORT', shares=10))
    with pytest.raises(ValueError, match='scope'):
        journal.claim_submission('id')
    assert journal.get('id')['state'] == 'PREPARED'
    journal.close()


def test_legacy_uncertain_intent_blocks_new_position(tmp_path):
    journal = IntentJournal(tmp_path / 'intents.sqlite')
    action = dict(ticker='TEST', side='SHORT', shares=10)
    journal.prepare('legacy', action)
    journal.connection.execute("UPDATE intents SET state='UNKNOWN' WHERE intent_id='legacy'")
    journal.prepare('new', action)
    assert not journal.claim_submission('new', 'account')
    journal.close()

