"""Single-owner SMG controller with durable intent and explicit activation gates.

No strategy is promoted here. Only source-bound decisions under a standing
policy can become orders; missing management rules produce review tasks.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from .decision_evidence import stamp
from .market import session_bounds
from .order_preparation import assess_preparation, assess_reduction
from .tinyfish_execution import action_fields
from zoneinfo import ZoneInfo


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


AUTHORITY_GATES = ('account_authorized', 'platform_method_allowed', 'competition_method_allowed',
                   'supported_confirmation_verified', 'sole_execution_owner_verified')


def activation_blockers(authority, now, owner_id):
    blockers = []
    if authority.get('enabled') is not True:
        blockers.append('EXECUTION_NOT_ENABLED')
    if authority.get('owner_id') != owner_id:
        blockers.append('EXECUTION_OWNER_MISMATCH')
    expires = stamp(authority.get('expires_at'))
    if expires is None or expires <= now:
        blockers.append('EXECUTION_AUTHORITY_EXPIRED_OR_MISSING')
    for gate in AUTHORITY_GATES:
        row = authority.get(gate, {})
        at = stamp(row.get('verified_at'))
        if row.get('verified') is not True or not row.get('source_record') or at is None or at > now:
            blockers.append(gate.upper() + '_UNVERIFIED')
    return sorted(set(blockers))


def management_queue(account, policies, now):
    """Expose every held security; unknown policy never becomes an invented exit."""
    output = []
    for ticker, side in sorted({(p['ticker'], p['side']) for p in account.get('positions', []) if p.get('status', 'open') == 'open'}):
        policy = policies.get(ticker + ':' + side)
        output.append(dict(ticker=ticker, position_side=side,
                           status='RULE_EVALUATION_REQUIRED' if policy and policy.get('source_record') else 'EXIT_POLICY_REQUIRED',
                           policy_id=(policy or {}).get('id'), automatic_order_created=False))
    at = stamp(account.get('observed_at'))
    age = (now-at).total_seconds() if at is not None else None
    return dict(generated_at=now.isoformat(), account_observed_at=account.get('observed_at'),
                account_age_seconds=age, account_current=age is not None and 0 <= age <= 300,
                positions=output, submission_authorized=False)


class ExecutionController:
    def __init__(self, journal, adapter, owner_id, account_scope, clock=None):
        self.journal, self.adapter = journal, adapter
        self.owner_id, self.account_scope = owner_id, account_scope
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def prepare(self, decision, account, rule, observations, authority, max_age_seconds=300):
        now = self.clock()
        if now.utcoffset() is None:
            raise ValueError('AWARE_CONTROLLER_CLOCK_REQUIRED')
        ticket = action_fields(decision['action'])
        action = dict(decision['action'], **ticket)
        blockers = activation_blockers(authority, now, self.owner_id)
        if account.get('account_scope') != self.account_scope or authority.get('account_scope') != self.account_scope:
            blockers.append('ACCOUNT_SCOPE_MISMATCH')
        policy = decision.get('policy', {})
        policy_hash = digest(policy.get('rules', {}))
        if (not policy.get('id') or not policy.get('source_record')
                or policy.get('execution_approved') is not True
                or policy.get('policy_sha256') != policy_hash
                or authority.get('approved_policies', {}).get(policy.get('id')) != policy_hash):
            blockers.append('STANDING_ACTION_POLICY_UNVERIFIED')
        limits = policy.get('rules', {})
        if (action['side'] not in limits.get('allowed_sides', [])
                or decision.get('reason_kind') not in limits.get('allowed_reason_kinds', [])
                or not decision.get('reason_source_record')):
            blockers.append('ACTION_OUTSIDE_APPROVED_POLICY')
        maximum = limits.get('max_shares_per_order')
        if type(maximum) is not int or not 0 < action['shares'] <= maximum:
            blockers.append('POLICY_ORDER_QUANTITY_EXCEEDED_OR_UNKNOWN')
        try:
            price, ceiling = Decimal(str(action.get('reference_price'))), Decimal(str(limits.get('max_estimated_notional')))
            if (not price.is_finite() or not ceiling.is_finite() or price <= 0 or ceiling <= 0
                    or isinstance(action.get('reference_price'), bool) or action['shares']*price > ceiling):
                raise ValueError()
        except (InvalidOperation, ValueError):
            blockers.append('POLICY_ESTIMATED_NOTIONAL_EXCEEDED_OR_UNKNOWN')
        quote_at = stamp(decision.get('quote_source_at'))
        if quote_at is None or not 0 <= (now-quote_at).total_seconds() <= max_age_seconds or not decision.get('quote_source_record'):
            blockers.append('DECISION_QUOTE_STALE_OR_UNSOURCED')
        at, expiry = stamp(decision.get('created_at')), stamp(decision.get('expires_at'))
        if at is None or expiry is None or not at <= now < expiry:
            blockers.append('DECISION_STALE_OR_FUTURE')
        if not decision.get('source_record') or decision.get('account_snapshot_sha256') != digest(account):
            blockers.append('DECISION_ACCOUNT_BINDING_MISMATCH')
        bounds = session_bounds(now.astimezone(ZoneInfo('America/New_York')).date())
        if bounds is None or not bounds[0] <= now < bounds[1] - timedelta(minutes=2):
            blockers.append('OUTSIDE_SMG_SUBMISSION_WINDOW')
        if action['side'] in ('SELL', 'COVER'):
            preparation = assess_reduction(action, account, now, max_age_seconds)
        elif action['side'] == 'SHORT':
            preparation = assess_preparation(action, account, rule, now, max_age_seconds, observations)
            if decision.get('qualified_entry') is not True:
                blockers.append('ENTRY_NOT_QUALIFIED')
        else:
            preparation = dict(blockers=['NEW_LONG_ENTRY_POLICY_NOT_CONNECTED'])
        blockers.extend(preparation['blockers'])
        if blockers:
            return dict(status='BLOCKED', blockers=sorted(set(blockers)), submission_authorized=False)
        payload = dict(action, decision_id=decision['decision_id'], policy_id=policy['id'],
                       decision_sha256=digest(decision), account_snapshot_sha256=digest(account),
                       authority_sha256=digest(authority), account_scope=self.account_scope,
                       prepared_at=now.isoformat(),
                       submit_start_by=min(stamp(account['observed_at']) + timedelta(seconds=max_age_seconds),
                                           quote_at + timedelta(seconds=max_age_seconds),
                                           now + timedelta(seconds=30), expiry).isoformat(),
                       deadline=min(expiry, bounds[1]-timedelta(minutes=2)).isoformat())
        self.journal.prepare(decision['decision_id'], payload)
        return dict(status='PREPARED', intent_id=decision['decision_id'], submission_authorized=False)

    def submit(self, intent_id, authority):
        now = self.clock()
        if activation_blockers(authority, now, self.owner_id):
            raise ValueError('EXECUTION_AUTHORITY_BLOCKED')
        current = self.journal.get(intent_id)
        action = current['action']
        if digest(authority) != action.get('authority_sha256') or action.get('account_scope') != self.account_scope:
            raise ValueError('PREPARED_AUTHORITY_CHANGED')
        deadline = stamp(action.get('deadline'))
        start_by = stamp(action.get('submit_start_by'))
        if start_by is None or now >= start_by:
            raise ValueError('PREPARATION_EXPIRED_REFRESH_ACCOUNT_AND_DECISION')
        if deadline is None or deadline-now < timedelta(seconds=90):
            raise ValueError('INSUFFICIENT_TIME_FOR_SUPPORTED_SUBMISSION')
        if not self.journal.claim_submission(intent_id, self.account_scope):
            return dict(status='RECONCILIATION_REQUIRED', intent_id=intent_id)
        try:
            response = self.adapter.submit(action_fields(action), intent_id, deadline.isoformat())
            self._apply(intent_id, response)
        except Exception:
            if self.journal.get(intent_id)['state'] == 'SUBMITTING':
                self.journal.record_uncertain(intent_id, dict(reason='SUBMISSION_UNRESOLVED_DO_NOT_RETRY',
                    adapter_request_id=getattr(self.adapter, 'last_request_id', None)))
            raise
        return self.journal.get(intent_id)

    def reconcile(self, intent_id):
        current = self.journal.get(intent_id)
        if current['action'].get('account_scope') != self.account_scope:
            raise ValueError('RECONCILIATION_ACCOUNT_SCOPE_UNVERIFIED')
        reference = (current.get('evidence') or {}).get('confirmation_id')
        response = self.adapter.reconcile(action_fields(current['action']), intent_id, reference)
        self._apply(intent_id, response, reference)
        return self.journal.get(intent_id)

    def _apply(self, intent_id, response, expected_reference=None):
        result = response.get('result', {})
        action = self.journal.get(intent_id)['action']
        at = stamp(result.get('observed_at'))
        source = result.get('source_url', '')
        if (result.get('ticker') != action['ticker'] or result.get('side') != action['side']
                or result.get('shares') != action['shares'] or at is None
                or not 0 <= (self.clock()-at).total_seconds() <= 300
                or source not in ('https://www.stockmarketgame.org/po.html',
                                  'https://www.stockmarketgame.org/tnotes.html')):
            raise ValueError('UNBOUND_OR_STALE_PLATFORM_RECEIPT')
        reference = result.get('confirmation_id')
        if not reference or (expected_reference and expected_reference != reference) or not result.get('record_text'):
            raise ValueError('EXACT_PLATFORM_REFERENCE_REQUIRED')
        status = result.get('status')
        if status not in ('PENDING', 'CONFIRMED', 'REJECTED', 'CANCELLED'):
            raise ValueError('UNRESOLVED_PLATFORM_STATUS')
        if status == 'CONFIRMED':
            if expected_reference is None:
                raise ValueError('PREVIOUSLY_BOUND_SUBMISSION_REFERENCE_REQUIRED')
            try:
                price = Decimal(str(result.get('executed_price')))
                if not price.is_finite() or price <= 0:
                    raise ValueError()
            except (InvalidOperation, ValueError):
                raise ValueError('EXPLICIT_EXECUTED_PRICE_REQUIRED')
            if result.get('platform_status') != 'Order Executed' or not source.endswith('/tnotes.html'):
                raise ValueError('EXPLICIT_EXECUTED_NOTE_REQUIRED')
        elif result.get('platform_status') != {'PENDING': 'Pending', 'REJECTED': 'Order Rejected',
                                             'CANCELLED': 'Order Cancelled'}[status]:
            raise ValueError('EXPLICIT_PLATFORM_STATUS_REQUIRED')
        evidence = dict(platform_record=result['record_text'], confirmation_id=reference,
                        source_url=source, observed_at=result['observed_at'],
                        filled_shares=result.get('filled_shares'), remaining_shares=result.get('remaining_shares'),
                        executed_price=result.get('executed_price'), adapter_request=response.get('request'))
        self.journal.reconcile_smg(intent_id, status, evidence)
