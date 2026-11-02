"""Independent research-only price source and Nasdaq official halt-feed intake.

No background streaming, no live trading, no SMG platform access and no implicit
real-time subscription. Single checkpoint GETs; snapshots are collected as-of
receipt, never rewritten into the previously frozen OBSIDIAN IEX capture.
"""
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
NASDAQ_RSS = "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"
MASSIVE_SNAPSHOT = "https://api.massive.com/v2/snapshot/locale/us/markets/stocks/tickers"
CENTRAL = ZoneInfo("America/Chicago")
EASTERN = ZoneInfo("America/New_York")
ALLOWED_PHASES = ("MORNING", "INTRADAY", "EARLY_BOARD", "AFTERHOURS")
SAFE_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.]{0,12}$")

# Published 2026 NYSE/Nasdaq U.S. equity schedule, not a live market-open
# attestation. Fail closed outside this explicitly reviewed calendar year.
# Sources: https://www.nyse.com/trade/hours-calendars
#          https://www.nasdaq.com/market-activity/stock-market-holiday-schedule
NYSE_NASDAQ_2026_CLOSED = frozenset(date.fromisoformat(d) for d in (
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
    "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
    "2026-11-26", "2026-12-25",
))
NYSE_NASDAQ_2026_EARLY_CLOSE = frozenset(date.fromisoformat(d) for d in (
    "2026-11-27", "2026-12-24",
))

