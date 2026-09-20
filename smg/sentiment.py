"""Best-effort free sentiment context. It never creates or suppresses a trade.

Each provider is optional and failures are recorded as data gaps. Responses are
cached by the caller; this module does not scrape at high frequency.
"""
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

from .transport import Http, ProviderError

def _news_score(title):
    positive=('surge','growth','raises','approval','contract','profit','beats','partnership')
    negative=('fraud','probe','lawsuit','offering','dilution','halts','warning','misses','loss')
    words=set(re.findall(r'[a-z]+',title.lower()))
    return sum(w in words for w in positive)-sum(w in words for w in negative)

def collect(ticker, http=None, now=None):
    http=http or Http();now=now or datetime.now(timezone.utc)
    out={'ticker':ticker,'observed_at':now.isoformat(),'providers':{},'score':None,'limitations':[]}
    scores=[]
    try:
        raw=http.text('https://finviz.com/quote.ashx?t='+quote(ticker),headers={'User-Agent':'Mozilla/5.0'})
        # Public page table values are context only; do not rely on fragile labels.
        mentions=len(re.findall(r'\b(?:short float|target price|news|insider)\b',raw,re.I))
        out['providers']['finviz']={'status':'AVAILABLE','observed_at':now.isoformat(),'source':'https://finviz.com/quote.ashx?t='+ticker,'context_markers':mentions}
    except Exception as exc:out['providers']['finviz']={'status':'UNAVAILABLE','observed_at':now.isoformat(),'error_type':type(exc).__name__}
    try:
        data=http.json('https://api.stocktwits.com/api/2/streams/symbol/'+quote(ticker)+'.json')
        messages=data.get('messages') or [];vals=[]
        for msg in messages[:30]:
            cls=(msg.get('entities') or {}).get('sentiment') or {};v=cls.get('basic')
            if v in {'Bullish','Bearish'}:vals.append(1 if v=='Bullish' else -1)
        if vals:scores.extend(vals)
        stamps=[m.get('created_at') for m in messages if m.get('created_at')]
        out['providers']['stocktwits']={'status':'AVAILABLE','observed_at':now.isoformat(),'source':'https://api.stocktwits.com/api/2/streams/symbol/'+ticker+'.json',
            'messages':len(messages),'bullish':vals.count(1),'bearish':vals.count(-1),'latest_source_timestamp':max(stamps) if stamps else None}
    except Exception as exc:out['providers']['stocktwits']={'status':'UNAVAILABLE','observed_at':now.isoformat(),'error_type':type(exc).__name__}
    try:
        data=http.text('https://news.google.com/rss/search?q='+quote(ticker+' stock'),headers={'User-Agent':'Mozilla/5.0'})
        root=ET.fromstring(data);items=root.findall('./channel/item')[:20];titles=[(x.findtext('title') or '') for x in items]
        vals=[_news_score(t) for t in titles];scores.extend(v for v in vals if v)
        stamps=[]
        for item in items:
            try:stamps.append(parsedate_to_datetime(item.findtext('pubDate')).astimezone(timezone.utc).isoformat())
            except (TypeError,ValueError):pass
        out['providers']['news']={'status':'AVAILABLE','observed_at':now.isoformat(),'source':'https://news.google.com/rss/search?q='+quote(ticker+' stock'),
            'articles':len(titles),'headline_score':sum(vals),'latest_source_timestamp':max(stamps) if stamps else None}
    except Exception as exc:out['providers']['news']={'status':'UNAVAILABLE','observed_at':now.isoformat(),'error_type':type(exc).__name__}
    if scores:out['score']=round(sum(scores)/len(scores),3)
    else:out['limitations'].append('No provider returned scored sentiment')
    out['limitations'].append('Sentiment is context only; it is never a hard eligibility gate or misconduct finding')
    return out
