"""Bounded news coverage by season on independent checkpoint candidates."""
import argparse,gzip,json,hashlib,os
from pathlib import Path
from collections import defaultdict
from smg.transport import Http


def collect(symbols,cache,budget=30):
    cache.mkdir(parents=True,exist_ok=True);http=Http();requests=0;rows=defaultdict(dict);audit=[]
    headers={'APCA-API-KEY-ID':os.environ['ALPACA_API_KEY'],'APCA-API-SECRET-KEY':os.environ['ALPACA_SECRET_KEY']}
    # One page per group/year per pass prevents 2025 consuming every request.
    pending=[(year,symbols[i:i+25],None,0) for i in range(0,len(symbols),25) for year in (2023,2024,2025)]
    while pending:
        year,group,token,page=pending.pop(0)
        query={'symbols':','.join(group),'start':f'{year}-09-01','end':f'{year}-12-05T23:59:59Z',
               'limit':50,'sort':'asc','include_content':'false'}
        if token:query['page_token']=token
        path=cache/(hashlib.sha256(json.dumps(query,sort_keys=True).encode()).hexdigest()+'.json')
        if path.exists():data=json.loads(path.read_text())
        elif requests<budget:
            try:data=http.json('https://data.alpaca.markets/v1beta1/news',headers=headers,params=query)
            except Exception as exc:
                audit.append({'year':year,'symbols':group,'status':'PROVIDER_UNAVAILABLE','error_type':type(exc).__name__});continue
            requests+=1;path.write_text(json.dumps(data))
        else:
            audit.append({'year':year,'symbols':group,'status':'REQUEST_BUDGET','page':page});continue
        for r in data.get('news',[]):
            value={k:r.get(k) for k in ('id','headline','url','created_at','updated_at','source','symbols')}
            for t in set(r.get('symbols',[]))&set(group):rows[t][str(r['id'])]=value
        following=data.get('next_page_token')
        audit.append({'year':year,'symbols':group,'status':'PARTIAL_PAGE_LIMIT' if following else 'QUERY_COMPLETE','page':page,'articles':len(data.get('news',[]))})
        if following and page<1 and following!=token:pending.append((year,group,following,page+1))
    return {t:list(r.values()) for t,r in rows.items()},{'provider_requests':requests,'audit':audit,
        'selection':'All independent checkpoint symbols; reference/friend inputs not read','limits':['Missing syndicated coverage is not absence of issuer news','Queries with page/request limits are incomplete']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--signals',required=True)
    p.add_argument('--out',default='reports/balanced/news');a=p.parse_args();folder=Path(a.signals)
    symbols=sorted({e['ticker'] for y in (2023,2024,2025) for es in json.loads((folder/f'{y}-all-checkpoint-signals.json').read_text()).values() for e in es})
    data,report=collect(symbols,Path('backtest/runtime/balanced-news'));packet=json.loads(gzip.decompress(Path(a.packet).read_bytes()))
    for t,items in data.items():
        combined={str(r['id']):r for r in packet.get('news',{}).get(t,[])}
        for r in items:combined[str(r['id'])]=r
        packet.setdefault('news',{})[t]=list(combined.values())
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with gzip.open(out/'inputs.json.gz','wt',encoding='utf-8') as f:json.dump(packet,f)
    report['symbols']=len(symbols);(out/'coverage.json').write_text(json.dumps(report,indent=2));print(json.dumps({'symbols':len(symbols),'provider_requests':report['provider_requests']}))


if __name__=='__main__':main()
