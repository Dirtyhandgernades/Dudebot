from __future__ import annotations
from datetime import date,datetime,timedelta,timezone
from urllib.parse import urlsplit,quote,urljoin
from email.utils import parsedate_to_datetime
import re,hashlib,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from .models import Bar,HaltCheck
from .transport import ProviderError
from .rules import years_ago
UTC=timezone.utc

class Alpaca:
    """Read-only Market Data API. Never calls account/order endpoints."""
    def __init__(self,http,key_id,secret,feed='sip',delay_minutes=16):
        if feed not in {'sip','iex'}:raise ValueError('Unsupported stock feed')
        if feed=='sip' and delay_minutes<16:raise ValueError('Free SIP mode needs the 16-minute delay')
        self.http=http;self.feed=feed;self.delay_minutes=delay_minutes
        self.headers={'APCA-API-KEY-ID':key_id,'APCA-API-SECRET-KEY':secret}
    def bars(self,ticker,start,end,*,asof=None):
        # The explicit end prevents accidental requests for subscription-only recent SIP data.
        if not isinstance(end,datetime):raise ValueError('Explicit timezone-aware end timestamp required')
        if end.tzinfo is None:raise ValueError('Timezone-aware end required')
        params={'symbols':ticker,'timeframe':'1Min','start':start.isoformat(),'end':end.isoformat(),
                'adjustment':'split','feed':self.feed,'limit':10000,'sort':'asc'}
        if asof is not None:
            params['asof']=date.fromisoformat(str(asof)).isoformat()
        seen=set();result=[]
        while True:
            data=self.http.json('https://data.alpaca.markets/v2/stocks/bars',params=dict(params),headers=self.headers)
            for r in (data.get('bars') or {}).get(ticker,[]):
                result.append(Bar(start=datetime.fromisoformat(r['t'].replace('Z','+00:00')),close=r['c'],high=r['h'],low=r['l'],volume=r['v']))
            token=data.get('next_page_token')
            if not token:break
            if token in seen:raise ValueError('Alpaca pagination loop')
            seen.add(token);params['page_token']=token
        return result

