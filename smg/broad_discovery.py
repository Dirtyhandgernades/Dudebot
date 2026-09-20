"""Efficient two-stage discovery of volatile NASDAQ/NYSE common equities.

The expensive market-wide pass runs only twice per trading day using batched
daily bars. It persists at most a small shortlist; the 15-minute live scanner
therefore does not request intraday history for thousands of symbols.
"""
from __future__ import annotations

import json
import re
from datetime import date,datetime,timedelta,timezone
from statistics import mean

from .extraction import evidence,search
from .game_rules import is_excluded_symbol
from .live_firms import extract_watch
from .models import Candidate

UTC=timezone.utc
CAP_URL='https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=0&exchange='

def number(value):
    try:return float(str(value).replace(',','').replace('$','').strip())
    except (TypeError,ValueError):return None

def market_features(rows):
    rows=sorted(rows,key=lambda r:r['t'])
    if len(rows)<22:return None
    last=rows[-1];prior=rows[-21:-1];base=mean(float(r['v']) for r in prior)
    if base<=0 or any(float(r['c'])<=0 for r in rows[-22:]):return None
    return {'price':float(last['c']),'return_21_pct':100*(last['c']/rows[-22]['c']-1),
        'return_5_pct':100*(last['c']/rows[-6]['c']-1),'return_1_pct':100*(last['c']/rows[-2]['c']-1),
        'drawdown_21_pct':100*(last['c']/max(r['h'] for r in rows[-22:])-1),
        'volume_ratio_20':float(last['v'])/base,'average_range_5_pct':100*mean((r['h']-r['l'])/r['c'] for r in rows[-5:]),
        'failed_previous_low':bool(last['c']<rows[-2]['l']),'bar_time':last['t']}

def shortlist(features,cfg,limit=None):
    rows=[]
    for symbol,item in features.items():
        f=item['features']
        pumped=f['return_21_pct']>=cfg.broad_min_monthly_return_pct
        volatile=f['average_range_5_pct']>=cfg.broad_min_daily_range_pct and abs(f['return_5_pct'])>=8
        failure=f['failed_previous_low'] or f['return_1_pct']<=-5 or f['drawdown_21_pct']<=-8
        if f['volume_ratio_20']<cfg.broad_min_volume_ratio or not failure or not (pumped or volatile):continue
        firm_bonus=20 if item.get('known_firm') else 0
        score=firm_bonus+25*int(f['failed_previous_low'])+max(f['return_21_pct'],0)+5*f['volume_ratio_20']+2*f['average_range_5_pct']
        rows.append((score,symbol,item))
    return [item for _,_,item in sorted(rows,key=lambda x:(-x[0],x[1]))[:limit or cfg.broad_shortlist_size]]

