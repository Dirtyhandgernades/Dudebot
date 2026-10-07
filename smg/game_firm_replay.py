"""Bounded game-period discovery and research replay without reference inputs.

Reuses immutable SEC source caches and date-stamped baseline decisions, extends
the search through game end, and admits new symbols only after source evidence.
No live delivery, reference files, friend transactions or probability claims.
"""
import argparse
import gzip
import hashlib
import json
import os
import shutil
import time
from collections import Counter,defaultdict,deque
from datetime import date
from pathlib import Path
from .backtest import write_json
from .cli import settings
from .firm_first import firm_structure
from .firm_search import collect_firm_search
from .models import Candidate
from .risk_model import earliest_firm_dates
from .rules import EntityList
from .source_replay import parse_source, select_sources
from .swing_backtest import download, simulate, stitch_rename
from .market import calendar
from .transport import Http


def dated_records(candidates,cfg,entities):
    """Reuse only earlier issuer-classification evidence for the same CIK."""
    classification={};records=[]
    for original in sorted(candidates,key=lambda c:c.reviewed_at):
        c=original;prior=classification.get(c.cik)
        if prior and (prior[0] is True or (c.is_acquisition_corp is None and
                0<=(c.reviewed_at.date()-prior[1].filed_at).days<=450)):
            c=c.model_copy(update={'is_acquisition_corp':prior[0],
                                  'evidence':{**c.evidence,'is_acquisition_corp':prior[1]}})
        proof=c.evidence.get('is_acquisition_corp')
        if proof is not None and c.is_acquisition_corp is not None:
            classification[c.cik]=(c.is_acquisition_corp,proof)
        result=firm_structure(c,cfg,entities,c.reviewed_at)
        records.append({'ticker':c.ticker,'cik':c.cik,'decision_at':c.reviewed_at.isoformat(),
                        'status':result.status,'reasons':result.reasons,'source_url':c.matches[0].evidence.url,
                        'firm_matches':result.matches})
    return records


def research_entries(entries):
    """Verified same-entity former names; no winner tickers or live list edits.

    EF Hutton LLC rebranded Nov8,2024. Keep the old name in historical evidence;
    this is a retrospective identity extension of the user's D.Boral watch.
    Do not match the unrelated1980s EF Hutton entities or all Hutton brands.
    """
    import copy
    result=copy.deepcopy(entries)
    for names in result.get('underwriter',{}).values():
        if 'D. Boral Capital' in names:
            names+=['EF Hutton LLC','E. F. Hutton LLC'];break
    for names in result.get('auditor',{}).values():
        if 'WWC, P.C.' in names:names.append('W. W. C., P.C.')
    return result


def interleave_years(items):
    buckets=defaultdict(deque)
    for item in items:buckets[item[1]['file_date'][:4]].append(item)
    result=[]
    while any(buckets.values()):
        for year in sorted(buckets):
            if buckets[year]:result.append(buckets[year].popleft())
    return result


