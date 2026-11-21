import unittest
import tempfile
from pathlib import Path
from backtest.obsidian_research_runner import verify_phase
from backtest.obsidian_strategy_lab import hashfile
from datetime import datetime,timezone,timedelta
from backtest.obsidian_strategy_lab import stats
from backtest.obsidian_portfolio_guard import propose,transition

class MetricsTests(unittest.TestCase):
    def result(self):
        return dict(trades=[dict(ticker='AAA',pnl=100),dict(ticker='BBB',pnl=-20)],net_profit=85,
                    initial_balance=1000,ending_balance=1085,realized_profit=80,interest_pnl=5,
                    daily_equity=[dict(date='2025-09-08',equity=1000),dict(date='2025-09-09',equity=1085)],
                    unresolved_open_positions=0,financial_status='CONDITIONAL_SIMULATION_COMPLETE',
                    max_observed_drawdown_pct=2,account_insolvent=False,gaps={})
    def test_accounting_removal_is_not_reinvestment_and_includes_interest(self):
        r=stats(self.result());self.assertEqual(r['profit_factor'],5)
        self.assertEqual(r['remove_top_winners_fixed_ledger']['1'],-15)
        self.assertEqual(r['pnl_reconciliation_delta'],0)
        self.assertAlmostEqual(r['expectancy_per_trade'],40)
    def test_unresolved_marks_never_become_final_profit(self):
        raw=self.result();raw.update(net_profit=None,ending_balance=None,unresolved_open_positions=1)
        raw['daily_equity'][-1]['equity']=None
        r=stats(raw);self.assertIsNone(r['return_pct']);self.assertIsNone(r['remove_top_winners_fixed_ledger']['1'])
        self.assertIsNone(r['monthly_marked_returns']['2025-09']['return_pct'])
    def test_no_losses_has_no_fabricated_infinite_profit_factor(self):
        raw=self.result();raw['trades']=raw['trades'][:1]
        self.assertIsNone(stats(raw)['profit_factor'])

class PortfolioTests(unittest.TestCase):
    now=datetime(2026,11,20,20,0,tzinfo=timezone.utc)
    def inputs(self):
        at=self.now.isoformat();receipt='fixture-only'
        account=dict(authenticated_read_verified=True,source_receipt=receipt,observed_at=at,
                     equity=100000,buying_power=100000,positions=[],pending_orders=[])
        names=('security_identity','instrument_permitted','exchange','prior_price','market_cap','corporate_actions',
               'halt_clear','liquidity','smg_permission','smg_borrow','local_rules')
        candidate=dict(ticker='AAA',thesis='fixture',validated_strategy=True,strategy_evidence=receipt,price=10,
                       price_at=at,quote_receipt=receipt,execution_deadline=(self.now+timedelta(minutes=30)).isoformat(),
                       calendar_receipt=receipt,gates={k:dict(status='PASS',source_receipt=receipt,observed_at=at) for k in names})
        return account,candidate
    def test_unknown_account_keeps_thesis_but_no_shares(self):
        _,candidate=self.inputs();r=propose({},candidate,self.now)
        self.assertEqual(r['underlying_thesis'],'fixture');self.assertIsNone(r['whole_share_quantity'])
        self.assertFalse(r['trade_authorized'])
    def test_paper_preview_cannot_submit(self):
        account,candidate=self.inputs();r=propose(account,candidate,self.now)
        self.assertGreaterEqual(r['whole_share_quantity'],10)
        self.assertLessEqual(r['estimated_notional'],r['exposure_envelope']['ceiling'])
        self.assertFalse(r['order_submitted'])
        with self.assertRaises(ValueError):transition('ORDER_PREPARATION','SUBMIT_ORDER')
    def test_stale_future_prices_and_deadline(self):
        for offset in (-61,1):
            a,c=self.inputs();c['price_at']=(self.now+timedelta(seconds=offset)).isoformat()
            self.assertEqual(propose(a,c,self.now)['status'],'BLOCKED')
        a,c=self.inputs();c['execution_deadline']=self.now.isoformat()
        self.assertIn('before_execution_deadline',propose(a,c,self.now)['blockers'])
    def test_pending_ambiguity_requires_reconciliation(self):
        a,c=self.inputs();a['pending_orders']=[dict(ticker='AAA',notional=100,confirmation_state='AMBIGUOUS')]
        r=propose(a,c,self.now);self.assertIsNone(r['whole_share_quantity'])
        self.assertEqual(transition('CONFIRMATION','AMBIGUOUS_CONFIRMATION'),'RECONCILIATION')
        with self.assertRaises(ValueError):transition('CONFIRMATION','EXECUTION_RECEIPT_OBSERVED',{'browser_clicked':True})
    def test_no_validated_strategy_and_insufficient_power_block(self):
        a,c=self.inputs();c['validated_strategy']=False
        self.assertIn('qualified_research_component',propose(a,c,self.now)['blockers'])
        a,c=self.inputs();a['buying_power']=1
        self.assertIn('INSUFFICIENT_ROOM_FOR_TEN_SHARES',propose(a,c,self.now)['blockers'])
    def test_broker_flag_does_not_supply_smg_borrow(self):
        a,c=self.inputs();c['gates'].pop('smg_borrow');c['alpaca_shortable']=True
        self.assertIn('smg_borrow',propose(a,c,self.now)['blockers'])

