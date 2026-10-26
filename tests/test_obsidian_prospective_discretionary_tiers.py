"""Offline regression suite for research-only speculative versus hard gates."""
import unittest
from datetime import datetime, timedelta, timezone
from backtest.obsidian_discretionary_tiers import evaluate, POLICY_ID

T = datetime(2026, 10, 26, 19, 50, tzinfo=timezone.utc)
def p(value, when=T, published=None):
    r = {"value": value, "observed_at": when, "source_id": "INDEPENDENT_TEST_SOURCE"}
    if published is not None: r["published_at"] = published
    return r
def s(when=T, published=None):
    r = p(True, when, published)
    r["verified"] = True
    return r
def hard():
    return {
        "exchange": p("NASDAQ"), "security_type": p("COMMON_STOCK"),
        "current_price": p(8.0), "prior_session_price": p(8.5),
        "prior_session_confirmed": p(True), "current_shares": p(5_000_000),
        "market_cap": p(40_000_000), "halt_clear": p(True),
        "corporate_actions_clear": p(True), "liquidity_sufficient": p(True),
        "buying_power": p(50_000), "equity": p(100_000),
        "exposure_within_limits": p(True),
        "smg_short_available": p(True), "smg_platform_short_available": p(True),
    }
def plan():
    return {"thesis": "Dated adverse disclosure plus weak tape", "entry_trigger": "Fresh failed rebound",
            "invalidation": "Reclaim prior support", "exit_rule": "Next permitted EOD or risk stop"}
def obs(**kw):
    r={"ticker": "TEST", "direction": "SHORT", "decision_at": T,
       "change_pct": -8, "hard": hard(), "soft": {},
       "plan": plan(), "rank_score": None}
    r.update(kw)
    return r
def full_short():
    return {k: s() for k in ("fresh_adverse_disclosure", "failed_rebound",
                              "support_loss", "selling_volume", "liquidity")}
