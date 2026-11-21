"""Connect the free research packet to V2 classification, triage and a full board.

Late reviews are never backdated predictions. No keyword establishes a verified
mechanism, no ordinal triage is a trained rank/probability, no orders/delivery.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone,time
import hashlib,json,math
from pathlib import Path
from zoneinfo import ZoneInfo
from backtest.obsidian_abc_board import assess_row
from backtest.obsidian_prospective_capture import asof

POLICY='OBSIDIAN_CONNECTED_FREE_RESEARCH_BOARD_V1_20261120'
CT=ZoneInfo('America/Chicago')


def build(packet,now,source_hash,reviews=None):
    symbols=packet.get('requested_symbols');rows=packet.get('rows')
    if (not isinstance(symbols,list) or not symbols or len(symbols)!=len(set(symbols)) or
        not isinstance(rows,list) or len(rows)!=len(symbols) or
        {r.get('ticker') for r in rows}!=set(symbols)):
        raise ValueError('INCOMPLETE_OR_DUPLICATE_SOURCE_UNIVERSE')
    received=asof(packet.get('finished_at'))
    if received is None or received>now:raise ValueError('INVALID_OR_FUTURE_SOURCE_PACKET')
    receipts=packet.get('receipts',[])
    if not isinstance(receipts,list):raise ValueError('INVALID_RECEIPTS')
    for receipt in receipts:
        if not isinstance(receipt,dict):raise ValueError('INVALID_RECEIPT')
        at=asof(receipt.get('retrieved_at'))
        if at is None or at>received or at>now:raise ValueError('FUTURE_OR_INVALID_RECEIPT')
    reviews=reviews or []
    if not isinstance(reviews,list):raise ValueError('REVIEWS_MUST_BE_LIST')
    known={r['sha256'] for r in receipts if r.get('sha256') and r.get('http_status')==200}
    reviewed={}
    for r in reviews:
        at=asof(r.get('reviewed_at')) if isinstance(r,dict) else None
        if (not isinstance(r,dict) or r.get('ticker') not in symbols or r['ticker'] in reviewed or
            r.get('packet_sha256')!=source_hash or at is None or at>now or not r.get('reviewer') or
            not isinstance(r.get('evidence_receipt_hashes'),list) or not r['evidence_receipt_hashes'] or
            not set(r['evidence_receipt_hashes'])<=known):
            raise ValueError('UNBOUND_FUTURE_OR_UNRECEIPTED_REVIEW')
        reviewed[r['ticker']]=r
    result=[]
    for raw in rows:
        iex=raw.get('iex',{});trade=iex.get('trade') or {};daily=iex.get('daily_bar') or {}
        p=(trade.get('values') or {}).get('p');opening=daily.get('o');change=None
        if all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in (p,opening)):
            change=p/opening-1
        filings=(raw.get('catalysts') or {}).get('filings',[])
        if not isinstance(filings,list):raise ValueError('INVALID_FILING_RECORDS')
        relevant=[]
        for f in filings:
            public=asof(f.get('public_at'));observed=asof(f.get('retrieved_at'))
            if public is None or observed is None or public>observed or observed>received:
                raise ValueError('INVALID_FILING_ASOF_PROVENANCE')
            relevant.append(f)
        adverse=sum(len(f.get('candidate_adverse_passages',[])) for f in relevant)
        counter=sum(len(f.get('candidate_counterevidence_passages',[])) for f in relevant)
        category='B' if change is not None and change<=-.25 else 'A' if adverse or change is not None and change<=-.02 else 'BLOCKED'
        source_at=asof(iex.get('observed_at')) or received
        if source_at>received:raise ValueError('FUTURE_MARKET_RECEIPT')
        market_stamp=asof(trade.get('source_timestamp'))
        safe_market_at=trade.get('source_timestamp') if market_stamp is not None and market_stamp<=received else None
        source_row=dict(ticker=raw['ticker'],classification=category,observed_at=received.isoformat(),
                        source_receipts=[r['sha256'] for r in receipts if r.get('sha256')],
                        source_latency_verified=iex.get('feed')=='iex',market_at=safe_market_at,
                        mechanism_verified=False,counterevidence_reviewed=False,halt_clear=False,
                        principal_collapse_not_occurred=False,weakness_evidence=None)
        if relevant:
            source_row.update(catalyst_public_at=relevant[0]['public_at'],catalyst_observed_at=relevant[0]['retrieved_at'])
        review=reviewed.get(raw['ticker'])
        allowed=('classification','catalyst_public_at','catalyst_observed_at','market_at','mechanism_verified',
                 'counterevidence_reviewed','halt_clear','principal_collapse_not_occurred','weakness_evidence','thesis_invalidation_verified')
        if review:
            for key in allowed:
                if key in review:source_row[key]=review[key]
            weakness=source_row.get('weakness_evidence') or {}
            if weakness.get('verified') is True and weakness.get('source_receipt') not in known:
                raise ValueError('WEAK_TAPE_RECEIPT_NOT_IN_SOURCE_PACKET')
        category=source_row['classification']
        assessed=assess_row(source_row,now)
        # Ordinary IEX-open changes / keyword snippets are not verified thesis evidence.
        blockers=set(assessed['blockers'])
        if not review or review.get('security_corporate_identity_verified') is not True:blockers.add('SECURITY_AND_CORPORATE_ACTION_IDENTITY_UNVERIFIED')
        if not review or review.get('independent_market_verified') is not True:blockers.add('INDEPENDENT_MARKET_CONFIRMATION_UNVERIFIED')
        if source_row.get('mechanism_verified') is not True:blockers.add('SOURCE_DATED_MECHANISM_REVIEW_PENDING')
        if source_row.get('counterevidence_reviewed') is not True:blockers.add('COUNTEREVIDENCE_REVIEW_PENDING')
        if market_stamp is not None and market_stamp>received:blockers.add('FUTURE_MARKET_TIMESTAMP_QUARANTINED')
        if packet.get('market_session_state')=='OUTSIDE_REGULAR_SESSION':blockers.add('OUTSIDE_REGULAR_SESSION_NO_CURRENT_EXECUTION')
        if trade.get('status')!='FRESH_SINGLE_VENUE':blockers.add('IEX_TRADE_NOT_FRESH_AT_SOURCE')
        if category=='BLOCKED':blockers.add('NO_SOURCED_DIRECTIONAL_THESIS')
        dims=dict(mechanism='SOURCE_BOUND_REVIEW_ASSERTS_VERIFIED' if source_row.get('mechanism_verified') is True else 'REVIEW_PENDING',supply_stage=review.get('supply_stage','UNKNOWN_NOT_INFERRED_FROM_FORM') if review else 'UNKNOWN_NOT_INFERRED_FROM_FORM',
                  selling_vs_recovery='UNVERIFIED',decline_already_experienced_diagnostic=change,
                  liquidity_execution='UNVERIFIED',counterevidence_squeeze='REVIEW_PENDING',
                  data_completeness=dict(has_trade_time=bool(trade.get('source_timestamp')),filings=len(relevant),
                                         adverse_keyword_passages=adverse,contrary_keyword_passages=counter,
                                         independent_source_confirmed=False))
        quality=int(trade.get('status')=='FRESH_SINGLE_VENUE')+int(bool(relevant))+int(not raw.get('halt',{}).get('error'))
        result.append(dict(ticker=raw['ticker'],classification='BLOCKED' if blockers else category,underlying_classification=category,
                           review_status='SOURCE_BOUND_HUMAN_ASSERTIONS_NOT_AUTOMATIC_AUTHENTICATION' if review else 'REVIEW_PENDING',
                           blocker_inventory=sorted(blockers),v2_gate_result=assessed,assessments=dims,
                           triage_sort_key=[int(not blockers and category in {'A','C'}),quality,(raw.get('shadow_rank') or {}).get('score') if (raw.get('shadow_rank') or {}).get('population_match_verified') is True and (raw.get('shadow_rank') or {}).get('score') is not None else -1,adverse],rank_is_probability=False,trained_rank_available=(raw.get('shadow_rank') or {}).get('score') is not None,shadow_rank=raw.get('shadow_rank'),
                           trained_rank_blocker='Historical model remains unqualified for live use; source/risk/counterevidence gates remain independent',
                           invalidation='Thesis contradicted, stale/invalid tape, identity/action mismatch, or rebound evidence; reassess with receipts',
                           original_source=raw,execution_gates={k:{'status':'UNKNOWN','source_receipt':None} for k in
                           ('smg_permission','smg_borrow','market_cap','prior_price','corporate_actions','current_account_exposure','buying_power')},
                           executable=False,trade_authorized=False))
    result.sort(key=lambda r:(*[-x for x in r['triage_sort_key']],r['ticker']))
    for i,r in enumerate(result):
        r['triage_priority']=i+1;r['ordering_explanation']='Source-bound qualified research first, then data completeness, fixed historical ordinal rank only for verified matching population (otherwise diagnostic, excluded), passage count and ticker; not expected return'
    local=now.astimezone(CT);window=local.weekday()<5 and time(14,20)<=local.time().replace(tzinfo=None)<=time(14,35)
    return dict(mode='RESEARCH_ONLY_NOT_AN_ORDER',policy=POLICY,created_at=now.isoformat(),source_packet_at=packet['finished_at'],
                source_packet_sha256=source_hash,publication_role='CHECKPOINT_WINDOW_RESEARCH_REQUIRES_DELIVERY_PROOF' if window else 'LATE_OR_OFF_CHECKPOINT_RESEARCH_REVIEW_NOT_PROSPECTIVE_BOARD',
                original_predictions_modified=False,denominator=len(symbols),requested_symbols=symbols,
                classification_counts=dict(Counter(r['classification'] for r in result)),
                underlying_thesis_counts=dict(Counter(r['underlying_classification'] for r in result)),rows=result,
                research_candidates=[{'ticker':r['ticker'],'classification':r['classification'],'executable':False} for r in result if r['classification'] in {'A','C'}],recommendations=[],trained_baseline_replaced=False,delivery_verified=False,actual_trades=None,
                position_review_status='AUTHENTICATED_CURRENT_ACCOUNT_UNAVAILABLE',performance_metrics=None)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--reviews',type=Path);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    raw=a.packet.read_bytes();r=build(json.loads(raw),datetime.now(timezone.utc),hashlib.sha256(raw).hexdigest(),json.loads(a.reviews.read_text()) if a.reviews else None)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(r,f,indent=2,sort_keys=True,allow_nan=False)
    print(json.dumps({k:r[k] for k in ('policy','denominator','classification_counts','underlying_thesis_counts','publication_role','delivery_verified')}))
if __name__=='__main__':main()
