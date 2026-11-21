import copy,unittest
from datetime import datetime,timezone,timedelta
from backtest.obsidian_candidate_pipeline import build

NOW=datetime(2026,11,20,20,20,tzinfo=timezone.utc)

class PipelineTests(unittest.TestCase):
    def packet(self):
        return dict(requested_symbols=['AAA','BBB'],finished_at=NOW.isoformat(),
                    receipts=[dict(sha256='fixture-price',retrieved_at=NOW.isoformat(),http_status=200)],rows=[
                    dict(ticker=s,iex=dict(feed='iex',observed_at=NOW.isoformat(),daily_bar={'o':10},
                         trade=dict(status='FRESH_SINGLE_VENUE',source_timestamp=NOW.isoformat(),values={'p':9})),
                         catalysts={'filings':[]},halt={'error':None}) for s in ['AAA','BBB']])
    def test_complete_source_board_no_forced_recommendations(self):
        r=build(self.packet(),NOW,'fixture-packet')
        self.assertEqual(r['denominator'],2);self.assertEqual(r['classification_counts'],{'BLOCKED':2})
        self.assertEqual(r['underlying_thesis_counts'],{'A':2})
        self.assertEqual(r['recommendations'],[]);self.assertFalse(r['delivery_verified'])
    def test_no_blanket_rejection_of_source_bound_partial_a(self):
        at=NOW.isoformat();review=dict(ticker='AAA',reviewed_at=at,reviewer='fixture-human',packet_sha256='fixture-packet',
            evidence_receipt_hashes=['fixture-price'],classification='A',catalyst_public_at=at,catalyst_observed_at=at,
            market_at=at,mechanism_verified=True,counterevidence_reviewed=True,halt_clear=True,
            principal_collapse_not_occurred=True,security_corporate_identity_verified=True,independent_market_verified=True,
            weakness_evidence=dict(verified=True,kind='failed_rebound',source_receipt='fixture-price',observed_at=at))
        r=build(self.packet(),NOW,'fixture-packet',[review]);row=next(x for x in r['rows'] if x['ticker']=='AAA')
        self.assertEqual(row['classification'],'A');self.assertFalse(row['executable'])
        self.assertEqual(row['execution_gates']['smg_permission']['status'],'UNKNOWN')
    def test_bad_binding_and_missing_rejections_fail(self):
        p=self.packet();p['rows'].pop()
        with self.assertRaises(ValueError):build(p,NOW,'x')
        with self.assertRaises(ValueError):build(self.packet(),NOW,'x',[{'ticker':'AAA'}])
    def test_future_receipt_and_stale_packets_not_promoted(self):
        p=self.packet();p['receipts'][0]['retrieved_at']=(NOW+timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):build(p,NOW,'x')
        r=build(self.packet(),NOW+timedelta(days=1),'x')
        self.assertEqual(r['publication_role'],'LATE_OR_OFF_CHECKPOINT_RESEARCH_REVIEW_NOT_PROSPECTIVE_BOARD')
        self.assertTrue(all(x['classification']=='BLOCKED' for x in r['rows']))

if __name__=='__main__':unittest.main()

class MarketQuarantineTests(unittest.TestCase):
    packet=PipelineTests.packet
    def test_future_trade_is_retained_as_blocked_not_whole_board_failure(self):
        p=self.packet();p['rows'][0]['iex']['trade']['source_timestamp']=(NOW+timedelta(minutes=1)).isoformat()
        r=build(p,NOW,'fixture');self.assertEqual(r['denominator'],2)
        row=next(x for x in r['rows'] if x['ticker']=='AAA')
        self.assertIn('FUTURE_MARKET_TIMESTAMP_QUARANTINED',row['blocker_inventory'])
