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
    second.reconcile('unique-1', 'PENDING', {'platform_record': 'test-pending-1', 'filled_shares': 0, 'remaining_shares': 10})
    second.reconcile('unique-1', 'CONFIRMED', {'platform_record': 'test-fill-1', 'filled_shares': 10, 'remaining_shares': 0})
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
    first.reconcile('a', 'PENDING', {'platform_record': 'pending', 'filled_shares': 0, 'remaining_shares': 10})
    assert not second.claim_submission('b', 'same-account')
    first.reconcile('a', 'REJECTED', {'platform_record': 'rejected', 'filled_shares': 0, 'remaining_shares': 0})
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


def test_partial_fill_retains_lock_and_cannot_regress(tmp_path):
    journal = IntentJournal(tmp_path / 'intents.sqlite')
    action = dict(ticker='TEST', side='SHORT', shares=10)
    journal.prepare('a', action)
    journal.prepare('b', action)
    assert journal.claim_submission('a', 'account')
    journal.reconcile('a', 'PARTIAL', dict(platform_record='partial', filled_shares=4, remaining_shares=6))
    assert not journal.claim_submission('b', 'account')
    with pytest.raises(ValueError, match='cumulative'):
        journal.reconcile('a', 'PARTIAL', dict(platform_record='stale', filled_shares=3, remaining_shares=7))
    with pytest.raises(ValueError, match='complete'):
        journal.reconcile('a', 'CONFIRMED', dict(platform_record='incomplete', filled_shares=4, remaining_shares=0))
    with pytest.raises(ValueError, match='Rejection'):
        journal.reconcile('a', 'REJECTED', dict(platform_record='cancelled-remainder', filled_shares=4, remaining_shares=0))
    assert journal.get('a')['state'] == 'PARTIAL'
    journal.reconcile('a', 'CONFIRMED', dict(platform_record='filled', filled_shares=10, remaining_shares=0))
    assert journal.claim_submission('b', 'account')
    journal.close()


def test_stale_same_state_update_cannot_overwrite_new_receipt(tmp_path):
    journal = IntentJournal(tmp_path / 'intents.sqlite')
    journal.prepare('a', dict(ticker='TEST', side='SHORT', shares=10))
    assert journal.claim_submission('a', 'account')
    earlier = dict(platform_record='p1', filled_shares=2, remaining_shares=8)
    later = dict(platform_record='p2', filled_shares=4, remaining_shares=6)
    journal.reconcile('a', 'PARTIAL', earlier)
    journal.reconcile('a', 'PARTIAL', later)
    with pytest.raises(ValueError, match='Concurrent'):
        journal._transition('a', 'PARTIAL', 'PARTIAL', earlier, earlier)
    assert journal.get('a')['evidence'] == later
    journal.close()


def test_cancelled_remainder_preserves_fills_across_restart(tmp_path):
    path = tmp_path / 'intents.sqlite'
    journal = IntentJournal(path)
    action = dict(ticker='TEST', side='SHORT', shares=10)
    journal.prepare('a', action)
    journal.prepare('b', action)
    assert journal.claim_submission('a', 'account')
    journal.reconcile('a', 'PARTIAL', dict(platform_record='partial', filled_shares=4, remaining_shares=6))
    with pytest.raises(ValueError, match='Cancellation'):
        journal.reconcile('a', 'CANCELLED', dict(platform_record='pending-cancel', filled_shares=4, remaining_shares=6))
    assert not journal.claim_submission('b', 'account')
    journal.reconcile('a', 'CANCELLED', dict(platform_record='cancelled', filled_shares=4, remaining_shares=0))
    journal.close()
    journal = IntentJournal(path)
    current = journal.get('a')
    assert current['state'] == 'CANCELLED'
    assert current['action']['shares'] == 10
    assert current['evidence']['filled_shares'] == 4
    assert [event['state'] for event in journal.history('a')] == [
        'PREPARED', 'SUBMITTING', 'PARTIAL', 'CANCELLED']
    assert journal.history('a')[2]['evidence']['remaining_shares'] == 6
    assert not journal.claim_submission('a', 'account')
    assert journal.claim_submission('b', 'account')
    journal.close()


def test_failed_history_write_rolls_back_state_and_position_claim(tmp_path):
    journal = IntentJournal(tmp_path / 'intents.sqlite')
    journal.prepare('a', dict(ticker='TEST', side='SHORT', shares=10))
    journal.connection.execute("""CREATE TRIGGER fail_events BEFORE INSERT ON intent_events
        BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
    assert not journal.claim_submission('a', 'account')
    assert journal.get('a')['state'] == 'PREPARED'
    assert journal.connection.execute('SELECT count(*) FROM position_claims').fetchone()[0] == 0
    assert len(journal.history('a')) == 1
    journal.close()


def test_legacy_history_snapshot_is_explicit_and_not_duplicated(tmp_path):
    path = tmp_path / 'intents.sqlite'
    journal = IntentJournal(path)
    journal.prepare('old', dict(ticker='TEST', side='SHORT', shares=10))
    journal.connection.execute('DELETE FROM intent_events')
    journal.connection.execute("UPDATE intents SET state='UNKNOWN' WHERE intent_id='old'")
    journal.close()
    for _ in range(2):
        journal = IntentJournal(path)
        events = journal.history('old')
        assert len(events) == 1
        assert events[0]['state'] == 'MIGRATION_SNAPSHOT:UNKNOWN'
        journal.close()


