"""Bounded SEC issuer-continuity diagnostic; never stitches prices or certifies aliases."""
import argparse
from datetime import datetime,timezone,timedelta,date
import hashlib,json,os,re
from pathlib import Path
from backtest.obsidian_free_quant_feed import Reader, decoded, passages
from backtest.obsidian_prospective_capture import asof

CASES={'VERB':('0001566610','2025-08-29'),'BREA':('0001939965','2025-10-02')}


def choose_documents(payload,last_day,now):
    r=payload.get('filings',{}).get('recent',{});rows=[]
    if not isinstance(r,dict):return rows
    keys=('accessionNumber','primaryDocument','acceptanceDateTime','form')
    arrays=[r.get(k,[]) for k in keys]
    if any(not isinstance(a,list) for a in arrays) or len({len(a) for a in arrays})!=1:return rows
    for acc,doc,at,form in zip(*arrays):
        stamp=asof(at)
        if stamp is None or stamp>now or not date.fromisoformat(last_day)<=stamp.date()<=date.fromisoformat(last_day)+timedelta(days=14):continue
        if form not in {'8-K','6-K'} or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',str(acc)) or not re.fullmatch(r'[A-Za-z0-9_.-]+',str(doc)):continue
        rows.append(dict(accession=acc,document=doc,public_at=at,form=form))
    return sorted(rows,key=lambda r:r['public_at'])[:2]


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);ua=os.environ.get('SEC_USER_AGENT','');reader=Reader(maximum=9,raw_dir=out/'raw-responses')
    result=dict(mode='RESEARCH_ONLY_NOT_AN_ORDER',cases=[],no_prices_stitched=True,credentials_present=bool(ua))
    for symbol,(cik,last_day) in CASES.items():
        row=dict(old_symbol=symbol,original_archive_cik=cik,last_original_raw_bar=last_day,
                 authenticated_same_security_share_entitlement=False,price_recovery_applied=False)
        if not ua:row['status']='SEC_USER_AGENT_BINDING_ABSENT';result['cases'].append(row);continue
        raw,receipt=reader.get(f'https://data.sec.gov/submissions/CIK{cik}.json',headers={'User-Agent':ua})
        row['submissions_receipt']=receipt;payload=decoded(raw)
        if not isinstance(payload,dict) or str(payload.get('cik','')).lstrip('0')!=cik.lstrip('0'):
            row['status']=receipt['error'] or 'SEC_ISSUER_IDENTITY_MISMATCH';result['cases'].append(row);continue
        row.update(status='CURRENT_SAME_CIK_METADATA_NOT_HISTORICAL_SECURITY_PROOF',current_issuer_name=payload.get('name'),
                   current_reported_tickers=payload.get('tickers'),former_names=payload.get('formerNames'),documents=[])
        saved=raw.replace(ua.encode(),b'[REDACTED_USER_AGENT]');(out/f'{symbol}-submissions.json').write_bytes(saved)
        row['saved_submissions_sha256']=hashlib.sha256(saved).hexdigest()
        for d in choose_documents(payload,last_day,datetime.now(timezone.utc)):
            url=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{d["accession"].replace("-","")}/{d["document"]}'
            body,doc_receipt=reader.get(url,headers={'User-Agent':ua});d.update(url=url,receipt=doc_receipt)
            if body:
                saved=body.replace(ua.encode(),b'[REDACTED_USER_AGENT]')
                name=f'{symbol}-{d["accession"]}.html';(out/name).write_bytes(saved)
                text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',saved.decode('utf-8',errors='replace')))
                d.update(saved_file=name,saved_sha256=hashlib.sha256(saved).hexdigest(),
                         review_passages=passages(text,('trading symbol','ticker','reverse split','change its name','Nasdaq')))
            row['documents'].append(d)
        result['cases'].append(row)
    announcement='https://www.nasdaq.com/press-release/brera-holdings-plc-nasdaq-brea-announces-new-ticker-symbol-slmt-reflecting-its'
    raw,receipt=reader.get(announcement,headers={'User-Agent':'OBSIDIAN-research/1.0'})
    result['brea_issuer_announcement_receipt']=receipt
    if raw:
        safe=raw.replace(ua.encode(),b'[REDACTED_USER_AGENT]') if ua else raw
        (out/'BREA-issuer-announcement.html').write_bytes(safe)
    candidates={'SLMT','BREA','VERB','SPY'}
    for case in result['cases']:
        for symbol in case.get('current_reported_tickers') or []:
            if re.fullmatch(r'[A-Z][A-Z0-9.]{0,12}',str(symbol)):candidates.add(symbol)
    candidates=sorted(candidates)[:6]
    key=os.environ.get('ALPACA_API_KEY','');secret=os.environ.get('ALPACA_SECRET_KEY','')
    result['market_probes']=[]
    for adjustment in ('raw','split'):
        if not key or not secret:
            result['market_probes'].append({'adjustment':adjustment,'status':'ALPACA_RESEARCH_BINDING_ABSENT'});continue
        params=dict(symbols=','.join(candidates),timeframe='1Day',feed='sip',adjustment=adjustment,
                    start='2025-08-01T00:00:00Z',end='2025-12-31T23:59:59Z',limit=1000)
        raw,receipt=reader.get('https://data.alpaca.markets/v2/stocks/bars',params=params,
                              headers={'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret})
        payload=decoded(raw)
        valid=isinstance(payload,dict) and isinstance(payload.get('bars'),dict) and not set(payload['bars'])-set(candidates)
        counts={symbol:len(bars) for symbol,bars in payload['bars'].items()} if valid and all(isinstance(b,list) for b in payload['bars'].values()) else {}
        result['market_probes'].append(dict(adjustment=adjustment,requested_symbols=candidates,receipt=receipt,
            status=receipt['error'] or ('PAGINATION_INCOMPLETE' if valid and payload.get('next_page_token') else 'DAILY_BARS_RETRIEVED_UNVERIFIED_IDENTITY' if counts else 'MALFORMED_OR_EMPTY_BARS'),
            bar_counts=counts,official_closes_verified=False,security_continuity_verified=False,prices_stitched=False))
    result['requests_used']=reader.used
    (out/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True));return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);a=p.parse_args()
    r=run(a.out);print(json.dumps({'requests':r['requests_used'],'cases':[(x['old_symbol'],x['status']) for x in r['cases']]}))
if __name__=='__main__':main()
