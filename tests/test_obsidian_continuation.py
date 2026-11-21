from backtest.obsidian_continuation import assess


def test_discount_requires_same_issuer_receipt_and_timely_early_setup():
    raw = dict(ticker='TEST', shadow_rank={'features': {'return_21': -.08}},
               catalysts={'filings':[dict(ticker='TEST', accession='index', document_receipt={'sha256':'doc'})]})
    sale = dict(accession='index', document_sha256='doc', completed_sale_reviewed=True,
                reference_sha256='ref', same_security_and_units_reviewed=True, sale_price=4, reference_price=5)
    review = dict(evidence_receipt_hashes=['doc','ref'], discounted_issuance=sale)
    assert assess(raw,review,'A',[],True)['status']=='RESEARCH_ALERT'
    assert assess(raw,review,'A',[],False)['status']=='BLOCKED'
    assert assess(raw,review,'A',['STALE_MARKET_DATA'],True)['status']=='BLOCKED'
    sale['completed_sale_reviewed']=False
    assert assess(raw,review,'A',[],True)['status']=='BLOCKED'
    sale['completed_sale_reviewed']=True
    raw['catalysts']['filings'][0]['ticker']='OTHER'
    assert assess(raw,review,'A',[],True)['status']=='BLOCKED'