def _trusted_response_origin(actual, expected, exact_query=False):
    """Reject redirected or substituted 200s before labeling official sources.

    Pin HTTPS endpoint origin/path without archiving credential-bearing URLs.
    This is a transport-origin gate, not an official-price entitlement proof.
    """
    if not isinstance(actual, str):
        return False
    try:
        got, want = urlsplit(actual), urlsplit(expected)
        return (got.scheme == want.scheme == "https"
                and got.netloc == want.netloc
                and got.path == want.path
                and not got.fragment
                and (not exact_query or got.query == want.query))
    except ValueError:
        return False


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _day(s):
    for fmt in ("%m/%d/%Y", "%m%d%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except (ValueError, TypeError):
            pass
    return None


def _when(day, time_str):
    parsed = _day(day)
    if not parsed or not str(time_str).strip():
        return None
    for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(str(time_str).strip(), fmt).time()
            return datetime.combine(parsed, t, tzinfo=EASTERN)
        except ValueError:
            continue
    return None


def phase(now):
    if not isinstance(now, datetime) or now.utcoffset() is None:
        return None
    t = now.astimezone(CENTRAL)
    # A weekday is not sufficient: full-session holidays and shortened
    # 13:00 ET sessions must never be treated as open intraday/board windows.
    # Extraordinary closures still require a separately authenticated
    # live session check; this finite module does not certify market open.
    if (t.weekday() >= 5 or t.date().year != 2026
            or t.date() in NYSE_NASDAQ_2026_CLOSED):
        return None
    hm=t.hour * 60 + t.minute
    if (t.date() in NYSE_NASDAQ_2026_EARLY_CLOSE
            and 12 * 60 <= hm < 15 * 60):
        return None
    if 9 * 60 <= hm <= 9 * 60 + 40:
        return "MORNING"
    if 12 * 60 + 40 <= hm <= 13 * 60 + 15:
        return "INTRADAY"
    if 14 * 60 <= hm < 14 * 60 + 45:
        return "EARLY_BOARD"
    if 15 * 60 <= hm <= 22 * 60 + 45:
        return "AFTERHOURS"
    return None


def parse_nasdaq_halts(raw, captured_at):
    """RSS may be updated once/minute. A missing row is NOT proof of no halt."""
    if not isinstance(captured_at, datetime) or captured_at.utcoffset() is None:
        raise ValueError("AWARE_CAPTURE_TIME_REQUIRED")
    if not isinstance(raw, bytes) or not raw or len(raw) > 3_000_000:
        raise ValueError("MISSING_OR_OVERSIZE_NASDAQ_XML")
    root = ET.fromstring(raw)
    if _local(root.tag) != "rss":
        raise ValueError("NOT_NASDAQ_RSS_FORMAT")
    channel=next((x for x in root if _local(x.tag)=="channel"), None)
    if channel is None:
        raise ValueError("RSS_CHANNEL_MISSING")
    rows = []
    seen = set()
    for item in channel:
        if _local(item.tag)!="item":
            continue
        fields={_local(c.tag).replace("_",""): (c.text or "").strip() for c in item}
        symbol=(fields.get("issuesymbol") or "").upper()
        if not SAFE_SYMBOL.fullmatch(symbol):
            raise ValueError("HALT_RSS_INVALID_SYMBOL")
        halt=_when(fields.get("haltdate"),fields.get("halttime"))
        if halt is None:
            raise ValueError("HALT_RSS_MISSING_EXACT_HALT_TIMESTAMP")
        # Nasdaq's RSS field names have changed over time; use only explicit
        # exact resume date+trade time when both are present.
        resume_date=fields.get("resumptiondate") or fields.get("resumedate")
        resume_time=(fields.get("traderesumptiontime") or
                     fields.get("resumptiontradetime") or fields.get("resumetradetime"))
        # The live RSS can contain a resumption date without an actual
        # trading-resumption time (or vice versa). Preserve the HALT rather
        # than rejecting the entire official feed or inventing a resume.
        resume=_when(resume_date,resume_time) if resume_date and resume_time else None
        resume_quality=("ABSENT" if not (resume_date or resume_time)
                        else "INCOMPLETE" if not (resume_date and resume_time)
                        else "UNPARSEABLE" if resume is None
                        else "BEFORE_HALT" if resume < halt
                        else "EXPLICIT_DATE_AND_TRADE_TIME")
        if resume_quality != "EXPLICIT_DATE_AND_TRADE_TIME":
            resume=None
        key=(symbol,halt.isoformat(),resume.isoformat() if resume else "")
        if key in seen:
            continue
        seen.add(key)
        if halt > captured_at.astimezone(EASTERN):
            state="HALT_FUTURE_EVENT_NOT_YET_EFFECTIVE"
        elif resume is None:
            state="HALT_REPORTED_WITHOUT_VERIFIED_RESUME"
        elif resume > captured_at.astimezone(EASTERN):
            state="HALT_SCHEDULED_RESUMPTION_NOT_YET_ELAPSED"
        else:
            state="RESUMPTION_TIME_HAS_PASSED_RECHECK_LIVE_STATUS"
        rows.append({
            "ticker":symbol, "halt_et":halt.isoformat(),
            "resume_et":resume.isoformat() if resume else None,
            "resumption_parse_status":resume_quality,
            "reason_code":fields.get("reasoncode") or None,
            "halt_state_at_receipt":state,
            "source":"NASDAQ_TRADER_OFFICIAL_RSS",
            "retrieved_at":captured_at.isoformat(),
            "not_proof_of_shortability":True,
        })
    return rows


def parse_massive_snapshot(payload, symbols, captured_at):
    """Independently supplied timestamped trades; provider plan is unverified."""
    if not isinstance(payload,dict) or payload.get("status")!="OK":
        raise ValueError("INDEPENDENT_PROVIDER_RETURNED_NON_OK")
    if not isinstance(payload.get("tickers"),list):
        raise ValueError("INDEPENDENT_PROVIDER_TICKERS_MISSING")
    output={}
    requested=set(symbols)
    for entry in payload["tickers"]:
        if not isinstance(entry,dict) or entry.get("ticker") not in requested:
            raise ValueError("INDEPENDENT_PROVIDER_EXTRA_OR_INVALID_SYMBOL")
        sym=entry["ticker"]
        if sym in output:
            raise ValueError("INDEPENDENT_PROVIDER_DUPLICATE_SYMBOL")
        trade=entry.get("lastTrade")
        t=trade.get("t") if isinstance(trade,dict) else None
        p=trade.get("p") if isinstance(trade,dict) else None
        if type(t) is not int or t <= 0 or type(p) not in (int,float) or not (0<p<1e9):
            output[sym]={"status":"NO_TIMED_INDEPENDENT_TRADE","price":None,
                         "price_at":None,"independent_provider":"MASSIVE"}
            continue
        try:
            when=datetime.fromtimestamp(t / 1_000_000_000, tz=timezone.utc)
        except (OverflowError,OSError,ValueError):
            output[sym]={"status":"INVALID_INDEPENDENT_TIMESTAMP","price":None,
                         "price_at":None,"independent_provider":"MASSIVE"}
            continue
        age=(captured_at-when).total_seconds()
        status=("FRESH_PROVIDER_TRADE_ENTITLEMENT_UNVERIFIED" if 0<=age<=60
                else "FUTURE_DATED_PROVIDER_PRINT" if age<0
                else "DELAYED_OR_STALE_PROVIDER_PRINT")
        output[sym]={"status":status,"price":p,"price_at":when.isoformat(),
                     "age_seconds":round(age,3),"independent_provider":"MASSIVE",
                     "has_verified_realtime_entitlement":False,
                     "independent_official_close_verified":False}
    for ticker in symbols:
        output.setdefault(ticker,{"status":"INDEPENDENT_PROVIDER_SYMBOL_ABSENT",
                                  "price":None,"price_at":None,
                                  "independent_provider":"MASSIVE"})
    return output


def inspect_sources(symbols, now, halt_xml=None, massive_payload=None):
    if not isinstance(now,datetime) or now.utcoffset() is None:
        raise ValueError("AWARE_OBSERVATION_TIME_REQUIRED")
    if phase(now) is None:
        raise ValueError("MONITOR_OUTSIDE_RESEARCH_CHECKPOINT")
    if not isinstance(symbols,list) or not symbols:
        raise ValueError("NONEMPTY_SYMBOL_LIST_REQUIRED")
    if any(not isinstance(s,str) or not SAFE_SYMBOL.fullmatch(s) for s in symbols):
        raise ValueError("INVALID_REQUESTED_SYMBOLS")
    if len(set(symbols))!=len(symbols):
        raise ValueError("DUPLICATE_REQUESTED_SYMBOL")
    if halt_xml is None:
        halt_events=[]
        halt_state="NASDAQ_HALT_FEED_NOT_RETRIEVED"
    else:
        halt_events=parse_nasdaq_halts(halt_xml,now)
        halt_state="NASDAQ_RSS_PARSED_WITH_ASOF_LIMITATIONS"
    quotes = (parse_massive_snapshot(massive_payload,symbols,now) if massive_payload is not None
              else {s:{"status":"INDEPENDENT_QUOTE_PROVIDER_NOT_CONNECTED",
                       "independent_provider":"MASSIVE","price":None} for s in symbols})
    bysymbol={}
    for event in halt_events:
        bysymbol.setdefault(event["ticker"],[]).append(event)
    result=[]
    for s in symbols:
        hs=bysymbol.get(s,[])
        state=("HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING" if any(
            x["halt_state_at_receipt"] in ("HALT_REPORTED_WITHOUT_VERIFIED_RESUME",
                "HALT_SCHEDULED_RESUMPTION_NOT_YET_ELAPSED") for x in hs)
            else "NO_ACTIVE_HALT_CONFIRMED_FROM_RECEIVED_FEED_ONLY")
        if halt_xml is None:
            state="HALT_SOURCE_UNAVAILABLE_BLOCK_EXECUTION"
        result.append({"ticker":s,"independent_quote":quotes[s],
                       "halt_evidence":hs,"halt_attention":state,
                       "smg_short_authorized":False,
                       "predictive_edge_established":False})
    return {"mode":MODE,"asof":now.isoformat(),"phase":phase(now),
            "requested_symbols":len(symbols),
            "nasdaq_halt_source":NASDAQ_RSS,
            "halt_feed_status":halt_state,
            "nasdaq_rss_sha256":hashlib.sha256(halt_xml).hexdigest() if halt_xml else None,
            "independent_quote_endpoint":MASSIVE_SNAPSHOT,
            "quote_source_connected":massive_payload is not None,
            "realtime_plan_entitlement_verified":False,
            "source_research_only_not_full_market":True,
            "calendar_basis":"PUBLISHED_2026_NYSE_NASDAQ_STATIC_NOT_LIVE_OPEN_PROOF",
            "live_exchange_session_open_verified":False,
            "complete_halt_history_or_guaranteed_open":False,
            "actual_smg_platform_eligibility_verified":False,
            "trade_authorized":False,"rows":result}


def fetch_once(symbols, now, massive_token=None, session=None):
    """At most one official halt GET and one Massive GET per research checkpoint."""
    # Validate time, phase, symbol syntax and uniqueness BEFORE any HTTP GET.
    # Direct callers must not bypass the main() collection gate or send malformed
    # tickers to a credential-bearing optional provider request.
    inspect_sources(symbols, now)
    # Offline deterministic tests inject a read-only session; only the real
    # hosted network collector needs the optional requests dependency.
    if session is None:
        import requests
        req = requests.Session()
    else:
        req = session
    halts=None
    halt_error=None
    try:
        response=req.get(NASDAQ_RSS,timeout=20,allow_redirects=False,
                         headers={"User-Agent":"OBSIDIAN-research-only/1.0"})
        if response.status_code == 200:
            if _trusted_response_origin(getattr(response, "url", None), NASDAQ_RSS,
                                        exact_query=True):
                halts=response.content
            else:
                halt_error="HALT_RSS_UNTRUSTED_RESPONSE_ORIGIN"
        else:
            halt_error="HALT_RSS_HTTP_"+str(response.status_code)
    except Exception:
        # Requests and injected read-only adapters can raise non-OSError
        # transport exceptions. Never expose provider error text or tokens.
        halt_error="HALT_RSS_UNAVAILABLE_OR_TRANSPORT_ERROR"
    prices=None
    massive_error=None
    if massive_token:
        try:
            response=req.get(MASSIVE_SNAPSHOT,params={"tickers":",".join(symbols),
                                                        "apiKey":massive_token},
                             timeout=25,allow_redirects=False,
                             headers={"User-Agent":"OBSIDIAN-research-only/1.0"})
            if response.status_code==200:
                if _trusted_response_origin(getattr(response, "url", None),
                                            MASSIVE_SNAPSHOT):
                    prices=response.json()
                else:
                    massive_error="INDEPENDENT_QUOTES_UNTRUSTED_RESPONSE_ORIGIN"
            else:
                massive_error="INDEPENDENT_QUOTES_HTTP_"+str(response.status_code)
        except Exception:
            # Provider adapters may fail with RequestException, JSON decoding
            # errors or other transport failures. Censor without leaking URLs.
            massive_error="INDEPENDENT_QUOTES_UNAVAILABLE_OR_TRANSPORT_ERROR"
    # HTTP 200 and an expected origin do not establish parseable source data.
    # Reject malformed payloads BEFORE inspect_sources, so a broken upstream
    # response cannot crash the finite checkpoint or imply an unhalted symbol.
    if halts is not None:
        try:
            parse_nasdaq_halts(halts, now)
        except (ValueError, TypeError, ET.ParseError, OverflowError):
            halts=None
            halt_error="HALT_RSS_MALFORMED_OR_UNVERIFIABLE"
    if prices is not None:
        try:
            parse_massive_snapshot(prices, symbols, now)
        except (ValueError, TypeError, OverflowError):
            prices=None
            massive_error="INDEPENDENT_QUOTES_MALFORMED_OR_UNVERIFIABLE"
    report=inspect_sources(symbols,now,halts,prices)
    report["halt_fetch_error"]=halt_error
    report["quote_fetch_error"]=massive_error
    return report


def main():
    import argparse
    import os
    p=argparse.ArgumentParser()
    p.add_argument("--master",default="backtest/obsidian_historical_watchlist_manifest_2026_10_26.json")
    p.add_argument("--supplemental",default="backtest/obsidian_supplemental_watchlist_2026_10_26.json")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    records=[]
    for path in (a.master,a.supplemental):
        records+=json.loads(Path(path).read_text(encoding="utf-8"))["records"]
    symbols=sorted({row["ticker"] for row in records})
    now=datetime.now(timezone.utc)
    if phase(now) is None:
        print(json.dumps({"status":"OUTSIDE_RESEARCH_CHECKPOINT_NO_COLLECTION","asof":now.isoformat()}))
        return
    report=fetch_once(symbols,now,os.getenv("OBSIDIAN_MASSIVE_API_KEY"))
    target=Path(a.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(report,f,sort_keys=True,indent=2,allow_nan=False)
        f.write("\n")
    print(json.dumps({
        "status":"SOURCE_LIMITED_INDEPENDENT_REVIEW_NOT_A_TRADE",
        "phase":report["phase"],"symbols":len(symbols),
        "halt_feed_status":report["halt_feed_status"],
        "quotes_connected":report["quote_source_connected"],
        "realtime_entitlement_verified":False,
        "trade_authorized":False},sort_keys=True))


if __name__=="__main__":
    main()
