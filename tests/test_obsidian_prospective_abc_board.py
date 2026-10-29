import copy
import unittest
from datetime import datetime
from backtest.obsidian_abc_board import build, POLICY

class EarlyBoardEvidenceTests(unittest.TestCase):
    def packet(self):
        row = dict(ticker='TEST', classification='A', observed_at='2026-10-29T14:19:30-05:00', source_receipts=['quote'], source_latency_verified=True, catalyst_public_at='2026-10-29T08:00:00-05:00', catalyst_observed_at='2026-10-29T14:18:00-05:00', market_at='2026-10-29T14:19:00-05:00', mechanism_verified=True, counterevidence_reviewed=True, halt_clear=True, principal_collapse_not_occurred=True)
        return dict(cutoff_at='2026-10-29T14:20:00-05:00', exchange_session_verified=True, calendar_receipt='calendar', universe=['TEST'], universe_receipt='roster', rows=[row])
    def run_board(self, p):
        return build(p, datetime.fromisoformat('2026-10-29T14:21:00-05:00'))
    def weakness(self):
        return dict(verified=True, kind='failed_rebound', source_receipt='bars', observed_at='2026-10-29T14:19:00-05:00')
    def test_supply_alone_never_promoted_and_denominator_preserved(self):
        r=self.run_board(self.packet())
        self.assertEqual(r['counts'], {'BLOCKED':1})
        self.assertEqual(r['denominator'], 1)
        self.assertEqual(r['rows'][0]['underlying_classification'], 'A')
        self.assertIn('WEAK_TAPE_UNVERIFIED', r['rows'][0]['blockers'])
    def test_partial_tape_can_be_early_research_without_full_collapse(self):
        p=self.packet();p['rows'][0]['weakness_evidence']=self.weakness()
        r=self.run_board(p)
        self.assertEqual(r['counts'], {'A':1})
        self.assertFalse(r['rows'][0]['executable'])
        self.assertFalse(r['rows'][0]['trade_authorized'])
        self.assertIn('V2', POLICY)
    def test_future_tape_rejected(self):
        p=self.packet();w=self.weakness();w['observed_at']='2026-10-29T14:20:01-05:00';p['rows'][0]['weakness_evidence']=w
        with self.assertRaisesRegex(ValueError,'FUTURE_WEAK_TAPE'):self.run_board(p)
    def test_missing_receipt_stale_and_unsupported_social_claim_block(self):
        for change, expected in [({'source_receipt':''},'WEAK_TAPE_RECEIPT_MISSING'),({'observed_at':'2026-10-29T14:00:00-05:00'},'STALE_WEAK_TAPE'),({'kind':'social_sentiment'},'WEAK_TAPE_KIND_UNSUPPORTED'),({'verified':False},'WEAK_TAPE_UNVERIFIED')]:
            with self.subTest(change=change):
                p=self.packet();w=self.weakness();w.update(change);p['rows'][0]['weakness_evidence']=w
                self.assertIn(expected,self.run_board(p)['rows'][0]['blockers'])