class TierTests(unittest.TestCase):
    def test_no_soft_evidence_watch_only_even_with_hard_gates(self):
        x=evaluate(obs())
        self.assertEqual(x["tier"],"WATCH_ONLY")
        self.assertTrue(x["hard_gates_passed"])
        self.assertFalse(x["confirmed_mechanism"])
    def test_partial_independent_thesis_is_speculative_not_confirmed(self):
        x=evaluate(obs(soft={"fresh_adverse_disclosure":s(),"failed_rebound":s()}))
        self.assertEqual(x["tier"],"SPECULATIVE_SETUP")
        self.assertFalse(x["confirmed_mechanism"])
        self.assertIn("support_loss",x["missing_soft_evidence"])
        self.assertEqual(x["speculative_initial_size_ceiling_usd"],2500)
        self.assertEqual(x["execution_status"],"RESEARCH_ONLY_NOT_AN_ORDER")
    def test_all_confirmed_tape_plus_catalyst(self):
        x=evaluate(obs(soft=full_short()))
        self.assertEqual(x["tier"],"CONFIRMED_SETUP")
        self.assertTrue(x["confirmed_mechanism"])
        self.assertIsNone(x["speculative_initial_size_ceiling_usd"])
    def test_unvalidated_rank_score_does_not_veto_evidence(self):
        r=obs(soft={"verified_saleable_supply":s(),"support_loss":s()})
        r["rank_score"]=None
        self.assertEqual(evaluate(r)["tier"],"SPECULATIVE_SETUP")
    def test_no_catalyst_cannot_be_speculative(self):
        x=evaluate(obs(soft={"failed_rebound":s(),"support_loss":s()}))
        self.assertEqual(x["tier"],"WATCH_ONLY")
    def test_firm_link_is_not_verified_catalyst(self):
        x=evaluate(obs(soft={"firm_relationship":s(),"failed_rebound":s()}))
        self.assertEqual(x["tier"],"WATCH_ONLY")
    def test_future_evidence_cannot_confirm(self):
        e={"fresh_adverse_disclosure":s(when=T+timedelta(seconds=1)),"failed_rebound":s()}
        self.assertEqual(evaluate(obs(soft=e))["tier"],"WATCH_ONLY")
    def test_future_filing_publication_rejected(self):
        e={"fresh_adverse_disclosure":s(published=T+timedelta(seconds=1)),"failed_rebound":s()}
        self.assertEqual(evaluate(obs(soft=e))["tier"],"WATCH_ONLY")
    def test_no_source_id_rejected(self):
        e={"fresh_adverse_disclosure":s(),"failed_rebound":s()}
        del e["fresh_adverse_disclosure"]["source_id"]
        self.assertEqual(evaluate(obs(soft=e))["tier"],"WATCH_ONLY")
    def test_missing_plan_cannot_be_speculative(self):
        e={"fresh_adverse_disclosure":s(),"failed_rebound":s()}
        x=evaluate(obs(soft=e,plan={"thesis":"a"}))
        self.assertEqual(x["tier"],"WATCH_ONLY")
        self.assertIn("exit_rule",x["missing_plan"])
    def test_missing_platform_short_blocks_but_preserves_soft_tier(self):
        h=hard(); h["smg_platform_short_available"]=p(False)
        x=evaluate(obs(hard=h,soft=full_short()))
        self.assertEqual(x["tier"],"HARD_BLOCKED")
        self.assertEqual(x["underlying_soft_tier"],"CONFIRMED_SETUP")
        self.assertIn("NO_VERIFIED_SMG_PLATFORM_SHORT_AVAILABLE",x["hard_blockers"])
    def test_alpaca_borrow_not_smg_borrow(self):
        h=hard(); del h["smg_short_available"]; h["alpaca_shortable"]=p(True)
        x=evaluate(obs(hard=h,soft=full_short()))
        self.assertEqual(x["tier"],"HARD_BLOCKED")
    def test_stale_quote_blocks(self):
        h=hard(); h["current_price"]=p(8,when=T-timedelta(minutes=16))
        x=evaluate(obs(hard=h,soft=full_short()))
        self.assertIn("UNVERIFIED_ASOF_CURRENT_PRICE",x["hard_blockers"])
    def test_below_three_prior_price_blocks(self):
        h=hard(); h["prior_session_price"]=p(2.99)
        self.assertEqual(evaluate(obs(hard=h,soft=full_short()))["tier"],"HARD_BLOCKED")
    def test_cap_below_25m_blocks(self):
        h=hard(); h["current_shares"]=p(2_000_000); h["market_cap"]=p(16_000_000)
        x=evaluate(obs(hard=h,soft=full_short()))
        self.assertIn("MARKET_CAP_GATE",x["hard_blockers"])
    def test_share_cap_split_mismatch_blocks(self):
        h=hard(); h["current_shares"]=p(500_000)
        x=evaluate(obs(hard=h,soft=full_short()))
        self.assertIn("SHARES_CAP_PRICE_MISMATCH",x["hard_blockers"])
    def test_ads_security_type_blocks(self):
        h=hard(); h["security_type"]=p("ADS")
        self.assertEqual(evaluate(obs(hard=h,soft=full_short()))["tier"],"HARD_BLOCKED")
    def test_unverified_halt_blocks(self):
        h=hard(); h["halt_clear"]=p(False)
        self.assertEqual(evaluate(obs(hard=h,soft=full_short()))["tier"],"HARD_BLOCKED")
    def test_exposure_and_buying_power_are_hard(self):
        h=hard(); h["buying_power"]=p(0); h["exposure_within_limits"]=p(False)
        x=evaluate(obs(hard=h,soft=full_short()))
        self.assertEqual(x["tier"],"HARD_BLOCKED")
        self.assertIsNone(x["speculative_initial_size_ceiling_usd"])
    def test_exhausted_drop_not_new_speculative_short(self):
        e={"fresh_adverse_disclosure":s(),"failed_rebound":s()}
        x=evaluate(obs(change_pct=-40,soft=e))
        self.assertEqual(x["category"],"B")
        self.assertEqual(x["tier"],"WATCH_ONLY")
    def test_intermediate_decline_not_dropped(self):
        e={"fresh_adverse_disclosure":s(),"failed_rebound":s()}
        x=evaluate(obs(change_pct=-20,soft=e))
        self.assertEqual(x["category"],"INTERMEDIATE")
        self.assertEqual(x["tier"],"SPECULATIVE_SETUP")
    def test_long_c_partial_is_speculative_not_confirmed(self):
        e={"failed_breakdown":s(),"support_reclaim":s()}
        x=evaluate(obs(direction="LONG",change_pct=3,soft=e))
        self.assertEqual(x["category"],"C_CANDIDATE")
        self.assertEqual(x["tier"],"SPECULATIVE_SETUP")
        self.assertFalse(x["confirmed_mechanism"])
    def test_long_c_full_confirmation(self):
        e={k:s() for k in ("failed_breakdown","support_reclaim","higher_low","buying_volume")}
        x=evaluate(obs(direction="LONG",change_pct=3,soft=e))
        self.assertEqual(x["category"],"C")
        self.assertEqual(x["tier"],"CONFIRMED_SETUP")
    def test_long_does_not_require_short_borrow(self):
        h=hard(); del h["smg_short_available"]; del h["smg_platform_short_available"]
        e={"failed_breakdown":s(),"support_reclaim":s()}
        x=evaluate(obs(direction="LONG",hard=h,soft=e))
        self.assertEqual(x["tier"],"SPECULATIVE_SETUP")
    def test_afterhours_discovery_is_not_eod_execution(self):
        later=T+timedelta(hours=2)
        h={k:p(v["value"],when=later) for k,v in hard().items()}
        e={"fresh_adverse_disclosure":s(when=later),"failed_rebound":s(when=later)}
        x=evaluate(obs(decision_at=later,hard=h,soft=e))
        self.assertEqual(x["tier"],"SPECULATIVE_SETUP")
        self.assertFalse(x["decision_window_open"])
        self.assertEqual(x["execution_status"],"RESEARCH_ONLY_NOT_AN_ORDER")
    def test_no_current_provider_evidence_hard_blocks(self):
        x=evaluate(obs(hard={},soft={"fresh_adverse_disclosure":s(),"failed_rebound":s()}))
        self.assertEqual(x["tier"],"HARD_BLOCKED")
        self.assertEqual(x["underlying_soft_tier"],"SPECULATIVE_SETUP")
    def test_policy_is_explicit_and_frozen(self):
        self.assertEqual(evaluate(obs())["policy_id"],POLICY_ID)
    def test_bad_direction_fails_closed(self):
        with self.assertRaises(ValueError): evaluate(obs(direction="BOTH"))
if __name__=="__main__": unittest.main()
