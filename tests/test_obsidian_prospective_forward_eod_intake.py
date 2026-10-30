"""Synthetic fail-closed EOD provenance and calendar intake tests; no network."""
import copy
import unittest

from backtest.obsidian_forward_eod_intake import assess, audit_packet
from backtest.obsidian_iex_corporate_actions import ACTION_FLAGS

DAY = "2026-10-28"
PREV = "2026-10-27"


def calendar():
    return {"session_date": DAY, "previous_regular_session": PREV,
            "regular_close_at":"2026-10-28T16:00:00-04:00",
            "source_url":"https://www.nyse.com/trade/hours-calendars",
            "session_open":True,"independently_checked":True,
            "source_checked_at":"2026-10-28T15:00:00-04:00"}


def source(provider, host, amount=8.0):
    return {"source_id":provider+"_eod","provider_group":provider,
            "url":"https://"+host+"/prices", "symbol":"ZZZZ",
            "session_date":DAY,"previous_session_date":PREV,
            "kind":"regular_close","session_complete":True,
            "regular_close":amount,"previous_regular_close":10.0,
            "regular_close_asof":"2026-10-28T20:00:00Z",
            "previous_regular_close_asof":"2026-10-27T20:00:00Z",
            "observed_at":"2026-10-28T20:05:00Z","verified":True}


def outcome():
    return {
        "ticker":"ZZZZ","session_date":DAY,"previous_session_date":PREV,
        "verified":True,"regular_session":True,"provider_conflict":False,
        "previous_regular_close":10.0,"regular_close":8.0,
        "corporate_actions_clear":True,
        "close_at":"2026-10-28T20:00:00Z",
        "collected_at":"2026-10-28T20:15:00Z",
        "source_url":"https://provider-a.example/report",
        "independent_eod_sources":[source("vendor_a","a.example"),
                                   source("vendor_b","b.example")],
        "corporate_action_review":{
            "status":"NO_ACTIONS_CONFIRMED","verified":True,
            "reviewed_sessions":[PREV,DAY],
            "checked_at":"2026-10-28T20:08:00Z",
            "source_url":"https://corp-actions.example/audit",
            "prior_symbol":"ZZZZ","current_symbol":"ZZZZ",
            "prior_security_id":"security-id-1",
            "current_security_id":"security-id-1",
            "action_flags":{flag:False for flag in ACTION_FLAGS},
        },
    }


class StrictIntakeTests(unittest.TestCase):
    def test_consistent_external_claims_are_not_authenticated(self):
        result=assess(outcome(),calendar())
        self.assertEqual(result["status"],"STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING")
        self.assertFalse(result["usable_for_automatic_frozen_forward_scoring"])
        self.assertFalse(result["official_close_verified_by_module"])
        self.assertFalse(result["actual_source_independence_authenticated"])

    def test_missing_previous_close_timestamp_blocks(self):
        row=outcome()
        del row["independent_eod_sources"][1]["previous_regular_close_asof"]
        self.assertIn("PREVIOUS_CLOSE_NOT_EXACT_1600_ET_SOURCE",
                      assess(row,calendar())["issues"])

    def test_missing_per_source_asof_blocks(self):
        row=outcome()
        del row["independent_eod_sources"][1]["regular_close_asof"]
        self.assertIn("NON_1600_ET_REGULAR_CLOSE_SOURCE",assess(row,calendar())["issues"])

    def test_two_aliases_are_not_independent(self):
        row=outcome()
        row["independent_eod_sources"][1]["provider_group"]="vendor_a"
        self.assertIn("INSUFFICIENT_DISTINCT_HOST_AND_PROVIDER_EVIDENCE",
                      assess(row,calendar())["issues"])

    def test_three_sources_with_one_conflicting_are_blocked(self):
        row=outcome()
        row["independent_eod_sources"].append(source("vendor_c","c.example",8.2))
        self.assertIn("CONFLICTING_REGULAR_CLOSE_REPORTS",assess(row,calendar())["issues"])

    def test_wrong_session_chain_blocks(self):
        row=outcome()
        row["previous_session_date"]="2026-10-26"
        self.assertIn("PREVIOUS_SESSION_CHAIN_MISMATCH",assess(row,calendar())["issues"])

    def test_never_assign_split_as_real_collapse(self):
        row=outcome()
        row["corporate_action_review"]["action_flags"]["reverse_split"]=True
        self.assertIn("SECURITY_OR_CORPORATE_ACTION_NOT_INDEPENDENTLY_CLEARED",
                      assess(row,calendar())["issues"])

    def test_no_calendar_evidence_does_not_pass(self):
        self.assertEqual(assess(outcome(),None)["status"],"BLOCKED_EOD_EVIDENCE")

    def test_holiday_adjacent_calendar_does_not_slip_through(self):
        other=calendar()
        other["previous_regular_session"]="2026-10-26"
        result=assess(outcome(),other)
        self.assertIn("FROZEN_PREVIOUS_WEEKDAY_DIFFERS_FROM_EXCHANGE_SESSION",result["issues"])

    def test_duplicate_calendar_prevents_ambiguous_time(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_CALENDAR_SESSION"):
            audit_packet([], [calendar(),calendar()])

    def test_duplicate_ticker_session_prevents_outcome_selection(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_TICKER_SESSION"):
            audit_packet([outcome(),outcome()],[calendar()])

    def test_empty_observation_batch_is_not_a_zero_hit_rate(self):
        report=audit_packet([],[])
        self.assertIsNone(report["performance_metrics"])
        self.assertEqual(report["externally_verified_completed_outcomes"],0)

    def test_packet_preserves_unverified_input_not_empty_performance(self):
        row=outcome()
        row["independent_eod_sources"]=[]
        report=audit_packet([row],[calendar()])
        self.assertEqual(report["input_outcomes"],1)
        self.assertEqual(report["outcomes_retained"],1)
        self.assertEqual(report["status_counts"],{"BLOCKED_EOD_EVIDENCE":1})
        self.assertIsNone(report["performance_metrics"])

if __name__=="__main__":
    unittest.main()