def discover(root, cfg, entries, *, max_documents=1200, max_seconds=600,priority_period='balanced'):
    entries=research_entries(entries)
    state=root/'backtest/runtime/game-firm-search'
    state.mkdir(parents=True,exist_ok=True)
    db=state/'firm-search.sqlite'
    if not db.exists():
        original=next((root/'backtest/runtime/independent-checkpoint').rglob('firm-search.sqlite'),None)
        if original:shutil.copyfile(original,db)
    searches={}
    for year in range(2021,2026):
        if max_documents==0:
            searches[str(year)]={'status':'CACHE_ONLY_NO_SEARCH','pages_this_run':0};continue
        searches[str(year)]=collect_firm_search(state,min(date(year,12,31),date(2025,12,5)),entries,
            start=date(year,1,1),max_pages=12,balanced=True,max_seconds=min(36,max_seconds/10))
    search={'status':'YEAR_BALANCED_SEARCH','years':searches,'page_budget_per_year':12,
            'complete':all(v.get('status')=='SEARCH_INDEX_COMPLETE' for v in searches.values())}
    if not db.exists():return [],{'search':search,'status':'SEARCH_NOT_RUN'}
    selected=select_sources(db,start=date(2021,1,1),end=date(2025,12,5))
    cache=root/'backtest/runtime/source-replay';cache.mkdir(parents=True,exist_ok=True)
    def source_order(item):
        identifier,src=item;accession,filename=identifier.split(':',1)
        url=f"https://www.sec.gov/Archives/edgar/data/{int(src['ciks'][0])}/{accession.replace('-','')}/{filename}"
        digest=hashlib.sha256(url.encode()).hexdigest()
        parsed=cache/(digest+'.game-balanced-v1.json')
        warm=cache/(digest+'.html')
        # Budget priority uses dates/forms/cache only, never winner tickers.
        if parsed.exists():bucket=0
        elif priority_period=='earlier_years' and src['file_date']<'2025-01-01':bucket=1
        elif src['file_date']>'2025-07-28' and src['form'].startswith('424B'):bucket=1
        elif warm.exists():bucket=2
        elif src['file_date']>'2025-07-28':bucket=3
        elif src['file_date']>='2025-01-01':bucket=4
        else:bucket=5
        return bucket,src['file_date'],identifier
    selected.sort(key=source_order)
    first=[];later=[];seen=set()
    for item in selected:
        cik=item[1]['ciks'][0]
        (later if cik in seen else first).append(item);seen.add(cik)
    selected=interleave_years(first+later)
    http=Http();started=time.monotonic();downloaded=0;candidates=[];sources=[]
    entities=EntityList(entries);year_downloads=Counter();year_reviews=Counter();quota=max_documents//5
    for identifier,src in selected:
        if time.monotonic()-started>=max_seconds:break
        accession,filename=identifier.split(':',1)
        import re
        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession) or '..' in filename:continue
        url=f"https://www.sec.gov/Archives/edgar/data/{int(src['ciks'][0])}/{accession.replace('-','')}/{filename}"
        digest=hashlib.sha256(url.encode()).hexdigest()
        raw_path=cache/(digest+'.html');parsed_path=cache/(digest+'.game-balanced-v1.json')
        try:
            legacy=cache/(digest+'.parsed-v5.json')
            if not legacy.exists():legacy=cache/(digest+'.game-v3.json')
            if not legacy.exists():legacy=cache/(digest+'.game-v1.json')
            # Positive cached evidence is immutable and already reviewed by the
            # same structural gates. Retry negatives with the improved parser.
            if not parsed_path.exists() and legacy.exists() and not raw_path.exists():
                saved=json.loads(legacy.read_text(encoding='utf-8'))
                if saved.get('candidate'):write_json(parsed_path,saved)
            if parsed_path.exists():
                parsed=json.loads(parsed_path.read_text(encoding='utf-8'))
                c=Candidate.model_validate(parsed['candidate']) if parsed['candidate'] else None
                status=parsed['status']
            else:
                if not raw_path.exists():
                    if downloaded>=max_documents or year_downloads[src['file_date'][:4]]>=quota:
                        sources.append({'id':identifier,'status':'SOURCE_DOWNLOAD_BUDGET','filed_at':src['file_date']});continue
                    raw_path.write_text(http.text(url,headers={'User-Agent':os.environ['SEC_USER_AGENT']}),encoding='utf-8')
                    downloaded+=1
                    year_downloads[src['file_date'][:4]]+=1
                c,status=parse_source(identifier,src,raw_path.read_text(encoding='utf-8'),entries)
                write_json(parsed_path,{'status':status,'candidate':c.model_dump(mode='json') if c else None})
            sources.append({'id':identifier,'status':status,'filed_at':src['file_date'],'source_url':url,
                            'ticker':c.ticker if c else None})
            year_reviews[src['file_date'][:4]]+=1
            if c:
                # Two punctuation variants of one LLC must not count twice.
                used=set();unique=[]
                for match in c.matches:
                    identity=('D.BORAL_VERIFIED_FORMER_LLC' if match.name in {'D. Boral Capital','EF Hutton LLC','E. F. Hutton LLC'}
                              else 'WWC_PC' if match.name in {'WWC, P.C.','W. W. C., P.C.'} else match.name)
                    key=(match.role,identity)
                    if key not in used:used.add(key);unique.append(match)
                c.matches=unique
                candidates.append(c)
        except Exception as exc:
            sources.append({'id':identifier,'status':'SOURCE_ERROR','error_type':type(exc).__name__,
                            'http_status':getattr(exc,'status',None)})
            if getattr(exc,'status',None) in {401,403,429}:break
    records=dated_records(candidates,cfg,entities)
    out=root/'reports/game-firm-replay';out.mkdir(parents=True,exist_ok=True)
    write_json(out/'discovery-decisions.json',records);write_json(out/'source-audit.json',sources)
    summary={'search':search,'selected_sources':len(selected),'sources_visited':len(sources),
             'source_documents_reviewed':sum(s['status'] in {'FIRM_CANDIDATE_EXTRACTED','NO_ATTACHED_LISTED_FIRM_ROLE_RECOGNIZED','SOURCE_SYMBOL_OR_EXCHANGE_UNRESOLVED'} for s in sources),
             'source_status_counts':dict(Counter(s['status'] for s in sources)),
             'unvisited_sources':len(selected)-len(sources),'downloads_this_run':downloaded,
             'source_seconds':round(time.monotonic()-started,2),'universe_complete':False,
             'new_download_quota_per_year':quota,'downloads_by_source_year':dict(year_downloads),
             'reviews_by_source_year':dict(year_reviews),
             'research_aliases':[{'canonical':'D. Boral Capital','former_legal_name':'EF Hutton LLC',
                 'identity_notice_date':'2024-11-08','source':'https://dboralcapital.com/news/ef-hutton-llc-announce-rebranding-to-d-boral-capital-llc/',
                 'scope':'Retrospective identity research; live entities.yaml unchanged'}],
             'budget_priority':'One source per issuer first; '+('earlier-year evidence before reused 2025 sources' if priority_period=='earlier_years' else 'cached evidence, post-July offerings, cached negatives, other dated game filings, earlier sources'),
             'priority_period':priority_period}
    write_json(out/'discovery-summary.json',summary)
    return records,summary


