"""Offline, source-accurate independent halt + quote intake tests."""
import unittest
import hashlib
import json
from unittest.mock import Mock
from datetime import datetime,timezone
from backtest.obsidian_independent_quote_halt import (
    parse_nasdaq_halts,parse_massive_snapshot,inspect_sources,phase,fetch_once,
    NASDAQ_RSS,MASSIVE_SNAPSHOT,
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

    def test_duplicate_issue_symbol_does_not_silently_replace_halt_identity(self):
        conflict=XML.replace(b"<n:IssueSymbol>JDZG</n:IssueSymbol>",
                             b"<n:IssueSymbol>JDZG</n:IssueSymbol><n:IssueSymbol>TJGC</n:IssueSymbol>")
        with self.assertRaisesRegex(ValueError,"HALT_RSS_DUPLICATE_FIELD"):
            parse_nasdaq_halts(conflict,AT)

    def test_duplicate_halt_time_does_not_silently_replace_event_time(self):
        conflict=XML.replace(b"<n:HaltTime>14:14:21</n:HaltTime>",
                             b"<n:HaltTime>14:14:21</n:HaltTime><n:HaltTime>15:14:21</n:HaltTime>")
        with self.assertRaisesRegex(ValueError,"HALT_RSS_DUPLICATE_FIELD"):
            parse_nasdaq_halts(conflict,AT)

    def test_duplicate_resume_time_censors_feed_before_halt_clearance(self):
        conflict=XML.replace(b"<n:TradeResumptionTime>15:29:22</n:TradeResumptionTime>",
                             b"<n:TradeResumptionTime>15:29:22</n:TradeResumptionTime><n:TradeResumptionTime>14:15:00</n:TradeResumptionTime>")
        session=Mock()
        session.get.return_value=Mock(status_code=200,url=NASDAQ_RSS,content=conflict)
        report=fetch_once(["JDZG"],AT,session=session)
        self.assertEqual(report["halt_fetch_error"],"HALT_RSS_MALFORMED_OR_UNVERIFIABLE")
        self.assertEqual(report["rows"][0]["halt_attention"],"HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION")
        self.assertFalse(report["trade_authorized"])
        self.assertFalse(report["complete_halt_history_or_guaranteed_open"])

    def test_resumption_date_alias_collision_is_ambiguous_evidence(self):
        duplicate=XML.replace(b"<n:ResumptionDate>10/28/2026</n:ResumptionDate>",
            b"<n:ResumptionDate>10/28/2026</n:ResumptionDate>"
            b"<n:ResumeDate>10/29/2026</n:ResumeDate>")
        with self.assertRaisesRegex(ValueError,"HALT_RSS_DUPLICATE_FIELD"):
            parse_nasdaq_halts(duplicate,AT)

    def test_resumption_trade_time_alias_collision_blocks_source(self):
        duplicate=XML.replace(b"<n:TradeResumptionTime>15:29:22</n:TradeResumptionTime>",
            b"<n:TradeResumptionTime>15:29:22</n:TradeResumptionTime>"
            b"<n:ResumptionTradeTime>15:30:22</n:ResumptionTradeTime>")
        session=Mock()
        session.get.return_value=Mock(status_code=200,url=NASDAQ_RSS,content=duplicate)
        report=fetch_once(["JDZG"],AT,session=session)
        self.assertEqual(report["halt_fetch_error"],"HALT_RSS_MALFORMED_OR_UNVERIFIABLE")
        self.assertEqual(report["rows"][0]["halt_attention"],"HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION")
        self.assertFalse(report["trade_authorized"])

    def test_single_alternate_resume_aliases_still_parse(self):
        for alias in (b"ResumptionTradeTime",b"ResumeTradeTime"):
            with self.subTest(alias=alias):
                xml=(XML.replace(b"ResumptionDate",b"ResumeDate")
                        .replace(b"TradeResumptionTime",alias))
                parsed=parse_nasdaq_halts(xml,AT)
                self.assertEqual(parsed[0]["resume_et"],"2026-10-28T15:29:22-04:00")
                self.assertEqual(parsed[0]["resumption_parse_status"],
                                 "EXPLICIT_DATE_AND_TRADE_TIME")

    def test_identical_repeated_halt_event_is_one_source_event(self):
        item=XML.split(b"<item>")[1].split(b"</item>")[0]
        duplicate=XML.replace(b"</channel>",b"<item>"+item+b"</item></channel>")
        parsed=parse_nasdaq_halts(duplicate,AT)
        self.assertEqual(len(parsed),1)
        self.assertEqual(parsed[0]["ticker"],"JDZG")

    def test_conflicting_reason_on_same_halt_event_rejects_rss(self):
        item=XML.split(b"<item>")[1].split(b"</item>")[0]
        changed=item.replace(b"<n:ReasonCode>LUDP</n:ReasonCode>",
                             b"<n:ReasonCode>T12</n:ReasonCode>")
        conflicting=XML.replace(b"</channel>",b"<item>"+changed+b"</item></channel>")
        with self.assertRaisesRegex(ValueError,"HALT_RSS_CONFLICTING_DUPLICATE_EVENT"):
            parse_nasdaq_halts(conflicting,AT)

    def test_conflicting_resume_on_same_halt_event_censors_collection(self):
        item=XML.split(b"<item>")[1].split(b"</item>")[0]
        changed=item.replace(b"15:29:22",b"15:30:22")
        conflicting=XML.replace(b"</channel>",b"<item>"+changed+b"</item></channel>")
        session=Mock()
        session.get.return_value=Mock(status_code=200,url=NASDAQ_RSS,content=conflicting)
        report=fetch_once(["JDZG"],AT,session=session)
        self.assertEqual(report["halt_fetch_error"],"HALT_RSS_MALFORMED_OR_UNVERIFIABLE")
        self.assertEqual(report["rows"][0]["halt_attention"],
                         "HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION")
        self.assertFalse(report["trade_authorized"])

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
                         "NO_HALT_ROW_IN_FINITE_RSS_NOT_LIVE_CLEARANCE")
        self.assertFalse(row["complete_halt_history_or_guaranteed_open"])

    def test_elapsed_resumption_never_becomes_positive_live_clearance(self):
        after=datetime(2026,10,28,20,40,tzinfo=timezone.utc)
        row=inspect_sources(["JDZG"],after,XML)["rows"][0]
        self.assertEqual(row["halt_attention"],
                         "RESUMPTION_TIME_ELAPSED_LIVE_STATUS_UNVERIFIED")
        self.assertFalse(row["smg_short_authorized"])

    def test_future_halt_notice_not_retroactively_active_or_cleared(self):
        future=XML.replace(b"10/28/2026",b"10/29/2026")
        row=inspect_sources(["JDZG"],AT,future)["rows"][0]
        self.assertEqual(row["halt_attention"],
                         "FUTURE_HALT_NOTICE_LIVE_STATUS_UNVERIFIED")
        self.assertFalse(row["smg_short_authorized"])

    def test_mixed_halt_history_prefers_unresolved_halt_over_elapsed_resume(self):
        unresolved=XML.replace(b"<n:TradeResumptionTime>15:29:22</n:TradeResumptionTime>",b"")
        extra=unresolved.split(b"<item>")[1].split(b"</item>")[0]
        mixed=XML.replace(b"</channel>",b"<item>"+extra+b"</item></channel>")
        after=datetime(2026,10,28,20,40,tzinfo=timezone.utc)
        row=inspect_sources(["JDZG"],after,mixed)["rows"][0]
        self.assertEqual(row["halt_attention"],
                         "HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING")
        self.assertFalse(row["smg_short_authorized"])

    def test_stale_massive_quote_blocks_freshness(self):
        t=int(datetime(2026,10,28,19,00,tzinfo=timezone.utc).timestamp()*1e9)
        payload={"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":{"t":t,"p":5.21}}]}
        result=parse_massive_snapshot(payload,["JDZG"],AT)
        self.assertEqual(result["JDZG"]["status"],"DELAYED_OR_STALE_PROVIDER_PRINT")
        self.assertIsNone(result["JDZG"]["price"])
        self.assertTrue(result["JDZG"]["quote_price_censored"])
        self.assertIsNotNone(result["JDZG"]["price_at"])

    def test_future_massive_quote_is_censored_not_usable_price(self):
        t=int(datetime(2026,10,28,19,28,10,tzinfo=timezone.utc).timestamp()*1e9)
        payload={"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":{"t":t,"p":9.01}}]}
        result=parse_massive_snapshot(payload,["JDZG"],AT)
        self.assertEqual(result["JDZG"]["status"],"FUTURE_DATED_PROVIDER_PRINT")
        self.assertIsNone(result["JDZG"]["price"])
        self.assertTrue(result["JDZG"]["quote_price_censored"])
        self.assertIsNotNone(result["JDZG"]["price_at"])

    def test_fresh_massive_quote_remains_diagnostic_not_official_close(self):
        t=int(datetime(2026,10,28,19,27,30,tzinfo=timezone.utc).timestamp()*1e9)
        payload={"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":{"t":t,"p":4.12}}]}
        result=parse_massive_snapshot(payload,["JDZG"],AT)
        self.assertEqual(result["JDZG"]["price"],4.12)
        self.assertFalse(result["JDZG"]["quote_price_censored"])
        self.assertFalse(result["JDZG"]["independent_official_close_verified"])
        self.assertFalse(result["JDZG"]["has_verified_realtime_entitlement"])

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


    def test_partial_resumption_date_preserves_halt_and_blocks_execution(self):
        # Live Nasdaq RSS may publish the resumption date before a trade time.
        xml=XML.replace(b"<n:TradeResumptionTime>15:29:22</n:TradeResumptionTime>",b"")
        parsed=parse_nasdaq_halts(xml,AT)
        self.assertEqual(len(parsed),1)
        self.assertIsNone(parsed[0]["resume_et"])
        self.assertEqual(parsed[0]["resumption_parse_status"],"INCOMPLETE")
        self.assertEqual(parsed[0]["halt_state_at_receipt"],
                         "HALT_REPORTED_WITHOUT_VERIFIED_RESUME")
        review=inspect_sources(["JDZG"],AT,xml)
        self.assertEqual(review["rows"][0]["halt_attention"],
                         "HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING")
        self.assertFalse(review["trade_authorized"])

    def test_unparseable_or_earlier_resume_does_not_drop_official_halt(self):
        for value,expected in (("NOT_YET_PUBLISHED","UNPARSEABLE"),
                               ("13:00:00","BEFORE_HALT")):
            with self.subTest(value=value):
                xml=XML.replace(b"15:29:22",value.encode("ascii"))
                parsed=parse_nasdaq_halts(xml,AT)
                self.assertEqual(parsed[0]["resumption_parse_status"],expected)
                self.assertIsNone(parsed[0]["resume_et"])
                self.assertEqual(parsed[0]["halt_state_at_receipt"],
                                 "HALT_REPORTED_WITHOUT_VERIFIED_RESUME")


    def test_redirects_are_never_followed_for_official_halts_or_independent_quotes(self):
        class Session:
            def __init__(self, statuses, urls):
                self.statuses=list(statuses)
                self.urls=list(urls)
                self.calls=[]
            def get(self, url, **kwargs):
                self.calls.append((url,kwargs))
                return Mock(status_code=self.statuses.pop(0),url=self.urls.pop(0))
        session=Session([302,307],[NASDAQ_RSS,MASSIVE_SNAPSHOT])
        report=fetch_once(["JDZG"],AT,massive_token="fixture",session=session)
        self.assertEqual(report["halt_fetch_error"],"HALT_RSS_HTTP_302")
        self.assertEqual(report["quote_fetch_error"],"INDEPENDENT_QUOTES_HTTP_307")
        self.assertEqual(report["rows"][0]["halt_attention"],"HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION")
        self.assertFalse(report["quote_source_connected"])
        self.assertFalse(report["trade_authorized"])
        self.assertEqual(len(session.calls),2)
        self.assertTrue(all(call[1].get("allow_redirects") is False for call in session.calls))

    def test_spoofed_200_origin_is_censored_without_parsing_body_or_token_leak(self):
        class Session:
            def __init__(self):
                self.calls=[]
            def get(self, url, **kwargs):
                self.calls.append((url,kwargs))
                return Mock(status_code=200,url="https://attacker.invalid/rss.aspx?feed=tradehalts")
        session=Session()
        report=fetch_once(["JDZG"],AT,massive_token="fixture-secret",session=session)
        self.assertEqual(report["halt_fetch_error"],"HALT_RSS_UNTRUSTED_RESPONSE_ORIGIN")
        self.assertEqual(report["quote_fetch_error"],"INDEPENDENT_QUOTES_UNTRUSTED_RESPONSE_ORIGIN")
        self.assertEqual(report["halt_feed_status"],"NASDAQ_HALT_FEED_NOT_RETRIEVED")
        self.assertFalse(report["quote_source_connected"])
        self.assertNotIn("fixture-secret",str(report))
        self.assertFalse(report["actual_smg_platform_eligibility_verified"])
        self.assertTrue(all(call[1].get("allow_redirects") is False for call in session.calls))

    def test_pinned_nasdaq_response_is_parsed_without_claiming_open_or_shortable(self):
        session=Mock()
        session.get.return_value=Mock(status_code=200,url=NASDAQ_RSS,content=XML)
        report=fetch_once(["JDZG"],AT,session=session)
        self.assertEqual(report["halt_feed_status"],"NASDAQ_RSS_PARSED_WITH_ASOF_LIMITATIONS")
        self.assertEqual(report["rows"][0]["halt_attention"],"HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING")
        self.assertFalse(report["trade_authorized"])
        self.assertFalse(report["quote_source_connected"])
        self.assertFalse(session.get.call_args.kwargs["allow_redirects"])

    def test_direct_collector_rejects_weekend_before_any_get(self):
        session=Mock()
        with self.assertRaisesRegex(ValueError,"OUTSIDE_RESEARCH_CHECKPOINT"):
            fetch_once(["JDZG"],datetime(2026,11,1,20,49,tzinfo=timezone.utc),
                       massive_token="fixture-secret",session=session)
        session.get.assert_not_called()

    def test_published_2026_full_holidays_reject_provider_gets(self):
        # 12:47 CST would otherwise fall inside the original INTRADAY gate.
        for day in (26,):
            at=datetime(2026,11,day,18,47,tzinfo=timezone.utc)
            session=Mock()
            self.assertIsNone(phase(at))
            with self.assertRaisesRegex(ValueError,"OUTSIDE_RESEARCH_CHECKPOINT"):
                fetch_once(["JDZG"],at,massive_token="fixture",session=session)
            session.get.assert_not_called()
        at=datetime(2026,12,25,18,47,tzinfo=timezone.utc)
        self.assertIsNone(phase(at))

    def test_early_close_blocks_post_close_intraday_and_board_windows(self):
        for at in (datetime(2026,11,27,18,47,tzinfo=timezone.utc),
                   datetime(2026,12,24,20,20,tzinfo=timezone.utc)):
            session=Mock()
            self.assertIsNone(phase(at))
            with self.assertRaisesRegex(ValueError,"OUTSIDE_RESEARCH_CHECKPOINT"):
                fetch_once(["JDZG"],at,massive_token="fixture",session=session)
            session.get.assert_not_called()

    def test_early_close_morning_and_postclose_research_remain_distinct(self):
        self.assertEqual(phase(datetime(2026,11,27,15,20,tzinfo=timezone.utc)),"MORNING")
        self.assertEqual(phase(datetime(2026,11,27,21,10,tzinfo=timezone.utc)),"AFTERHOURS")
        self.assertEqual(phase(datetime(2026,11,2,18,47,tzinfo=timezone.utc)),"INTRADAY")

    def test_unreviewed_calendar_year_fails_closed_before_network(self):
        at=datetime(2027,1,4,18,47,tzinfo=timezone.utc)
        session=Mock()
        self.assertIsNone(phase(at))
        with self.assertRaisesRegex(ValueError,"OUTSIDE_RESEARCH_CHECKPOINT"):
            fetch_once(["JDZG"],at,massive_token="fixture",session=session)
        session.get.assert_not_called()

    def test_direct_collector_rejects_bad_symbols_before_any_get(self):
        session=Mock()
        with self.assertRaisesRegex(ValueError,"INVALID_REQUESTED_SYMBOLS"):
            fetch_once(["JDZG&apiKey=leak"],AT,massive_token="fixture-secret",
                       session=session)
        session.get.assert_not_called()

    def test_direct_collector_rejects_duplicates_before_any_get(self):
        session=Mock()
        with self.assertRaisesRegex(ValueError,"DUPLICATE_REQUESTED_SYMBOL"):
            fetch_once(["JDZG","JDZG"],AT,massive_token="fixture-secret",
                       session=session)
        session.get.assert_not_called()

    def test_network_adapter_failures_are_censored_without_leaking_tokens(self):
        class BrokenSession:
            def get(self, url, **kwargs):
                raise RuntimeError("private credential echoed by transport")
        report=fetch_once(["JDZG"],AT,massive_token="secret-fixture",session=BrokenSession())
        self.assertEqual(report["halt_fetch_error"],"HALT_RSS_UNAVAILABLE_OR_TRANSPORT_ERROR")
        self.assertEqual(report["quote_fetch_error"],"INDEPENDENT_QUOTES_UNAVAILABLE_OR_TRANSPORT_ERROR")
        self.assertEqual(report["rows"][0]["halt_attention"],"HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION")
        self.assertFalse(report["quote_source_connected"])
        self.assertNotIn("secret-fixture",str(report))
        self.assertFalse(report["trade_authorized"])

    def test_malformed_200_nasdaq_xml_is_censored_not_open(self):
        session=Mock()
        session.get.return_value=Mock(status_code=200,url=NASDAQ_RSS,
                                      content=b"<rss><channel><item>")
        report=fetch_once(["JDZG"],AT,session=session)
        self.assertEqual(report["halt_fetch_error"],"HALT_RSS_MALFORMED_OR_UNVERIFIABLE")
        self.assertEqual(report["halt_feed_status"],"NASDAQ_HALT_FEED_NOT_RETRIEVED")
        self.assertEqual(report["rows"][0]["halt_attention"],"HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION")
        self.assertFalse(report["complete_halt_history_or_guaranteed_open"])

    def test_malformed_200_massive_payload_is_censored_without_losing_halt(self):
        session=Mock()
        session.get.side_effect=[
            Mock(status_code=200,url=NASDAQ_RSS,content=XML),
            Mock(status_code=200,url=MASSIVE_SNAPSHOT,
                 content=b'{"status":"OK","tickers":"not-a-list"}'),
        ]
        report=fetch_once(["JDZG"],AT,massive_token="secret-fixture",session=session)
        self.assertEqual(report["quote_fetch_error"],"INDEPENDENT_QUOTES_MALFORMED_OR_UNVERIFIABLE")
        self.assertFalse(report["quote_source_connected"])
        self.assertEqual(report["rows"][0]["independent_quote"]["status"],
                         "INDEPENDENT_QUOTE_PROVIDER_NOT_CONNECTED")
        self.assertEqual(report["halt_feed_status"],"NASDAQ_RSS_PARSED_WITH_ASOF_LIMITATIONS")
        self.assertEqual(report["rows"][0]["halt_attention"],"HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING")
        self.assertFalse(report["trade_authorized"])

    def test_duplicate_nested_massive_json_keys_are_censored_and_halt_retained(self):
        raw=(b'{"status":"OK","tickers":[{"ticker":"JDZG",'
             b'"lastTrade":{"t":1793215650000000000,"p":4.12,"p":7.31}}]}')
        session=Mock()
        session.get.side_effect=[
            Mock(status_code=200,url=NASDAQ_RSS,content=XML),
            Mock(status_code=200,url=MASSIVE_SNAPSHOT,content=raw),
        ]
        report=fetch_once(["JDZG"],AT,massive_token="fixture-secret",session=session)
        self.assertEqual(report["quote_fetch_error"],"INDEPENDENT_QUOTES_MALFORMED_OR_UNVERIFIABLE")
        self.assertFalse(report["quote_source_connected"])
        self.assertEqual(report["independent_quote_receipt_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["independent_quote_receipt_bytes"],len(raw))
        self.assertEqual(report["rows"][0]["halt_attention"],
                         "HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING")
        self.assertFalse(report["independent_quote_receipt_independently_authenticated"])
        self.assertNotIn("fixture-secret",str(report))

    def test_valid_massive_json_has_receipt_digest_but_no_official_close_proof(self):
        stamp=int(datetime(2026,10,28,19,27,30,tzinfo=timezone.utc).timestamp()*1e9)
        raw=json.dumps({"status":"OK","tickers":[{"ticker":"JDZG",
                        "lastTrade":{"t":stamp,"p":4.12}}]}).encode("utf-8")
        session=Mock()
        session.get.side_effect=[
            Mock(status_code=200,url=NASDAQ_RSS,content=XML),
            Mock(status_code=200,url=MASSIVE_SNAPSHOT,content=raw),
        ]
        report=fetch_once(["JDZG"],AT,massive_token="fixture",session=session)
        self.assertIsNone(report["quote_fetch_error"])
        self.assertTrue(report["quote_source_connected"])
        self.assertEqual(report["independent_quote_receipt_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["rows"][0]["independent_quote"]["status"],
                         "FRESH_PROVIDER_TRADE_ENTITLEMENT_UNVERIFIED")
        self.assertFalse(report["rows"][0]["independent_quote"]["independent_official_close_verified"])
        self.assertFalse(report["realtime_plan_entitlement_verified"])
        self.assertFalse(report["trade_authorized"])

    def test_massive_nested_numeric_rounding_and_integer_overflow_are_censored(self):
        # A valid-looking quote must not be admitted when any JSON numeric
        # token silently loses its declared value, even in auxiliary fields.
        oversized_integer=b"9"*101
        invalid_bodies=(
            b'{"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":'
            b'{"t":1793215650000000000,"p":4.12},"aux":1e-400}]}',
            b'{"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":'
            b'{"t":1793215650000000000,"p":4.1200000000000001}}]}',
            b'{"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":'
            b'{"t":1793215650000000000,"p":4.12},"aux":'+oversized_integer+b'}]}',
        )
        for raw in invalid_bodies:
            with self.subTest(raw=raw[-35:]):
                session=Mock()
                session.get.side_effect=[
                    Mock(status_code=200,url=NASDAQ_RSS,content=XML),
                    Mock(status_code=200,url=MASSIVE_SNAPSHOT,content=raw),
                ]
                report=fetch_once(["JDZG"],AT,massive_token="fixture",session=session)
                self.assertEqual(report["quote_fetch_error"],
                                 "INDEPENDENT_QUOTES_MALFORMED_OR_UNVERIFIABLE")
                self.assertFalse(report["quote_source_connected"])
                self.assertEqual(report["independent_quote_receipt_sha256"],
                                 hashlib.sha256(raw).hexdigest())
                self.assertEqual(report["rows"][0]["halt_attention"],
                                 "HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING")
                self.assertFalse(report["trade_authorized"])

    def test_massive_ordinary_float_exponent_and_integer_auxiliary_remain_accepted(self):
        t=int(datetime(2026,10,28,19,27,30,tzinfo=timezone.utc).timestamp()*1e9)
        raw=(b'{"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":'
             b'{"t":'+str(t).encode()+b',"p":4.12},"aux":1e-12,"count":12}]}')
        session=Mock()
        session.get.side_effect=[
            Mock(status_code=200,url=NASDAQ_RSS,content=XML),
            Mock(status_code=200,url=MASSIVE_SNAPSHOT,content=raw),
        ]
        report=fetch_once(["JDZG"],AT,massive_token="fixture",session=session)
        self.assertIsNone(report["quote_fetch_error"])
        self.assertTrue(report["quote_source_connected"])
        self.assertEqual(report["rows"][0]["independent_quote"]["status"],
                         "FRESH_PROVIDER_TRADE_ENTITLEMENT_UNVERIFIED")
        self.assertFalse(report["realtime_plan_entitlement_verified"])

    def test_nonfinite_and_oversized_massive_json_fail_closed(self):
        for raw in (
            b'{"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":{"t":1,"p":NaN}}]}',
            b'{"status":"OK","tickers":[{"ticker":"JDZG","lastTrade":{"t":1,"p":1e999}}]}',
            b" " * 3_000_001,
        ):
            with self.subTest(size=len(raw)):
                session=Mock()
                session.get.side_effect=[
                    Mock(status_code=200,url=NASDAQ_RSS,content=XML),
                    Mock(status_code=200,url=MASSIVE_SNAPSHOT,content=raw),
                ]
                report=fetch_once(["JDZG"],AT,massive_token="fixture",session=session)
                self.assertEqual(report["quote_fetch_error"],
                                 "INDEPENDENT_QUOTES_MALFORMED_OR_UNVERIFIABLE")
                self.assertFalse(report["quote_source_connected"])
                self.assertEqual(report["rows"][0]["halt_attention"],
                                 "HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING")
                self.assertFalse(report["trade_authorized"])
                if len(raw)>3_000_000:
                    self.assertIsNone(report["independent_quote_receipt_sha256"])

if __name__=="__main__":
    unittest.main()
