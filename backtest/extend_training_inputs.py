"""Fill previously missing early training history; enrich past-only context."""
import argparse
import gzip
import json
import math
from pathlib import Path
import numpy as np
import yaml
from smg.market import calendar
from smg.rules import EntityList,normalize_name
from smg.swing_backtest import download
from backtest.repair_study import build_rows

EXTRA_FEATURES=('focus_auditor_association','focus_underwriter_association','focus_counsel_association',
                'documented_former_focus_auditor','listed_role_count','auditor_underwriter_focus_pair',
                'return3','trend_acceleration','range_compression','volume_climax',
                'market_return21','market_return5','market_volatility21','market_history_available')


def augment_rows(rows,packet,entities):
    sessions=packet['sessions'];index={d:i for i,d in enumerate(sessions)};known=EntityList(entities).entries
    spy=packet['split'].get('SPY',{});output=[]
    for row in rows:
        i=index[row['signal_date']];series=packet['split'][row['ticker']]
        bars=[series[d] for d in sessions[i-21:i+1]];last=bars[-1];focus=set();former=False;roles=set()
        for link in row['dated_firms']:
            role='underwriter' if link['role']=='placement_agent' else link['role'];roles.add(role)
            entry=known.get((role,normalize_name(link['name'])))
            if entry and entry['priority']<=0:
                focus.add(role)
                if role=='auditor' and link['relationship_at_source'].startswith('FORMER_PARTY'):former=True
        return3=last['c']/bars[-4]['c']-1
        ranges=[(b['h']-b['l'])/b['c'] for b in bars[:-1]];average=sum(ranges)/len(ranges)
        compression=(sum(ranges[-5:])/5)/average if average>0 else 1
        vol=sum(b['v'] for b in bars[-6:-1])/5
        market=[spy.get(d) for d in sessions[i-21:i+1]];complete=all(market)
        macro=[market[-1]['c']/market[0]['c']-1,market[-1]['c']/market[-6]['c']-1,
               float(np.std([market[j]['c']/market[j-1]['c']-1 for j in range(1,22)])),1.] if complete else [0.,0.,0.,0.]
        extra=[float('auditor' in focus),float('underwriter' in focus),float('counsel' in focus),float(former),
               float(len(roles)),float({'auditor','underwriter'}<=focus),return3,return3-.6*row['x'][1],
               compression,math.log1p(last['v']/vol) if vol>0 else 0]+macro
        output.append({**row,'x':row['x']+extra})
    return output


def align_early_history(packet,extra,end='2022-06-07'):
    added=0;gaps=[]
    for ticker in extra['raw']:
        current=packet['raw'].get(ticker,{});old=extra['raw'][ticker]
        overlap=sorted(set(current)&set(old))
        if overlap and any(abs(current[d]['c']/old[d]['c']-1)>1e-6 for d in overlap):
            gaps.append({'ticker':ticker,'reason':'RAW_HISTORY_REVISION_REQUIRES_REVIEW'});continue
        ratio=1.
        if overlap:
            d=overlap[-1];a=packet['split'][ticker].get(d);b=extra['split'].get(ticker,{}).get(d)
            if not a or not b:gaps.append({'ticker':ticker,'reason':'ADJUSTMENT_ALIGNMENT_MISSING'});continue
            ratio=a['c']/b['c']
        for mode in ('raw','split'):
            for day,bar in extra.get(mode,{}).get(ticker,{}).items():
                if day in packet[mode].get(ticker,{}):continue
                value=dict(bar)
                if mode=='split':value.update({k:value[k]*ratio for k in ('o','h','l','c') if k in value})
                packet[mode].setdefault(ticker,{})[day]=value
                if mode=='raw':added+=1
    return {'added_raw_symbol_days':added,'alignment_gaps':gaps}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packet',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--collect',action='store_true');args=parser.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    packet=json.loads(gzip.decompress(Path(args.packet).read_bytes()));requests=0;collection={}
    if args.collect:
        early=sorted(s for s,d in packet['first_dates'].items() if d<'2023-01-01')
        cache=Path('backtest/runtime/action-history');cache.mkdir(parents=True,exist_ok=True)
        extra,n=download(early,'2021-09-01','2022-06-07',cache);requests+=n
        collection=align_early_history(packet,extra)
        market,n=download(['SPY'],'2021-09-01','2025-12-05',cache);requests+=n
        for mode in ('raw','split'):packet[mode].update(market[mode])
        packet['sessions']=[str(d.date()) for d in calendar(2025).sessions_in_range('2021-09-01','2025-12-05')]
        collection['early_independent_symbols']=len(early)
    entities=yaml.safe_load(Path('config/entities.yaml').read_text());rows,gaps,first=build_rows(packet,packet['records'])
    rows=augment_rows(rows,packet,entities)
    for name,value in [('inputs',packet),('observations',rows)]:
        with gzip.open(out/(name+'.json.gz'),'wt',encoding='utf-8') as f:json.dump(value,f)
    summary={'provider_requests':requests,'collection':collection,'feature_additions':EXTRA_FEATURES,
             'rows':len(rows),'gaps':gaps,'selection':'Only prior independent firm dates select early-history requests; SPY is context, never a candidate'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
