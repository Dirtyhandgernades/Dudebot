"""User's hard DECA research eligibility gates, separate from order execution."""
APPROVED_EXCHANGES={'XNAS','NASDAQ','XNYS','NYSE'}

def eligibility(snapshot,cfg,now):
    if snapshot.price<=cfg.game_min_price_exclusive:return 'EXCLUDED',['GAME_PRICE_NOT_ABOVE_3']
    if snapshot.market_cap is None:return 'REVIEW_REQUIRED',['GAME_MARKET_CAP_UNKNOWN']
    if not snapshot.market_cap_source or not snapshot.market_cap_observed_at or not snapshot.market_cap_basis:
        return 'REVIEW_REQUIRED',['GAME_MARKET_CAP_SOURCE_UNKNOWN']
    age=(now-snapshot.market_cap_observed_at).total_seconds()
    if not 0<=age<=26*3600:return 'REVIEW_REQUIRED',['GAME_MARKET_CAP_STALE_OR_FUTURE']
    if snapshot.market_cap<cfg.game_min_market_cap:return 'EXCLUDED',['GAME_MARKET_CAP_BELOW_25M']
    return None,[]

class NasdaqMarketCaps:
    """Public current screener values. Never substituted for historical market cap."""
    def __init__(self,http):self.http=http;self.rows={};self.loaded=False;self.issues=[]
    def apply(self,candidate,snapshot,now):
        if not self.loaded:
            self.loaded=True
            for exchange in ['nasdaq','nyse']:
                url='https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=0&exchange='+exchange
                try:
                    data=self.http.json(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json','Origin':'https://www.nasdaq.com'},timeout=15)
                    rows=data.get('data',{}).get('table',{}).get('rows',[])
                    if not rows:raise ValueError('EMPTY_MARKET_CAP_SOURCE')
                    for row in rows:
                        value=str(row.get('marketCap','')).replace(',','').replace('$','')
                        try:cap=float(value)
                        except ValueError:continue
                        if cap>0:self.rows[row['symbol']]=(cap,now,url)
                except Exception as exc:self.issues.append('MARKET_CAP_SOURCE_UNAVAILABLE:'+exchange+':'+type(exc).__name__)
        if candidate.ticker in self.rows:
            value,observed,url=self.rows[candidate.ticker]
            snapshot.market_cap=value;snapshot.market_cap_observed_at=observed;snapshot.market_cap_source=url
            snapshot.market_cap_basis='CURRENT_VENDOR_REPORT; source does not publish a value timestamp'
        return snapshot
