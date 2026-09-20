"""Append-only evidence collection for live decisions and future replays.

This module does not turn today's vendor fields into historical facts. It creates
the archive Dudebot was previously missing, one timestamped observation at a
time, and labels provider failures instead of filling them with assumptions.
"""
from __future__ import annotations

import csv
import io
from datetime import date,datetime,timedelta,timezone
from urllib.parse import quote
import xml.etree.ElementTree as ET

from .market import calendar,is_open
from .providers import HALT_URL
from .sentiment import collect as collect_sentiment
from .shortability import current_assets

UTC=timezone.utc
FINRA_DAILY='https://cdn.finra.org/equity/regsho/daily/CNMSshvol{day}.txt'
SEC_TICKERS='https://www.sec.gov/files/company_tickers_exchange.json'
SEC_FACTS='https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json'

def parse_finra(text,symbols=None):
    """Parse FINRA's consolidated NMS pipe file without treating it as SI/borrow."""
    wanted={s.upper() for s in symbols} if symbols else None
    rows=list(csv.DictReader(io.StringIO(text),delimiter='|'))
    required={'Date','Symbol','ShortVolume','ShortExemptVolume','TotalVolume','Market'}
    if not rows or not required.issubset(rows[0]):raise ValueError('Invalid FINRA short-volume file')
    out={}
    for row in rows:
        symbol=(row.get('Symbol') or '').upper()
        if not symbol or symbol.startswith('#') or (wanted is not None and symbol not in wanted):continue
        try:short=int(row['ShortVolume']);exempt=int(row['ShortExemptVolume']);total=int(row['TotalVolume'])
        except (TypeError,ValueError):continue
        if total<0 or short<0 or exempt<0:continue
        out[symbol]={'trade_date':row['Date'],'short_volume':short,'short_exempt_volume':exempt,
            'reported_total_volume':total,'short_volume_ratio':round(short/total,6) if total else None,
            'market':row['Market']}
    return out

def halt_events(xml):
    """Preserve historical halt rows, including rows that later resumed."""
    root=ET.fromstring(xml);channel=root.find('channel')
    if root.tag!='rss' or channel is None:raise ValueError('Invalid halt RSS document')
    rows=[]
    for item in channel.findall('item'):
        fields={el.tag.split('}')[-1].lower():''.join(el.itertext()).strip() for el in item}
        symbol=(fields.get('issuesymbol') or fields.get('symbol') or '').upper()
        if not symbol:raise ValueError('Halt item lacks a symbol')
        rows.append({'symbol':symbol,'halt_date':fields.get('haltdate'),'halt_time':fields.get('halttime'),
            'reason_code':fields.get('reasoncode'),'market':fields.get('market'),
            'resumption_date':fields.get('resumptiondate'),'resumption_quote_time':fields.get('resumptionquotetime'),
            'resumption_trade_time':fields.get('resumptiontradetime')})
    return rows

SHARE_TAGS=(
    ('dei','EntityCommonStockSharesOutstanding'),
    ('us-gaap','CommonStockSharesOutstanding'),
    ('ifrs-full','NumberOfSharesOutstanding'),
)

def select_share_fact(companyfacts,asof):
    """Select the latest share fact that was public by asof; never use later filings."""
    cutoff=str(asof)[:10];candidates=[]
    facts=companyfacts.get('facts') or {}
    for priority,(namespace,tag) in enumerate(SHARE_TAGS):
        concept=(facts.get(namespace) or {}).get(tag) or {}
        for unit in (concept.get('units') or {}).values():
            for fact in unit:
                if fact.get('filed','9999-99-99')>cutoff or fact.get('end','9999-99-99')>cutoff:continue
                value=fact.get('val')
                if not isinstance(value,(int,float)) or value<=0:continue
                candidates.append((fact.get('filed',''),fact.get('end',''),-priority,dict(fact,namespace=namespace,tag=tag)))
    return max(candidates,key=lambda x:x[:3])[3] if candidates else None