class Sec:
    def __init__(self,http,user_agent,store):
        if '@' not in user_agent:raise ValueError('SEC_USER_AGENT must include your contact email')
        self.http=http;self.headers={'User-Agent':user_agent,'Accept-Encoding':'gzip, deflate'};self.store=store
    def text(self,url):
        if urlsplit(url).hostname not in {'www.sec.gov','data.sec.gov'}:raise ValueError('Untrusted SEC URL')
        return self.http.text(url,headers=self.headers)
    def json(self,url):return self.http.json(url,headers=self.headers)
    def universe(self):
        raw=self.json('https://www.sec.gov/files/company_tickers_exchange.json')
        return [dict(zip(raw['fields'],r)) for r in raw['data'] if dict(zip(raw['fields'],r)).get('exchange')=='Nasdaq']
    def submissions(self,cik,since):
        raw=self.json(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json')
        sets=[raw['filings']['recent']]
        for item in raw['filings'].get('files',[]):
            if item['filingTo']>=str(since): sets.append(self.json('https://data.sec.gov/submissions/'+item['name']))
        rows=[]
        for block in sets:
            for i,acc in enumerate(block.get('accessionNumber',[])):
                if block['filingDate'][i]<str(since):continue
                rows.append({'cik':str(int(cik)),'accession':acc,'date':block['filingDate'][i],'form':block['form'][i],
                    'url':f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/{block["primaryDocument"][i]}'})
        return sorted({r['accession']:r for r in rows}.values(),key=lambda r:r['date'],reverse=True)
    def document(self,url):
        key='document:'+hashlib.sha256(url.encode()).hexdigest()
        from pathlib import Path
        import json
        cache=self.store.path.parent/'cache'/(key.split(':')[1]+'.json')
        if cache.exists():return json.loads(cache.read_text())
        raw=self.text(url)
        soup=BeautifulSoup(raw,'html.parser')
        for el in soup(['script','style','ix:header']):el.decompose()
        text=' '.join(soup.get_text(' ',strip=True).split())
        item={'url':url,'text':text,'sha256':hashlib.sha256(raw.encode()).hexdigest()}
        cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(json.dumps(item));return item
    def quarterly_events(self,since,until,ciks,forms=None):
        forms=forms or {'424B3','424B4','424B5','8-K','6-K'}
        periods=set();day=since
        while day<=until:
            periods.add((day.year,(day.month-1)//3+1));day+=timedelta(days=1)
        rows=[]
        for year,qtr in sorted(periods):
            text=self.text(f'https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx')
            for line in text.splitlines():
                parts=line.split('|')
                if len(parts)!=5 or not parts[0].isdigit():continue
                cik,name,form,fd,path=parts
                if cik in ciks and form in forms and str(since)<=fd<=str(until):
                    rows.append({'cik':cik,'date':fd,'form':form,'url':'https://www.sec.gov/Archives/'+path,'accession':path.rsplit('/',1)[-1].removesuffix('.txt')})
        return rows
    def current_events(self,ciks):
        # Atom current filings supplies same-day discovery; quarterly index catches missed filings tomorrow.
        rows=[]
        for start in range(0,1000,100):
            url=f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&owner=exclude&start={start}&count=100&output=atom'
            root=ET.fromstring(self.text(url));entries=root.findall('{http://www.w3.org/2005/Atom}entry')
            if not entries:break
            for ent in entries:
                title=ent.findtext('{http://www.w3.org/2005/Atom}title','')
                match=re.search(r'\((\d{6,10})\)',title)
                if not match:continue
                cik=str(int(match.group(1)))
                if cik not in ciks:continue
                form=title.split(' - ',1)[0]
                if form not in {'424B3','424B4','424B5','8-K','6-K'}:continue
                link=ent.find('{http://www.w3.org/2005/Atom}link').get('href')
                acc=re.search(r'(\d{10}-\d{2}-\d{6})',link)
                if not acc:continue
                fd=ent.findtext('{http://www.w3.org/2005/Atom}updated','')[:10]
                rows.append({'cik':cik,'form':form,'date':fd,'accession':acc.group(1),'url':f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.group(1)}.txt'})
        return rows

HALT_URL='https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts'
def parse_halts(xml,now):
    root=ET.fromstring(xml)
    channel=root.find('channel')
    if root.tag!='rss' or channel is None:raise ValueError('Invalid halt RSS document')
    halted=set()
    for item in channel.findall('item'):
        fields={el.tag.split('}')[-1].lower():''.join(el.itertext()).strip() for el in item}
        symbol=fields.get('issuesymbol') or fields.get('symbol')
        if not symbol:raise ValueError('Halt item lacks a symbol; schema changed')
        resume_date=fields.get('resumptiondate','');resume_time=fields.get('resumptiontradetime','')
        resumed=False
        if resume_date and resume_time:
            from zoneinfo import ZoneInfo
            try:
                dt=datetime.strptime(resume_date+' '+resume_time,'%m/%d/%Y %H:%M:%S').replace(tzinfo=ZoneInfo('America/New_York'))
                resumed=dt<=now
            except ValueError:pass
        if not resumed:halted.add(symbol.upper())
    return halted

class NasdaqHalts:
    def __init__(self,http):self.http=http;self.last=None;self.halted=set();self.healthy=False
    def refresh(self,now):
        if self.last and 0<=(now-self.last).total_seconds()<60:return
        self.last=now;self.healthy=False
        try:
            r=self.http.response(HALT_URL)
            stamp=parsedate_to_datetime(r.headers['Date'])
            if not -60<=(now-stamp).total_seconds()<=300 or int(r.headers.get('Age','0'))>60:return
            self.halted=parse_halts(r.text,now);self.healthy=True
        except (ProviderError,ValueError,KeyError,ET.ParseError):return
    def check(self,ticker,now):
        self.refresh(now)
        return HaltCheck(checked_at=self.last,status='UNKNOWN' if not self.healthy else 'HALTED' if ticker in self.halted else 'CLEAR',
            reason='Current-day Nasdaq feed; fresh regular-session market bars additionally required',source_url=HALT_URL)
