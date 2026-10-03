"""Conditional price-outcome research, never a verified executable backtest.

Uses a pre-period independent filing cohort, not reference tickers. Dates and
rules are fixed before outcomes are read. Missing eligibility is never imputed.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import gzip
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from .market import calendar,session_bounds
from .transport import Http
from .game_rules import is_excluded_symbol

START='2025-09-08'
END='2025-12-05'
PERIODS=[
    ('2023-09-08','2023-12-05'),
    ('2024-09-08','2024-12-05'),
    (START,END),
]

def frozen_cohort(records, start=START):
    latest={}
    for row in records:
        if row['decision_at'][:10]>=start or not row.get('cik'):continue
        key=row['cik']
        if key not in latest or row['decision_at']>latest[key]['decision_at']:latest[key]=row
    # No price outcome, current asset membership or reference label selects the cohort.
    return sorted({r['ticker'] for r in latest.values()
        if 'VERIFIED_LISTED_FIRM_RELATIONSHIP' in r.get('reasons',[]) and not is_excluded_symbol(r['ticker'])})

def broad_cohort(records, start=START):
    """Independent long universe: every issuer-linked extracted symbol before start.
    It still excludes five-letter symbols and does not read reference labels.
    """
    return sorted({r['ticker'] for r in records if r.get('cik') and r['decision_at'][:10]<start
                   and r.get('ticker') and not is_excluded_symbol(r['ticker'])
                   and not __import__('re').fullmatch('[A-Z]{5}',r['ticker'])})

def download(symbols, start, end, cache):
    http=Http();headers={'APCA-API-KEY-ID':os.environ['ALPACA_API_KEY'],'APCA-API-SECRET-KEY':os.environ['ALPACA_SECRET_KEY']}
    output={};requests=0
    for adjustment in ['raw','split']:
        result=defaultdict(dict)
        contract=dict(timeframe='1Day',start=start,end=end+'T23:59:59Z',feed='sip',adjustment=adjustment,asof='-')
        paths={symbol:cache/('symbol-v1-'+hashlib.sha256(json.dumps({**contract,'symbol':symbol},sort_keys=True).encode()).hexdigest()+'.json') for symbol in set(symbols)}
        missing=[]
        for symbol in sorted(paths):
            path=paths[symbol]
            if path.exists():
                bars=json.loads(path.read_text())
                if bars:result[symbol].update(bars)
            else:missing.append(symbol)
        for offset in range(0,len(missing),100):
            group=missing[offset:offset+100]
            query=dict(symbols=','.join(group),**contract,limit=10000)
            seen=set()
            while True:
                path=cache/(hashlib.sha256(json.dumps(query,sort_keys=True).encode()).hexdigest()+'.json')
                if path.exists():data=json.loads(path.read_text())
                else:
                    data=http.json('https://data.alpaca.markets/v2/stocks/bars',params=query,headers=headers);requests+=1
                    path.write_text(json.dumps(data))
                for symbol,bars in (data.get('bars') or {}).items():
                    for bar in bars:result[symbol][bar['t'][:10]]=bar
                token=data.get('next_page_token')
                if not token:break
                if token in seen:raise ValueError('Repeated provider page token')
                seen.add(token);query['page_token']=token
            # Commit symbol coverage only after every provider page completes.
            # Growing a universe must not invalidate already downloaded symbols.
            for symbol in group:paths[symbol].write_text(json.dumps(result.get(symbol,{})))
        output[adjustment]=dict(result)
    return output,requests

def signal(history):
    """Fixed hypotheses, not tuned on test outcomes. All bars predate entry."""
    if len(history)<22:return []
    last=history[-1];previous=history[-21:-1]
    baseline=sum(b['v'] for b in previous)/20
    if baseline<=0:return []
    surge=last['c']/history[-22]['c']-1
    result=['FIRM_BASELINE_SHORT']
    if surge>=.12 and last['c']<history[-2]['l'] and last['v']/baseline>=1:
        result.append('PUMP_FAILURE_SHORT')
    if last['c']>max(b['h'] for b in previous) and last['v']/baseline>=2:
        result.append('BREAKOUT_LONG')
    # Strict daily proxy for a rapid pump failure. This is deliberately a
    # separate hypothesis: a >=25% 21-session run, high volume, and a close
    # below the prior low. It does not change the live 12% screen.
    if surge>=.25 and last['c']<history[-2]['l'] and last['v']/baseline>=1.5:
        result.append('RAPID_PUMP_FAILURE_SHORT')
    # Composite research lane: require the ordinary pump-failure setup plus
    # at least two independent collapse confirmations. This combines trend,
    # volume and failed-support evidence without changing the live screen.
    if surge>=.12 and last['c']<history[-2]['l'] and last['v']/baseline>=1:
        confirmations=sum((
            last['v']/baseline>=1.5,
            last['c']/history[-2]['c']-1<=-.05,
            last['c']/max(b['h'] for b in history[-22:])-1<=-.08,
            (last['c']-last['l'])/max(last['h']-last['l'],1e-12)<=.35,
            last['h']<history[-2]['h'],
        ))
        if confirmations>=2:
            result.append('COMBINED_COLLAPSE_SHORT')
    return result

def dump_structure_score(history):
    """The live chart-structure rank, computed only from bars known at signal time."""
    if len(history)<22:return 0
    last=history[-1];previous=history[-21:-1];base=sum(b['v'] for b in previous)/20
    if base<=0:return 0
    span=max(last['h']-last['l'],1e-12);close_location=(last['c']-last['l'])/span
    return (25*(last['c']<history[-2]['l'])+20*(last['c']/history[-2]['c']-1<=-.05)+
        15*(last['c']/max(b['h'] for b in history[-22:])-1<=-.08)+15*(last['v']/base>=1.5)+
        10*(sum((b['h']-b['l'])/b['c'] for b in history[-5:])/5>=.08)+
        10*(close_location<=.35)+5*(last['h']<history[-2]['h']))

def daily_firm_trigger(history,cfg):
    """Reuse the live price trigger; daily RVOL is a disclosed intraday proxy."""
    from .firm_first import firm_short_trigger
    if len(history)<22:return None
    last=history[-1];base=sum(b['v'] for b in history[-21:-1])/20
    if base<=0 or any(b['c']<=0 for b in history[-22:]):return None
    snapshot=SimpleNamespace(monthly_return=100*(last['c']/history[-22]['c']-1),
        one_day_return=100*(last['c']/history[-2]['c']-1),
        drawdown_pct=100*(last['c']/max(b['h'] for b in history[-22:])-1),rvol=last['v']/base)
    return firm_short_trigger(snapshot,cfg)


def firm_exhaustion_trigger(history,cfg):
    """Predeclared research hypothesis near a pumped high; no future bars.

    These chart thresholds are not calibrated probabilities or live alerts.
    """
    if len(history)<22:return None
    last=history[-1];base=sum(b['v'] for b in history[-21:-1])/20
    if base<=0 or any(b['c']<=0 for b in history[-22:]):return None
    span=last['h']-last['l']
    if span<=0:return None
    monthly=100*(last['c']/history[-22]['c']-1)
    drawdown=last['c']/max(b['h'] for b in history[-22:])-1
    upper_wick=(last['h']-max(last.get('o',last['c']),last['c']))/span
    daily=last['c']/history[-2]['c']-1
    if (monthly>=(cfg.surge_return_min_pct or 12) and drawdown>=-.20 and
            daily>-.10 and last['v']/base>=1.5 and span/last['c']>=.08 and upper_wick>=.35):
        return 'FIRM_EXHAUSTION_RESEARCH'
    return None

def stitch_rename(data,change):
    """Same-security rename, never a merger or an inferred current alias."""
    old=change['old_symbol'];new=change['new_symbol'];effective=change['effective_date']
    if change['action']!='rename_only' or change['published_at'][:10]>effective:
        raise ValueError('Rename must have dated public same-security evidence')
    old_raw=data['raw'].get(old,{});old_split=data['split'].get(old,{})
    new_raw=data['raw'].get(new,{});new_split=data['split'].get(new,{})
    before=sorted(d for d in old_raw if d<effective and d in old_split)
    after=sorted(d for d in new_raw if d>=effective and d in new_split)
    if not before or not after:return {'status':'RENAME_BARS_UNAVAILABLE',**change}
    # Separate provider symbol series can use different split-adjusted units.
    # A documented pure rename preserves share units, so align adjustment
    # factors using raw/split ratios on either side without smoothing returns.
    prior=before[-1];first=after[0]
    scale=(new_raw[first]['c']/new_split[first]['c'])/(old_raw[prior]['c']/old_split[prior]['c'])
    for day in after:
        old_raw[day]=dict(new_raw[day])
        old_split[day]={**new_split[day],**{k:new_split[day][k]*scale for k in ('o','h','l','c') if k in new_split[day]}}
    data['raw'][old]=old_raw;data['split'][old]=old_split
    return {'status':'STITCHED_RENAME','mapped_sessions':len(after),'adjusted_scale':scale,**change}

def borrow_metrics(signal_events,observations):
    """Use only borrow evidence known by the planned entry close.

    A missing or failed provider observation cannot establish execution. The
    daily asset flag is a broker indication, not a reserved locate or SMG fill.
    """
    by_symbol=defaultdict(list)
    for row in observations or []:
        try:stamp=datetime.fromisoformat(row['observed_at'].replace('Z','+00:00'))
        except (KeyError,ValueError,AttributeError):continue
        if stamp.tzinfo is None:continue
        by_symbol[row['subject'].upper()].append((stamp.astimezone(timezone.utc),row))
    counts=Counter(detected=len(signal_events));examples=[]
    for event in signal_events:
        entry_day=date.fromisoformat(event['planned_entry_date'])
        bounds=session_bounds(entry_day)
        cutoff=bounds[1] if bounds else None
        candidates=[(stamp,row) for stamp,row in by_symbol[event['ticker'].upper()]
                    if cutoff and stamp.date()==cutoff.date() and stamp<=cutoff]
        if not candidates:status='unavailable'
        else:
            stamp,row=max(candidates,key=lambda pair:pair[0]);asset=row['value']
            if asset.get('status')=='UNAVAILABLE' or not all(k in asset for k in ('tradable','shortable','borrow_status')) or asset['borrow_status'] is None:
                status='unavailable'
            else:
                status='executable' if asset['tradable'] is True and asset['shortable'] is True and asset['borrow_status']=='easy_to_borrow' else 'rejected'
        counts[status]+=1
        if len(examples)<25:examples.append({**event,'borrow_result':status})
    return {'detected':counts['detected'],'executable':counts['executable'],'unavailable':counts['unavailable'],
        'rejected':counts['rejected'],'examples':examples}

def marked_equity(cash,positions,adjusted,day,side):
    total=cash
    for ticker,p in positions.items():
        mark=adjusted.get(ticker,{}).get(day)
        if not mark:return None
        total+=p['notional']*(1+side*(mark['c']/p['adjusted_entry']-1))
    return total

def simulate(raw, adjusted, symbols, sessions, start=START, end=END, hold=3, strategy='PUMP_FAILURE_SHORT',cost_bps=30,initial=100000,commission=5,borrow_rate=.10,borrow_observations=None,position_target=None,buying_power=None,firm_dates=None,firm_cfg=None,risk_controls=False,signal_share_sizing=False,intraday_signals=None):
    """Cash collateral, ten slots, one position/symbol, next-session close fills.

    Fixed 10% initial-capital allocation, whole shares, min 10. Both sides pay
    cost_bps on entry/exit; shorts additionally pay assumed 10% annual borrow.
    These are sensitivity assumptions, not certified SMG fees/borrow availability.
    """
    index={day:i for i,day in enumerate(sessions)};days=[d for d in sessions if start<=d<=end]
    cash=float(initial);positions={};trades=[];curve=[];gaps=Counter();signals=0;signal_events=[];peak=initial;drawdown=0
    position_target=position_target or initial*.10;buying_power=buying_power or initial
    side=1 if strategy.endswith('LONG') else -1
    if strategy in {'LIVE_FIRM_TIMING_SHORT','FIRM_EXHAUSTION_RESEARCH'} and (firm_dates is None or firm_cfg is None):
        raise ValueError('Live firm proxy requires dated public firm evidence and configured timing rules')
    if strategy=='FIRM_INTRADAY_EXHAUSTION_RESEARCH' and (intraday_signals is None or firm_dates is None or not signal_share_sizing):
        raise ValueError('Intraday research requires dated signals, firm evidence and decision-price share sizing')
    if intraday_signals is not None and strategy!='FIRM_INTRADAY_EXHAUSTION_RESEARCH':raise ValueError('Unexpected intraday signals')
    fee=cost_bps/10000
    for day in days:
        i=index[day]
        # Share orders must be sized before today's fills/exits are known.
        decision_equity=marked_equity(cash,positions,adjusted,sessions[i-1],side) if i else None
        decision_room=0
        if decision_equity is not None and decision_equity>0:
            previous_exposure=sum(p['notional']*adjusted[t][sessions[i-1]]['c']/p['adjusted_entry']
                                  for t,p in positions.items())
            decision_room=max(0,min(buying_power,decision_equity*buying_power/initial)-previous_exposure)
        for ticker,p in list(positions.items()):
            exit_reason='TIME_LIMIT'
            prior_mark=adjusted.get(ticker,{}).get(sessions[i-1]) if i else None
            if risk_controls and prior_mark and sessions[i-1]>=p['entry_date']:
                previous_return=side*(prior_mark['c']/p['adjusted_entry']-1)
                if previous_return<=-.12:exit_reason='STOP_SIGNAL_PREVIOUS_CLOSE'
                elif previous_return>=.20:exit_reason='TAKE_PROFIT_SIGNAL_PREVIOUS_CLOSE'
            if day<p['planned_exit'] and day!=days[-1] and exit_reason=='TIME_LIMIT':continue
            if day==days[-1] and exit_reason=='TIME_LIMIT':exit_reason='GAME_END'
            bar=adjusted.get(ticker,{}).get(day)
            if not bar:
                gaps['MISSING_EXIT_BAR']+=1;continue
            ratio=bar['c']/p['adjusted_entry'];gross=p['notional']*side*(ratio-1)
            exit_fee=p['notional']*ratio*fee+commission
            borrow=p['notional']*borrow_rate*(date.fromisoformat(day)-date.fromisoformat(p['entry_date'])).days/365 if side<0 else 0
            pnl=gross-p['entry_fee']-exit_fee-borrow
            cash+=p['notional']+gross-exit_fee-borrow
            trades.append({**p,'exit_date':day,'exit_reason':exit_reason,'ticker':ticker,'side':'LONG' if side>0 else 'SHORT','pnl':pnl,'return_pct':100*pnl/p['notional'],'gross_return_pct':100*side*(ratio-1)})
            del positions[ticker]
        # Signal is formed at prior close, never using today's fill/outcome bar.
        if day!=days[-1] and i>=22:
            opportunities=[]
            for ticker in symbols:
                event=next((e for e in intraday_signals.get(day,[]) if e['ticker']==ticker),None) if intraday_signals is not None else None
                prior=sessions[i-22:i]
                series=adjusted.get(ticker,{})
                if intraday_signals is not None:
                    if event is None:continue
                    decision=datetime.fromisoformat(event['decision_at']);cutoff=datetime.fromisoformat(event['data_cutoff'])
                    if decision.tzinfo is None or cutoff.tzinfo is None or decision-cutoff<timedelta(minutes=16) or decision.date().isoformat()!=day:
                        raise ValueError('Intraday signal timestamps must precede the entry close')
                    bounds=session_bounds(date.fromisoformat(day))
                    if not bounds or not bounds[0]<=decision<bounds[1]:raise ValueError('Intraday decision outside session')
                    if day<firm_dates.get(ticker,'9999-99-99'):continue
                    trigger=event['timing_trigger'];signal_day=day;sizing_price=event['decision_price']
                    structure_score=event['dump_structure_score']
                    if sizing_price<=3:continue
                    signals+=1;signal_events.append({**event,'signal_date':signal_day,'planned_entry_date':day})
                    if ticker in positions or len(positions)>=10:continue
                    entry=raw.get(ticker,{}).get(day);adj=series.get(day)
                    if not entry or not adj:gaps['MISSING_ENTRY_BAR']+=1;continue
                    if entry['c']<=3:gaps['ENTRY_PRICE_BELOW_GATE']+=1;continue
                    opportunities.append((structure_score,ticker,entry,adj,signal_day,trigger,sizing_price))
                    continue
                if any(d not in series for d in prior):
                    gaps['INCOMPLETE_SIGNAL_HISTORY']+=1;continue
                raw_prior=raw.get(ticker,{}).get(prior[-1])
                if not raw_prior or raw_prior['c']<=3:continue
                history=[series[d] for d in prior]
                signal_names=signal(history)
                trigger=strategy
                if firm_dates is not None and prior[-1]<firm_dates.get(ticker,'9999-99-99'):continue
                if strategy in {'LIVE_FIRM_TIMING_SHORT','FIRM_EXHAUSTION_RESEARCH'}:
                    if prior[-1]<firm_dates.get(ticker,'9999-99-99'):continue
                    trigger=(firm_exhaustion_trigger if strategy=='FIRM_EXHAUSTION_RESEARCH' else daily_firm_trigger)(history,firm_cfg)
                    if not trigger:continue
                elif strategy=='ADAPTIVE_COLLAPSE_SHORT':
                    if not ({'PUMP_FAILURE_SHORT','COMBINED_COLLAPSE_SHORT'} & set(signal_names)):continue
                elif strategy not in signal_names:continue
                structure_score=dump_structure_score(history)
                signals+=1;signal_events.append({'ticker':ticker,'signal_date':prior[-1],'planned_entry_date':day,'dump_structure_score':structure_score,'timing_trigger':trigger})
                if ticker in positions or len(positions)>=10:continue
                entry=raw.get(ticker,{}).get(day);adj=series.get(day)
                if not entry or not adj:
                    gaps['MISSING_ENTRY_BAR']+=1;continue
                if entry['c']<=3:
                    gaps['ENTRY_PRICE_BELOW_GATE']+=1;continue
                opportunities.append((structure_score,ticker,entry,adj,prior[-1],trigger,raw_prior['c']))
            key=(lambda x:(-x[0],x[1])) if side<0 else (lambda x:x[1])
            for structure_score,ticker,entry,adj,signal_day,trigger,decision_price in sorted(opportunities,key=key):
                if ticker in positions or len(positions)>=10:continue
                marked=marked_equity(cash,positions,adjusted,day,side)
                if marked is None:
                    gaps['NEW_ENTRY_BLOCKED_UNVALUED_CAPITAL']+=1;continue
                if marked<=0:
                    gaps['NEW_ENTRY_BLOCKED_NONPOSITIVE_EQUITY']+=1;continue
                # Buying power is not a permanent credit line after losses.
                # Unknown marks cannot finance new hypothetical positions.
                limit=min(buying_power,marked*buying_power/initial)
                exposure=sum(p['notional']*adjusted[t][day]['c']/p['adjusted_entry']
                             for t,p in positions.items())
                room=limit-exposure
                budget=min(position_target,room)
                if signal_share_sizing:
                    budget=min(position_target,decision_room)
                    if decision_equity is None:budget=0
                if risk_controls:budget=min(budget,(decision_equity or 0)*.25 if signal_share_sizing else marked*.25)
                if buying_power<=initial:budget=min(budget,max(0,(cash-commission)/(1+fee)))
                sizing_price=decision_price if signal_share_sizing else entry['c']
                shares=math.floor(budget/sizing_price)
                if shares<10:continue
                if signal_share_sizing:decision_room=max(0,decision_room-shares*sizing_price*(1+fee)-commission)
                notional=shares*entry['c'];entry_fee=notional*fee+commission
                if signal_share_sizing and (notional+entry_fee>room or
                        (buying_power<=initial and notional+entry_fee>cash)):
                    gaps['ORDER_REJECTED_BUYING_POWER_AT_FILL']+=1;continue
                cash-=notional+entry_fee
                selected_hold = (1 if strategy=='ADAPTIVE_COLLAPSE_SHORT' and structure_score>=90 else hold)
                planned=sessions[min(i+selected_hold,index[days[-1]])]
                positions[ticker]=dict(signal_date=signal_day,entry_date=day,planned_exit=planned,entry_price=entry['c'],adjusted_entry=adj['c'],shares=shares,notional=notional,entry_fee=entry_fee,dump_structure_score=structure_score,timing_trigger=trigger)
        equity=marked_equity(cash,positions,adjusted,day,side)
        if equity is not None:
            peak=max(peak,equity);drawdown=max(drawdown,(peak-equity)/peak)
        curve.append(dict(date=day,equity=equity,open_positions=len(positions)))
    profits=[t['pnl'] for t in trades]
    final=cash if not positions else None
    insolvent=any(row['equity'] is not None and row['equity']<=0 for row in curve)
    financial_status=('ACCOUNT_INSOLVENT_MARGIN_RULES_UNMODELED' if insolvent else
                      'UNRESOLVED_POSITIONS' if positions else 'CONDITIONAL_SIMULATION_COMPLETE')
    return dict(strategy=strategy,hold_sessions=hold,cost_bps_each_way=cost_bps,commission_per_order=commission,borrow_rate=borrow_rate,initial_balance=initial,position_target=position_target,buying_power=buying_power,
        risk_controls=risk_controls,signal_share_sizing=signal_share_sizing,
        account_insolvent=insolvent,financial_status=financial_status,
        ending_balance=round(final,2) if final is not None else None,net_profit=round(final-initial,2) if final is not None else None,
        realized_profit=round(sum(profits),2),closed_trades=len(trades),unresolved_open_positions=len(positions),
        win_rate=sum(p>0 for p in profits)/len(profits) if profits else None,max_observed_drawdown_pct=round(drawdown*100,3),
        gross_20pct_winners=sum(t['gross_return_pct']>=20-1e-10 for t in trades),gross_30pct_winners=sum(t['gross_return_pct']>=30-1e-10 for t in trades),
        signals=signals,borrow_execution=borrow_metrics(signal_events,borrow_observations),gaps=dict(gaps),
        signal_events=signal_events,unresolved_positions=positions,trades=trades,daily_equity=curve)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--replay',default='backtest/runtime/corrected-replay/decisions.json')
    parser.add_argument('--evidence-db',default='backtest/runtime/evidence/runtime/state.sqlite')
    args=parser.parse_args();root=Path.cwd();records=json.loads(Path(args.replay).read_text())
    cohorts={start:dict(short=frozen_cohort(records,start),long=broad_cohort(records,start)) for start,_ in PERIODS}
    symbols=cohorts[START]['short'];long_symbols=cohorts[START]['long']
    download_symbols=sorted({ticker for group in cohorts.values() for side in group.values() for ticker in side})
    cache=root/'backtest/runtime/swing-bars';cache.mkdir(parents=True,exist_ok=True)
    if not symbols or not long_symbols:raise ValueError('No independently discovered pre-period cohort')
    borrow_observations=[]
    if Path(args.evidence_db).exists():
        from .storage import Store
        borrow_observations=Store(args.evidence_db).observations('market_borrow')
    sessions=[]
    for year in range(2022,2026):
        sessions.extend(str(s.date()) for s in calendar(year).sessions_in_range(f'{year}-06-01',f'{year}-12-05'))
    data,requests=download(download_symbols,'2022-06-01',END,cache)
    alias_audit=[]
    with (root/'config/historical_symbol_changes.csv').open(newline='') as handle:
        changes=list(csv.DictReader(handle))
    for change in changes:
        if change['old_symbol'] not in download_symbols or change['effective_date']>END:continue
        extra,count=download([change['new_symbol']],change['effective_date'],END,cache);requests+=count
        for mode in ('raw','split'):data[mode].update(extra[mode])
        alias_audit.append(stitch_rename(data,change))
    out=root/'reports/swing-backtest';out.mkdir(parents=True,exist_ok=True)
    summaries=[]
    for period_start,period_end in PERIODS:
        for strategy in ['FIRM_BASELINE_SHORT','PUMP_FAILURE_SHORT','RAPID_PUMP_FAILURE_SHORT',
                         'COMBINED_COLLAPSE_SHORT','ADAPTIVE_COLLAPSE_SHORT','BREAKOUT_LONG']:
            for hold in [1,3,4,5,7]:
                universe=cohorts[period_start]['long' if strategy=='BREAKOUT_LONG' else 'short']
                result=simulate(data['raw'],data['split'],universe,sessions,start=period_start,end=period_end,hold=hold,strategy=strategy,borrow_observations=borrow_observations)
                result['period_start']=period_start;result['period_end']=period_end
                (out/f'{period_start}-{strategy}-{hold}.json').write_text(json.dumps(result))
                summaries.append({k:v for k,v in result.items() if k not in {'trades','daily_equity','unresolved_positions','signal_events'}})
    stress=[]
    for hold in [1,3,4,5,7]:
        result=simulate(data['raw'],data['split'],symbols,sessions,start=START,end=END,hold=hold,cost_bps=100,borrow_rate=1.0,borrow_observations=borrow_observations)
        stress.append({k:v for k,v in result.items() if k not in {'trades','daily_equity','unresolved_positions','signal_events'}})
    aggressive=[]
    for strategy in ['PUMP_FAILURE_SHORT','COMBINED_COLLAPSE_SHORT','RAPID_PUMP_FAILURE_SHORT','ADAPTIVE_COLLAPSE_SHORT']:
        for hold in [1,3]:
            result=simulate(data['raw'],data['split'],symbols,sessions,start=START,end=END,hold=hold,
                strategy=strategy,position_target=30000,buying_power=150000,borrow_observations=borrow_observations)
            result['period_start']=START;result['period_end']=END
            (out/f'{START}-{strategy}-{hold}-aggressive.json').write_text(json.dumps(result))
            aggressive.append({k:v for k,v in result.items() if k not in {'trades','daily_equity','unresolved_positions','signal_events'}})
    from .risk_model import walk_forward_report,firm_watch_lead_report,earliest_firm_dates
    from .cli import settings
    firm_cfg,_=settings(root);firm_dates=earliest_firm_dates(records)
    live_policy=[]
    for period_start,period_end in PERIODS:
        for strategy in ['LIVE_FIRM_TIMING_SHORT','ADAPTIVE_COLLAPSE_SHORT']:
            result=simulate(data['raw'],data['split'],cohorts[period_start]['short'],sessions,
                start=period_start,end=period_end,hold=firm_cfg.live_short_hold_sessions_max,
                strategy=strategy,position_target=30000,buying_power=150000,
                borrow_observations=borrow_observations,firm_dates=firm_dates,firm_cfg=firm_cfg)
            result.update(period_start=period_start,period_end=period_end)
            (out/f'{period_start}-{strategy}-primary.json').write_text(json.dumps(result))
            live_policy.append({k:v for k,v in result.items() if k not in {'trades','daily_equity','unresolved_positions','signal_events'}})
    sensitivity=[]
    for target,cost,rate in [(15000,30,.10),(50000,30,.10),(30000,100,1.0)]:
        result=simulate(data['raw'],data['split'],symbols,sessions,start=START,end=END,
            hold=firm_cfg.live_short_hold_sessions_max,strategy='LIVE_FIRM_TIMING_SHORT',
            position_target=target,buying_power=150000,cost_bps=cost,borrow_rate=rate,
            borrow_observations=borrow_observations,firm_dates=firm_dates,firm_cfg=firm_cfg)
        (out/f'{START}-LIVE_FIRM_TIMING_SHORT-size-{target}-cost-{cost}.json').write_text(json.dumps(result))
        sensitivity.append({k:v for k,v in result.items() if k not in {'trades','daily_equity','unresolved_positions','signal_events'}})
    # Cache the research inputs for efficient offline checks; no credentials or
    # reference tickers are included, and the selection evidence stays dated.
    short_symbols=sorted({t for c in cohorts.values() for t in c['short']})
    packet={'sessions':sessions,'cohorts':cohorts,'firm_dates':firm_dates,
        'config':firm_cfg.model_dump(),'raw':{t:data['raw'].get(t,{}) for t in short_symbols},
        'split':{t:data['split'].get(t,{}) for t in short_symbols}}
    with gzip.open(out/'firm-timing-inputs.json.gz','wt',encoding='utf-8') as handle:json.dump(packet,handle)
    ranking_model=walk_forward_report(records,data['raw'],data['split'],sessions)
    (out/'ranking-model.json').write_text(json.dumps(ranking_model,indent=2))
    firm_lead=firm_watch_lead_report(records,data['raw'],data['split'],sessions,PERIODS,cohorts)
    (out/'firm-watch-lead.json').write_text(json.dumps(firm_lead,indent=2))
    report=dict(status='CONDITIONAL_RESEARCH_ONLY',start=START,end=END,periods=[dict(start=s,end=e,
        short_cohort_size=len(cohorts[s]['short']),long_cohort_size=len(cohorts[s]['long'])) for s,e in PERIODS],
        cohort_symbols=symbols,cohort_size=len(symbols),long_universe_size=len(long_symbols),market_requests=requests,
        data_symbols=len(data['raw']),historical_symbol_change_audit=alias_audit,verified_executable_profit=None,results=summaries,short_cost_stress=stress,aggressive_fast_dump=aggressive,ranking_model=ranking_model,firm_watch_lead=firm_lead,
        revised_live_policy={'status':'CONDITIONAL_DAILY_PROXY','hold_sessions':firm_cfg.live_short_hold_sessions_max,
            'profit_target':70000,'initial_balance':100000,'position_target':30000,'buying_power_assumption':150000,
            'periods':live_policy,'sensitivity':sensitivity,
            'limitations':['Daily volume / previous 20 complete sessions proxies live same-minute 60-session RVOL',
                'Price and timing thresholds reuse the deployed helper; intraday signal timing is not reproduced',
                'Position sizes are predetermined sensitivity cases, not selected to maximize 2025 return',
                '2025 has been inspected repeatedly and is no longer an untouched holdout']},
        assumptions=['Baseline: $100,000 cash; no leverage; ten positions maximum; 10% starting capital per position; minimum ten shares',
          'Revised policy and aggressive cases: $100,000 equity with $150,000 gross buying-power assumption; fixed dollar targets, not calibrated confidence sizing',
          'New entries require complete current portfolio marks; modeled buying power scales down with marked equity and current gross exposure',
          'Signals at prior close; next-session close entry; closes only; terminal liquidation on December 5',
          '$5 commission per order plus 30 basis points each side slippage assumption; shorts assume 10% annual borrow; stress uses 100 bps and 100% borrow',
          'Raw price for $3 gate; split-adjusted ratios for signals and returns; only explicitly sourced dated same-security renames are stitched',
          'Deterministic alphabetical tie-break; same-close position sizing assumes a dollar allocation filled in whole shares'],
        limitations=['Historical cap, halt, borrow availability, dividends and SMG security availability unverified; NOT executable profit',
          'Independent firm cohort frozen from sources through July 2025; later IPOs and updated filing context missing',
          'Long hypothesis evaluated in same firm cohort, not a broad-market long universe',
          'Daily bars can include extended sessions; close-fill model must be checked against game execution',
          'No reference labels loaded; fixed model splits are 2022-2023 train, 2024 validation and 2025 holdout',
          'Missing exit bars keep positions unresolved and ending balance null; observed drawdown can be understated where marks are missing'])
    (out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':main()
