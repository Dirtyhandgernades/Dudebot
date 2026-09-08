"""Local SEC text parser. No hosted model, tokens, credit balance, or network calls."""
from datetime import date,datetime
import re
from .models import Candidate,Evidence,EntityMatch

MONEY=r'(?:US\$|U\.S\.\s*\$|\$)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(million|billion)?'
MONTH=r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
DATE=r'('+MONTH+r'\s+\d{1,2},?\s+20\d{2})'
COUNTRIES={'CN':r'China|People.s Republic of China|\bPRC\b','US':r'United States|\bUSA\b',
           'CA':r'Canada','HK':r'Hong Kong','SG':r'Singapore','MY':r'Malaysia',
           'TW':r'Taiwan','GB':r'United Kingdom|\bUK\b','IN':r'India','IL':r'Israel',
           'AU':r'Australia','JP':r'Japan','KR':r'South Korea','VN':r'Vietnam',
           'ID':r'Indonesia','TH':r'Thailand','DE':r'Germany','FR':r'France'}

def evidence(doc,start,end,padding=120):
    text=doc['text'];a=max(0,start-padding);b=min(len(text),end+padding)
    return Evidence(url=doc['url'],filed_at=doc['date'],quote=text[a:b],document_sha256=doc['sha256'])

def search(docs,pattern,flags=re.I):
    for doc in docs:
        m=re.search(pattern,doc['text'],flags)
        if m:return m,doc,evidence(doc,m.start(),m.end())
    return None

def amount(match,offset=1):
    value=float(match.group(offset).replace(',',''))
    scale=match.group(offset+1)
    return value*({'million':1e6,'billion':1e9}.get((scale or '').lower(),1))

def parse_date(value):
    return datetime.strptime(value.replace(',',''),'%B %d %Y').date()

def name_pattern(name):
    tokens=re.findall(r'[A-Za-z0-9]+',name)
    return r'\b'+r'[\W_]*'.join(r'(?:and|&)' if t.lower()=='and' else re.escape(t) for t in tokens)+r'\b'

