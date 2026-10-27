"""Offline regression tests for safe workflow-auth failure triage."""
import unittest
from pathlib import Path
from backtest.obsidian_workflow_failure_guard import classify_log, credential_contract, triage


ROOT = Path(__file__).resolve().parents[1]


class WorkflowFailureGuardTests(unittest.TestCase):
    def test_main_and_paper_secret_names_are_not_conflated(self):
        result = credential_contract(ROOT)
        self.assertEqual(result["status"], "SEPARATE_CREDENTIAL_FAMILIES")
        self.assertFalse(result["paper_diagnostic_proves_main_auth"])
        self.assertFalse(result["secret_values_read"])

    def test_market_data_auth_rejected(self):
        self.assertEqual(classify_log("ERROR: data.alpaca.markets: HTTP 401"),
                         "ALPACA_MARKET_DATA_AUTH_401")

    def test_market_data_entitlement_rejected(self):
        self.assertEqual(classify_log("data.alpaca.markets: HTTP 403"),
                         "ALPACA_MARKET_DATA_ACCESS_403")

    def test_unit_test_failure_distinct_from_auth(self):
        self.assertEqual(classify_log("AssertionError: 0 != 2\nFAILED (failures=2)"),
                         "OFFLINE_TEST_ASSERTION")

    def test_cache_warning_not_counted_as_job_failure(self):
        self.assertEqual(classify_log("Path Validation Error: Path(s) not found"),
                         "CACHE_PATH_WARNING_ONLY")

    def test_secret_values_not_echoed_in_result(self):
        marker = "DONOTEMIT_PRIVATE_TEST_TOKEN"
        result = str(triage(ROOT, marker + "\nERROR: data.alpaca.markets: HTTP 401"))
        self.assertNotIn(marker, result)
        self.assertIn("RESEARCH_ONLY_NOT_AN_ORDER", result)


if __name__ == "__main__":
    unittest.main()
