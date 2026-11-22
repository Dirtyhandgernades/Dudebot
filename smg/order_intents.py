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
        self.connection.execute('''CREATE TABLE IF NOT EXISTS position_claims (
            account_scope TEXT NOT NULL, ticker TEXT NOT NULL,
            intent_id TEXT NOT NULL UNIQUE,
            PRIMARY KEY (account_scope, ticker))''')
        self.connection.execute('''CREATE TABLE IF NOT EXISTS intent_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT, intent_id TEXT NOT NULL,
            state TEXT NOT NULL, evidence TEXT, observed_at TEXT NOT NULL)''')
        self.connection.execute('''INSERT INTO intent_events (intent_id,state,evidence,observed_at)
            SELECT intent_id,'MIGRATION_SNAPSHOT:' || state,evidence,
                strftime('%Y-%m-%dT%H:%M:%fZ','now') FROM intents
            WHERE NOT EXISTS (SELECT 1 FROM intent_events e WHERE e.intent_id=intents.intent_id)''')

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
        self.connection.execute('BEGIN IMMEDIATE')
        try:
            self.connection.execute('INSERT INTO intents VALUES (?, ?, ?, NULL, ?)',
                                    (intent_id, payload, 'PREPARED', self._now()))
            self._event(intent_id, 'PREPARED', None)
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def claim_submission(self, intent_id, account_scope=None):
        # A single atomic compare-and-set grants at most one submit attempt.
        if not isinstance(account_scope, str) or not account_scope.strip():
            raise ValueError('Private account scope required')
        self.connection.execute('BEGIN IMMEDIATE')
        try:
            current = self.get(intent_id)
            if current['state'] != 'PREPARED':
                self.connection.rollback()
                return False
            ticker = current['action']['ticker'].strip().upper()
            legacy = self.connection.execute(
                "SELECT payload FROM intents WHERE state IN ('SUBMITTING','UNKNOWN','PENDING','PARTIAL') "
                "AND intent_id NOT IN (SELECT intent_id FROM position_claims)").fetchall()
            if any(json.loads(row[0])['ticker'].strip().upper() == ticker for row in legacy):
                self.connection.rollback()
                return False
            self.connection.execute('INSERT INTO position_claims VALUES (?, ?, ?)',
                                    (account_scope, ticker, intent_id))
            self.connection.execute(
                "UPDATE intents SET state='SUBMITTING', updated_at=? WHERE intent_id=?",
                (self._now(), intent_id))
            self._event(intent_id, 'SUBMITTING', None)
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            self.connection.rollback()
            return False
        except Exception:
            self.connection.rollback()
            raise

    def record_uncertain(self, intent_id, evidence):
        self._transition(intent_id, 'SUBMITTING', 'UNKNOWN', evidence)

    def reconcile(self, intent_id, status, evidence):
        if status not in ('PENDING', 'PARTIAL', 'CONFIRMED', 'REJECTED', 'CANCELLED'):
            raise ValueError('Explicit platform outcome required')
        if not isinstance(evidence, dict) or not evidence.get('platform_record'):
            raise ValueError('Platform record required')
        current = self.get(intent_id)
        if current['state'] not in ('SUBMITTING', 'UNKNOWN', 'PENDING', 'PARTIAL'):
            raise ValueError('Intent requires reconciliation')
        filled = evidence.get('filled_shares')
        remaining = evidence.get('remaining_shares')
        total = current['action']['shares']
        if type(filled) is not int or type(remaining) is not int or min(filled, remaining) < 0:
            raise ValueError('Explicit whole-share fill quantities required')
        previous_filled = (current['evidence'] or {}).get('filled_shares', 0)
        if filled < previous_filled or filled + remaining > total:
            raise ValueError('Conflicting cumulative fill quantities')
        if status == 'CONFIRMED' and (filled != total or remaining != 0):
            raise ValueError('Confirmation requires complete intended fill')
        if status == 'REJECTED' and (filled != 0 or remaining != 0):
            raise ValueError('Rejection requires no fills or pending shares')
        if status == 'PARTIAL' and not (0 < filled < total and remaining == total - filled):
            raise ValueError('Partial fill requires unresolved remaining quantity')
        if status == 'PENDING' and (filled != 0 or remaining != total):
            raise ValueError('Pending requires full unfilled quantity')
        if status == 'CANCELLED' and (remaining != 0 or filled >= total):
            raise ValueError('Cancellation requires an ended unfilled remainder')
        self._transition(intent_id, current['state'], status, evidence, current['evidence'])

    def reconcile_smg(self, intent_id, status, evidence):
        """Apply SMG's published whole-fill semantics to adapter receipts."""
        current = self.get(intent_id)
        filled = evidence.get('filled_shares') if isinstance(evidence, dict) else None
        if status == 'PARTIAL' or (type(filled) is int and 0 < filled < current['action']['shares']):
            raise ValueError('Unexpected SMG partial fill; retain unresolved state and investigate')
        self.reconcile(intent_id, status, evidence)

    def get(self, intent_id):
        row = self.connection.execute(
            'SELECT payload, state, evidence FROM intents WHERE intent_id=?', (intent_id,)).fetchone()
        if row is None:
            raise KeyError(intent_id)
        return dict(action=json.loads(row[0]), state=row[1],
                    evidence=json.loads(row[2]) if row[2] else None)

    def _transition(self, intent_id, previous, state, evidence, previous_evidence=None):
        receipt = json.dumps(evidence, sort_keys=True, allow_nan=False)
        prior_receipt = (json.dumps(previous_evidence, sort_keys=True, allow_nan=False)
                         if previous_evidence is not None else None)
        self.connection.execute('BEGIN IMMEDIATE')
        try:
            cursor = self.connection.execute(
                'UPDATE intents SET state=?, evidence=?, updated_at=? WHERE intent_id=? AND state=? AND evidence IS ?',
                (state, receipt, self._now(), intent_id, previous, prior_receipt))
            if cursor.rowcount != 1:
                raise ValueError('Concurrent or invalid intent transition')
            self._event(intent_id, state, receipt)
            if state in ('CONFIRMED', 'REJECTED', 'CANCELLED'):
                self.connection.execute('DELETE FROM position_claims WHERE intent_id=?', (intent_id,))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def history(self, intent_id):
        self.get(intent_id)
        return [dict(sequence=row[0], state=row[1], evidence=json.loads(row[2]) if row[2] else None,
                     observed_at=row[3]) for row in self.connection.execute(
                         'SELECT sequence,state,evidence,observed_at FROM intent_events '
                         'WHERE intent_id=? ORDER BY sequence', (intent_id,))]

    def _event(self, intent_id, state, receipt):
        self.connection.execute(
            'INSERT INTO intent_events (intent_id,state,evidence,observed_at) VALUES (?, ?, ?, ?)',
            (intent_id, state, receipt, self._now()))

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()
