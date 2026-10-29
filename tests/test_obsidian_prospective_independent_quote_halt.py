"""Offline, source-accurate independent halt + quote intake tests."""
import unittest
from datetime import datetime,timezone
from backtest.obsidian_independent_quote_halt import (
    parse_nasdaq_halts,parse_massive_snapshot,inspect_sources,phase,
)
AT=datetime(2026,10,28,19,28,tzinfo=timezone.utc)
XML=b"""<?xml version="1.0"?><rss version="2.0" xmlns:n="http://www.nasdaqtrader.com/rss"><channel><title>Current Trade Halts</title><item><n:IssueSymbol>JDZG</n:IssueSymbol><n:HaltDate>10/28/2026</n:HaltDate><n:HaltTime>14:14:21</n:HaltTime><n:ReasonCode>LUDP</n:ReasonCode><n:ResumptionDate>10/28/2026</n:ResumptionDate><n:TradeResumptionTime>15:29:22</n:TradeResumptionTime></item></channel></rss>"""


class SourceGateTests(unittest.TestCase):
    def test_halt_feed_has_exact_eastern_and_temporary_status(self):
        parsed=parse_nasdaq_halts(XML,AT)
        self.assertEqual(len(parsed),1)
        self.assertEqual(parsed[0]["ticker"],"JDZG")
        self.assertEqual(parsed[0]["halt_et"],"2026-10-28T14:14:21-04:00")
        self.assertEqual(parsed[0]["halt_state_at_receipt"],
                         "HALT_SCHEDULED_RESUMPTION_NOT_YET_ELAPSED")

    def test_nasdaq_namespace_is_supported(self):
        self.assertEqual(phase(AT),"EARLY_BOARD")

    def test_missing_feed_does_not_claim_open(self):
        row=inspect_sources(["JDZG"],AT)
        self.assertEqual(row["rows"][0]["halt_attention"],"HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION")
        self.assertFalse(row["trade_authorized"])

    def test_empty_feed_not_equivalent_to_confirmed_open(self):
        empty=b"<rss><channel><title>No halts</title></channel></rss>"
        row=inspect_sources(["JDZG"],AT,empty)
        self.assertEqual(row["rows"][0]["halt_attention"],
                         "NO_ACTIVE_HALT_CONFIRMED_FROM_RECEIVED_FEED_ONLY")
        self.assertFalse(row["complete_halt_history_or_guaranteed_open"])

    def test_stale_massive_quote_blocks_freshness(self):
        t=int(datetime(2026,10,28,19,00,tzinfo=timezone.utc).timestamp()*1e9)
        payload={"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":{"t":t,"p":5.21}}]}
        result=parse_massive_snapshot(payload,["JDZG"],AT)
        self.assertEqual(result["JDZG"]["status"],"DELAYED_OR_STALE_PROVIDER_PRINT")

    def test_fresh_quote_does_not_claim_subscription_entitlement(self):
        t=int(datetime(2026,10,28,19,27,30,tzinfo=timezone.utc).timestamp()*1e9)
        row=inspect_sources(["JDZG"],AT,XML,{"status":"OK","tickers":[
            {"ticker":"JDZG","lastTrade":{"t":t,"p":4.12}}]})["rows"][0]
        self.assertEqual(row["independent_quote"]["status"],
                         "FRESH_PROVIDER_TRADE_ENTITLEMENT_UNVERIFIED")
        self.assertFalse(row["independent_quote"]["has_verified_realtime_entitlement"])
        self.assertFalse(row["smg_short_authorized"])

    def test_unexpected_symbol_and_duplicates_fail(self):
        payload={"status":"OK","tickers":[{"ticker":"OTHER","lastTrade":{"p":7,"t":1}}]}
        with self.assertRaisesRegex(ValueError,"EXTRA_OR_INVALID"):
            parse_massive_snapshot(payload,["JDZG"],AT)
        with self.assertRaisesRegex(ValueError,"DUPLICATE_REQUESTED"):
            inspect_sources(["JDZG","JDZG"],AT)

    def test_future_halt_not_retrospectively_asof(self):
        earlier=datetime(2026,10,28,17,00,tzinfo=timezone.utc)
        self.assertEqual(parse_nasdaq_halts(XML,earlier)[0]["halt_state_at_receipt"],
                         "HALT_FUTURE_EVENT_NOT_YET_EFFECTIVE")

    def test_outside_checkpoint_rejected(self):
        with self.assertRaisesRegex(ValueError,"OUTSIDE"):
            inspect_sources(["JDZG"],datetime(2026,10,31,19,48,tzinfo=timezone.utc))

if __name__=="__main__":
    unittest.main()
