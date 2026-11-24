"""One registered bounded-exposure comparison on cached frozen hybrid signals."""
import argparse
import gzip
import hashlib
import json
import zipfile
from pathlib import Path

from backtest.obsidian_strategy_lab import stats
from smg.exposure import POLICY
from smg.models import Config
from smg.risk_model import feature_row, predict
from smg.swing_backtest import simulate


def run(original, hosted, output):
    baseline_path = Path('backtest/evidence/2026-11-21/portfolio-033/baseline-metrics.json')
    paths = [original, hosted, Path(__file__), Path('smg/exposure.py'), baseline_path,
             Path('smg/swing_backtest.py'), Path('smg/risk_model.py'), Path('smg/models.py'),
             Path('backtest/obsidian_strategy_lab.py')]
    inputs = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    key = hashlib.sha256(json.dumps(dict(inputs=inputs, policy=POLICY), sort_keys=True).encode()).hexdigest()
    if output.exists():
        saved = json.loads(output.read_text())
        if saved['experiment_key'] != key:
            raise ValueError('EXISTING_EXPERIMENT_INPUTS_CHANGED')
        print('Reused completed experiment', key)
        return saved
    with zipfile.ZipFile(original) as archive:
        packet = json.loads(gzip.decompress(archive.read('firm-timing-inputs.json.gz')))
        signals = {year: json.loads(archive.read(f'{year}-hybrid-signals.json')) for year in (2023, 2024, 2025)}
    baseline = json.loads(baseline_path.read_text())
    results = []
    with zipfile.ZipFile(hosted) as archive:
        for year in (2023, 2024, 2025):
            model = json.loads(archive.read(f'backtest/target-rank-2026-10-05/{year}-model.json'))
            selected = {}
            for day, events in signals[year].items():
                index = packet['sessions'].index(day)
                for event in events:
                    history = [packet['split'][event['ticker']][d] for d in packet['sessions'][index-22:index]]
                    score = predict(model['model'], [{'x': feature_row(history)}])[0]
                    if score >= model['thresholds']['top_half']:
                        selected.setdefault(day, []).append({**event, 'historical_rank': score})
            for case, bps, borrow in [('base', 30, .1), ('stress', 100, 1.)]:
                result = simulate(packet['raw'], packet['split'], packet['cohorts'][f'{year}-09-08']['short'],
                    packet['sessions'], start=f'{year}-09-08', end=f'{year}-12-05', hold=3,
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH', cost_bps=bps, borrow_rate=borrow,
                    position_target=50000, buying_power=150000, firm_dates=packet['firm_dates'],
                    firm_cfg=Config(**packet['config']), risk_controls=True, signal_share_sizing=True,
                    intraday_signals=selected, smg_cash_interest=True, max_position_equity_fraction=.30,
                    exposure_policy=POLICY)
                reference = next(row['metrics'] for row in baseline if row['year'] == year
                    and row['benchmark'] == 'aggressive' and row['hold'] == 3 and row['cost'] == case)
                results.append(dict(year=year, cost=case, baseline=reference, challenger=stats(result, packet)))
    report = dict(experiment_id='SQUEEZE-073', experiment_key=key, inputs=inputs, policy=POLICY,
                  baseline_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(), simulations=6,
                  rows=results, independent_holdout=False, promotion_authorized=False)
    with output.open('x', encoding='utf-8') as file:
        json.dump(report, file, indent=2, allow_nan=False)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--hosted', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = run(args.original, args.hosted, args.output)
    for row in report['rows']:
        print(row['year'], row['cost'], *(round(row[group][field], 2)
            for group in ('baseline', 'challenger') for field in ('net_profit', 'max_observed_drawdown_pct')))


if __name__ == '__main__':
    main()
