"""Targeted benchmark audit ONLY. Never merge its findings into blind selection."""
import argparse,gzip,json,hashlib,os,time
from pathlib import Path
from collections import Counter
from smg.transport import Http
from smg.game_firm_replay import research_entries
from smg.source_replay import parse_source,source_identity
from lxml import html as lhtml
from urllib.parse import urlencode
import yaml


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--labels',default='backtest/friend_short_audit_labels.json')
    p.add_argument('--out',default='reports/balanced/source-gap-audit');a=p.parse_args()
    packet=json.loads(gzip.decompress(Path(a.packet).read_bytes()));labels=json.loads(Path(a.labels).read_text())
    cache=Path('backtest/runtime/labelled-source-audit');cache.mkdir(parents=True,exist_ok=True)
    http=Http();headers={'User-Agent':os.environ['SEC_USER_AGENT']};requests=0;started=time.monotonic()
    def fetch(url):
        nonlocal requests
        path=cache/(hashlib.sha256(url.encode()).hexdigest()+'.txt')
        if path.exists():return path.read_text(encoding='utf-8')
        if requests>=80 or time.monotonic()-started>240:raise RuntimeError('AUDIT_BUDGET')
        requests+=1;value=http.text(url,headers=headers);path.write_text(value,encoding='utf-8');return value
    mapping=json.loads(fetch('https://www.sec.gov/files/company_tickers_exchange.json'))
    hints={r[2]:{'cik':r[0],'name':r[1]} for r in mapping['data']}
    entries=research_entries(yaml.safe_load(Path('config/entities.yaml').read_text(encoding='utf-8')));rows=[]
    for label in labels:
        ticker=label['ticker'];row={**label,'selection_scope':'LABELLED_AUDIT_ONLY_NOT_BACKTEST_INPUT','findings':[]}
        if ticker in packet['first_dates']:
            row['status']='INDEPENDENT_EVIDENCE_ALREADY_PRESENT';rows.append(row);continue
        if ticker not in hints:
            # A missing current listing must not erase a historical issuer.
            # These benchmark-directed queries remain entirely audit-only.
            try:
                query=urlencode({'q':'"'+ticker+'"','forms':'20-F,10-K,424B4',
                    'dateRange':'custom','startdt':'2021-01-01','enddt':label['first_short_date']})
                search=json.loads(fetch('https://efts.sec.gov/LATEST/search-index?'+query))
                for hit in search.get('hits',{}).get('hits',[])[:5]:
                    src=hit['_source']
                    if len(src.get('ciks',[]))!=1 or src.get('file_type',src.get('form'))!=src.get('form'):continue
                    acc,name=hit['_id'].split(':',1)
                    url=f"https://www.sec.gov/Archives/edgar/data/{int(src['ciks'][0])}/{acc.replace('-','')}/{name}"
                    raw=fetch(url);tree=lhtml.document_fromstring(raw.encode('utf-8'),parser=lhtml.HTMLParser(encoding='utf-8',no_network=True))
                    symbol,exchange,_=source_identity(tree,' '.join(tree.itertext()))
                    if symbol==ticker and exchange in {'XNAS','XNYS'}:
                        hints[ticker]={'cik':src['ciks'][0],'name':'Historical issuer verified in own filing',
                                       'historical_lookup_proof':url};break
            except Exception as exc:
                row['historical_lookup_gap']=type(exc).__name__
            if ticker not in hints:
                row['status']='HISTORICAL_MAPPING_UNRESOLVED_AFTER_BOUNDED_LOOKUP';rows.append(row);continue
        row['current_hint']=hints[ticker]
        try:
            data=json.loads(fetch(f"https://data.sec.gov/submissions/CIK{int(hints[ticker]['cik']):010d}.json"));blocks=[data['filings']['recent']]
            for item in data['filings'].get('files',[]):
                if item['filingFrom']<=label['first_short_date'] and item['filingTo']>='2021-01-01':
                    blocks.append(json.loads(fetch('https://data.sec.gov/submissions/'+item['name'])))
                    break
            filings=[]
            for block in blocks:
                for i,acc in enumerate(block.get('accessionNumber',[])):
                    day=block['filingDate'][i];form=block['form'][i]
                    if '2021-01-01'<=day<label['first_short_date'] and form in {'20-F','10-K','424B4','424B3','424B5'}:
                        filings.append((day,acc,form,block['primaryDocument'][i]))
            if not filings:row['status']='NO_SAMPLED_PRE_ENTRY_FILINGS'
            else:
                row['status']='SAMPLED_FILINGS_NO_MATCH_NOT_EXHAUSTIVE'
                annual=sorted((r for r in set(filings) if r[2] in {'20-F','10-K'}),reverse=True)[:1]
                offerings=sorted(r for r in set(filings) if r[2]=='424B4')[:1]
                selected=list(dict.fromkeys(annual+offerings+sorted(set(filings),reverse=True)))[:2]
                for day,acc,form,name in selected:
                    url=f"https://www.sec.gov/Archives/edgar/data/{int(hints[ticker]['cik'])}/{acc.replace('-','')}/{name}"
                    raw=fetch(url);candidate,status=parse_source(acc+':'+name,{'ciks':[str(hints[ticker]['cik'])],'file_date':day,'form':form},raw,entries)
                    tree=lhtml.document_fromstring(raw.encode('utf-8'),parser=lhtml.HTMLParser(encoding='utf-8',no_network=True))
                    historical_symbol,exchange,_=source_identity(tree,' '.join(tree.itertext()))
                    finding={'url':url,'filed_at':day,'parser_status':status,'historical_symbol':historical_symbol,
                             'exchange':exchange,'historical_identity_verified':historical_symbol==ticker and exchange in {'XNAS','XNYS'}}
                    if candidate and candidate.ticker==ticker:
                        finding['parties']=[{'name':m.name,'role':m.role,'quote':m.evidence.quote} for m in candidate.matches]
                        finding['historical_identity_verified']=True;row['status']='LABELLED_PRE_ENTRY_FIRM_EVIDENCE_FOUND'
                        finding['is_acquisition_corp']=candidate.is_acquisition_corp
                    elif candidate:finding['historical_identity_verified']=False;finding['gap']='CURRENT_HINT_DID_NOT_ESTABLISH_HISTORICAL_SYMBOL'
                    row['findings'].append(finding)
        except Exception as exc:
            row['status']='AUDIT_UNAVAILABLE';row['error_type']=type(exc).__name__;row['http_status']=getattr(exc,'status',None)
        rows.append(row)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    report={'selection_used_labels':False,'audit_queries_used_labels':True,'findings_merged_into_selection':False,
        'provider_requests':requests,'counts':dict(Counter(r['status'] for r in rows)),'rows':rows,
        'limits':['Current CIK mapping is a hint until a dated own-issuer symbol is verified',
                  'Two sampled filings cannot establish absence of every listed firm',
                  'Label-directed sources must not be inserted into an independent backtest']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__=='__main__':main()
