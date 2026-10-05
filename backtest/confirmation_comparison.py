"""Fixed retrospective confirmation test and 1-3-session drop measurement."""
import csv
import gzip
import json
from pathlib import Path

from smg.intraday_replay import confirmed_hybrid_events,scaled_hybrid_events
from smg.models import Config
from smg.swing_backtest import simulate


def drop_timing(result, packet, end):
    sessions=packet['sessions'];index={d:i for i,d in enumerate(sessions)}
    report={}
    for horizon in (1,2,3):
        known=declined=dumped=missing=0
        for trade in result['trades']:
            i=index[trade['entry_date']]
            future=sessions[i+1:i+1+horizon]
            bars=[packet['split'].get(trade['ticker'],{}).get(d) for d in future]
            # Censored season-end trades and missing bars stay out of the denominator.
            if len(future)!=horizon or future[-1]>end or not all(bars):
                missing+=1;continue
            returns=[b['c']/trade['adjusted_entry']-1 for b in bars]
            known+=1;declined+=any(r<0 for r in returns);dumped+=any(r<=-.20+1e-10 for r in returns)
        report[str(horizon)]={'assessable_entries':known,'any_lower_close':declined,
            'drop_20pct_at_close':dumped,'unavailable_or_season_end':missing,
            'drop_20pct_rate':dumped/known if known else None}
    return report


def run():
    source=Path('outputs/backtest/hybrid-37386241124')
    out=Path('outputs/backtest/confirmation-2026-10-05');out.mkdir(parents=True,exist_ok=True)
    packet=json.loads(gzip.decompress((source/'firm-timing-inputs.json.gz').read_bytes()))
    cfg=Config(**packet['config']);rows=[]
    for year in (2023,2024,2025):
        events=json.loads((source/f'{year}-hybrid-signals.json').read_text())
        confirmed,audit=confirmed_hybrid_events(packet,events)
        scaled,_=scaled_hybrid_events(packet,events)
        for policy,event_set in (('baseline',events),('confirmed',confirmed),('scaled',scaled)):
            for hold in (3,5):
                for case,bps,borrow in (('base',30,.1),('stress',100,1.0)):
                    end=f'{year}-12-05'
                    result=simulate(packet['raw'],packet['split'],packet['cohorts'][f'{year}-09-08']['short'],
                        packet['sessions'],start=f'{year}-09-08',end=end,hold=hold,
                        strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',cost_bps=bps,borrow_rate=borrow,
                        position_target=30000,buying_power=150000,firm_dates=packet['firm_dates'],
                        firm_cfg=cfg,risk_controls=True,signal_share_sizing=True,
                        intraday_signals=event_set,smg_cash_interest=True)
                    prefix=f'{year}-{policy}-hold-{hold}-{case}'
                    (out/f'{prefix}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                    fields=['ticker','entry_date','exit_date','exit_reason','shares','notional','pnl','return_pct']
                    with (out/f'{prefix}-trades.csv').open('w',newline='',encoding='utf-8') as f:
                        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(result['trades'])
                    row={'year':year,'policy':policy,'hold_sessions':hold,'cost_case':case,
                        **{k:result[k] for k in ('net_profit','ending_balance','closed_trades','signals','max_observed_drawdown_pct')},
                        'filter_audit':audit if policy=='confirmed' else {},'drop_timing':drop_timing(result,packet,end)}
                    rows.append(row)
                    print(json.dumps({k:v for k,v in row.items() if k not in ('drop_timing','filter_audit')}),flush=True)
    report={'status':'RETROSPECTIVE_RESEARCH_ONLY','live_enabled':False,'results':rows,
        'limitations':['Filter was motivated by inspected losses; all three years are reused research data',
            'No calibrated dump confidence, no guarantee of consistent future returns',
            'Forward timing uses split-adjusted closing prices from entry close; intraday lows are not claimed executable',
            'A price drop within 1-3 sessions can occur after an earlier exit and is separate from realized profit',
            'Historical cap, halt, borrow, corporate actions and exact SMG account accounting remain incomplete']}
    (out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':run()
