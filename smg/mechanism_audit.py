"""Full roster research audit, not a live strategy or fraud determination.

Reference/friend symbols extend the audit coverage only. Warning tests use
the independently discovered firm corpus; names and future returns never
select a chart rule. Existing frozen forecasts are not modified.
"""
import argparse
import csv
import gzip
import json
import os
import re
from collections import Counter,defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import yaml
from .market import calendar,session_bounds
from .game_rules import is_excluded_symbol
from .risk_model import feature_row,earliest_firm_dates
from .swing_backtest import download
from .transport import Http,ProviderError

UTC=timezone.utc
FAMILIES=('EXHAUSTION_WICK','FAILED_BREAKOUT','SUPPORT_FAILURE','REBOUND_FAILURE')


def patterns(history):
    x=feature_row(history)
    if x is None:return []
    last=history[-1];prior=history[-6:-1];span=last['h']-last['l']
    wick=(last['h']-max(last.get('o',last['c']),last['c']))/span if span>0 else 0
    ramp=x[0]>=.12 or x[1]>=.20
    result=[]
    if ramp and x[4]>=1:result.append('RAMP_WATCH_ONLY')
    if ramp:result.append('RAMP_WATCH_NO_VOLUME_GATE')
    if ramp and x[4]>=1.5 and x[6]>=.08 and wick>=.35 and -.10<x[2]<=.10:
        result.append('EXHAUSTION_WICK')
    prior_high=max(b['h'] for b in prior)
    if ramp and last['h']>=prior_high and last['c']<prior_high and wick>=.30 and x[4]>=1 and -.10<x[2]<=.10:
        result.append('FAILED_BREAKOUT')
    if ramp and x[5] and x[4]>=1 and -.12<=x[2]<=-.03:
        result.append('SUPPORT_FAILURE')
    if x[3]<=-.25 and x[1]>=.10 and x[5] and x[4]>=1 and x[2]>=-.12:
        result.append('REBOUND_FAILURE')
    return result


def chart_family(history):
    x=feature_row(history)
    if x is None:return 'HISTORY_UNAVAILABLE'
    if x[3]<=-.25 and x[1]>=.10:return 'RECOVERY_BOUNCE'
    if x[1]>=.30:return 'SHORT_BURST_RAMP'
    if x[0]>=.50:return 'EXTENDED_RAMP'
    if x[0]>=.12:return 'MODEST_RAMP'
    return 'NO_MEASURED_PRIOR_PUMP'


def longer_ramp_watch(history):
    """Quarter-length pump memory; no timing or fraud certainty is inferred."""
    if len(history)!=63 or not all(history) or any(b['c']<=0 for b in history):return False
    peak=max(b['c'] for b in history)
    return peak/history[0]['c']-1>=.50 and history[-1]['c']/peak-1>=-.25


def compact_records(paths,entities):
    known={name.casefold():role for role,groups in entities.items() for names in groups.values() for name in names}
    unique={}
    for path in paths:
        if not Path(path).exists():continue
        for r in json.loads(Path(path).read_text(encoding='utf-8')):
            if not r.get('ticker') or not r.get('decision_at'):continue
            matches=r.get('firm_matches') or [{'name':n,'role':known.get(n.casefold(),'ROLE_UNCONFIRMED'),
                'relationship':'CONTEXT_NOT_RETAINED','evidence':{'url':r.get('source_url'),'filed_at':r.get('source_date')}} for n in r.get('firms',[])]
            key=(r['ticker'],r.get('source_url'),tuple((m['name'],m['role']) for m in matches))
            if key not in unique or r['decision_at']<unique[key]['decision_at']:
                unique[key]={**{k:r.get(k) for k in ('ticker','cik','decision_at','source_url','status','reasons')},'firm_matches':matches}
    return list(unique.values())