def market_cap_proxy(companyfacts,price,asof):
    fact=select_share_fact(companyfacts,asof)
    if not fact:return {'status':'UNAVAILABLE','reason':'NO_POINT_IN_TIME_SHARE_FACT'}
    return {'status':'AVAILABLE','market_cap_proxy':round(fact['val']*price,2),'price':price,
        'shares':fact['val'],'shares_end':fact.get('end'),'shares_filed':fact.get('filed'),
        'shares_accession':fact.get('accn'),'shares_form':fact.get('form'),'shares_tag':fact['namespace']+':'+fact['tag'],
        'basis':'SEC reported shares outstanding multiplied by observed market price; class/ADS comparability requires review'}

def _recent_market(http,headers,symbols,effective):
    if not symbols:return {}
    params={'symbols':','.join(symbols),'timeframe':'1Min','start':(effective-timedelta(minutes=20)).isoformat(),
        'end':effective.isoformat(),'adjustment':'raw','feed':'sip','limit':10000,'sort':'asc'}
    data=http.json('https://data.alpaca.markets/v2/stocks/bars',params=params,headers=headers)
    if data.get('next_page_token'):raise ValueError('Unexpected archive pagination')
    out={}
    for symbol,rows in (data.get('bars') or {}).items():
        rows=sorted(rows,key=lambda r:r['t'])
        if rows:out[symbol]={'price':rows[-1]['c'],'price_time':rows[-1]['t'],'window_volume':sum(r['v'] for r in rows),'bars':len(rows)}
    return out

def previous_session(day):
    sessions=calendar(day.year).sessions_in_range(day-timedelta(days=10),day-timedelta(days=1))
    return sessions[-1].date() if len(sessions) else None