def lead_metrics(result,raw,adjusted,sessions,start,end):
    """Score future drops after selection; failed/missing outcomes remain gaps."""
    index={day:i for i,day in enumerate(sessions)};events=[];unknown=0
    signal_days={}
    for signal in result['signal_events']:
        signal_days.setdefault(signal['ticker'],set()).add(signal['signal_date'])
    for ticker in adjusted:
        series=adjusted[ticker]
        in_event=False
        for i,day in enumerate(sessions):
            if not start<=day<=end or i==0:continue
            previous=sessions[i-1]
            before=series.get(previous);after=series.get(day)
            if not before or not after:
                unknown+=1;in_event=False;continue
            raw_before=raw.get(ticker,{}).get(previous)
            if not raw_before or raw_before['c']<=3:
                in_event=False;continue
            drop=after['c']/before['c']-1<=-.20
            if drop and not in_event:
                prior=[s for s in signal_days.get(ticker,set()) if s in index and 1<=i-index[s]<=5]
                fills=[t for t in result['trades'] if t['ticker']==ticker and t['entry_date']<day<=t['exit_date']]
                events.append({'ticker':ticker,'drop_date':day,'one_session_drop_pct':100*(after['c']/before['c']-1),
                               'prior_signal_dates':sorted(prior),'position_open_before_drop':bool(fills)})
            in_event=drop
    covered=sum(bool(e['prior_signal_dates']) for e in events)
    return {'definition':'Distinct >=20% one-session close drops, scored only after simulation; prior alerts 1-5 sessions',
            'events':len(events),'events_with_prior_signal':covered,'event_recall':covered/len(events) if events else None,
            'events_with_position_open_before_drop':sum(e['position_open_before_drop'] for e in events),
            'missing_symbol_day_outcomes':unknown,'rows':events,
            'limitations':['Outcome universe is discovered firm corpus, not whole market or friend winners',
                           'Firm watch visibility is distinct from timing signals and actual executable positions']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',required=True)
    parser.add_argument('--max-documents',type=int,default=1200)
    parser.add_argument('--max-seconds',type=int,default=600)
    parser.add_argument('--priority-period',choices=['balanced','earlier_years'],default='balanced')
    parser.add_argument('--gather-only',action='store_true',help='Collect independent sources without repeating market downloads/backtests')
    args=parser.parse_args();root=Path.cwd();cfg,entries=settings(root)
    additions,discovery=discover(root,cfg,entries,max_documents=args.max_documents,max_seconds=args.max_seconds,priority_period=args.priority_period)
    if args.gather_only:
        print(json.dumps({'status':'BOUNDED_SOURCE_GATHER','discovery':discovery,'records':len(additions)}));return
    records=json.loads(Path(args.baseline).read_text())+additions
    first=earliest_firm_dates(records)
    # Include within-game discoveries, but gate each signal by its known date.
    from .game_rules import is_excluded_symbol
    import re,csv
    symbols=sorted(t for t,day in first.items() if day<='2025-12-05' and
                   not is_excluded_symbol(t) and not re.fullmatch('[A-Z]{5}',t))
    if not symbols:raise ValueError('No independently discovered firm universe')
    barcache=root/'backtest/runtime/swing-bars';barcache.mkdir(parents=True,exist_ok=True)
    data,requests=download(symbols,'2022-06-01','2025-12-05',barcache)
    alias=[]
    for change in csv.DictReader((root/'config/historical_symbol_changes.csv').open()):
        if change['old_symbol'] not in symbols:continue
        extra,n=download([change['new_symbol']],change['effective_date'],'2025-12-05',root/'backtest/runtime/swing-bars');requests+=n
        for mode in ('raw','split'):data[mode].update(extra[mode])
        alias.append(stitch_rename(data,change))
    sessions=[]
    for year in range(2022,2026):
        sessions.extend(str(s.date()) for s in calendar(year).sessions_in_range(f'{year}-06-01',f'{year}-12-05'))
    out=root/'reports/game-firm-replay';results=[]
    for year in [2023,2024,2025]:
        start=f'{year}-09-08';end=f'{year}-12-05'
        universe=[t for t in symbols if first[t]<=end]
        for strategy in ['LIVE_FIRM_TIMING_SHORT','FIRM_EXHAUSTION_RESEARCH']:
            result=simulate(data['raw'],data['split'],universe,sessions,start=start,end=end,hold=3,
                            strategy=strategy,position_target=30000,buying_power=150000,
                            firm_dates=first,firm_cfg=cfg,risk_controls=True,signal_share_sizing=True)
            result.update(period_start=start,period_end=end)
            write_json(out/f'{year}-{strategy}.json',result)
            if year==2025:
                write_json(out/f'{strategy}-lead.json',lead_metrics(result,
                    {t:data['raw'].get(t,{}) for t in universe},{t:data['split'].get(t,{}) for t in universe},sessions,start,end))
            results.append({k:v for k,v in result.items() if k not in {'trades','signal_events','daily_equity','unresolved_positions'}})
    packet={'sessions':sessions,'config':cfg.model_dump(),'firm_dates':first,
            'cohorts':{f'{y}-09-08':{'short':[t for t in symbols if first[t]<=f'{y}-12-05']} for y in [2023,2024,2025]},
            'raw':{t:data['raw'].get(t,{}) for t in symbols},'split':{t:data['split'].get(t,{}) for t in symbols}}
    with gzip.open(out/'firm-timing-inputs.json.gz','wt',encoding='utf-8') as handle:json.dump(packet,handle)
    summary={'status':'PARTIAL_INDEPENDENT_GAME_RESEARCH','discovery':discovery,'dynamic_firm_symbols':len(symbols),
             'new_game_firm_symbols':sorted(t for t in symbols if '2025-07-28'<first[t]<='2025-12-05'),
             'market_requests':requests,'alias_audit':alias,'results':results,'live_enabled':False,
             'limitations':['Unreviewed sources and historical identity/classification gaps remain visible',
                            'Historical borrow/cap/halts/game/margin rules unavailable; conditional P&L only',
                            'All fixed research hypotheses declared before this run; 2025 is not a fresh holdout',
                            'Stops execute at next close after prior-close breach; not guaranteed stop prices',
                            'No reference or friend ticker input is opened by discovery or simulation']}
    write_json(out/'summary.json',summary)
    print(json.dumps({'status':summary['status'],'symbols':len(symbols),'new_game_symbols':len(summary['new_game_firm_symbols']),
                      'results':[{k:r[k] for k in ['period_start','strategy','net_profit','closed_trades','account_insolvent']} for r in results]}))


if __name__=='__main__':main()
