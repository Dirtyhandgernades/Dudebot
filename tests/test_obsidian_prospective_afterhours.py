"""No-lookahead after-hours attribution regression tests (offline)."""
import unittest
from datetime import datetime, timedelta, timezone
from backtest.obsidian_afterhours_catchability import (
    classify_missed_move, ads_equivalent_market_cap,
)

CUT=datetime(2026,10,26,19,58,tzinfo=timezone.utc) # 14:58 Central
OUT=datetime(2026,10,26,20,24,tzinfo=timezone.utc)
BEFORE=CUT-timedelta(minutes=5)
AFTER=CUT+timedelta(minutes=2)

def audit(**kw):
    return classify_missed_move(decision_cutoff=CUT,outcome_observed_at=OUT,
                                board_state="SCREENED_WATCH",**kw)

class AfterHoursCatchabilityTests(unittest.TestCase):
    def test_known_future_event_without_tape_not_trade(self):
        r=audit(catalyst_public_at=datetime(2026,10,23,13,5,tzinfo=timezone.utc))
        self.assertEqual(r["catchability"],"WATCH_OR_EVENT_ONLY_NO_PREDECISION_SIGNAL")
        self.assertIsNone(r["hypothetical_profit"])
    def test_afterhours_signal_never_backdated(self):
        r=audit(preclose_signal_at=OUT,quote_asof=BEFORE,
                smg_eligibility_verified=True,smg_platform_borrow_verified=True)
        self.assertEqual(r["catchability"],"SIGNAL_AFTER_CUTOFF_NO_RETROACTIVE_TRADE")
    def test_unknown_board_not_screened_rejected(self):
        r=classify_missed_move(decision_cutoff=CUT,outcome_observed_at=OUT,
                               board_state="UNKNOWN_BOARD")
        self.assertEqual(r["catchability"],"PREDECISION_BOARD_NOT_RECOVERED")
    def test_missing_data_not_no_opportunity(self):
        r=classify_missed_move(decision_cutoff=CUT,outcome_observed_at=OUT,
                               board_state="MISSING_DATA")
        self.assertEqual(r["catchability"],"UNRESOLVED_DATA_GAP")
    def test_missing_quote_blocks_even_confirmed_tape(self):
        r=audit(preclose_signal_at=BEFORE,smg_eligibility_verified=True,
                smg_platform_borrow_verified=True)
        self.assertEqual(r["catchability"],"NO_VERIFIED_PRECLOSE_QUOTE")
    def test_post_cutoff_catalyst_blocks(self):
        r=audit(preclose_signal_at=BEFORE,quote_asof=BEFORE,catalyst_public_at=AFTER,
                smg_eligibility_verified=True,smg_platform_borrow_verified=True)
        self.assertEqual(r["catchability"],"CATALYST_AFTER_CUTOFF")
    def test_eligibility_and_borrow_are_independent_gates(self):
        r=audit(preclose_signal_at=BEFORE,quote_asof=BEFORE,
                smg_eligibility_verified=True,smg_platform_borrow_verified=False)
        self.assertEqual(r["catchability"],"SMG_ELIGIBILITY_OR_BORROW_UNVERIFIED")
    def test_signal_is_not_execution(self):
        r=audit(preclose_signal_at=BEFORE,quote_asof=BEFORE,
                smg_eligibility_verified=True,smg_platform_borrow_verified=True)
        self.assertEqual(r["catchability"],"PRECLOSE_SIGNAL_BUT_EXECUTION_UNVERIFIED")
        self.assertFalse(r["actual_trade"])
    def test_no_hindsight_profit_even_with_execution_evidence(self):
        r=audit(preclose_signal_at=BEFORE,quote_asof=BEFORE,
                smg_eligibility_verified=True,smg_platform_borrow_verified=True,
                preclose_execution_evidence=True)
        self.assertEqual(r["catchability"],"POTENTIALLY_CATCHABLE_WITH_RECORDED_EVIDENCE")
        self.assertIsNone(r["hypothetical_profit"])
    def test_naive_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            classify_missed_move(decision_cutoff=datetime(2026,10,26,14,58),
                                 outcome_observed_at=OUT,board_state="UNKNOWN_BOARD")
    def test_outcome_must_be_after_cutoff(self):
        with self.assertRaises(ValueError):
            classify_missed_move(decision_cutoff=CUT,outcome_observed_at=CUT,
                                 board_state="UNKNOWN_BOARD")
    def test_ads_ratio_six_prevents_sixfold_cap_error(self):
        cap=ads_equivalent_market_cap(5.25,96_410_000,6)
        self.assertAlmostEqual(cap,84_358_750)
    def test_bad_ads_ratio_rejected(self):
        with self.assertRaises(ValueError):
            ads_equivalent_market_cap(5.25,96_410_000,0)

if __name__=="__main__": unittest.main()
