"""Durable simulated-order intent journal. Platform integration is external."""
import json
import sqlite3
from datetime import datetime, timezone


class IntentJournal:
    def __init__(self, path):
        self.connection = sqlite3.connect(path, isolation_level=None)
        self.connection.execute('''CREATE TABLE IF NOT EXISTS intents (
            intent_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
            state TEXT NOT NULL, evidence TEXT, updated_at TEXT NOT NULL)''')

    def close(self):
        self.connection.close()

    def prepare(self, intent_id, action):
        if not isinstance(intent_id, str) or not intent_id.strip():
            raise ValueError('Unique intent ID required')
        if action.get('side') not in ('SHORT', 'COVER'):
            raise ValueError('Unsupported simulated action')
        if type(action.get('shares')) is not int or action['shares'] <= 0:
            raise ValueError('Positive whole shares required')
        if not isinstance(action.get('ticker'), str) or not action['ticker'].strip():
            raise ValueError('Ticker required')
        payload = json.dumps(action, sort_keys=True, allow_nan=False)
        with self.connection:
            self.connection.execute('INSERT INTO intents VALUES (?, ?, ?, NULL, ?)',
                                    (intent_id, payload, 'PREPARED', self._now()))

    def claim_submission(self, intent_id):
        # A single atomic compare-and-set grants at most one submit attempt.
        cursor = self.connection.execute(
            "UPDATE intents SET state='SUBMITTING', updated_at=? "
            "WHERE intent_id=? AND state='PREPARED'", (self._now(), intent_id))
        return cursor.rowcount == 1

    def record_uncertain(self, intent_id, evidence):
        self._transition(intent_id, 'SUBMITTING', 'UNKNOWN', evidence)

    def reconcile(self, intent_id, status, evidence):
        if status not in ('PENDING', 'CONFIRMED', 'REJECTED'):
            raise ValueError('Explicit platform outcome required')
        if not isinstance(evidence, dict) or not evidence.get('platform_record'):
            raise ValueError('Platform record required')
        current = self.get(intent_id)
        if current['state'] not in ('SUBMITTING', 'UNKNOWN', 'PENDING'):
            raise ValueError('Intent requires reconciliation')
        self._transition(intent_id, current['state'], status, evidence)

    def get(self, intent_id):
        row = self.connection.execute(
            'SELECT payload, state, evidence FROM intents WHERE intent_id=?', (intent_id,)).fetchone()
        if row is None:
            raise KeyError(intent_id)
        return dict(action=json.loads(row[0]), state=row[1],
                    evidence=json.loads(row[2]) if row[2] else None)

    def _transition(self, intent_id, previous, state, evidence):
        receipt = json.dumps(evidence, sort_keys=True, allow_nan=False)
        cursor = self.connection.execute(
            'UPDATE intents SET state=?, evidence=?, updated_at=? WHERE intent_id=? AND state=?',
            (state, receipt, self._now(), intent_id, previous))
        if cursor.rowcount != 1:
            raise ValueError('Concurrent or invalid intent transition')

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()
