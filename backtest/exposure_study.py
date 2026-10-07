"""Fixed exposure limits on both original and expanded independent corpora."""
import argparse,gzip,json
from pathlib import Path
from smg.exposure import POLICY
from smg.swing_backtest import simulate
from backtest.firm_timing_study import keep


def run(packet,signals,out,corpus):
    out.mkdir(parents=True,exist_ok=True);rows=[]
    for year in (2023,2024,2025):
        source=json.loads((signals/f'{year}-PRECLOSE_ONLY-signals.json').read_text())
        for name,timing,protection in [('BASELINE','BASELINE',None),
                                      ('BOUNDED_EXPOSURE','BASELINE',POLICY),
                                      ('BOUNDED_CONFIRMED_PRIOR','PRIOR_NONPOSITIVE',POLICY)]:
            events={d:[e for e in es if keep(e,timing)] for d,es in source.items()}
            symbols=sorted({e['ticker'] for es in events.values() for e in es});row={'corpus':corpus,'year':year,'policy':name}
            for case,bps,borrow in [('base',30,.1),('stress',100,1.)]:
                result=simulate(packet['raw'],packet['split'],symbols,packet['sessions'],
                    start=f'{year}-09-08',end=f'{year}-12-05',hold=3,
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',firm_dates=packet['first_dates'],
                    intraday_signals=events,signal_share_sizing=True,risk_controls=True,
                    position_target=50000,buying_power=150000,max_position_equity_fraction=.30,
                    decision_price_buffer=1.2,smg_cash_interest=True,cost_bps=bps,borrow_rate=borrow,
                    exposure_policy=protection)
                (out/f'{year}-{name}-{case}.json').write_text(json.dumps(result,indent=2))
                row[case]={k:result[k] for k in ('net_profit','closed_trades','max_observed_drawdown_pct','gaps')}
                row[case]['worst_trade_loss']=round(min((t['pnl'] for t in result['trades']),default=0),2)
            rows.append(row)
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);p.add_argument('--expanded',required=True)
    p.add_argument('--original-signals',required=True);p.add_argument('--expanded-signals',required=True)
    p.add_argument('--out',default='outputs/backtest/exposure-2026-10-06-five-session');a=p.parse_args();out=Path(a.out)
    rows=[]
    for name,packet,folder in [('original',a.original,a.original_signals),('expanded',a.expanded,a.expanded_signals)]:
        rows+=run(json.loads(gzip.decompress(Path(packet).read_bytes())),Path(folder),out/name,name)
    report={'status':'FIXED_EXPOSURE_RESEARCH','policy':POLICY,'results':rows,'live_changed':False,'provider_requests':0,
        'limits':['Closing-price stops cannot bound short losses','Historical borrow/cap/halts remain unknown',
                  'Both corpora are repeatedly inspected, not untouched validation','No known loser/winner ticker filters']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


if __name__=='__main__':main()
