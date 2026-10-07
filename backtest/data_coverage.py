"""Separate source coverage, price coverage, eligibility and market opportunity."""
import argparse,gzip,json
from pathlib import Path
from collections import Counter
from smg.risk_model import samples,matured_before
from smg.game_rules import is_excluded_symbol
from smg.swing_backtest import simulate


def rolling_gains(portfolio):
    curve=portfolio['daily_equity'];output={}
    for horizon in (1,2,3):
        values=[{'start':curve[i-horizon]['date'],'end':curve[i]['date'],
                 'gain':round(curve[i]['equity']-curve[i-horizon]['equity'],2)}
                for i in range(horizon,len(curve))
                if curve[i]['equity'] is not None and curve[i-horizon]['equity'] is not None]
        output[str(horizon)]={'best':max(values,key=lambda r:r['gain']) if values else None,
                             'worst':min(values,key=lambda r:r['gain']) if values else None,
                             'windows_above_70000':sum(r['gain']>=70000 for r in values)}
    return output


def run(packet,signals,portfolios,out):
    out.mkdir(parents=True,exist_ok=True);index={d:i for i,d in enumerate(packet['sessions'])}
    labels=samples(packet['records'],packet['raw'],packet['split'],packet['sessions'],firm_dates=packet['first_dates'])
    common=[t for t,d in packet['first_dates'].items() if d<='2023-09-08' and
            any(day<'2023-09-08' for day in packet['raw'].get(t,{})) and
            not is_excluded_symbol(t) and not (len(t)==5 and t.isalpha())]
    results=[]
    for year in (2023,2024,2025):
        start=f'{year}-09-08';end=f'{year}-12-05';days=[d for d in packet['sessions'] if start<=d<=end]
        known=[t for t,d in packet['first_dates'].items() if d<=end and not is_excluded_symbol(t) and not(len(t)==5 and t.isalpha())]
        history=above=missing_history=0;missing_symbols=[]
        for ticker in known:
            raw=packet['raw'].get(ticker,{});split=packet['split'].get(ticker,{})
            if not any(d in raw for d in days):missing_symbols.append(ticker)
            for day in days:
                if day<packet['first_dates'][ticker]:continue
                prior=packet['sessions'][index[day]-22:index[day]]
                if len(prior)!=22 or not all(d in raw and d in split for d in prior):missing_history+=1;continue
                history+=1;above+=int(raw[prior[-1]]['c']>3)
        events=json.loads((signals/f'{year}-PRECLOSE_ONLY-signals.json').read_text())
        matched={d:[e for e in es if e['ticker'] in common] for d,es in events.items()}
        control=simulate(packet['raw'],packet['split'],common,packet['sessions'],start=start,end=end,
            strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',hold=3,firm_dates=packet['first_dates'],intraday_signals=matched,
            signal_share_sizing=True,risk_controls=True,position_target=50000,buying_power=150000,
            max_position_equity_fraction=.30,decision_price_buffer=1.2,smg_cash_interest=True,cost_bps=30,borrow_rate=.1)
        (out/f'{year}-matched-cohort.json').write_text(json.dumps(control,indent=2))
        full=json.loads((portfolios/f'{year}-PRECLOSE_ONLY-base.json').read_text())
        results.append({'year':year,'source_records':sum(r['decision_at'].startswith(str(year)) for r in packet['records']),
            'known_firms_by_game_end':len(known),'known_no_game_price_symbols':missing_symbols,
            'no_game_price_count':len(missing_symbols),'complete_prior_history_symbol_days':history,
            'incomplete_prior_history_symbol_days':missing_history,'history_price_above3_symbol_days':above,
            'price_gate_pass_rate_given_complete_history':above/history if history else None,
            'training_rows_before_year':len(matured_before(labels,f'{year}-01-01')),
            'training_rows_prior_two_years':len(matured_before(labels,f'{year}-01-01',f'{year-2}-01-01')),
            'timestamped_signals':sum(map(len,events.values())),
            'full_cohort':{k:full[k] for k in ('net_profit','closed_trades','max_observed_drawdown_pct')},
            'matched_pre2023_cohort':{k:control[k] for k in ('net_profit','closed_trades','max_observed_drawdown_pct')},
            'full_cohort_rolling_session_gains':rolling_gains(full)})
    report={'status':'CROSS_YEAR_DATA_AND_OPPORTUNITY_AUDIT','years':results,
            'first_source_year_counts':dict(Counter(d[:4] for d in packet['first_dates'].values())),
            'matched_cohort_symbols':len(common),'provider_requests':0,'live_changed':False,
            'limits':['Different roster sizes can reflect missing discovery OR firms that did not yet exist/list',
                      'Missing histories include ticker changes/delistings; do not impute IPO dates',
                      'Source records are not identical independent issuer samples; expanding training is not equal lookback',
                      'Profits remain conditional on unavailable historical borrow/eligibility facts',
                      'Matched cohort isolates roster membership only; year-specific prior-trained ranks still differ']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--signals',required=True)
    p.add_argument('--portfolios',required=True);p.add_argument('--out',default='outputs/backtest/year-coverage');a=p.parse_args()
    r=run(json.loads(gzip.decompress(Path(a.packet).read_bytes())),Path(a.signals),Path(a.portfolios),Path(a.out))
    print(json.dumps({'years':r['years'],'matched_cohort_symbols':r['matched_cohort_symbols']}))


if __name__=='__main__':main()
