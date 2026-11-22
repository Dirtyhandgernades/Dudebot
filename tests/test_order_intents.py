import sqlite3

import pytest

from smg.order_intents import IntentJournal


def test_restart_ambiguity_and_duplicate_claim(tmp_path):
    path = tmp_path / 'intents.sqlite'
    first = IntentJournal(path)
    first.prepare('unique-1', dict(ticker='TEST', side='SHORT', shares=10))
    second = IntentJournal(path)
    assert first.claim_submission('unique-1')
    assert not second.claim_submission('unique-1')
    first.record_uncertain('unique-1', {'reason': 'timeout'})
    first.close()
    assert second.get('unique-1')['state'] == 'UNKNOWN'
    assert not second.claim_submission('unique-1')
    with pytest.raises(sqlite3.IntegrityError):
        second.prepare('unique-1', dict(ticker='TEST', side='SHORT', shares=10))
    second.reconcile('unique-1', 'PENDING', {'platform_record': 'test-pending-1'})
    second.reconcile('unique-1', 'CONFIRMED', {'platform_record': 'test-fill-1'})
    assert second.get('unique-1')['state'] == 'CONFIRMED'
    assert not second.claim_submission('unique-1')
    second.close()


def test_confirmation_requires_platform_evidence(tmp_path):
    journal = IntentJournal(tmp_path / 'intents.sqlite')
    journal.prepare('id', dict(ticker='TEST', side='COVER', shares=10))
    assert journal.claim_submission('id')
    with pytest.raises(ValueError, match='record'):
        journal.reconcile('id', 'CONFIRMED', {})
    assert journal.get('id')['state'] == 'SUBMITTING'
    journal.close()