if __name__=='__main__':unittest.main()

class ReceiptRegressionTests(unittest.TestCase):
    inputs=PortfolioTests.inputs
    now=PortfolioTests.now
    def test_missing_price_and_strategy_receipts_block_preview(self):
        for field in ('quote_receipt','calendar_receipt','strategy_evidence'):
            account,candidate=self.inputs();candidate.pop(field)
            self.assertEqual(propose(account,candidate,self.now)['status'],'BLOCKED')


class CheckpointTests(unittest.TestCase):
    def test_changed_or_deleted_output_fails_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'ledger.json';p.write_text('original')
            manifest={'files':{'ledger.json':hashfile(p)}}
            verify_phase(root,manifest)
            p.write_text('modified')
            with self.assertRaises(ValueError):verify_phase(root,manifest)
            p.unlink()
            with self.assertRaises(ValueError):verify_phase(root,manifest)


class IdentityProbeTests(unittest.TestCase):
    def test_only_asof_near_gap_safe_primary_documents(self):
        from backtest.obsidian_identity_probe import choose_documents
        now=datetime(2026,11,20,tzinfo=timezone.utc)
        p={'filings':{'recent':{'accessionNumber':['0000000001-25-000001']*4,
           'primaryDocument':['safe.htm','../bad','too-late.htm','future.htm'],
           'acceptanceDateTime':['2025-10-03T10:00:00Z','2025-10-04T10:00:00Z','2025-11-03T10:00:00Z','2027-10-03T10:00:00Z'],
           'form':['6-K']*4}}}
        rows=choose_documents(p,'2025-10-02',now)
        self.assertEqual([r['document'] for r in rows],['safe.htm'])


class ExecutionFailureRegressionTests(unittest.TestCase):
    inputs=PortfolioTests.inputs
    now=PortfolioTests.now
    def test_expired_account_wrong_ticker_and_negative_target(self):
        account,candidate=self.inputs();account['observed_at']=(self.now-timedelta(minutes=6)).isoformat()
        self.assertIn('fresh_account',propose(account,candidate,self.now)['blockers'])
        account,candidate=self.inputs();candidate['ticker']='WRONG TICKER'
        self.assertIn('ticker_syntax',propose(account,candidate,self.now)['blockers'])
        account,candidate=self.inputs();candidate['target_notional']=-1
        self.assertIn('sizing_target_known',propose(account,candidate,self.now)['blockers'])