class EvidenceArchiver:
    def __init__(self,http,store,alpaca_headers,sec_headers):
        self.http=http;self.store=store;self.alpaca_headers=alpaca_headers;self.sec_headers=sec_headers

    def _record_failure(self,kind,subject,now,source,exc):
        self.store.observe(kind,subject,now,source,{'status':'UNAVAILABLE','error_type':type(exc).__name__})

    def collect(self,symbol_to_cik,now=None):
        now=now or datetime.now(UTC);symbols=sorted(symbol_to_cik)
        effective=now-timedelta(minutes=16);summary={'observed_at':now.isoformat(),'symbols':len(symbols),'failures':[]}
        if not symbols:return {**summary,'status':'EMPTY_WATCHLIST'}
        try:assets=current_assets(self.http,symbols,self.alpaca_headers)['assets']
        except Exception as exc:
            assets={s:{'status':'UNAVAILABLE','error_type':type(exc).__name__} for s in symbols}
        try:market=_recent_market(self.http,self.alpaca_headers,symbols,effective) if is_open(effective) else {}
        except Exception as exc:market={};summary['failures'].append('MARKET:'+type(exc).__name__)
        for symbol in symbols:
            value={**assets.get(symbol,{'status':'UNAVAILABLE'}),**market.get(symbol,{})}
            value['effective_at']=effective.isoformat();value['data_delay_minutes']=16
            self.store.observe('market_borrow',symbol,now,'https://paper-api.alpaca.markets/v2/assets/'+quote(symbol),value)

        try:
            xml=self.http.text(HALT_URL);events=halt_events(xml);halted={e['symbol'] for e in events if not e.get('resumption_trade_time')}
            for event in events:self.store.observe('halt_event',event['symbol'],now,HALT_URL,event)
            for symbol in symbols:self.store.observe('halt_status',symbol,now,HALT_URL,{'status':'HALTED' if symbol in halted else 'CLEAR'})
        except Exception as exc:
            summary['failures'].append('HALTS:'+type(exc).__name__)
            for symbol in symbols:self._record_failure('halt_status',symbol,now,HALT_URL,exc)

        daily_key='evidence_daily:'+str(now.date())
        if not self.store.get(daily_key):
            self._daily(symbol_to_cik,market,now,summary)
            self.store.put(daily_key,{'completed_at':now.isoformat()})
        self.store.put('evidence_archive:last',summary)
        return {**summary,'status':'ARCHIVED','market_rows':len(market),'asset_rows':len(assets)}

    def _daily(self,symbol_to_cik,market,now,summary):
        symbols=sorted(symbol_to_cik)
        try:
            raw=self.http.json(SEC_TICKERS,headers=self.sec_headers)
            for values in raw.get('data',[]):
                row=dict(zip(raw['fields'],values));symbol=str(row.get('ticker','')).upper()
                if symbol not in symbol_to_cik:continue
                value={'cik':str(int(row['cik'])),'ticker':symbol,'name':row.get('name'),'exchange':row.get('exchange')}
                self.store.observe('sec_identity',symbol,now,SEC_TICKERS,value)
        except Exception as exc:summary['failures'].append('SEC_IDENTITY:'+type(exc).__name__)

        for symbol,cik in symbol_to_cik.items():
            try:
                facts=self.http.json(SEC_FACTS.format(cik=int(cik)),headers=self.sec_headers)
                proxy=market_cap_proxy(facts,market[symbol]['price'],now) if symbol in market else {'status':'UNAVAILABLE','reason':'NO_CURRENT_PRICE'}
                self.store.observe('sec_cap_proxy',symbol,now,SEC_FACTS.format(cik=int(cik)),proxy)
            except Exception as exc:self._record_failure('sec_cap_proxy',symbol,now,SEC_FACTS.format(cik=int(cik)),exc)
            try:
                sentiment=collect_sentiment(symbol,self.http,now=now)
                self.store.observe('sentiment',symbol,now,'multiple; see provider records',sentiment)
            except Exception as exc:self._record_failure('sentiment',symbol,now,'multiple',exc)

        day=previous_session(now.date())
        if day:
            url=FINRA_DAILY.format(day=day.strftime('%Y%m%d'))
            try:
                values=parse_finra(self.http.text(url),symbols)
                for symbol in symbols:
                    value=values.get(symbol,{'trade_date':day.strftime('%Y%m%d'),'status':'NO_REPORTED_ROW'})
                    value.setdefault('status','AVAILABLE')
                    value['limitation']='FINRA off-exchange short-sale volume is not short interest, borrow availability, or total consolidated volume'
                    self.store.observe('finra_short_volume',symbol,now,url,value)
            except Exception as exc:
                summary['failures'].append('FINRA:'+type(exc).__name__)
                for symbol in symbols:self._record_failure('finra_short_volume',symbol,now,url,exc)

    def backfill_public(self,symbols,days,now=None):
        """Bounded daily history fill. Call repeatedly; observations are idempotent."""
        now=now or datetime.now(UTC);done=0;failures=[]
        for day in days:
            halt_url=HALT_URL+'&haltdate='+day.strftime('%m%d%Y')
            try:
                for event in halt_events(self.http.text(halt_url)):
                    if not symbols or event['symbol'] in symbols:self.store.observe('halt_event',event['symbol'],now,halt_url,event)
            except Exception as exc:failures.append({'day':str(day),'source':'NASDAQ_HALT','error_type':type(exc).__name__})
            finra_url=FINRA_DAILY.format(day=day.strftime('%Y%m%d'))
            try:
                for symbol,value in parse_finra(self.http.text(finra_url),symbols).items():
                    value['status']='AVAILABLE';value['limitation']='FINRA short volume is not borrow availability or short interest'
                    self.store.observe('finra_short_volume',symbol,now,finra_url,value)
            except Exception as exc:failures.append({'day':str(day),'source':'FINRA','error_type':type(exc).__name__})
            done+=1
        return {'processed_days':done,'failures':failures,'historical_borrow':'UNAVAILABLE_BEFORE_ARCHIVE_START'}
