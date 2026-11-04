"""Offline fail-closed public-rule regression tests; no account access or orders."""
import unittest
from datetime import datetime, timezone
from backtest.obsidian_smg_readonly_gate import check

class TestSmgPublicGate(unittest.TestCase):
    def setUp(self):
        self.public = dict(exchange="NASDAQ", stock_security_class_verified=True,
            previous_regular_close=4.0, decision_day_price=4.2,
            price_sources_independently_checked=True, market_cap_usd=30_000_000,
            capitalization_independently_verified=True, proposed_shares=10,
            halt_source_checked=True, halt_unresolved=False)
        self.when = datetime(2026,11,4,14,47,tzinfo=timezone.utc)

    def compatible(self, data):
        return check("TEST",data,observed_at=self.when)["public_rules_compatible_assuming_inputs_valid"]

    def test_complete_public_inputs_not_trade_authorization(self):
        result=check("TEST",self.public,observed_at=self.when)
        self.assertTrue(result["public_rules_compatible_assuming_inputs_valid"])
        self.assertFalse(result["eligible_to_call_executable"])

    def test_missing_or_unverified_inputs_fail_closed(self):
        for key in ("exchange","stock_security_class_verified","previous_regular_close",
                    "decision_day_price","price_sources_independently_checked",
                    "market_cap_usd","capitalization_independently_verified",
                    "halt_source_checked","halt_unresolved"):
            with self.subTest(key=key):
                data=self.public.copy()
                data.pop(key)
                self.assertFalse(self.compatible(data))

    def test_below_thresholds_fail_closed(self):
        for key,value in (("previous_regular_close",2.99),("decision_day_price",2.99),
                          ("market_cap_usd",24_999_999),("proposed_shares",9)):
            with self.subTest(key=key):
                data=self.public.copy()
                data[key]=value
                self.assertFalse(self.compatible(data))

if __name__=="__main__":
    unittest.main()