def historical_news(symbols,cache,budget=40,pages_per_group=2):
    if not 1<=pages_per_group<=20:raise ValueError('News pages per group must be between 1 and 20')
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);http=Http();out={};audit=[];requests=0
    headers={'APCA-API-KEY-ID':os.environ['ALPACA_API_KEY'],'APCA-API-SECRET-KEY':os.environ['ALPACA_SECRET_KEY']}
    for offset in range(0,len(symbols),25):
        group=symbols[offset:offset+25];page=None;seen=set();new_pages=0
        while True:
            query={'symbols':','.join(group),'start':'2023-01-01','end':'2025-12-05T23:59:59Z',
                   'limit':50,'sort':'desc','include_content':'false'}
            if page:query['page_token']=page
            import hashlib
            key=hashlib.sha256(json.dumps(query,sort_keys=True).encode()).hexdigest();path=cache/(key+'.json')
            if path.exists():data=json.loads(path.read_text())
            else:
                if requests>=budget:
                    audit.append({'symbols':group,'status':'NEWS_REQUEST_BUDGET'});break
                requests+=1;new_pages+=1
                try:data=http.json('https://data.alpaca.markets/v1beta1/news',params=query,headers=headers)
                except ProviderError as exc:
                    audit.append({'symbols':group,'status':'NEWS_UNAVAILABLE','http_status':exc.status})
                    if exc.status in {401,403,429}:return {s:list(r.values()) for s,r in out.items()},audit,requests
                    break
                path.write_text(json.dumps(data),encoding='utf-8')
            for r in data.get('news',[]):
                row={k:r.get(k) for k in ('id','headline','url','created_at','updated_at','source','symbols')}
                for symbol in set(row.get('symbols') or []) & set(group):out.setdefault(symbol,{})[str(row['id'])]=row
            page=data.get('next_page_token')
            if not page:
                audit.append({'symbols':group,'status':'PROVIDER_SEARCH_COMPLETE_NOT_EXHAUSTIVE_WEB_COVERAGE'});break
            # Bound each group so a few frequently-covered stocks do not use
            # every request before the rest of the audit roster is queried.
            # Cache hits must not consume the per-run pagination allowance:
            # otherwise every resumed run gets stuck at exactly the old page.
            if new_pages>=pages_per_group or len(seen)>=100:
                audit.append({'symbols':group,'status':'PROVIDER_PAGINATION_TRUNCATED'});break
            if page in seen:raise ValueError('Repeated historical news page token')
            seen.add(page)
    return {s:list(r.values()) for s,r in out.items()},audit,requests


def news_before(rows,day):
    close=session_bounds(date.fromisoformat(day))[1];start=close-timedelta(days=7);out=[]
    for r in rows:
        try:
            created=datetime.fromisoformat(r['created_at'].replace('Z','+00:00'))
            updated=datetime.fromisoformat((r.get('updated_at') or r['created_at']).replace('Z','+00:00'))
        except (TypeError,ValueError,KeyError):continue
        if created.tzinfo is not None and updated.tzinfo is not None and start<=created<=close and updated<=close:
            out.append(r)
    return out


def roles_before(records,ticker,day):
    found={};bounds=session_bounds(date.fromisoformat(day))
    if not bounds:return []
    for r in records.get(ticker,[]):
        try:available=datetime.fromisoformat(r['decision_at'].replace('Z','+00:00'))
        except (ValueError,TypeError,AttributeError):continue
        if available.tzinfo is None or available>bounds[1]:continue
        for m in r['firm_matches']:
            relation=m.get('relationship','CURRENT_AT_SOURCE_DATE_ONLY')
            for change in RELATIONSHIP_CHANGES:
                if ticker==change['ticker'] and m['role']==change['role'] and m['name'].casefold()==change['former_party'].casefold() and day>=change['available_by']:
                    relation='FORMER_PARTY_DOCUMENTED; '+change['source_url']
            key=(m['name'],m['role'])
            if key not in found or r['decision_at']>found[key]['decision_at']:
                found[key]={'name':m['name'],'role':m['role'],'relationship_at_source':relation,
                    'decision_at':r['decision_at'],'url':(m.get('evidence') or {}).get('url') or r.get('source_url')}
    return list(found.values())


RELATIONSHIP_CHANGES=[{'ticker':'DTCK','role':'auditor','former_party':'OneStop Assurance PAC',
    'replacement':'AOGB CPA Limited','effective_date':'2024-08-30','available_by':'2024-09-03',
    'source_url':'https://www.sec.gov/Archives/edgar/data/1949478/000168316824006129/davis_6k.htm',
    'publication_proof':'https://www.sec.gov/Archives/edgar/data/1949478/000168316824006129/0001683168-24-006129-index.html',
    'inference_scope':'Auditor relationship status only; never a ticker selection feature'}]


