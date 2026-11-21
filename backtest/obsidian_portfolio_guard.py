"""Paper-only portfolio review and reconciliation state machine. No order API."""
from datetime import datetime, timedelta
import math
import re
from smg.exposure import budget

STATES=('DISCOVERY','VALIDATION','PORTFOLIO_REVIEW','POSITION_SIZING','ORDER_PREPARATION',
        'CONFIRMATION','RECONCILIATION','PERFORMANCE_AUDIT')


def finite(value):return type(value) in (int,float) and math.isfinite(value)


def aware(value):
    try:r=datetime.fromisoformat(value.replace('Z','+00:00'))
    except (AttributeError,ValueError):return None
    return r if r.utcoffset() is not None else None


def freshness(at,now,seconds):
    stamp=aware(at)
    return now-timedelta(seconds=seconds)<=stamp<=now if stamp is not None else None


def propose(account,candidate,now):
    """Unknown account facts block sizing without deleting the research candidate."""
    if now.utcoffset() is None:raise ValueError('AWARE_REVIEW_TIME_REQUIRED')
    reasons=[];gates={}
    def gate(name,passed,source=None):
        gates[name]=dict(status='PASS' if passed is True else 'FAIL' if passed is False else 'UNKNOWN',source=source)
        if passed is not True:reasons.append(name)
    gates_in=candidate.get('gates',{})
    gate('qualified_research_component',True if candidate.get('validated_strategy') is True and candidate.get('strategy_evidence') else False if candidate.get('validated_strategy') is False else None,candidate.get('strategy_evidence'))
    gate('authenticated_account',True if account.get('authenticated_read_verified') is True and account.get('source_receipt') else None,account.get('source_receipt'))
    gate('fresh_account',freshness(account.get('observed_at'),now,300),account.get('source_receipt'))
    gate('fresh_price',freshness(candidate.get('price_at'),now,60) if candidate.get('quote_receipt') else None,candidate.get('quote_receipt'))
    deadline=aware(candidate.get('execution_deadline'))
    gate('before_execution_deadline',now<deadline if deadline is not None and candidate.get('calendar_receipt') else None,candidate.get('calendar_receipt'))
    for name in ('security_identity','instrument_permitted','exchange','prior_price','market_cap','corporate_actions',
                 'halt_clear','liquidity','smg_permission','smg_borrow','local_rules'):
        row=gates_in.get(name,{})
        status=row.get('status')
        value=True if status=='PASS' and row.get('source_receipt') and freshness(row.get('observed_at'),now,300) else False if status=='FAIL' else None
        gate(name,value,row.get('source_receipt'))
    price=candidate.get('price');equity=account.get('equity');available=account.get('buying_power')
    gate('current_price_floor',price>=3 if finite(price) else None,candidate.get('quote_receipt'))
    gate('account_amounts_known',True if finite(equity) and equity>0 and finite(available) and available>=0 else None)
    positions=account.get('positions');pending=account.get('pending_orders')
    gate('positions_and_pending_known',True if isinstance(positions,list) and isinstance(pending,list) else None)
    ticker=candidate.get('ticker');reserved=0.;grouped={}
    gate('ticker_syntax',bool(isinstance(ticker,str) and re.fullmatch(r'[A-Z][A-Z0-9.]{0,12}',ticker)))
    target=candidate.get('target_notional',20000)
    gate('sizing_target_known',finite(target) and target>=0)
    if isinstance(positions,list) and isinstance(pending,list):
        for row in positions+pending:
            if not isinstance(row,dict) or not finite(row.get('notional')) or row['notional']<0:
                reasons.append('UNVALUED_EXISTING_OR_PENDING_EXPOSURE');continue
            reserved+=row['notional'];key=row.get('issuer_id') or row.get('ticker')
            grouped[key]=grouped.get(key,0)+row['notional']
            if row.get('ticker')==ticker and row in pending:reasons.append('DUPLICATE_PENDING_INTENT_RECONCILE_FIRST')
            if row.get('confirmation_state')=='AMBIGUOUS':reasons.append('AMBIGUOUS_INTENT_RECONCILE_FIRST')
        if grouped.get(candidate.get('issuer_id') or ticker,0)>0:reasons.append('EXISTING_ISSUER_EXPOSURE_REQUIRES_EXPLICIT_AGGREGATE_REVIEW')
    quantity=None;envelope=None
    if not reasons:
        envelope=budget(equity,available,target,
                        candidate.get('prior_observed_range'),reserved=reserved)
        quantity=max(0,math.floor(max(0,envelope['ceiling']-5)/(price*1.10)))
        if quantity<10:reasons.append('INSUFFICIENT_ROOM_FOR_TEN_SHARES');quantity=None
    return dict(research_candidate=candidate.get('ticker'),underlying_thesis=candidate.get('thesis'),
                status='BLOCKED' if reasons else 'PAPER_PREVIEW_REQUIRES_USER_CONFIRMATION',gates=gates,
                blockers=sorted(set(reasons)),whole_share_quantity=quantity,
                estimated_notional=quantity*price if quantity is not None else None,
                portfolio_existing_and_pending_by_issuer=grouped,exposure_envelope=envelope,
                cash_is_available_alternative=True,score_is_probability=False,
                short_loss_can_exceed_opening_notional=True,trade_authorized=False,order_submitted=False)


def transition(state,event,receipt=None):
    if state not in STATES:raise ValueError('INVALID_STATE')
    if event in {'AMBIGUOUS_CONFIRMATION','TIMEOUT_AFTER_INTENT','DUPLICATE_INTENT'}:
        return 'RECONCILIATION'
    if event=='SUBMIT_ORDER':raise ValueError('NO_ORDER_SUBMISSION_CAPABILITY')
    expected={'DISCOVERY':'VALIDATED_RESEARCH','VALIDATION':'ACCOUNT_REVIEWED',
              'PORTFOLIO_REVIEW':'RISK_APPROVED','POSITION_SIZING':'PAPER_TICKET_PREPARED',
              'ORDER_PREPARATION':'USER_REVIEWED_PREVIEW','CONFIRMATION':'EXECUTION_RECEIPT_OBSERVED',
              'RECONCILIATION':'PLATFORM_EXECUTION_RECONCILED'}
    if expected.get(state)!=event:raise ValueError('INVALID_OR_DUPLICATE_TRANSITION')
    if state in {'CONFIRMATION','RECONCILIATION'} and (not isinstance(receipt,dict) or
            receipt.get('platform_execution_verified') is not True or not receipt.get('source_receipt')):
        raise ValueError('PLATFORM_EXECUTION_RECEIPT_REQUIRED_NOT_BROWSER_SUCCESS')
    return STATES[STATES.index(state)+1]