class LocalParser:
    def __init__(self,entities):self.entities=entities
    def extract(self,context,docs,now):
        pipeline=context['pipeline'];primary=[d for d in docs if not d.get('context_only')]
        if not primary:return None
        direct=r'\bregistered\s+direct\s+offering\b|\bdirect\s+(?:public\s+)?offering\b'
        ipo=r'\b(?:This is (?:an?|our|the)|We are (?:making|conducting) (?:an?|our|the)) initial public offering\b'
        event_docs=primary if pipeline=='DIRECT_OFFERING' else [dict(d,text=d['text'][:25000]) for d in primary]
        event=search(event_docs,direct if pipeline=='DIRECT_OFFERING' else ipo)
        if not event:return None
        proofs={};notes=['Facts extracted by deterministic SEC text patterns; ambiguous fields require team review.']
        # Transaction terms are restricted to the cover/nearby event paragraphs, not the entire filing.
        event_match,event_doc,_=event
        if pipeline=='DIRECT_OFFERING':
            a=max(0,event_match.start()-900);b=min(len(event_doc['text']),event_match.end()+6500)
        else:a=0;b=min(len(event_doc['text']),25000)
        terms=dict(event_doc,text=event_doc['text'][a:b])
        # Evidence quotes point to the same document and are exact substrings despite the restricted view.
        td=[terms];price=None;gross=None;shares=None
        price_hit=search(td,r'(?:initial public offering price|public offering price|offering price|purchase price)\s*(?:is|was|of|:)?\s*'+MONEY+r'\s*(?:per|for each)\s+(?:ordinary |common |Class [AB] |American depositary )?(?:share|ADS)')
        if not price_hit:price_hit=search(td,r'(?:at a (?:public offering |purchase )?price of|at)\s*'+MONEY+r'\s*per\s+(?:ordinary |common |Class [AB] |American depositary )?(?:share|ADS)')
        if price_hit:price=amount(price_hit[0]);proofs['offer_price']=price_hit[2]
        gross_hit=search(td,r'(?:aggregate |total |approximately |expected )*gross proceeds\s*(?:of|were|was|are|will be|to us of|to the company of)?\s*(?:approximately |about )?'+MONEY)
        if gross_hit:gross=amount(gross_hit[0]);proofs['offer_gross']=gross_hit[2]
        count_hit=search(td,r'(?:we are offering|offering of|sale of|aggregate of|offer and sell)\s+([\d,]+)\s+(?:of our |of its )?(?:Class [AB] |ordinary |common |American depositary )?(?:shares|ADSs)\b')
        if count_hit:shares=float(count_hit[0].group(1).replace(',',''))
        if gross is None and shares and price:
            gross=shares*price
            lo=min(count_hit[0].start(),price_hit[0].start());hi=max(count_hit[0].end(),price_hit[0].end())
            proofs['offer_gross']=evidence(terms,lo,hi,0)
            notes.append('Base gross proceeds calculated as offered shares × offering price.')
        country=None
        for code,rx in COUNTRIES.items():
            hit=search(docs,r'(?:principal (?:business )?operations|substantially all of (?:our|its) (?:business )?operations|(?:we|the company) (?:conduct|conducts) (?:our |its )?(?:business |operations)|(?:we|the company) (?:is|are) (?:a [^.]{0,70})?based)\s+(?:are |is |primarily |principally |located |conducted )*(?:in|out of)\s+(?:the )?(?:'+rx+r')\b')
            if hit:
                if country and country!=code:country=None;proofs.pop('operations_country',None);notes.append('Conflicting operating-country phrases; review required.');break
                country=code;proofs['operations_country']=hit[2]
        # A positive business description is required; absence of the word SPAC is insufficient.
        acquisition=search(docs,r'\b(?:we are|we were|the company is|the company was)\s+(?:a |an )?(?:blank.check company|special purpose acquisition company)\b')
        is_acquisition=None
        if acquisition:is_acquisition=True;proofs['is_acquisition_corp']=acquisition[2]
        elif re.search(r'\bacquisition\s+corp(?:oration)?\b',context['name'],re.I):is_acquisition=True
        elif country:
            is_acquisition=False;proofs['is_acquisition_corp']=proofs['operations_country']
        security=None
        security_hit=search(td,r'\b(?:ordinary shares|common (?:shares|stock)|American depositary shares|ADSs)\b')
        if security_hit:
            security='ADS' if re.search(r'American|ADS',security_hit[0].group(),re.I) else 'CS'
            proofs['security_type']=security_hit[2]
        currency=None
        currency_hit=search(docs,r'\bU\.?S\.? dollars\b|\bUnited States dollars\b|\bUS\$\s*\d|\bU\.S\.\s*\$\s*\d|\bdollars.{0,50}United States')
        if currency_hit:currency='USD';proofs['currency']=currency_hit[2]
        ipo_date=None
        date_hit=search(docs,r'(?:began|commenced|started)\s+(?:publicly )?trading\s+(?:on |in )?(?:the )?(?:Nasdaq|NASDAQ)[^.]{0,110}?\bon\s+'+DATE)
        if date_hit:
            try:ipo_date=parse_date(date_hit[0].group(1));proofs['ipo_date']=date_hit[2]
            except ValueError:pass
        event_date=date.fromisoformat(context['date'])
        event_id='IPO' if pipeline=='RECENT_IPO' else context.get('accession',str(event_date))
        dated=search(td,r'\bOn\s+'+DATE+r'[^.]{0,220}?(?:entered into|priced|announced|completed|closed)')
        if dated:
            try:event_date=parse_date(dated[0].group(1));event_id='IPO' if pipeline=='RECENT_IPO' else str(event_date)
            except ValueError:pass
        elif pipeline=='DIRECT_OFFERING':notes.append('Event date uses filing date; related amendments/closing filings may require grouping.')
        status='unknown'
        canceled=search(td,r'(?:canceled|cancelled|terminated)\s+(?:the |its |our )?(?:registered direct )?offering')
        closed=search(td,r'(?:closed|completed|closing of)\s+(?:the |its |our |an? )?(?:initial public|registered direct|direct|public)?\s*offering')
        priced=search(td,r'\b(?:priced|entered into (?:a |an? )?securities purchase agreement)\b')
        if canceled:status='canceled';proofs['status']=canceled[2]
        elif closed:status='closed';proofs['status']=closed[2]
        elif priced or price_hit:status='priced';proofs['status']=(priced or price_hit)[2]
        matches=[]
        for role,groups in self.entities.items():
            for _,names in groups.items():
                for name in names:
                    for doc in docs:
                        m=re.search(name_pattern(name),doc['text'],re.I)
                        if not m:continue
                        start=max(0,m.start()-250);end=min(len(doc['text']),m.end()+250)
                        passage=doc['text'][start:end]
                        role_terms={'underwriter':r'underwrit|placement agent','auditor':r'audit|independent registered public accounting','counsel':r'counsel|legal matters|legal advisor|legal adviser'}[role]
                        if not re.search(role_terms,passage,re.I):continue
                        relationship='current' if doc.get('context_only') else 'transaction'
                        if doc.get('context_only') and role=='underwriter':relationship='historical'
                        if doc.get('context_only') and (now.date()-date.fromisoformat(doc['date'])).days>450:relationship='historical'
                        actual_role='placement_agent' if role=='underwriter' and re.search('placement agent',passage,re.I) else role
                        matches.append(EntityMatch(name=name,role=actual_role,relationship=relationship,evidence=evidence(doc,start,end,0)));break
        ambiguous=False
        if re.search(r'pre.funded warrant|(?:share|ADS).{0,70}(?:accompanying warrant|and one warrant)|combined (?:purchase |offering )?price',terms['text'],re.I):
            ambiguous=True;notes.append('Bundled securities/warrants require verification of standalone share price.')
        if price and shares and gross and abs(price*shares-gross)>max(1000,gross*.005):
            ambiguous=True;notes.append('Share count × price conflicts with reported gross proceeds.')
        for doc in docs:
            if re.search(r'change.{0,40}(?:independent |registered )?auditor|dismissed.{0,100}(?:auditor|accounting firm)|engaged.{0,100}(?:auditor|accounting firm)',doc['text'],re.I):notes.append('Auditor-change language found: '+doc['url'])
            if re.search(r'ADS ratio|depositary share ratio',doc['text'],re.I):notes.append('ADS ratio requires comparison with market-data unit.')
        return Candidate(pipeline=pipeline,cik=context['cik'],ticker=context['ticker'],name=context['name'],event_id=event_id,
            exchange='XNAS',operations_country=country,ipo_date=ipo_date,event_date=event_date,status=status,security_type=security,
            is_acquisition_corp=is_acquisition,offer_price=price,offer_gross=gross,currency=currency,base_shares=shares,
            terms_unambiguous=bool(price and gross and not ambiguous),matches=matches,evidence=proofs,notes=list(dict.fromkeys(notes)),reviewed_at=now)
