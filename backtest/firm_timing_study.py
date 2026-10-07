"""Four fixed confirmation policies on cached, timestamped firm signals.

Quote confirmation never sees the closing fill or later drop. No provider
request, order, allocation increase or automatic live policy replacement.
"""
import argparse,gzip,json
from pathlib import Path
from collections import Counter
from smg.swing_backtest import simulate
from smg.drop_probability import outcome,independent
from backtest.repair_study import fixed_trade_cost_sensitivity

POLICIES=('BASELINE','CURRENT_ONLY','PRIOR_NONPOSITIVE','PRIOR_GAIN_MAX_2PCT')


def keep(event,policy):
    if policy not in POLICIES:raise ValueError('Unknown timing policy')
    if policy=='BASELINE':return True
    if event.get('source_policy')=='FIRM_INTRADAY_EXHAUSTION_RESEARCH':return True
    if policy=='CURRENT_ONLY':return False
    change=event.get('observed_change_from_prior_close')
    return isinstance(change,(int,float)) and change<=(0 if policy=='PRIOR_NONPOSITIVE' else .02)


def run(packet,folder,out):
    out.mkdir(parents=True,exist_ok=True);results=[]
    for year in (2023,2024,2025):
        source=json.loads((folder/f'{year}-PRECLOSE_ONLY-signals.json').read_text())
        for policy in POLICIES:
            events={d:[e for e in es if keep(e,policy)] for d,es in source.items()}
            row={'year':year,'policy':policy,'source_counts':dict(Counter(e['source_policy'] for es in events.values() for e in es)),
                 'provider_requests':0,'live_enabled':False}
            symbols=sorted({e['ticker'] for es in events.values() for e in es})
            for case,bps,rate in [('base',30,.1),('stress',100,1.)]:
                result=simulate(packet['raw'],packet['split'],symbols,packet['sessions'],
                    start=f'{year}-09-08',end=f'{year}-12-05',strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',hold=3,
                    firm_dates=packet['first_dates'],intraday_signals=events,signal_share_sizing=True,risk_controls=True,
                    position_target=50000,buying_power=150000,max_position_equity_fraction=.30,decision_price_buffer=1.2,
                    smg_cash_interest=True,cost_bps=bps,borrow_rate=rate)
                (out/f'{year}-{policy}-{case}.json').write_text(json.dumps(result,indent=2))
                row[case]={k:result[k] for k in ('net_profit','closed_trades','max_observed_drawdown_pct')}
                if case=='base':base=result
            row['same_trade_stress']=fixed_trade_cost_sensitivity({**base,'open_positions':base.get('unresolved_positions',{})},packet['split'])
            labels=[]
            for t in base['trades']:
                observed=outcome(t,packet['split'],packet['raw'])
                if observed:labels.append({**t,**observed})
            row['filled_trades_drop20_within_3_sessions']=sum(r['day_3'] for r in labels)
            row['known_filled_trade_outcomes']=len(labels)
            results.append(row)
    output={'status':'FIXED_FIRM_TIMING_COMPARISON','results':results,'provider_requests':0,'live_changed':False,
            'limitations':['Reused partial independently discovered firm cohort, not untouched validation',
                           'Historical cap/halts/borrow/SMG membership unknown; profits remain conditional',
                           'Losing variants retained; improved capture alone cannot authorize promotion']}
    (out/'summary.json').write_text(json.dumps(output,indent=2));return output


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--signals',required=True)
    p.add_argument('--out',default='outputs/backtest/firm-timing-2026-10-06');a=p.parse_args()
    report=run(json.loads(gzip.decompress(Path(a.packet).read_bytes())),Path(a.signals),Path(a.out))
    print(json.dumps(report))


if __name__=='__main__':main()
