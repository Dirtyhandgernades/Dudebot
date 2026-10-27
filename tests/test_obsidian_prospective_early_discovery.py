"""Research-only regression checks: observed vs retained, early vs exhausted."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

from backtest.obsidian_early_discovery import (
    audit_archive_health, reconcile_coverage, prioritize_early_discovery,
)

ROOT = Path(__file__).resolve().parents[1]
T = datetime(2026, 10, 26, 19, 50, tzinfo=timezone.utc)


def p(t=T, **extra):
    return {"verified": True, "observed_at": t.isoformat(),
            "source_id": "OFFLINE_TEST_SOURCE", **extra}


def quote(value, t=T):
    return p(t, value=value)


def prior(value, t=T):
    return p(t - timedelta(days=3), value=value,
             complete_regular_session=True, previous_session_confirmed=True)


class EarlyDiscoveryTests(unittest.TestCase):
    def test_historical_union_preserved(self):
        master = json.loads((ROOT / "backtest/obsidian_historical_watchlist_manifest_2026_10_26.json").read_text())["records"]
        supplemental = json.loads((ROOT / "backtest/obsidian_supplemental_watchlist_2026_10_26.json").read_text())["records"]
        x = reconcile_coverage(master, supplemental, [])
        self.assertEqual(x["manifest_symbols"], 136)
        self.assertEqual(x["observed_symbol_union"], 136)
        self.assertEqual(x["authenticated_screen_evidence_symbols"], 0)

    def test_off_manifest_does_not_mean_unseen_or_never_screened(self):
        x = reconcile_coverage([{"ticker": "CPIX"}], [{"ticker": "AIOK"}],
                               [{"ticker": "XP", "kind": "CHAT_REFERENCE",
                                 "source_ref": "dated-trading-chat",
                                 "observation_date": "2026-10-26"}])
        rows = {row["ticker"]: row for row in x["rows"]}
        self.assertTrue(rows["XP"]["absent_from_retained_manifests"])
        self.assertTrue(rows["XP"]["observed_elsewhere"])
        self.assertEqual(rows["XP"]["actual_screen_evidence"], "NO_AUTHENTICATED_SCREEN_EVIDENCE")
        self.assertEqual(rows["CPIX"]["actual_screen_evidence"], "NO_AUTHENTICATED_SCREEN_EVIDENCE")
        self.assertEqual(rows["AIOK"]["actual_screen_evidence"], "NO_AUTHENTICATED_SCREEN_EVIDENCE")

    def test_postcutoff_scan_cannot_be_backdated(self):
        events = [{"ticker": "XP", "kind": "AUTHENTICATED_SCANNER",
                   "source_ref": "immutable-scan-1", "scan_id": "1",
                   "authenticated": True, "observed_at": (T + timedelta(hours=2)).isoformat()}]
        r = reconcile_coverage([], [], events, decision_cutoff=T.isoformat())["rows"][0]
        self.assertEqual(r["actual_screen_evidence"], "ONLY_AFTER_CUTOFF_SCREEN")

    def test_date_only_scanner_attestation_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_coverage([], [], [{"ticker": "XP",
                "kind": "AUTHENTICATED_SCANNER", "source_ref": "x",
                "authenticated": True, "scan_id": "x", "observation_date": "2026-10-26"}])

    def test_complete_explicit_inventory_can_prove_considered(self):
        x = reconcile_coverage([], [], [], decision_cutoff=T.isoformat(),
            scan_inventory=[{"authenticated": True, "captured_at": T.isoformat(),
                             "scan_id": "future_write_once", "considered_symbols": ["XP"]}])
        self.assertEqual(x["rows"][0]["actual_screen_evidence"], "AUTHENTICATED_INVENTORY_CONSIDERED")

    def test_no_automatically_usable_archive_from_empty(self):
        health = audit_archive_health({"status":"ARCHIVED", "market_rows":0,
                                       "asset_rows":166,"asset_available_rows":0})
        self.assertEqual(health["provider_coverage"], "EMPTY_OR_UNKNOWN_COVERAGE")
        self.assertFalse(health["may_claim_full_screen"])

    def test_partial_rows_still_not_full_universe(self):
        self.assertFalse(audit_archive_health({"market_rows":12,"asset_available_rows":12})["may_claim_full_screen"])

    def test_early_verified_catalyst_and_tape_is_higher_priority_than_price_only(self):
        x = prioritize_early_discovery(dict(ticker="ZZZZ", observed_at=T, phase="PRECLOSE",
            prior_regular_close=10, observed_price=9.3, quote=quote(9.3), prior_regular_close_proof=prior(10),
            catalyst=p(type="ADVERSE_SEC_FILING", published_at=(T-timedelta(minutes=40)).isoformat()),
            tape={"failed_rebound":p()}))
        self.assertEqual(x["lane"], "EARLY_ADVERSE_MECHANISM_AND_TAPE")
        self.assertEqual(x["priority_ordinal_not_probability"],1)
        self.assertFalse(x["potentially_executable"])

    def test_small_weakness_without_catalyst_not_promoted(self):
        x = prioritize_early_discovery(dict(ticker="ZZZZ", observed_at=T, phase="PRECLOSE",
            prior_regular_close=10, observed_price=9.8, quote=quote(9.8), prior_regular_close_proof=prior(10), tape={"failed_rebound":p()}))
        self.assertEqual(x["lane"], "EARLY_PRICE_ONLY_WATCH")

    def test_future_disclosure_cannot_make_past_setup(self):
        x = prioritize_early_discovery(dict(ticker="ZZZZ", observed_at=T, phase="PRECLOSE",
            prior_regular_close=10, observed_price=9.1, quote=quote(9.1), prior_regular_close_proof=prior(10),
            catalyst=p(type="ADVERSE_ISSUER_RELEASE",published_at=(T+timedelta(seconds=1)).isoformat()),
            tape={"support_loss":p()}))
        self.assertFalse(x["catalyst_asof_verified"])
        self.assertEqual(x["lane"],"EARLY_PRICE_ONLY_WATCH")

    def test_registration_is_not_actual_selling(self):
        x = prioritize_early_discovery(dict(ticker="ZZZZ",observed_at=T,phase="PRECLOSE",
            prior_regular_close=10,observed_price=9.2,quote=quote(9.2),prior_regular_close_proof=prior(10),
            catalyst=p(type="VERIFIED_ACTUAL_SALEABLE_SUPPLY", issued=False,legally_saleable=True),
            tape={"selling_volume":p()}))
        self.assertEqual(x["lane"],"EARLY_PRICE_ONLY_WATCH")

    def test_30pct_preexisting_collapse_never_ranked_early(self):
        x = prioritize_early_discovery(dict(ticker="XP",observed_at=T,phase="PRECLOSE",
            prior_regular_close=30,observed_price=15,quote=quote(15),prior_regular_close_proof=prior(30),
            catalyst=p(type="PUBLIC_MACRO_SHOCK"),tape={"support_loss":p()}))
        self.assertEqual(x["lane"], "EXHAUSTED_NOT_AN_EARLY_CATCH")
        self.assertIsNone(x["priority_ordinal_not_probability"])

    def test_afterhours_cannot_promote_trade_timing(self):
        later = T + timedelta(hours=2)
        x = prioritize_early_discovery(dict(ticker="CPIX", observed_at=later, phase="AFTERHOURS",
            prior_regular_close=10, observed_price=9, quote=quote(9, later), prior_regular_close_proof=prior(10, later),
            catalyst=p(later,type="ADVERSE_ISSUER_RELEASE"), tape={"support_loss":p(later)}))
        self.assertEqual(x["lane"],"AFTERHOURS_DISCOVERY_NOT_PRECLOSE_ENTRY")
        self.assertFalse(x["decision_clock_window_only"])

    def test_absent_prior_close_proof_keeps_candidate_unknown(self):
        x = prioritize_early_discovery(dict(ticker="CPIX", observed_at=T,
            phase="PRECLOSE", prior_regular_close=10, observed_price=9,
            quote=quote(9), catalyst=p(type="ADVERSE_SEC_FILING"),
            tape={"support_loss": p()}))
        self.assertEqual(x["lane"], "QUOTE_OR_PRIOR_CLOSE_UNVERIFIED")

    def test_uncompleted_prior_session_rejected(self):
        proof = prior(10)
        proof["complete_regular_session"] = False
        x = prioritize_early_discovery(dict(ticker="CPIX", observed_at=T,
            phase="PRECLOSE", prior_regular_close=10, observed_price=9,
            quote=quote(9), prior_regular_close_proof=proof))
        self.assertIsNone(x["change_from_previous_regular_close_pct"])

    def test_quote_value_mismatch_censored(self):
        x = prioritize_early_discovery(dict(ticker="XP", observed_at=T,
            phase="PRECLOSE", prior_regular_close=30, observed_price=27,
            quote=quote(15), prior_regular_close_proof=prior(30)))
        self.assertEqual(x["lane"], "QUOTE_OR_PRIOR_CLOSE_UNVERIFIED")

    def test_future_prior_close_publication_rejected(self):
        proof = prior(10)
        proof["published_at"] = (T + timedelta(seconds=1)).isoformat()
        x = prioritize_early_discovery(dict(ticker="XP", observed_at=T,
            phase="PRECLOSE", prior_regular_close=10, observed_price=9,
            quote=quote(9), prior_regular_close_proof=proof))
        self.assertEqual(x["lane"], "QUOTE_OR_PRIOR_CLOSE_UNVERIFIED")

    def test_stale_quote_is_unknown_not_negative(self):
        x = prioritize_early_discovery(dict(ticker="CPIX",observed_at=T,phase="PRECLOSE",
            prior_regular_close=10,observed_price=8,quote=quote(8, T-timedelta(minutes=20)),prior_regular_close_proof=prior(10)))
        self.assertEqual(x["lane"],"QUOTE_OR_PRIOR_CLOSE_UNVERIFIED")
        self.assertIsNone(x["change_from_previous_regular_close_pct"])

    def test_corporate_action_quarantine(self):
        x = prioritize_early_discovery(dict(ticker="AIOK",observed_at=T,phase="PRECLOSE",
            prior_regular_close=10,observed_price=9,quote=quote(9),prior_regular_close_proof=prior(10),corporate_action_unresolved=True))
        self.assertEqual(x["lane"],"CORPORATE_ACTION_REVIEW_REQUIRED")

    def test_ineligible_previous_price_hard_block(self):
        x = prioritize_early_discovery(dict(ticker="BRAI",observed_at=T,phase="PRECLOSE",
            prior_regular_close=2.5,observed_price=3.4,quote=quote(3.4),prior_regular_close_proof=prior(2.5)))
        self.assertEqual(x["lane"],"PRICE_HARD_BLOCK")


if __name__ == "__main__":
    unittest.main()
