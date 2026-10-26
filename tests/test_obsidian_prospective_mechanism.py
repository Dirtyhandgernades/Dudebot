"""Offline tests for independent OBSIDIAN mechanism taxonomy."""
import unittest
from datetime import datetime, timedelta, timezone
from backtest.obsidian_early_mechanism_audit import price_band, classify

T = datetime(2026, 10, 26, 19, 40, tzinfo=timezone.utc)
def proof(verified=True, at=T):
    return {"verified": verified, "observed_at": at}
def row(change=-8, **kw):
    return {"ticker": "TEST", "decision_at": T, "change_pct": change, **kw}
class TaxonomyTests(unittest.TestCase):
    def test_all_decline_bands_have_explicit_status(self):
        expected=[(-1,"OTHER_PRICE"),(-2,"EARLY_2_TO_15"),(-15,"EARLY_2_TO_15"),
                  (-15.001,"INTERMEDIATE_15_TO_25"),(-20,"INTERMEDIATE_15_TO_25"),
                  (-24.999,"INTERMEDIATE_15_TO_25"),(-25,"EXHAUSTED_25_PLUS"),
                  (-45,"EXHAUSTED_25_PLUS")]
        for value,band in expected:
            with self.subTest(value=value): self.assertEqual(price_band(value),band)
    def test_missing_price_explicit(self):
        self.assertEqual(classify(row(None))["price_band"],"UNKNOWN_PRICE")
    def test_price_only_is_never_confirmed_mechanism(self):
        result=classify(row())
        self.assertEqual(result["category"],"A")
        self.assertFalse(result["breakdown_mechanism_confirmed"])
        self.assertEqual(result["trade_status"],"BLOCKED_RESEARCH_ONLY")
    def test_verified_structure_without_catalyst_not_confirmed(self):
        e={k:proof() for k in ("failed_rebound","support_loss","selling_volume","liquidity")}
        self.assertFalse(classify(row(evidence=e))["breakdown_mechanism_confirmed"])
    def test_fresh_adverse_plus_tape_is_research_watch_not_trade(self):
        e={k:proof() for k in ("failed_rebound","support_loss","selling_volume","liquidity","verified_saleable_supply")}
        result=classify(row(evidence=e))
        self.assertTrue(result["breakdown_mechanism_confirmed"])
        self.assertEqual(result["trade_status"],"BLOCKED_RESEARCH_ONLY")
    def test_future_disclosure_rejected(self):
        e={k:proof() for k in ("failed_rebound","support_loss","selling_volume","liquidity")}
        e["fresh_adverse_disclosure"]=proof(at=T+timedelta(minutes=1))
        self.assertFalse(classify(row(evidence=e))["breakdown_mechanism_confirmed"])
    def test_unverified_firm_link_not_adverse(self):
        e={k:proof() for k in ("failed_rebound","support_loss","selling_volume","liquidity")}
        e["verified_saleable_supply"]=proof(False)
        self.assertFalse(classify(row(evidence=e))["breakdown_mechanism_confirmed"])
    def test_c_requires_all_four_proofs(self):
        e={k:proof() for k in ("failed_breakdown","support_reclaim","higher_low","buying_volume")}
        result=classify(row(2,evidence=e))
        self.assertEqual(result["category"],"C")
        self.assertEqual(result["trade_status"],"BLOCKED_RESEARCH_ONLY")
        del e["buying_volume"]
        result=classify(row(2,evidence=e,claims_reversal=True))
        self.assertNotEqual(result["category"],"C")
        self.assertIn("CATEGORY_C_EVIDENCE_INCOMPLETE",result["reasons"])
    def test_future_reversal_evidence_rejected(self):
        e={k:proof() for k in ("failed_breakdown","support_reclaim","higher_low","buying_volume")}
        e["higher_low"]=proof(at=T+timedelta(seconds=1))
        self.assertNotEqual(classify(row(1,evidence=e))["category"],"C")
    def test_intermediate_band_never_silent(self):
        result=classify(row(-20))
        self.assertEqual(result["category"],"INTERMEDIATE")
        self.assertIn("PRICE_BAND_REQUIRES_INDEPENDENT_MECHANISM_REVIEW",result["reasons"])
    def test_missing_smg_borrow_blocks_even_full_evidence(self):
        e={k:proof() for k in ("failed_rebound","support_loss","selling_volume","liquidity","fresh_adverse_disclosure")}
        result=classify(row(evidence=e))
        self.assertIn("UNKNOWN_SMG_BORROW_VERIFIED",result["reasons"])
    def test_unknown_timestamp_cannot_validate_evidence(self):
        e={k:proof() for k in ("failed_rebound","support_loss","selling_volume","liquidity","fresh_adverse_disclosure")}
        result=classify(row(evidence=e,decision_at=datetime(2026,10,26,14,40)))
        self.assertFalse(result["breakdown_mechanism_confirmed"])
        self.assertIn("UNKNOWN_DECISION_TIME",result["reasons"])
if __name__=="__main__": unittest.main()
