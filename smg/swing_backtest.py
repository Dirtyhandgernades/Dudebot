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
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from .market import calendar
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
        for offset in range(0,len(symbols),100):
            query=dict(symbols=','.join(symbols[offset:offset+100]),timeframe='1Day',start=start,end=end+'T23:59:59Z',feed='sip',adjustment=adjustment,asof='-',limit=10000)
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
    return result

def simulate(raw, adjusted, symbols, sessions, start=START, end=END, hold=3, strategy='PUMP_FAILURE_SHORT',cost_bps=30,initial=100000,commission=5,borrow_rate=.10):
    """Cash collateral, ten slots, one position/symbol, next-session close fills.

    Fixed 10% initial-capital allocation, whole shares, min 10. Both sides pay
    cost_bps on entry/exit; shorts additionally pay assumed 10% annual borrow.
    These are sensitivity assumptions, not certified SMG fees/borrow availability.
    """
    index={day:i for i,day in enumerate(sessions)};days=[d for d in sessions if start<=d<=end]
    cash=float(initial);positions={};trades=[];curve=[];gaps=Counter();signals=0;peak=initial;drawdown=0
    side=1 if strategy.endswith('LONG') else -1
    fee=cost_bps/10000
    for day in days:
        i=index[day]
        for ticker,p in list(positions.items()):
            if day<p['planned_exit'] and day!=days[-1]:continue
            bar=adjusted.get(ticker,{}).get(day)
            if not bar:
                gaps['MISSING_EXIT_BAR']+=1;continue
            ratio=bar['c']/p['adjusted_entry'];gross=p['notional']*side*(ratio-1)
            exit_fee=p['notional']*ratio*fee+commission
            borrow=p['notional']*borrow_rate*(date.fromisoformat(day)-date.fromisoformat(p['entry_date'])).days/365 if side<0 else 0
            pnl=gross-p['entry_fee']-exit_fee-borrow
            cash+=p['notional']+gross-exit_fee-borrow
            trades.append({**p,'exit_date':day,'ticker':ticker,'side':'LONG' if side>0 else 'SHORT','pnl':pnl,'return_pct':100*pnl/p['notional'],'gross_return_pct':100*side*(ratio-1)})
            del positions[ticker]
        # Signal is formed at prior close, never using today's fill/outcome bar.
        if day!=days[-1] and i>=22:
            for ticker in symbols:
                prior=sessions[i-22:i]
                series=adjusted.get(ticker,{})
                if any(d not in series for d in prior):
                    gaps['INCOMPLETE_SIGNAL_HISTORY']+=1;continue
                raw_prior=raw.get(ticker,{}).get(prior[-1])
                if not raw_prior or raw_prior['c']<=3:continue
                if strategy not in signal([series[d] for d in prior]):continue
                signals+=1
                if ticker in positions or len(positions)>=10:continue
                entry=raw.get(ticker,{}).get(day);adj=series.get(day)
                if not entry or not adj:
                    gaps['MISSING_ENTRY_BAR']+=1;continue
                if entry['c']<=3:
                    gaps['ENTRY_PRICE_BELOW_GATE']+=1;continue
                shares=math.floor(min(initial*.10,(cash-commission)/(1+fee))/entry['c'])
                if shares<10:continue
                notional=shares*entry['c'];entry_fee=notional*fee+commission
                cash-=notional+entry_fee
                planned=sessions[min(i+hold,index[days[-1]])]
                positions[ticker]=dict(signal_date=prior[-1],entry_date=day,planned_exit=planned,entry_price=entry['c'],adjusted_entry=adj['c'],shares=shares,notional=notional,entry_fee=entry_fee)
        equity=cash;valuation_complete=True
        for ticker,p in positions.items():
            mark=adjusted.get(ticker,{}).get(day)
            if not mark:valuation_complete=False;continue
            equity+=p['notional']*(1+side*(mark['c']/p['adjusted_entry']-1))
        if valuation_complete:
            peak=max(peak,equity);drawdown=max(drawdown,(peak-equity)/peak)
        curve.append(dict(date=day,equity=equity if valuation_complete else None,open_positions=len(positions)))
    profits=[t['pnl'] for t in trades]
    final=cash if not positions else None
    return dict(strategy=strategy,hold_sessions=hold,cost_bps_each_way=cost_bps,commission_per_order=commission,borrow_rate=borrow_rate,initial_balance=initial,
        ending_balance=round(final,2) if final is not None else None,net_profit=round(final-initial,2) if final is not None else None,
        realized_profit=round(sum(profits),2),closed_trades=len(trades),unresolved_open_positions=len(positions),
        win_rate=sum(p>0 for p in profits)/len(profits) if profits else None,max_observed_drawdown_pct=round(drawdown*100,3),
        gross_20pct_winners=sum(t['gross_return_pct']>=20-1e-10 for t in trades),gross_30pct_winners=sum(t['gross_return_pct']>=30-1e-10 for t in trades),
        signals=signals,gaps=dict(gaps),unresolved_positions=positions,trades=trades,daily_equity=curve)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--replay',default='backtest/runtime/corrected-replay/decisions.json')
    args=parser.parse_args();root=Path.cwd();records=json.loads(Path(args.replay).read_text())
    cohorts={start:dict(short=frozen_cohort(records,start),long=broad_cohort(records,start)) for start,_ in PERIODS}
    symbols=cohorts[START]['short'];long_symbols=cohorts[START]['long']
    download_symbols=sorted({ticker for group in cohorts.values() for side in group.values() for ticker in side})
    cache=root/'backtest/runtime/swing-bars';cache.mkdir(parents=True,exist_ok=True)
    if not symbols or not long_symbols:raise ValueError('No independently discovered pre-period cohort')
    sessions=[]
    for year in range(2023,2026):
        sessions.extend(str(s.date()) for s in calendar(year).sessions_in_range(f'{year}-06-01',f'{year}-12-05'))
    data,requests=download(download_symbols,'2023-06-01',END,cache)
    out=root/'reports/swing-backtest';out.mkdir(parents=True,exist_ok=True)
    summaries=[]
    for period_start,period_end in PERIODS:
        for strategy in ['FIRM_BASELINE_SHORT','PUMP_FAILURE_SHORT','BREAKOUT_LONG']:
            for hold in [1,3,4,5,7]:
                universe=cohorts[period_start]['long' if strategy=='BREAKOUT_LONG' else 'short']
                result=simulate(data['raw'],data['split'],universe,sessions,start=period_start,end=period_end,hold=hold,strategy=strategy)
                result['period_start']=period_start;result['period_end']=period_end
                (out/f'{period_start}-{strategy}-{hold}.json').write_text(json.dumps(result))
                summaries.append({k:v for k,v in result.items() if k not in {'trades','daily_equity','unresolved_positions'}})
    stress=[]
    for hold in [1,3,4,5,7]:
        result=simulate(data['raw'],data['split'],symbols,sessions,start=START,end=END,hold=hold,cost_bps=100,borrow_rate=1.0)
        stress.append({k:v for k,v in result.items() if k not in {'trades','daily_equity','unresolved_positions'}})
    report=dict(status='CONDITIONAL_RESEARCH_ONLY',start=START,end=END,periods=[dict(start=s,end=e,
        short_cohort_size=len(cohorts[s]['short']),long_cohort_size=len(cohorts[s]['long'])) for s,e in PERIODS],
        cohort_symbols=symbols,cohort_size=len(symbols),long_universe_size=len(long_symbols),market_requests=requests,
        data_symbols=len(data['raw']),verified_executable_profit=None,results=summaries,short_cost_stress=stress,
        assumptions=['$100,000 cash; no leverage; ten positions maximum; 10% starting capital per position; minimum ten shares',
          'Signals at prior close; next-session close entry; closes only; terminal liquidation on December 5',
          '$5 commission per order plus 30 basis points each side slippage assumption; shorts assume 10% annual borrow; stress uses 100 bps and 100% borrow',
          'Raw price for $3 gate; split-adjusted price ratios for signals and returns; no current-symbol alias mapping',
          'Deterministic alphabetical tie-break; same-close position sizing assumes a dollar allocation filled in whole shares'],
        limitations=['Historical cap, halt, borrow availability, dividends and SMG security availability unverified; NOT executable profit',
          'Independent firm cohort frozen from sources through July 2025; later IPOs and updated filing context missing',
          'Long hypothesis evaluated in same firm cohort, not a broad-market long universe',
          'Daily bars can include extended sessions; close-fill model must be checked against game execution',
          'No reference labels loaded; no parameter search; all preset horizons and three preset fall periods reported',
          'Missing exit bars keep positions unresolved and ending balance null; observed drawdown can be understated where marks are missing'])
    (out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':main()
