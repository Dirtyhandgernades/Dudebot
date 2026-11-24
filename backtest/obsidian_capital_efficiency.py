"""Attribute SQUEEZE-073 capital efficiency using saved metrics only."""
import argparse
import hashlib
import json
from pathlib import Path


def compare(report):
    rows = []
    for case in report['rows']:
        row = dict(year=case['year'], cost=case['cost'])
        for name in ('baseline', 'challenger'):
            metrics = case[name]
            efficiency = metrics['realized_trade_return_on_summed_entry_notional']
            trade_profit = metrics['realized_trade_profit']
            row[name] = dict(net_profit=metrics['net_profit'], trade_profit=trade_profit,
                interest=metrics['interest_pnl'], trade_return_per_notional=efficiency,
                summed_entry_notional=trade_profit / efficiency if efficiency else None,
                mean_gross_to_equity=metrics['mean_daily_marked_gross_to_equity'],
                missing_exposure_sessions=metrics['exposure_mark_missing_sessions'],
                closed_trades=metrics['closed_trades'])
            if abs(metrics['pnl_reconciliation_delta']) > .02:
                raise ValueError('Unreconciled trade profit and interest')
        old, new = row['baseline'], row['challenger']
        row['efficiency_change_pp'] = 100 * (new['trade_return_per_notional'] - old['trade_return_per_notional'])
        row['notional_retained_fraction'] = new['summed_entry_notional'] / old['summed_entry_notional']
        row['trade_profit_retained_fraction'] = new['trade_profit'] / old['trade_profit']
        row['net_profit_change'] = new['net_profit'] - old['net_profit']
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    result = dict(source_sha256=hashlib.sha256(raw).hexdigest(), simulations=0,
                  interpretation='Accounting attribution; summed notional reuses capital, not equity return. '
                  'Mean gross/equity is a marked exposure diagnostic, not verified SMG buying power. '
                  'Changed allocation and cooldown prevent causal isolation of volatility sizing.',
                  rows=compare(json.loads(raw)))
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2)
    for row in result['rows']:
        print(row['year'], row['cost'], 'efficiency pp', round(row['efficiency_change_pp'], 3),
              'notional retained', round(row['notional_retained_fraction'], 3),
              'profit retained', round(row['trade_profit_retained_fraction'], 3),
              'missing exposure', row['baseline']['missing_exposure_sessions'], row['challenger']['missing_exposure_sessions'])


if __name__ == '__main__':
    main()
