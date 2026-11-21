"""Registered unranked control; original ranker and signal source unchanged."""
import argparse,json
from pathlib import Path
from backtest.obsidian_data_audit import load_checked
from backtest.obsidian_strategy_lab import hashfile, stats
from smg.risk_model import feature_row
from smg.swing_backtest import simulate
from smg.models import Config


def run(source,baseline,registration,out):
    source,baseline,out=Path(source),Path(baseline),Path(out)
    spec=json.loads(Path(registration).read_text())
    if hashfile(source/'firm-timing-inputs.json.gz')!=spec['source_packet_sha256']:raise ValueError('INPUT_HASH_MISMATCH')
    if out.exists():raise FileExistsError(out)
    packet,integrity=load_checked(source);out.mkdir(parents=True);rows=[]
    index={d:i for i,d in enumerate(packet['sessions'])}
    for year in (2023,2024,2025):
        original=json.loads((source/f'{year}-hybrid-signals.json').read_text());events={}
        for day,items in original.items():
            i=index[day];events[day]=[]
            for e in items:
                history=[packet['split'].get(e['ticker'],{}).get(d) for d in packet['sessions'][i-22:i]]
                if len(history)==22 and all(history) and feature_row(history) is not None:events[day].append(e)
        for cost,bps,borrow in [('base',30,.1),('stress',100,1.)]:
            r=simulate(packet['raw'],packet['split'],packet['cohorts'][f'{year}-09-08']['short'],packet['sessions'],
                start=f'{year}-09-08',end=f'{year}-12-05',hold=3,strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',
                cost_bps=bps,borrow_rate=borrow,position_target=50000,buying_power=150000,
                firm_dates=packet['firm_dates'],firm_cfg=Config(**packet['config']),risk_controls=True,
                signal_share_sizing=True,intraday_signals=events,smg_cash_interest=True,max_position_equity_fraction=.30)
            ref=json.loads((baseline/f'{year}-top_half_30pct-50000-{cost}.json').read_text())
            (out/f'{year}-unranked-{cost}.json').write_text(json.dumps(r,indent=2,sort_keys=True))
            rows.append(dict(year=year,cost_case=cost,control_metrics=stats(r,packet),ranked_metrics=stats(ref,packet),
                             ranked_minus_control_net_profit=ref['net_profit']-r['net_profit'] if ref['net_profit'] is not None and r['net_profit'] is not None else None,
                             prediction_edge_established=False,reason='Inspected conditional samples, no untouched test, missing execution evidence'))
    cash=[]
    for year in (2023,2024,2025):
        r=simulate(packet['raw'],packet['split'],packet['cohorts'][f'{year}-09-08']['short'],packet['sessions'],
            start=f'{year}-09-08',end=f'{year}-12-05',hold=3,strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',
            position_target=50000,buying_power=150000,firm_dates=packet['firm_dates'],firm_cfg=Config(**packet['config']),
            risk_controls=True,signal_share_sizing=True,intraday_signals={},smg_cash_interest=True)
        cash.append(dict(year=year,metrics=stats(r,packet),interest_is_conditional_assumption=True))
    result=dict(registration=spec,comparisons=rows,cash_control=cash,input_integrity=integrity,trade_costs_identical=True,production_changed=False)
    (out/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True));return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',default='outputs/backtest/hybrid-37386241124')
    p.add_argument('--baseline',default='outputs/backtest/target-rank-2026-10-05')
    p.add_argument('--registration',default='backtest/evidence/2026-11-20/strategy-overhaul/ranking-control-registration.json')
    p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.baseline,a.registration,a.out)
    print(json.dumps([dict(year=x['year'],cost=x['cost_case'],ranked_minus_control=x['ranked_minus_control_net_profit']) for x in r['comparisons']]))
if __name__=='__main__':main()
