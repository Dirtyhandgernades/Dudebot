"""Free, bounded research evidence packet. Never an order or full A/B/C prediction."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone, time
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from backtest.obsidian_independent_quote_halt import parse_nasdaq_halts, NASDAQ_RSS
from backtest.obsidian_sip_fallback import classify_bars, BAR_WIDTH
from backtest.obsidian_prospective_capture import asof

UTC = timezone.utc
ET = ZoneInfo('America/New_York')
CT = ZoneInfo('America/Chicago')
MODE = 'RESEARCH_ONLY_NOT_AN_ORDER'
POLICY = 'OBSIDIAN_FREE_QUANT_FEED_V1'
MAX_SYMBOLS = 200
SIP_LAG = timedelta(minutes=17)
SAFE = re.compile(r'^[A-Z][A-Z0-9.]{0,12}$')


def positive(x):
    return type(x) in (int, float) and math.isfinite(x) and x > 0


def market_record(snapshot, observed):
    """IEX quote/trade ages are independent. No NBBO or official-close inference."""
    if not isinstance(snapshot, dict):
        return {'status': 'MISSING_IEX_SNAPSHOT', 'trade': None, 'quote': None}
    def event(value, kind):
        if not isinstance(value, dict):
            return {'status': 'MISSING', 'source_timestamp': None}
        stamp = asof(value.get('t'))
        age = (observed-stamp).total_seconds() if stamp else None
        prices = [value.get('p')] if kind == 'trade' else [value.get('bp'),value.get('ap')]
        state = ('INVALID' if not all(positive(p) for p in prices) or stamp is None else
                 'FUTURE' if age < 0 else 'FRESH_SINGLE_VENUE' if age <= 60 else 'STALE_SINGLE_VENUE')
        if kind == 'quote' and all(positive(p) for p in prices) and prices[0] > prices[1]: state='CROSSED_QUOTE'
        return dict(status=state, source_timestamp=value.get('t'),age_seconds=age,
                    values={k:value.get(k) for k in (('p','s') if kind=='trade' else ('bp','ap','bs','as'))})
    trade=event(snapshot.get('latestTrade'),'trade');quote=event(snapshot.get('latestQuote'),'quote')
    daily=snapshot.get('dailyBar')
    return dict(status=trade['status'],trade=trade,quote=quote,
                daily_bar={k:daily.get(k) for k in ('t','o','h','l','c','v','n')} if isinstance(daily,dict) else None,
                daily_volume_scope='IEX_SINGLE_VENUE_NOT_CONSOLIDATED',nbbo_verified=False)


def filing_records(payload, symbol, cik, cutoff, retrieved, limit=3):
    """SEC acceptance times establish publication, not catalyst polarity or market causation."""
    recent=payload.get('filings',{}).get('recent',{}) if isinstance(payload,dict) else {}
    if not isinstance(recent,dict): return []
    keys=('form','accessionNumber','primaryDocument','acceptanceDateTime')
    arrays=[recent.get(k,[]) for k in keys]
    if any(not isinstance(a,list) for a in arrays) or len({len(a) for a in arrays})!=1:return []
    result=[]
    for form,acc,document,accepted in zip(*arrays):
        published=asof(accepted)
        if (form not in {'8-K','6-K','10-Q','10-K','S-1','S-3','424B3','424B4','424B5'} or
            published is None or published>cutoff or published>retrieved or
            cutoff-published>timedelta(days=7)):continue
        if not isinstance(acc,str) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):continue
        if not isinstance(document,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+',document):continue
        result.append(dict(ticker=symbol,cik=cik,form=form,accession=acc,public_at=accepted,
                           retrieved_at=retrieved.isoformat(),source_url=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/{document}',
                           mechanism_status='UNREVIEWED_FILING_NOT_VERIFIED_ADVERSE',
                           counterevidence_status='UNREVIEWED',actual_issuance_or_sale_verified=False))
        if len(result)>=limit:break
    return result


def passages(text, terms):
    result=[]
    for term in terms:
        match=re.search(re.escape(term),text,re.IGNORECASE)
        if match:
            result.append(dict(term=term,excerpt=text[max(0,match.start()-120):match.end()+220],review_required=True))
    return result


class Reader:
    """GET-only. Fixed total budget, no retries, stop each host after auth/429 errors."""
    def __init__(self, session=None, maximum=24):
        if session is None:
            import requests
            session=requests.Session()
        self.session=session;self.maximum=maximum;self.used=0;self.stopped=set();self.receipts=[]
    def get(self,url,params=None,headers=None):
        from urllib.parse import urlsplit
        host=urlsplit(url).hostname
        receipt=dict(source_url=url,retrieved_at=datetime.now(UTC).isoformat(),http_status=None,sha256=None,error=None)
        if self.used>=self.maximum or host in self.stopped:
            receipt['error']='BUDGET_OR_PROVIDER_STOP';self.receipts.append(receipt);return None,receipt
        self.used+=1
        try:
            r=self.session.get(url,params=params,headers=headers,timeout=20)
            raw=r.content
            receipt.update(http_status=r.status_code,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
            if r.status_code in (401,403,429):self.stopped.add(host)
            if r.status_code!=200:receipt['error']='HTTP_'+str(r.status_code);raw=None
            if raw is not None and len(raw)>8_000_000:receipt['error']='BODY_TOO_LARGE';raw=None
        except Exception:
            receipt['error']='NETWORK_OR_RESPONSE_ERROR';raw=None
        receipt['retrieved_at']=datetime.now(UTC).isoformat()
        self.receipts.append(receipt);return raw,receipt


def decoded(raw):
    try:return json.loads(raw) if raw is not None else None
    except (ValueError,TypeError):return None


def collect(symbols, reader=None, clock=None, sec_limit=8):
    symbols=list(symbols)
    if not symbols or len(symbols)>MAX_SYMBOLS or len(set(symbols))!=len(symbols) or any(not SAFE.fullmatch(s) for s in symbols):
        raise ValueError('INVALID_BOUNDED_SYMBOL_UNIVERSE')
    if not 0<=sec_limit<=8:raise ValueError('SEC_BUDGET_MAX_8')
    now=clock or datetime.now(UTC)
    if now.utcoffset() is None:raise ValueError('AWARE_CLOCK_REQUIRED')
    local=now.astimezone(CT)
    if local.weekday()>4 or time(14,45)<=local.time().replace(tzinfo=None)<=time(14,58):
        raise ValueError('OUTSIDE_RESEARCH_OR_PROTECTED_PRECLOSE_WINDOW')
    reader=reader or Reader();headers={'APCA-API-KEY-ID':os.environ.get('ALPACA_API_KEY',''),
                                       'APCA-API-SECRET-KEY':os.environ.get('ALPACA_SECRET_KEY','')}
    snapshots={};snap_error='ALPACA_CREDENTIALS_ABSENT';snap_at=now
    bars={s:[] for s in symbols};sip_error='ALPACA_CREDENTIALS_ABSENT';pages=0
    cutoff=now-SIP_LAG
    opening=now.astimezone(ET).replace(hour=9,minute=30,second=0,microsecond=0).astimezone(UTC)
    start=max(opening,cutoff-timedelta(minutes=60))
    if all(headers.values()):
        raw,receipt=reader.get('https://data.alpaca.markets/v2/stocks/snapshots',{'symbols':','.join(symbols),'feed':'iex'},headers)
        snap_at=asof(receipt['retrieved_at']);value=decoded(raw)
        if isinstance(value,dict) and not (set(value)-set(symbols)):
            snapshots=value;snap_error=None
        else:snap_error=receipt['error'] or 'INVALID_SNAPSHOT_RESPONSE'
        sip_error=None;token=None;seen=set()
        if start>=cutoff:sip_error='NO_COMPLETED_DELAYED_REGULAR_SESSION_BAR_WINDOW'
        else:
            for page in range(2):
                params=dict(symbols=','.join(symbols),timeframe='1Min',feed='sip',adjustment='raw',
                            start=start.isoformat(),end=(cutoff-BAR_WIDTH).isoformat(),limit=10000)
                if token:params['page_token']=token
                raw,receipt=reader.get('https://data.alpaca.markets/v2/stocks/bars',params,headers);pages+=1
                value=decoded(raw)
                if not isinstance(value,dict) or not isinstance(value.get('bars'),dict) or set(value['bars'])-set(symbols):
                    sip_error=receipt['error'] or 'INVALID_SIP_RESPONSE';break
                if any(not isinstance(v,list) for v in value['bars'].values()):sip_error='INVALID_BAR_LIST';break
                for symbol,items in value['bars'].items():bars[symbol].extend(items)
                token=value.get('next_page_token')
                if not token:break
                if not isinstance(token,str) or token in seen:sip_error='PAGINATION_LOOP';break
                seen.add(token)
            else:
                if token:sip_error='SIP_PAGINATION_BUDGET_EXHAUSTED'
    raw,halt_receipt=reader.get(NASDAQ_RSS,headers={'User-Agent':'OBSIDIAN-research-only/1.0'})
    events=[];halt_error=halt_receipt['error']
    if raw:
        try:events=parse_nasdaq_halts(raw,asof(halt_receipt['retrieved_at']))
        except Exception:halt_error='INVALID_HALT_FEED'
    filings={};sec_states={s:'NOT_REQUESTED_SEC_BUDGET' for s in symbols}
    ua=os.environ.get('SEC_USER_AGENT','')
    if ua and sec_limit:
        raw,map_receipt=reader.get('https://www.sec.gov/files/company_tickers_exchange.json',headers={'User-Agent':ua})
        mapping=decoded(raw);matches={s:[] for s in symbols}
        if isinstance(mapping,dict) and isinstance(mapping.get('fields'),list) and isinstance(mapping.get('data'),list):
            for values in mapping['data']:
                if not isinstance(values,list) or len(values)!=len(mapping['fields']):continue
                item=dict(zip(mapping['fields'],values))
                if item.get('ticker') in matches:matches[item['ticker']].append(item)
        for symbol in symbols[:sec_limit]:
            if len(matches[symbol])!=1:sec_states[symbol]='SEC_MAPPING_MISSING_OR_AMBIGUOUS';continue
            cik=matches[symbol][0].get('cik')
            try:cik=f'{int(cik):010d}'
            except (ValueError,TypeError):sec_states[symbol]='INVALID_CIK';continue
            raw,receipt=reader.get(f'https://data.sec.gov/submissions/CIK{cik}.json',headers={'User-Agent':ua})
            value=decoded(raw)
            if not isinstance(value,dict):sec_states[symbol]=receipt['error'] or 'INVALID_SEC_RESPONSE';continue
            if str(value.get('cik','')).lstrip('0')!=cik.lstrip('0') or not isinstance(value.get('tickers'),list) or symbol not in value['tickers']:
                sec_states[symbol]='SEC_IDENTITY_MISMATCH';continue
            filings[symbol]=filing_records(value,symbol,cik,now,asof(receipt['retrieved_at']))
            sec_states[symbol]='RECENT_FILING_METADATA_COLLECTED_REVIEW_REQUIRED'
    elif not ua:sec_states={s:'SEC_USER_AGENT_ABSENT' for s in symbols}
    document_budget=2
    for symbol in symbols:
        for filing in filings.get(symbol,[]):
            if document_budget<=0:break
            document_budget-=1
            raw,receipt=reader.get(filing['source_url'],headers={'User-Agent':ua})
            filing['document_receipt']=receipt
            if raw is not None:
                text=html.unescape(re.sub('<[^>]+>',' ',raw.decode('utf-8',errors='replace')))
                text=re.sub(r'\s+',' ',text)
                filing['candidate_adverse_passages']=passages(text,('going concern','material weakness','offering','liquidity','impairment'))
                filing['candidate_counterevidence_passages']=passages(text,('no substantial doubt','withdrawn','terminated','repaid','no material adverse','increased'))
                filing['passage_status']='KEYWORD_CANDIDATES_REQUIRING_CONTEXT_REVIEW_NOT_VERIFIED_CATALYST'
    rows=[]
    for symbol in symbols:
        iex=market_record(snapshots.get(symbol),snap_at)
        status,latest=classify_bars(bars[symbol],start,cutoff) if not sip_error else ('SIP_UNAVAILABLE_OR_INCOMPLETE',None)
        hs=[e for e in events if e['ticker']==symbol]
        rows.append(dict(ticker=symbol,iex=dict(provider='Alpaca',feed='iex',observed_at=snap_at.isoformat(),error=snap_error,**iex),
                         sip=dict(provider='Alpaca',feed='sip',status=status,error=sip_error,latest_completed_bar=latest,
                                  safe_asof=cutoff.isoformat(),minimum_delay_minutes=17,price_type='DELAYED_RAW_MINUTE_BAR_NOT_LIVE_QUOTE',
                                  window_volume=sum(b.get('v',0) for b in bars[symbol] if isinstance(b,dict) and type(b.get('v')) in (int,float)) if latest else None,
                                  volume_window_start=start.isoformat(),rvol_verified=False),
                         halt=dict(provider='Nasdaq RSS',retrieved_at=halt_receipt['retrieved_at'],error=halt_error,events=hs,
                                   status='SOURCE_UNAVAILABLE' if halt_error else 'HALT_EVENT_REQUIRES_REVIEW' if hs else 'NO_ROW_NOT_PROOF_OPEN',
                                   executable_halt_clearance=False),
                         catalysts=dict(status=sec_states[symbol],filings=filings.get(symbol,[]),adverse_mechanism_verified=False,
                                        counterevidence_review='PENDING',issuer_release_review='PENDING'),
                         research_classification='BLOCKED_PENDING_MECHANISM_AND_ELIGIBILITY',trade_authorized=False,
                         smg_eligibility_verified=False))
    return dict(mode=MODE,policy=POLICY,started_at=now.isoformat(),finished_at=datetime.now(UTC).isoformat(),
                source_scope='SUPPLIED_WATCHLIST_NOT_FULL_MARKET',requested_symbols=symbols,rows=rows,
                coverage=dict(denominator=len(rows),iex_states=dict(Counter(r['iex']['status'] for r in rows)),
                              sip_states=dict(Counter(r['sip']['status'] for r in rows)),
                              sec_states=dict(Counter(r['catalysts']['status'] for r in rows))),
                request_budget=dict(maximum=reader.maximum,used=reader.used,sip_pages=pages,sec_maximum=sec_limit),
                receipts=reader.receipts,official_closes_verified=False,verified_predictions=0,trade_authorized=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watchlist',default='backtest/obsidian_historical_watchlist_manifest_2026_10_26.json')
    parser.add_argument('--supplemental',default='backtest/obsidian_supplemental_watchlist_2026_10_26.json')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--sec-limit',type=int,default=8)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    records=json.loads(Path(args.watchlist).read_text())['records']+json.loads(Path(args.supplemental).read_text())['records']
    symbols=sorted({r['ticker'] for r in records})
    packet=collect(symbols,sec_limit=args.sec_limit)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:json.dump(packet,f,indent=2,sort_keys=True,allow_nan=False)
    print(json.dumps(dict(policy=POLICY,coverage=packet['coverage'],request_budget=packet['request_budget'])))


if __name__=='__main__':main()
