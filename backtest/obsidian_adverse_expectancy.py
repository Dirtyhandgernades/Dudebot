"""Registered iterations 016–018 on frozen hybrid events."""
import argparse
from collections import defaultdict
from datetime import date
import gzip
import json
from pathlib import Path

import numpy as np

from backtest.obsidian_strategy_lab import hashfile, stats
from smg.models import Config
from smg.risk_model import feature_row, matured_before, predict, samples
from smg.swing_backtest import simulate


def closing_outcomes(series, days, index, horizon, end):
    future = days[index + 1:index + horizon + 1]
    if len(future) != horizon or future[-1] > end or any(d not in series for d in [days[index], *future]):
        return None
    ratio = [series[d]['c'] / series[days[index]]['c'] for d in future]
    elapsed = (date.fromisoformat(future[-1]) - date.fromisoformat(days[index])).days
    return dict(adverse=max(0, max(ratio) - 1), favorable=max(0, 1 - min(ratio)),
                net=1 - ratio[-1] - .003 * (1 + ratio[-1]) - 10 / 50000 - .10 * elapsed / 365)


def estimate(training, packet, index):
    x = np.array([r['x'] for r in training])
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-12] = 1
    z = (x - mean) / scale
    targets = []
    for r in training:
        label = closing_outcomes(packet['split'][r['ticker']], packet['sessions'], index[r['entry_date']], 3, r['label_end'])
        targets.append([label['adverse'], label['net']])
    y = np.array(targets)
    weights = np.linalg.solve(z.T @ z + len(z) * np.eye(z.shape[1]), z.T @ (y - y.mean(axis=0)))
    def forecast(features):
        return (np.asarray(features) - mean) / scale @ weights + y.mean(axis=0)
    scores = forecast(x)
    return forecast, np.quantile(scores[:, 0], .75), np.median(scores[:, 1])


def run(repair):
    source = Path('outputs/backtest/hybrid-37386241124')
    archive = Path('outputs/backtest/target-rank-2026-10-05')
    original = source / 'firm-timing-inputs.json.gz'
    assert hashfile(original) == 'e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb'
    assert hashfile(repair) == 'a069e8d6d95f201f3b379139c844f3cb1ea94f26cb2900de930259334ebaa9d8'
    packet = json.loads(gzip.decompress(original.read_bytes()))
    repaired = json.loads(gzip.decompress(repair.read_bytes()))
    days = packet['sessions']
    index = {d: i for i, d in enumerate(days)}
    training_pool = samples([], packet['raw'], packet['split'], days, packet['firm_dates'])
    report = dict(inputs={original.name: hashfile(original), repair.name: hashfile(repair)}, years={})
    for year in (2023, 2024, 2025):
        events_file = source / f'{year}-hybrid-signals.json'
        model_file = archive / f'{year}-model.json'
        report['inputs'].update({p.name: hashfile(p) for p in [events_file, model_file]})
        model = json.loads(model_file.read_text())
        training = matured_before(training_pool, f'{year}-01-01')
        forecast, risk_limit, profit_floor = estimate(training, packet, index)
        end = f'{year}-12-05'
        lanes = {k: defaultdict(list) for k in ['baseline','adverse','expectancy']}
        diagnostic = []
        for day, events in json.loads(events_file.read_text()).items():
            for event in events:
                symbol = event['ticker']
                series = packet['split'][symbol]
                i = index[day]
                x = feature_row([series[d] for d in days[i-22:i]])
                rank = predict(model['model'], [{'x': x}])[0]
                risk, profit = forecast(x)
                base = rank >= model['thresholds']['top_half']
                selected = dict(baseline=base, adverse=bool(base and risk <= risk_limit), expectancy=bool(profit >= profit_floor))
                for lane, keep in selected.items():
                    if keep:
                        lanes[lane][day].append({**event, 'historical_rank': rank})
                diagnostic.append(dict(selected=selected, ticker=symbol, day=day,
                                       outcomes={h: closing_outcomes(series, days, i, h, end) for h in (1,2,3,5)}))
        runs = {}
        for lane in [*lanes, 'valuation']:
            prices = repaired if lane == 'valuation' else packet
            for case, bps, borrow in [('base',30,.10),('stress',100,1.)]:
                r = simulate(prices['raw'], prices['split'], packet['cohorts'][f'{year}-09-08']['short'], days,
                             start=f'{year}-09-08', end=end, hold=3, strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',
                             cost_bps=bps, borrow_rate=borrow, position_target=50000, buying_power=150000,
                             firm_dates=packet['firm_dates'], firm_cfg=Config(**packet['config']), risk_controls=True,
                             signal_share_sizing=True, intraday_signals=lanes['baseline' if lane=='valuation' else lane],
                             smg_cash_interest=True, max_position_equity_fraction=.30)
                ref=json.loads((archive/f'{year}-top_half_30pct-50000-{case}.json').read_text())
                if lane=='baseline':
                    assert r['trades']==ref['trades'] and r['daily_equity']==ref['daily_equity']
                if lane=='valuation':
                    def entries(result):
                        return sorted((t['ticker'],t['entry_date'],t['shares']) for t in result['trades'])
                    assert entries(r)==entries(ref)
                runs[lane+'_'+case]=stats(r,prices)
        controls = {c: stats(json.loads((archive/f'{year}-top_quartile-30000-{c}.json').read_text()),packet)
                    for c in ('base','stress')}
        report['years'][year]=dict(training_count=len(training), last_label=max(r['label_end'] for r in training),
                                  risk_limit=risk_limit,profit_floor=profit_floor,portfolio=runs,archived_quartile=controls,
                                  diagnostics=diagnostic)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repair',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    result=run(args.repair)
    with args.out.open('x') as handle:
        json.dump(result,handle,allow_nan=False,sort_keys=True)