class BroadVolatilityDiscovery:
    def __init__(self,sec,store,cfg,entries,alpaca_headers):
        self.sec=sec;self.store=store;self.cfg=cfg;self.entries=entries;self.headers=alpaca_headers;self.issues=[];self.requests=0

    def _eligible_universe(self,now):
        sec_rows={u['ticker'].upper():u for u in self.sec.universe()}
        result={};loaded=0
        for exchange in ['nasdaq','nyse']:
            url=CAP_URL+exchange
            try:
                raw=self.sec.http.json(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json','Origin':'https://www.nasdaq.com'},timeout=20)
                rows=raw.get('data',{}).get('table',{}).get('rows') or []
                if not rows:raise ValueError('EMPTY_MARKET_CAP_SOURCE')
                loaded+=1
            except Exception as exc:self.issues.append('NASDAQ_UNIVERSE:'+exchange+':'+type(exc).__name__);continue
            for row in rows:
                symbol=str(row.get('symbol','')).upper();identity=sec_rows.get(symbol)
                price=number(row.get('lastsale'));cap=number(row.get('marketCap'));name=(row.get('name') or (identity or {}).get('name') or '').strip()
                if not identity or not symbol or re.fullmatch('[A-Z]{5}',symbol) or is_excluded_symbol(symbol):continue
                if price is None or price<=self.cfg.game_min_price_exclusive or cap is None or cap<self.cfg.game_min_market_cap:continue
                if re.search(r'\b(?:acquisition|blank check)\b',name,re.I):continue
                result[symbol]={'ticker':symbol,'cik':str(int(identity['cik'])),'name':name,'exchange':'XNYS' if identity.get('exchange')=='NYSE' else 'XNAS',
                    'vendor_price':price,'market_cap':cap,'market_cap_source':url}
        return result,loaded==2

    def _daily_bars(self,symbols,now):
        output={};end=now-timedelta(minutes=self.cfg.market_data_delay_minutes);start=end-timedelta(days=55)
        for offset in range(0,len(symbols),100):
            params={'symbols':','.join(symbols[offset:offset+100]),'timeframe':'1Day','start':start.isoformat(),'end':end.isoformat(),
                'feed':self.cfg.market_feed,'adjustment':'split','limit':10000,'sort':'asc'};seen=set()
            while True:
                data=self.sec.http.json('https://data.alpaca.markets/v2/stocks/bars',params=params,headers=self.headers);self.requests+=1
                for symbol,rows in (data.get('bars') or {}).items():output.setdefault(symbol,[]).extend(rows)
                token=data.get('next_page_token')
                if not token:break
                if token in seen:raise ValueError('Alpaca broad-discovery pagination loop')
                seen.add(token);params['page_token']=token
        return output

    def _enrich(self,item,now):
        try:filings=self.sec.submissions(item['cik'],now.date()-timedelta(days=3*365))
        except Exception as exc:self.issues.append(item['ticker']+':SUBMISSIONS:'+type(exc).__name__);return None
        filing=next((f for f in filings if f['form'] in {'10-K','20-F','F-1','S-1','424B4'}),None)
        if not filing:return None
        try:raw=self.sec.document(filing['url'])
        except Exception as exc:self.issues.append(item['ticker']+':DOCUMENT:'+type(exc).__name__);return None
        doc=dict(raw,date=filing['date'])
        acquisition=search([doc],r'\b(?:we are|we were|the company is|the company was)\s+(?:a |an )?(?:blank.check company|special purpose acquisition company)\b')
        if acquisition:return None
        business=search([doc],r'\b(?:we|the company)\s+(?:(?:are|is)\s+(?:(?:a|an|the)\s+)?(?:[\w,-]+\s+){0,10}(?:company|provider|manufacturer|operator|developer|supplier|distributor)|(?:manufacture|manufactures|develop|develops|operate|operates|provide|provides|sell|sells)\s+[^.]{10,180})',re.I)
        security=search([doc],r'\b(?:ordinary shares|common stock|common shares|American depositary shares)\b')
        if not business or not security:return None
        known=extract_watch(dict(cik=item['cik'],ticker=item['ticker'],name=item['name'],exchange=item['exchange']),[doc],now,self.entries)
        kind='ADS' if 'depositary' in security[0].group().lower() else 'CS'
        notes=['Broad volatility lane; no listed-firm match required for discovery.',
            'Daily prefilter: '+json.dumps(item['features'],sort_keys=True,separators=(',',':'))]
        return Candidate(pipeline='VOLATILITY_WATCH',cik=item['cik'],ticker=item['ticker'],name=item['name'],event_id='VOLATILITY:'+item['ticker'],
            exchange=item['exchange'],operations_country=None,ipo_date=None,event_date=date.fromisoformat(filing['date']),status='unknown',
            security_type=kind,is_acquisition_corp=False,offer_price=None,offer_gross=None,currency=None,base_shares=None,terms_unambiguous=False,
            matches=known.matches if known else [],evidence={'is_acquisition_corp':business[2],'security_type':security[2]},notes=notes,reviewed_at=now)

    def run(self,now=None):
        now=now or datetime.now(UTC);universe,universe_complete=self._eligible_universe(now);symbols=sorted(universe)
        bars_complete=True
        try:bars=self._daily_bars(symbols,now)
        except Exception as exc:
            self.issues.append('ALPACA_DAILY:'+type(exc).__name__);bars={};bars_complete=False
        features={}
        firm_tickers={raw['ticker'] for _,raw in self.store.items('candidate:FIRM_WATCH:')}
        for symbol,item in universe.items():
            f=market_features(bars.get(symbol,[]))
            if f:features[symbol]={**item,'features':f,'known_firm':symbol in firm_tickers}
        selected=shortlist(features,self.cfg,self.cfg.broad_shortlist_size*3);candidates=[]
        for item in selected:
            candidate=self._enrich(item,now)
            if candidate:candidates.append(candidate)
            if len(candidates)>=self.cfg.broad_shortlist_size:break
        replaced=universe_complete and bars_complete and bool(features)
        if replaced:
            self.store.delete_prefix('candidate:VOLATILITY_WATCH:')
            for candidate in candidates:self.store.put('candidate:'+candidate.key,candidate.model_dump(mode='json'))
        else:
            # A transient universe or bar outage must not erase the last valid
            # shortlist. Its 26-hour review TTL still makes it fail closed.
            self.issues.append('SHORTLIST_PRESERVED_AFTER_INCOMPLETE_SOURCE')
        summary={'at':now.isoformat(),'eligible_universe':len(universe),'feature_rows':len(features),'prefiltered':len(selected),
            'verified_shortlist':len(candidates),'symbols':[c.ticker for c in candidates],'shortlist_replaced':replaced,
            'alpaca_requests':self.requests,'issues':self.issues}
        self.store.put('broad_discovery',summary)
        return candidates,summary
