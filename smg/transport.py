"""Credential-redacted HTTP client. No automatic retries of mutating calls."""
import time
from urllib.parse import urlsplit
import requests
class ProviderError(RuntimeError):
    def __init__(self,host,status=None,reason=None):
        self.status=status;self.reason=reason
        message=f'{host}: HTTP {status}' if status else f'{host}: connection failed'
        super().__init__(message+(' ('+reason+')' if reason else ''))
class Http:
    def __init__(self): self.session=requests.Session();self.last={}
    def response(self,url,method='GET',params=None,headers=None,body=None,timeout=25):
        host=urlsplit(url).hostname
        if urlsplit(url).scheme!='https':raise ValueError('HTTPS required')
        # SEC requests are serialized below 10/s; Nasdaq feed no more than once/minute is cached by caller.
        interval=.2 if host in {'www.sec.gov','data.sec.gov','efts.sec.gov'} else .35 if host=='data.alpaca.markets' else 1 if host=='api.github.com' and method!='GET' else .03
        time.sleep(max(0,interval-(time.monotonic()-self.last.get(host,0))))
        self.last[host]=time.monotonic()
        for attempt in range(3 if method=='GET' else 1):
            try:r=self.session.request(method,url,params=params,headers=headers,json=body,timeout=timeout,allow_redirects=False)
            except requests.RequestException:
                if method=='GET' and attempt<2:time.sleep(2*(attempt+1));continue
                raise ProviderError(host) from None
            message=''
            if host=='api.github.com' and r.status_code in (403,409):
                try:message=str(r.json().get('message','')).lower()
                except (ValueError,AttributeError,TypeError):pass
            secondary='secondary rate' in message or 'abuse detection' in message
            limited=r.status_code==429 or (r.status_code==403 and (secondary or r.headers.get('Retry-After') or r.headers.get('X-RateLimit-Remaining')=='0'))
            if limited and method=='GET' and attempt<2:
                try:
                    if 'Retry-After' in r.headers:delay=float(r.headers['Retry-After'])
                    elif r.headers.get('X-RateLimit-Remaining')=='0':delay=float(r.headers['X-RateLimit-Reset'])-time.time()+1
                    else:delay=61 if secondary else 2
                except (ValueError,KeyError):delay=31
                # Never retry early when the provider asks for a longer wait.
                # The next scheduled run handles long rate-limit windows.
                if 0<=delay<=30:time.sleep(max(delay,1));continue
            if not 200<=r.status_code<300:
                reason='SECONDARY_RATE_LIMIT' if secondary else 'RATE_LIMIT' if limited else 'STATE_SHA_CONFLICT' if r.status_code==409 and 'sha' in message else 'ACCESS_DENIED' if r.status_code==403 else None
                raise ProviderError(host,r.status_code,reason)
            return r
        raise ProviderError(host,429)
    def json(self,url,**kw):
        r=self.response(url,**kw)
        try:return r.json()
        except ValueError:raise ProviderError(urlsplit(url).hostname,r.status_code) from None
    def text(self,url,**kw):return self.response(url,**kw).text
