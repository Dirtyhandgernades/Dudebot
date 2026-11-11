"""Research-only byte preservation for public Nasdaq RSS; never market clearance."""
import base64
import hashlib
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from backtest.obsidian_independent_quote_halt import NASDAQ_RSS, fetch_once

AT = datetime(2026, 11, 11, 18, 53, tzinfo=timezone.utc)
RSS = (b'<?xml version="1.0"?><rss><channel><item>'
       b'<IssueSymbol>JDZG</IssueSymbol>'
       b'<HaltDate>11/11/2026</HaltDate>'
       b'<HaltTime>12:40:00</HaltTime>'
       b'</item></channel></rss>')


class NasdaqRawReceiptEvidenceTests(unittest.TestCase):
    def test_pinned_valid_public_rss_is_byte_rehashable_without_claiming_authenticity(self):
        session = Mock()
        session.get.return_value = Mock(status_code=200, url=NASDAQ_RSS, content=RSS)
        report = fetch_once(["JDZG"], AT, session=session)
        raw = base64.b64decode(report["nasdaq_rss_raw_base64"], validate=True)
        self.assertEqual(raw, RSS)
        self.assertEqual(report["nasdaq_rss_raw_bytes"], len(RSS))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), report["nasdaq_rss_sha256"])
        self.assertTrue(report["nasdaq_rss_body_rehashable_from_artifact"])
        self.assertFalse(report["nasdaq_rss_upstream_authenticity_independently_verified"])
        self.assertFalse(report["live_exchange_session_open_verified"])
        self.assertFalse(report["complete_halt_history_or_guaranteed_open"])
        self.assertFalse(report["trade_authorized"])
        json.dumps(report, allow_nan=False)

    def test_invalid_public_rss_is_censored_not_archived(self):
        session = Mock()
        session.get.return_value = Mock(
            status_code=200, url=NASDAQ_RSS, content=b"<rss><channel><item>")
        report = fetch_once(["JDZG"], AT, session=session)
        self.assertIsNone(report["nasdaq_rss_raw_base64"])
        self.assertIsNone(report["nasdaq_rss_raw_bytes"])
        self.assertFalse(report["nasdaq_rss_body_rehashable_from_artifact"])
        self.assertEqual(report["halt_fetch_error"], "HALT_RSS_MALFORMED_OR_UNVERIFIABLE")
        self.assertEqual(report["halt_feed_status"], "NASDAQ_HALT_FEED_NOT_RETRIEVED")

    def test_spoofed_origin_cannot_archive_untrusted_rss(self):
        session = Mock()
        session.get.return_value = Mock(
            status_code=200, url="https://attacker.invalid/rss.aspx?feed=tradehalts",
            content=RSS)
        report = fetch_once(["JDZG"], AT, session=session)
        self.assertIsNone(report["nasdaq_rss_raw_base64"])
        self.assertFalse(report["nasdaq_rss_body_rehashable_from_artifact"])
        self.assertEqual(report["halt_fetch_error"], "HALT_RSS_UNTRUSTED_RESPONSE_ORIGIN")

    def test_massive_raw_payload_never_archived_even_if_vendor_reply_malformed(self):
        session = Mock()
        session.get.side_effect = [
            Mock(status_code=200, url=NASDAQ_RSS, content=RSS),
            Mock(status_code=200,
                 url="https://api.massive.com/v2/snapshot/locale/us/markets/stocks/tickers",
                 content=b'{"status":"OK","tickers":"private-secret-fixture"}'),
        ]
        report = fetch_once(["JDZG"], AT, massive_token="private-secret-fixture",
                            session=session)
        self.assertTrue(report["nasdaq_rss_body_rehashable_from_artifact"])
        self.assertEqual(report["quote_fetch_error"],
                         "INDEPENDENT_QUOTES_MALFORMED_OR_UNVERIFIABLE")
        self.assertNotIn("private-secret-fixture", json.dumps(report))
        self.assertNotIn("massive_raw_base64", report)
        self.assertFalse(report["trade_authorized"])


if __name__ == "__main__":
    unittest.main()
