"""Synthetic offline regression tests; no market, broker, or alert calls."""
import json
import tempfile
import unittest
from pathlib import Path
from backtest.obsidian_prospective_journal import audit, write_journal


def sample():
    row = dict(screen_id="independent-20261026", ticker="ABCD", direction="SHORT", category="A",
               session_date="2026-10-26", decision_at="2026-10-26T14:50:00-05:00",
               exchange="NASDAQ", security_type="COMMON_STOCK", halted=False,
               corporate_actions_clear=True, decision_price=9.5, previous_close=10,
               shares_outstanding=10_000_000, borrow_available=True, smg_short_available=True,
               cutoff_at="2026-10-26T14:48:00-05:00", last_complete_at="2026-10-26T14:45:00-05:00")
    for key in ("screen", "quote", "previous_close", "shares", "listing", "corporate_actions", "borrow", "smg_short"):
        row[key + "_verified"] = True
        row[key + "_url"] = "https://example.org/" + key
        row[key + "_at"] = "2026-10-23T15:00:00-05:00" if key == "previous_close" else "2026-10-26T14:49:00-05:00"
    return row


class JournalTests(unittest.TestCase):
    def test_eligible_is_never_trade_authorized(self):
        result = audit(sample())
        self.assertEqual(result["status"], "RESEARCH_ELIGIBLE_NOT_EXECUTABLE")
        self.assertFalse(result["trade_authorized"])
        self.assertTrue(result["frozen_minus_2pct_short_diagnostic"])

    def test_unknown_borrow_blocks(self):
        row = sample(); row["borrow_available"] = None
        self.assertIn("BORROW_OR_SMG_SHORT_UNKNOWN", audit(row)["blockers"])

    def test_future_evidence_rejected(self):
        row = sample(); row["shares_at"] = "2026-10-27T09:00:00-05:00"
        with self.assertRaisesRegex(ValueError, "FUTURE_SHARES"):
            audit(row)

    def test_future_candle_rejected(self):
        row = sample(); row["last_complete_at"] = "2026-10-26T15:00:00-05:00"
        with self.assertRaisesRegex(ValueError, "FUTURE_OR_INVALID_CUTOFF"):
            audit(row)

    def test_stale_quote_and_borrow_block(self):
        row = sample(); row["quote_at"] = row["borrow_at"] = "2026-10-26T14:35:00-05:00"
        self.assertIn("STALE_QUOTE_EVIDENCE", audit(row)["blockers"])
        self.assertIn("STALE_BORROW_EVIDENCE", audit(row)["blockers"])

    def test_central_window_and_dst(self):
        row = sample(); row["decision_at"] = "2026-10-26T15:50:00-04:00"
        self.assertEqual(audit(row)["decision_at_central"], "2026-10-26T14:50:00-05:00")
        row["decision_at"] = "2026-10-26T15:10:00-05:00"
        self.assertIn("OUTSIDE_CENTRAL_EXECUTION_WINDOW", audit(row)["blockers"])

    def test_cap_and_type_block(self):
        row = sample(); row["shares_outstanding"] = 1000; row["security_type"] = "ETF"
        self.assertIn("MARKET_CAP_UNKNOWN_OR_BELOW_25M", audit(row)["blockers"])
        self.assertIn("NOT_VERIFIED_US_LISTED_COMMON_STOCK", audit(row)["blockers"])

    def test_immutable_journal_retains_unknown(self):
        good = sample(); bad = dict(good, ticker="WXYZ", borrow_available=None)
        with tempfile.TemporaryDirectory() as temp:
            src, dest = Path(temp)/"in.jsonl", Path(temp)/"out.jsonl"
            src.write_text(json.dumps(good)+"\n"+json.dumps(bad)+"\n")
            self.assertEqual(write_journal(src, dest)["blocked"], 1)
            self.assertEqual(len(dest.read_text().splitlines()), 2)
            with self.assertRaises(FileExistsError):
                write_journal(src, dest)

    def test_duplicates_rejected_before_output(self):
        row = sample()
        with tempfile.TemporaryDirectory() as temp:
            src, dest = Path(temp)/"in.jsonl", Path(temp)/"out.jsonl"
            src.write_text(json.dumps(row)+"\n"+json.dumps(row)+"\n")
            with self.assertRaisesRegex(ValueError, "DUPLICATE_SCREEN_ROW"):
                write_journal(src, dest)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