def news_topics(rows):
    terms={'FINANCING_MENTION':r'offer|private placement|shelf|warrant|resale|convertible|dilut',
        'CORPORATE_OR_DISTRESS_EVENT':r'bankrupt|restructur|delist|reverse.split|going.concern',
        'HEALTHCARE_CATALYST':r'\bfda\b|clinical|\btrial\b|pdufa',
        'SPECULATIVE_NARRATIVE_MENTION':r'\bai\b|token|blockchain|crypto|\besg\b|evaluat|non.binding',
        'ALLEGATION_OR_REGULATORY_MENTION':r'fraud|manipulat|sec.charg|investigat|stock.promo'}
    return sorted(k for k,pattern in terms.items() if any(re.search(pattern,r.get('headline') or '',re.I) for r in rows))


def audit(data,sessions,roster,independent,first,records,news,start,end):
    index={d:i for i,d in enumerate(sessions)};by_ticker=defaultdict(list)
    for r in records:by_ticker[r['ticker']].append(r)
    events=[];stock_rows=[];controls=[];alerts=defaultdict(set);gaps=Counter()
    for ticker in roster:
        series=data['split'].get(ticker,{});raw=data['raw'].get(ticker,{})
        active=False;own=[];available=0
        for i,day in enumerate(sessions):
            if not start<=day<=end or i<22:continue
            prior=sessions[i-22:i];outcome=sessions[i-3:i+1]
            if any(d not in series for d in outcome):
                active=False;gaps['OUTCOME_WINDOW_UNAVAILABLE']+=1;continue
            history=[series.get(d) for d in prior];complete=all(history)
            prev=prior[-1];raw_prev=raw.get(prev)
            eligible=(ticker in independent and prev>=first.get(ticker,'9999-99-99') and raw_prev and raw_prev['c']>3
                      and not is_excluded_symbol(ticker) and not re.fullmatch('[A-Z]{5}',ticker))
            if complete:
                available+=1;triggers=patterns(history)
                if i>=63 and longer_ramp_watch([series.get(d) for d in sessions[i-63:i]]):triggers.append('LONGER_RAMP_WATCH_ONLY')
                if 'RAMP_WATCH_NO_VOLUME_GATE' in triggers or 'LONGER_RAMP_WATCH_ONLY' in triggers:
                    triggers.append('COMBINED_SUSCEPTIBILITY_WATCH_ONLY')
                if eligible:
                    for tag in triggers:alerts[tag].add((prev,ticker))
                    if set(triggers)&set(FAMILIES):alerts['COMBINED'].add((prev,ticker))
                    # Nonoverlapping warning windows. This benchmark is next
                    # three closes from the observed close, not a certified fill.
                    future=sessions[i:i+3]
                    if len(future)==3 and future[-1]<=end and all(d in series for d in future) and (i%3==0):
                        hit=min(series[d]['c'] for d in future)/history[-1]['c']-1<=-.20+1e-10
                        controls.append({'ticker':ticker,'signal_date':prev,'tags':triggers,'label':int(hit),
                            'chart_family':chart_family(history),'firms':roles_before(by_ticker,ticker,prev)})
            peak_day=max(outcome[:-1],key=lambda d:series[d]['c']);drop=series[day]['c']/series[peak_day]['c']-1
            if drop>-.20+1e-10:active=False;continue
            if active:continue
            active=True;x=feature_row(history) if complete else None
            prior_news=news_before(news.get(ticker,[]),prev)
            row={'ticker':ticker,'drop_date':day,'prior_decision_date':prev,'peak_date':peak_day,'drop_pct':round(100*drop,3),
                'chart_family':chart_family(history) if complete else 'HISTORY_UNAVAILABLE',
                'outcome_style':'GAP_DOWN' if series[day].get('o',series[day]['c'])/series[prev]['c']-1<=-.20 else
                                'ONE_SESSION_CRASH' if series[day]['c']/series[prev]['c']-1<=-.20 else 'MULTI_SESSION_WATERFALL',
                'raw_price_before':raw_prev['c'] if raw_prev else None,'independent_firm_corpus':ticker in independent,
                'price_and_evidence_scope':bool(eligible),'pre_drop_patterns':patterns(history) if complete else [],
                'return_21_pct':100*x[0] if x else None,'return_5_pct':100*x[1] if x else None,
                'prior_day_return_pct':100*x[2] if x else None,'volume_ratio_20':x[4] if x else None,
                'dated_firm_links':roles_before(by_ticker,ticker,prev),'news_before_signal':prior_news,'news_topic_candidates':news_topics(prior_news),
                'cause_status':'NO_MANIPULATION_FINDING_FROM_PRICE_DATA','float_status':'UNVERIFIED_FROM_THIS_PRICE_PACKET',
                'historical_cap_halt_borrow':'UNAVAILABLE; partial scope is not fully trade eligible'}
            own.append(row);events.append(row)
        links=roles_before(by_ticker,ticker,end)
        stock_rows.append({'ticker':ticker,'daily_bar_count':len(series),'complete_history_days':available,
            'observed_collapse_episodes':len(own),'families':'|'.join(sorted({r['chart_family'] for r in own})),
            'source_firms':'|'.join(sorted({r['name'] for r in links})),
            'source_roles':'|'.join(sorted({r['role'] for r in links})),
            'source_urls':'|'.join(sorted({r['url'] for r in links if r['url']})),
            'data_status':'NO_PROVIDER_BARS' if not series else 'PRICE_HISTORY_ONLY_CAUSE_UNVERIFIED',
            'independent_firm_corpus':ticker in independent,'hard_symbol_exclusion':is_excluded_symbol(ticker) or bool(re.fullmatch('[A-Z]{5}',ticker)),
            'news_articles_archived':len(news.get(ticker,[]))})
    eligible_events=[r for r in events if r['price_and_evidence_scope']]
    scores=[]
    for tag in FAMILIES+('COMBINED','RAMP_WATCH_ONLY','RAMP_WATCH_NO_VOLUME_GATE','LONGER_RAMP_WATCH_ONLY','COMBINED_SUSCEPTIBILITY_WATCH_ONLY'):
        selected=[r for r in controls if (bool(set(r['tags'])&set(FAMILIES)) if tag=='COMBINED' else tag in r['tags'])]
        covered=[e for e in eligible_events if any((d,e['ticker']) in alerts[tag] for d in sessions[max(0,index[e['drop_date']]-3):index[e['drop_date']]])]
        detected=len(covered)
        scores.append({'pattern':tag,'sampled_warning_windows':len(selected),'true_20pct_warning_windows':sum(r['label'] for r in selected),
            'warning_precision':sum(r['label'] for r in selected)/len(selected) if selected else None,
            'price_evidence_scope_events':len(eligible_events),'events_with_prior_warning':detected,
            'partial_scope_event_recall':detected/len(eligible_events) if eligible_events else None,
            'price_evidence_scope_tickers':len({e['ticker'] for e in eligible_events}),
            'tickers_with_some_prior_warning':len({e['ticker'] for e in covered}),
            'warning_days':len(alerts[tag]),'fully_verified_executable_recall':None})
    firms=defaultdict(list)
    for r in controls:
        for f in r['firms']:firms[(f['name'],f['role'])].append(r)
    firm_rates=[{'firm':name,'role':role,'windows':len(rows),'tickers':len({r['ticker'] for r in rows}),
        'positive_windows':sum(r['label'] for r in rows),'observed_rate':sum(r['label'] for r in rows)/len(rows),
        'causal_or_fraud_inference':False} for (name,role),rows in sorted(firms.items())]
    return {'stock_rows':stock_rows,'events':events,'pattern_comparison':scores,'firm_control_rates':firm_rates,
        'control_population_windows':len(controls),'control_positive_windows':sum(r['label'] for r in controls),
        'gaps':dict(gaps),'role_comparison_limitation':'Conditioned on independently discovered watched-firm corpus; cannot establish causality or compare reliably to all unlisted firms',
        'controls':controls}


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--records',nargs='+',required=True)
    p.add_argument('--out',default='outputs/mechanism-audit');p.add_argument('--collect',action='store_true')
    p.add_argument('--news-budget',type=int,default=40);p.add_argument('--end',default='2025-12-05')
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    packet=json.loads(gzip.decompress(Path(args.packet).read_bytes()))
    inventory=json.loads(Path('backtest/audit_inventory.json').read_text());refs=list(csv.DictReader(Path('backtest/reference_events.csv').open()))
    entities=yaml.safe_load(Path('config/entities.yaml').read_text());records=compact_records(args.records,entities)
    first=dict(packet['firm_dates'])
    for ticker,day in earliest_firm_dates(records).items():first[ticker]=min(day,first.get(ticker,day))
    independent=set(first);roster=sorted(independent|{r['ticker'] for r in refs}|set(inventory['friend_short_symbols'])|set(inventory['named_examples']))
    data={k:packet[k] for k in ('raw','split')};requests=0;news={};news_audit=[]
    if args.collect:
        cache=Path('backtest/runtime/mechanism-bars');cache.mkdir(parents=True,exist_ok=True)
        missing=[s for s in roster if not data['raw'].get(s)]
        extra,n=download(missing,'2022-06-01','2025-12-05',cache);requests+=n
        for mode in data:data[mode].update(extra[mode])
        news,news_audit,n=historical_news(roster,'backtest/runtime/mechanism-news',args.news_budget);requests+=n
    sessions=[str(s.date()) for s in calendar(2025).sessions_in_range('2022-06-01','2025-12-05')]
    result=audit(data,sessions,roster,independent,first,records,news,'2023-01-01',args.end)
    lineage=json.loads(Path('backtest/issuer_lineage.json').read_text())['changes']
    for row in result['stock_rows']:
        row['identity_history']=[c for c in lineage if row['ticker'] in {c['old_symbol'],c['new_symbol']}]
        if any(row['ticker']==c['new_symbol'] and args.end<c['effective_date'] for c in row['identity_history']):
            row['data_status']='SYMBOL_NOT_EFFECTIVE_DURING_AUDIT_WINDOW; historical MCTR row is separate'
    periods=[]
    for year in (2023,2024,2025):
        subset=audit(data,sessions,roster,independent,first,records,news,f'{year}-09-08',f'{year}-12-05')
        periods.append({'year':year,'events':len(subset['events']),'patterns':subset['pattern_comparison']})
    result['smg_periods']=periods
    if args.collect:
        extended,n=download(['XHLD','WCT','TJGC'],'2025-12-06','2026-10-05',cache);requests+=n
        for mode in data:
            for symbol,bars in extended[mode].items():data[mode].setdefault(symbol,{}).update(bars)
        full_sessions=[str(s.date()) for s in calendar(2026).sessions_in_range('2022-06-01','2026-10-05')]
        current=audit(data,full_sessions,['XHLD','WCT','TJGC'],independent,first,records,{},'2026-01-01','2026-10-05')
        (out/'named-2026-examples.json').write_text(json.dumps(current,indent=2),encoding='utf-8')
    with gzip.open(out/'audit-inputs.json.gz','wt',encoding='utf-8') as f:
        json.dump({'sessions':sessions,'first_dates':first,'independent_symbols':sorted(independent),
                   'raw':data['raw'],'split':data['split'],'records':records,'news':news},f)
    for name,rows in [('stocks',result['stock_rows']),('episodes',result['events']),('firm-rates',result['firm_control_rates'])]:
        (out/f'{name}.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        if rows:
            with (out/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
                w.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
    comparison=[]
    idx={d:i for i,d in enumerate(sessions)}
    for r in refs:
        series=data['split'].get(r['ticker'],{});day=r['event_date'];i=idx.get(day)
        measured=None
        if i and day in series and sessions[i-1] in series:measured=100*(series[day]['c']/series[sessions[i-1]]['c']-1)
        comparison.append({**r,'measured_close_change_pct':measured,'status':'DAILY_CLOSE_MEASURED_NOT_INTRADAY_REPORT_VERIFICATION' if measured is not None else 'PRICE_OR_SYMBOL_INTERVAL_UNAVAILABLE'})
    (out/'reference-verification.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    summary={k:v for k,v in result.items() if k not in ('stock_rows','events','controls')}
    summary.update(stock_count=len(roster),independent_symbols=len(independent),events=len(result['events']),
        family_counts=dict(Counter(r['chart_family'] for r in result['events'])),market_and_news_requests=requests,
        news_coverage=news_audit,news_articles=sum(len(r) for r in news.values()),reference_events=len(refs),
        reference_events_with_close_data=sum(r['measured_close_change_pct'] is not None for r in comparison),
        stock_data_missing=sum(r['data_status']=='NO_PROVIDER_BARS' for r in result['stock_rows']),
        live_changed=False,frozen_forward_changed=False,
        limitations=['Audit-only friend/reference names never enter pattern selection or independent warning tests',
            'Warning precision/recall uses closes, not assured pre-close executable fills or certified SMG eligibility',
            'No stock is declared fraudulent by price pattern or association',
            'News budget and absent private chats prevent an exhaustive cause determination',
            '2025 repeatedly inspected; hypotheses need new forward validation'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('stock_count','independent_symbols','events','family_counts','pattern_comparison','news_articles','stock_data_missing','reference_events_with_close_data','market_and_news_requests')}))


if __name__=='__main__':main()
