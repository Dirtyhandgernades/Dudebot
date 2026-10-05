"""Replay fixed hybrid policies offline, preserving per-year coverage failures.

Run from the repository root with python -m backtest.compare_cached_years.
This module reads completed research signals; it never sends notifications.
"""
import argparse
import gzip
import hashlib
import json
import csv
from pathlib import Path

from smg.models import Config
from smg.swing_backtest import simulate


def run(source, out):
    source, out = Path(source), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    packet_path = source / 'firm-timing-inputs.json.gz'
    packet = json.loads(gzip.decompress(packet_path.read_bytes()))
    cfg = Config(**packet['config'])
    rows = []
    for year in (2023, 2024, 2025):
        signal_path = source / f'{year}-hybrid-signals.json'
        signals = json.loads(signal_path.read_text(encoding='utf-8'))
        audit = json.loads((source / f'{year}-intraday-audit.json').read_text(encoding='utf-8'))
        start, end = f'{year}-09-08', f'{year}-12-05'
        expected = {d for d in packet['sessions'] if start <= d < end}
        missing = sorted(expected - signals.keys())
        for hold in (3, 5):
            for label, bps, borrow in (('base', 30, .1), ('stress', 100, 1.0)):
                result = simulate(packet['raw'], packet['split'], packet['cohorts'][start]['short'],
                    packet['sessions'], start=start, end=end, hold=hold,
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH', cost_bps=bps, borrow_rate=borrow,
                    position_target=30000, buying_power=150000, firm_dates=packet['firm_dates'],
                    firm_cfg=cfg, risk_controls=True, signal_share_sizing=True,
                    intraday_signals=signals, smg_cash_interest=True)
                prefix = f'{year}-hold-{hold}-{label}'
                (out / f'{prefix}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
                fields = ['ticker','signal_date','entry_date','exit_date','exit_reason','shares',
                          'entry_price','notional','pnl','return_pct','gross_return_pct']
                with (out / f'{prefix}-trades.csv').open('w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(result['trades'])
                row = {'year': year, 'hold_sessions': hold, 'cost_case': label,
                    **{k: result[k] for k in ('ending_balance','net_profit','closed_trades',
                        'win_rate','max_observed_drawdown_pct','signals','interest_pnl',
                        'unresolved_open_positions','account_insolvent','borrow_execution')},
                    'cohort_size': len(packet['cohorts'][start]['short']),
                    'missing_scan_sessions': missing, 'scan_data_gaps': audit['gaps'],
                    'simulation_data_gaps': result['gaps'],
                    'target_reached_conditionally': result['ending_balance'] is not None and result['ending_balance'] >= 189000}
                rows.append(row)
    report = {'status': 'CONDITIONAL_RESEARCH_ONLY', 'initial_balance': 100000,
        'position_target': 30000, 'buying_power_assumption': 150000,
        'input_packet_sha256': hashlib.sha256(packet_path.read_bytes()).hexdigest(),
        'results': rows, 'provider_requests': 0, 'live_policy_changed': False,
        'limitations': ['2025 was inspected before this comparison and is not an untouched holdout',
            'Three- and five-session policies are fixed across years; no selection from each year outcome',
            'Historical market cap, halts, borrow, SMG eligibility, SEC fees and exact margin treatment remain unverified',
            'Interest uses the simulator collateral cash ledger, which is not certified SMG account accounting',
            'Firm filing coverage and minute windows are incomplete; drawdown can be understated by missing marks',
            '2022 and earlier lack completed independent intraday signal inputs and are not reported as tested']}
    (out / 'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for row in rows:
        print(json.dumps({k: row[k] for k in ('year', 'hold_sessions', 'cost_case',
            'ending_balance', 'net_profit', 'closed_trades', 'max_observed_drawdown_pct')}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', default='outputs/backtest/hybrid-37386241124')
    p.add_argument('--out', default='outputs/backtest/other-years-2026-10-05')
    args = p.parse_args()
    run(args.source, args.out)
