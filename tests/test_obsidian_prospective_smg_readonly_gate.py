"""Official public SMG constraints and account separation tests."""
import unittest
from datetime import datetime,timezone
from backtest.obsidian_smg_readonly_gate import check,batch

AT=datetime(2026,10,28,19,30,tzinfo=timezone.utc)
def public(**more):
    x={"exchange":"NASDAQ","stock_security_class_verified":True,
       "previous_regular_close":9.5,"decision_day_price":8.9,
       "price_sources_independently_checked":True,
       "market_cap_usd":100_000_000,"capitalization_independently_verified":True,
       "proposed_shares":100,"halt_source_checked":True,"halt_unresolved":False}
    x.update(more)
    return x
def account(**more):
    a={"platform":"SMG","blocked_symbol_checked":True,"blocked_symbol":False,
       "security_table_validated":True,"margin_account_short_enabled":True,
       "available_equity_verified":True,"checked_at":"2026-10-28T19:29:00Z",
       "source_read_only_authenticated":True}
    a.update(more)
    return a

class SMGTests(unittest.TestCase):
    def test_public_rules_still_do_not_authorize_short(self):
        x=check("JDZG",public(),account(),AT)
        self.assertFalse(x["eligible_to_call_executable"])
        self.assertFalse(x["smg_actual_shortability_independently_confirmed_by_module"])
        self.assertFalse(x["trade_authorized"])
    def test_below_floor_even_when_alpaca_reports_shortable(self):
        x=check("JDZG",public(decision_day_price=1.33),account(),AT)
        self.assertIn("SMG_3_DOLLAR_PREVIOUS_OR_CURRENT_PRICE_BLOCK",x["issues"])
        self.assertFalse(x["public_rules_compatible_assuming_inputs_valid"])
    def test_below_25m_cap(self):
        x=check("SMAL",public(market_cap_usd=24_999_999),account(),AT)
        self.assertIn("SMG_25M_MARKET_CAP_BLOCK",x["issues"])
    def test_missing_smg_account_is_unknown_not_allow(self):
        x=check("JDZG",public(),None,AT)
        self.assertIn("NO_AUTHENTICATED_SMG_ACCOUNT_EVIDENCE",x["issues"])
        self.assertIn("SMG_BLOCKED_SYMBOL_NOT_EXCLUDED",x["issues"])
    def test_halt_cannot_be_ignored(self):
        x=check("JDZG",public(halt_unresolved=True),account(),AT)
        self.assertIn("EXCHANGE_HALT_NOT_EXCLUDED",x["issues"])
    def test_borrow_status_does_not_replace_platform(self):
        r=check("ABC",public(),{"platform":"ALPACA","shortable":True},AT)
        self.assertIn("NO_AUTHENTICATED_SMG_ACCOUNT_EVIDENCE",r["issues"])
    def test_account_stale(self):
        x=check("ABC",public(),account(checked_at="2026-10-28T18:00:00Z"),AT)
        self.assertIn("ACCOUNT_EVIDENCE_STALE_OR_FUTURE",x["issues"])
    def test_not_shortable_at_foreign_venue(self):
        x=check("ABC",public(exchange="OTC"),account(),AT)
        self.assertIn("NOT_A_CONFIRMED_NASDAQ_OR_NYSE_SMG_LISTED_SECURITY",x["issues"])
    def test_no_borrow_on_cash_account(self):
        x=check("ABC",public(),account(margin_account_short_enabled=False),AT)
        self.assertIn("SMG_ACCOUNT_SHORT_PERMISSIONS_NOT_CONFIRMED",x["issues"])
    def test_batch_requires_unique_symbols(self):
        with self.assertRaisesRegex(ValueError,"UNIQUE"):
            batch(["JDZG","JDZG"],{},decision_at=AT)

if __name__=="__main__":
    unittest.main()
