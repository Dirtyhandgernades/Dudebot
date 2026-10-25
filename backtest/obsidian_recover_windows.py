"""Bounded, point-in-time recovery of missing/stale intraday candidate windows.

Requires original historical artifact and Alpaca SIP credentials. This never
changes original signals, trades, production state or the original dataset.
Re-run with previous recovery artifact restored to continue checkpoints.
"""
import argparse
import gzip
import json
import os
from collections import Counter
from pathlib import Path

from smg.intraday_replay import Bars, candidates, decision_window, partial_bar


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', default='outputs/backtest/hybrid-37386241124')
    p.add_argument('--out', default='outputs/backtest/obsidian-recovery')
    p.add_argument('--max-requests', type=int, default=120)
    args = p.parse_args()
    source, out = Path(args.source), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    packet = json.loads(gzip.decompress((source/'firm-timing-inputs.json.gz').read_bytes()))
    if not os.getenv('ALPACA_API_KEY') or not os.getenv('ALPACA_SECRET_KEY'):
        raise RuntimeError('ALPACA_CREDENTIALS_UNAVAILABLE')
    client = Bars(out/'bar-cache', max_requests=args.max_requests)
    results = []
    totals = Counter()
    for year in (2023, 2024, 2025):
        audit = json.loads((source/f'{year}-intraday-audit.json').read_text())
        for day_record in audit['sessions']:
            day = day_record.get('day')
            if not day or 'candidate_audit' not in day_record:
                continue
            names = [row['ticker'] for row in day_record['candidate_audit']
                     if row.get('status') == 'SPLIT_WINDOW_UNAVAILABLE']
            if not names:
                continue
            opened, _, _, cutoff = decision_window(day)
            for ticker in names:
                totals['target_windows'] += 1
                try:
                    # One ticker per request to isolate partial provider failures.
                    bars = client.get([ticker], opened, cutoff, 'split')
                    partial = partial_bar(bars.get(ticker, []), opened, cutoff)
                    status = 'RECOVERED' if partial else 'STILL_MISSING_OR_STALE'
                except RuntimeError as exc:
                    if str(exc) == 'REQUEST_BUDGET':
                        status = 'DEFERRED_REQUEST_BUDGET'
                    else:
                        status = 'PROVIDER_ERROR'
                except Exception:
                    status = 'PROVIDER_ERROR'
                totals[status] += 1
                results.append({'year': year, 'day': day, 'ticker': ticker,
                                'status': status})
                # Preserve progress even when the request budget is exhausted.
                (out/'recovery.json').write_text(json.dumps({
                    'status': 'PARTIAL_REPAIR_NOT_VALIDATED',
                    'counts': dict(totals),
                    'requests': client.requests,
                    'records': results,
                    'warning': 'Do not treat recovered bars as rebuilt signals or repaired replay',
                }, indent=2))
                if status == 'DEFERRED_REQUEST_BUDGET':
                    print(json.dumps({'status': 'BUDGET_REACHED', 'counts': dict(totals)}))
                    return
    print(json.dumps({'status': 'PROBE_COMPLETE', 'counts': dict(totals)}))


if __name__ == '__main__':
    main()
