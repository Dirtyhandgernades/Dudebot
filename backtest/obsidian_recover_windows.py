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
    p.add_argument('--max-error-attempts', type=int, default=3)
    args = p.parse_args()
    if args.max_requests < 1 or args.max_error_attempts < 1:
        p.error('request budget and retry attempts must be positive')

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
    # Copy rather than mutate old['records']: the old alias previously made
    # cumulative progress appear unchanged and inflated remaining_unchecked.
    records = dict(old.get('records', {}))
    windows = {}
    for year, day, ticker, baseline_missing in target_windows(packet, source):
        key = f'{day}|{ticker}'
        if key in windows:
            raise RuntimeError(f'DUPLICATE_TARGET_WINDOW: {key}')
        windows[key] = (year, day, ticker, baseline_missing)
    unexpected = set(records) - set(windows)
    if unexpected:
        raise RuntimeError(f'CHECKPOINT_TARGET_MISMATCH: {len(unexpected)} unexpected windows')

    # Retry transient provider errors in later runs; do not retry indefinitely.
    # Old checkpoints lack attempts, so treat an old error as one prior attempt.
    def attempts(key):
        record = records.get(key)
        return int(record.get('attempts', 1)) if record else 0

    pending = [
        (key, *window) for key, window in windows.items()
        if key not in records or (
            records[key]['status'] == 'PROVIDER_ERROR_RETRYABLE'
            and attempts(key) < args.max_error_attempts
        )
    ]
    client = Bars(out / 'bar-cache', max_requests=args.max_requests)
    attempted_this_run = 0
    for key, year, day, ticker, baseline_missing in pending:
        opened, _, _, cutoff = decision_window(day)
        try:
            bars = client.get([ticker], opened, cutoff, 'split').get(ticker, [])
            partial = partial_bar(bars, opened, cutoff)
            status = 'RECOVERED' if partial else 'PROVIDER_EMPTY_OR_STALE'
            record = {
                'year': year, 'day': day, 'ticker': ticker,
                'baseline_missing': baseline_missing, 'status': status,
                'bar_count': len(bars),
                'last_complete_at': partial['last_complete_at'] if partial else None,
            }
        except RuntimeError as exc:
            if str(exc) == 'REQUEST_BUDGET':
                break
            record = {
                'year': year, 'day': day, 'ticker': ticker,
                'baseline_missing': baseline_missing,
                'status': 'PROVIDER_ERROR_RETRYABLE',
                'error_type': type(exc).__name__,
            }
        except Exception as exc:
            record = {
                'year': year, 'day': day, 'ticker': ticker,
                'baseline_missing': baseline_missing,
                'status': 'PROVIDER_ERROR_RETRYABLE',
                'error_type': type(exc).__name__,
            }
        record['attempts'] = attempts(key) + 1
        records[key] = record
        attempted_this_run += 1
        write_atomic(checkpoint, {'source_sha256': source_hash, 'records': records})

    counts = Counter(r['status'] for r in records.values())
    baseline_recovered = sum(
        r['status'] == 'RECOVERED' and r['baseline_missing'] is True
        for r in records.values()
    )
    unknown_recovered = sum(
        r['status'] == 'RECOVERED' and r['baseline_missing'] is None
        for r in records.values()
    )
    remaining = sum(key not in records for key in windows)
    retry_pending = sum(
        r['status'] == 'PROVIDER_ERROR_RETRYABLE' and attempts(key) < args.max_error_attempts
        for key, r in records.items()
    )
    retry_exhausted = sum(
        r['status'] == 'PROVIDER_ERROR_RETRYABLE' and attempts(key) >= args.max_error_attempts
        for key, r in records.items()
    )
    if len(records) + remaining != len(windows):
        raise RuntimeError('RECOVERY_ACCOUNTING_INVARIANT_FAILED')
    report = {
        'status': 'PARTIAL_REPLAY_RECOVERY',
        'source_sha256': source_hash,
        'total_candidate_windows': len(windows),
        'requests_this_run': client.requests,
        'windows_attempted_this_run': attempted_this_run,
        'windows_checked_cumulative': len(records),
        'counts': dict(counts),
        'confirmed_baseline_gap_recoveries': baseline_recovered,
        'unmapped_recoveries': unknown_recovered,
        'remaining_unchecked': remaining,
        'retryable_pending': retry_pending,
        'retry_exhausted': retry_exhausted,
        'caveat': (
            'The original audit has no per-ticker candidate status for most windows. '
            'Unmapped recoveries are not confirmed repairs of its aggregate 2,259 gaps. '
            'Provider empty/stale is not proof of permanent unavailability. '
            'Regenerate full point-in-time replay before any performance comparison.'
        ),
    }
    write_atomic(out / 'recovery.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
