"""Evaluate the registered continuation lane on an existing source-bound A review."""
from math import isfinite


def assess(raw, review, category, blockers, timely):
    reasons = list(blockers)
    if not timely:
        reasons.append('OUTSIDE_CHECKPOINT')
    if category != 'A':
        reasons.append('EARLY_A_SETUP_REQUIRED')
    value = ((raw.get('shadow_rank') or {}).get('features') or {}).get('return_21')
    if type(value) not in (int, float) or not isfinite(value) or value >= 0:
        reasons.append('NEGATIVE_PRIOR_RETURN_UNCONFIRMED')
    review = review or {}
    sale = review.get('discounted_issuance') or {}
    hashes = set(review.get('evidence_receipt_hashes', []))
    filings = (raw.get('catalysts') or {}).get('filings', [])
    bound = any(f.get('ticker') == raw['ticker'] and f.get('accession') and
                f['accession'] == sale.get('accession') and
                (f.get('document_receipt') or {}).get('sha256') == sale.get('document_sha256')
                and sale.get('document_sha256') in hashes for f in filings)
    if not bound or sale.get('completed_sale_reviewed') is not True:
        reasons.append('COMPLETED_ISSUANCE_UNCONFIRMED')
    price, reference = sale.get('sale_price'), sale.get('reference_price')
    if (not all(type(x) in (int,float) and isfinite(x) and x > 0 for x in (price,reference))
            or price >= reference or not sale.get('reference_sha256')
            or sale['reference_sha256'] not in hashes or sale.get('same_security_and_units_reviewed') is not True):
        reasons.append('DISCOUNT_UNCONFIRMED')
    return dict(status='BLOCKED' if reasons else 'RESEARCH_ALERT',
                reasons=sorted(set(reasons)), original_hybrid_call='UNKNOWN_WITHOUT_FROZEN_TRIGGER',
                execution_authorized=False)
