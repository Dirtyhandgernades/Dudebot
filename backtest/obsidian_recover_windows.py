"""Resumable, evidence-preserving point-in-time SIP coverage recovery.

Do not conflate provider non-return with proof a historical bar never existed.
Only complete valid partial bars are recovered. Original artifact is immutable.
"""
import argparse
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from smg.intraday_replay import Bars, candidates, decision_window, partial_bar


def write_atomic(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True))
    temp.replace(path)


def target_windows(packet, source):
    for year in (2023, 2024, 2025):
        audit = json.loads((source / f'{year}-intraday-audit.json').read_text())
        for session in audit['sessions']:
            day = session.get('day')
            if not day:
                continue
            unavailable = {row['ticker'] for row in session.get('candidate_audit', [])
                           if row.get('status') == 'SPLIT_WINDOW_UNAVAILABLE'}
            for ticker in candidates(packet, day):
                yield year, day, ticker, (ticker in unavailable if 'candidate_audit' in session else None)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', default='outputs/backtest/hybrid-37386241124')
    p.add_argument('--out', default='outputs/backtest/obsidian-recovery')
    p.add_argument('--max-requests', type=int, default=120)
    args = p.parse_args()
    source, out = Path(args.source), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    packet_bytes = (source / 'firm-timing-inputs.json.gz').read_bytes()
    source_hash = hashlib.sha256(packet_bytes).hexdigest()
    packet = json.loads(gzip.decompress(packet_bytes))
    if not os.getenv('ALPACA_API_KEY') or not os.getenv('ALPACA_SECRET_KEY'):
        raise RuntimeError('ALPACA_CREDENTIALS_UNAVAILABLE')
    checkpoint = out / 'checkpoint.json'
    old = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
    if old and old.get('source_sha256') != source_hash:
        raise RuntimeError('SOURCE_PACKET_CHANGED_REJECT_CHECKPOINT')
    records = old.get('records', {})
    client = Bars(out / 'bar-cache', max_requests=args.max_requests)
    pending = []
    for year, day, ticker, baseline_missing in target_windows(packet, source):
        key = f'{day}|{ticker}'
        if key in records:
            continue
        pending.append((year, day, ticker, baseline_missing))
    for year, day, ticker, baseline_missing in pending:
        opened, _, _, cutoff = decision_window(day)
        try:
            bars = client.get([ticker], opened, cutoff, 'split').get(ticker, [])
            partial = partial_bar(bars, opened, cutoff)
            status = 'RECOVERED' if partial else 'PROVIDER_EMPTY_OR_STALE'
            record = {'year': year, 'day': day, 'ticker': ticker,
                      'baseline_missing': baseline_missing, 'status': status,
                      'bar_count': len(bars), 'last_complete_at': partial['last_complete_at'] if partial else None}
        except RuntimeError as exc:
            if str(exc) == 'REQUEST_BUDGET':
                break
            record = {'year': year, 'day': day, 'ticker': ticker, 'baseline_missing': baseline_missing,
                      'status': 'PROVIDER_ERROR_RETRYABLE', 'error_type': type(exc).__name__}
        except Exception as exc:
            record = {'year': year, 'day': day, 'ticker': ticker, 'baseline_missing': baseline_missing,
                      'status': 'PROVIDER_ERROR_RETRYABLE', 'error_type': type(exc).__name__}
        records[f'{day}|{ticker}'] = record
        write_atomic(checkpoint, {'source_sha256': source_hash, 'records': records})
    counts = Counter(r['status'] for r in records.values())
    baseline_recovered = sum(r['status'] == 'RECOVERED' and r['baseline_missing'] is True for r in records.values())
    unknown_recovered = sum(r['status'] == 'RECOVERED' and r['baseline_missing'] is None for r in records.values())
    report = {'status': 'PARTIAL_REPLAY_RECOVERY', 'source_sha256': source_hash,
              'requests_this_run': client.requests, 'windows_checked_cumulative': len(records),
              'counts': dict(counts), 'confirmed_baseline_gap_recoveries': baseline_recovered,
              'unmapped_recoveries': unknown_recovered, 'remaining_unchecked': len(pending) - (len(records) - len(old.get('records', {}))),
              'caveat': 'Provider empty/stale is not proof of permanent unavailability. Full replay must be regenerated before performance comparison.'}
    write_atomic(out / 'recovery.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
