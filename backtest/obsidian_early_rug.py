"""Offline early-weakness threshold ablation; NEVER sends Discord alerts.

Run: python -m backtest.obsidian_early_rug --source outputs/backtest/hybrid-37386241124
This re-ranks EXISTING independently discovered hybrid events. It does not
claim to discover previously unseen securities or verify historical borrow.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

from smg.intraday_replay import confirmed_hybrid_events
from smg.models import Config
from smg.swing_backtest import simulate
from backtest.confirmation_comparison import drop_timing

# Frozen before outcomes are inspected in this experiment.
# More negative thresholds select early weakness; positive permits rallies.
THRESHOLDS = (-0.10, -0.05, -0.02, 0.0, 0.02, 0.05)


def run(source, out):
    source, out = Path(source), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    packet_file = source / 'firm-timing-inputs.json.gz'
    packet = json.loads(gzip.decompress(packet_file.read_bytes()))
    cfg = Config(**packet['config'])
    results = []
    for year in (2023, 2024, 2025):
        signal_file = source / f'{year}-hybrid-signals.json'
        events = json.loads(signal_file.read_text(encoding='utf-8'))
        for threshold in THRESHOLDS:
            filtered, audit = confirmed_hybrid_events(
                packet, events, max_observed_gain=threshold
            )
            for cost, bps, borrow in (('base', 30, 0.1), ('stress', 100, 1.0)):
                end = f'{year}-12-05'
                simulation = simulate(
                    packet['raw'], packet['split'],
                    packet['cohorts'][f'{year}-09-08']['short'],
                    packet['sessions'], start=f'{year}-09-08', end=end,
                    hold=3, strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',
                    cost_bps=bps, borrow_rate=borrow, position_target=30000,
                    buying_power=150000, firm_dates=packet['firm_dates'],
                    firm_cfg=cfg, risk_controls=True, signal_share_sizing=True,
                    intraday_signals=filtered, smg_cash_interest=True
                )
                prefix = f'{year}-maxgain-{threshold:+.2f}-{cost}'
                with (out / f'{prefix}-trades.csv').open(
                    'w', newline='', encoding='utf-8'
                ) as f:
                    columns = ['ticker', 'signal_date', 'entry_date', 'exit_date',
                               'shares', 'pnl', 'exit_reason']
                    writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(simulation['trades'])
                results.append({
                    'year': year, 'max_observed_gain': threshold,
                    'cost_case': cost, 'filter_audit': audit,
                    'net_profit': simulation['net_profit'],
                    'ending_balance': simulation['ending_balance'],
                    'closed_trades': simulation['closed_trades'],
                    'max_observed_drawdown_pct': simulation['max_observed_drawdown_pct'],
                    'drop_timing': drop_timing(simulation, packet, end),
                })
    report = {
        'status': 'REUSED_DATA_ABLATION_NOT_VALIDATED',
        'source_sha256': hashlib.sha256(packet_file.read_bytes()).hexdigest(),
        'thresholds': THRESHOLDS,
        'results': results,
        'production_changed': False,
        'limitations': [
            'Only filters existing independent hybrid signals; cannot measure full-market rug recall',
            '2023-2025 already inspected; selecting a winner is in-sample optimization',
            'Historical borrow, halt, cap and actual SMG execution are incomplete',
            'Future closing-price dump hit is not the same as realized trade profit',
            'Must freeze candidate and validate on genuinely later live decisions',
        ],
    }
    (out / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for row in results:
        print(json.dumps({k: row[k] for k in
                          ('year', 'max_observed_gain', 'cost_case', 'net_profit',
                           'closed_trades', 'max_observed_drawdown_pct')}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='outputs/backtest/hybrid-37386241124')
    parser.add_argument('--out', default='outputs/backtest/obsidian-early-rug-2026-10-25')
    args = parser.parse_args()
    run(args.source, args.out)
