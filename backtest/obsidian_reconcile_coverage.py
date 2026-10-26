"""Independent historical coverage reconciliation (research only).

Original audits generally record only aggregate missing split-window counts.
Usable provider bars cannot be called repaired gaps without per-window evidence.
No network, credentials, live alerts or orders.
"""
import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

YEARS = (2023, 2024, 2025)
STATUSES = {'RECOVERED', 'PROVIDER_EMPTY_OR_STALE', 'PROVIDER_ERROR_RETRYABLE'}


def expected_windows(packet, audits):
    sessions = packet['sessions']
    indices = {day: i for i, day in enumerate(sessions)}
    expected = {}
    for year in YEARS:
        for session in audits[year]['sessions']:
            day = session['day']
            i = indices[day]
            previous = sessions[i - 22:i] if i >= 22 else []
            found = 0
            if previous:
                for ticker, first in sorted(packet['firm_dates'].items()):
                    if first > day or ticker not in packet['raw']:
                        continue
                    raw = packet['raw'][ticker].get(previous[-1])
                    history = [packet['split'].get(ticker, {}).get(d) for d in previous]
                    if not raw or raw['c'] <= 3 or not all(history):
                        continue
                    if history[-1]['c'] / history[0]['c'] - 1 < 0:
                        continue
                    key = f'{day}|{ticker}'
                    if key in expected:
                        raise ValueError(f'DUPLICATE_EXPECTED_WINDOW: {key}')
                    expected[key] = year
                    found += 1
            if found != session['candidates']:
                raise ValueError(f'ORIGINAL_CANDIDATE_COUNT_MISMATCH: {day}: {found} != {session["candidates"]}')
    return expected


def run(source, recovery, output=None):
    source, recovery = Path(source), Path(recovery)
    packet_bytes = (source / 'firm-timing-inputs.json.gz').read_bytes()
    source_hash = hashlib.sha256(packet_bytes).hexdigest()
    packet = json.loads(gzip.decompress(packet_bytes))
    audits = {year: json.loads((source / f'{year}-intraday-audit.json').read_text()) for year in YEARS}
    checkpoint = json.loads((recovery / 'checkpoint.json').read_text())
    progress = json.loads((recovery / 'recovery.json').read_text())
    if checkpoint.get('source_sha256') != source_hash or progress.get('source_sha256') != source_hash:
        raise ValueError('SOURCE_PACKET_HASH_MISMATCH')
    expected = expected_windows(packet, audits)
    records = checkpoint['records']
    if set(records) - set(expected):
        raise ValueError(f'UNEXPECTED_CHECKPOINT_WINDOWS: {len(set(records) - set(expected))}')
    for key, record in records.items():
        day, ticker = key.split('|', 1)
        if (record.get('day'), record.get('ticker'), record.get('year')) != (day, ticker, expected[key]):
            raise ValueError(f'CHECKPOINT_RECORD_IDENTITY_MISMATCH: {key}')
        if record.get('status') not in STATUSES:
            raise ValueError(f'UNKNOWN_RECOVERY_STATUS: {key}')
    counts = Counter(row['status'] for row in records.values())
    remaining = len(expected) - len(records)
    if (progress['total_candidate_windows'] != len(expected)
            or progress['windows_checked_cumulative'] != len(records)
            or progress['remaining_unchecked'] != remaining
            or Counter(progress['counts']) != counts):
        raise ValueError('RECOVERY_REPORT_CHECKPOINT_MISMATCH')
    years = {}
    confirmed_repairs = 0
    original_gap_total = 0
    mapped_original_gap_total = 0
    for year in YEARS:
        keys = {key for key, yr in expected.items() if yr == year}
        checked = {key: records[key] for key in keys if key in records}
        by_status = Counter(row['status'] for row in checked.values())
        original_gaps = audits[year]['gaps'].get('MISSING_OR_STALE_SPLIT_WINDOW', 0)
        mapped = {
            f'{session["day"]}|{row["ticker"]}'
            for session in audits[year]['sessions']
            for row in session.get('candidate_audit', [])
            if row.get('status') == 'SPLIT_WINDOW_UNAVAILABLE'
        }
        if not mapped <= keys or len(mapped) > original_gaps:
            raise ValueError(f'ORIGINAL_GAP_MAPPING_INCONSISTENT: {year}')
        repaired = sum(checked[key]['status'] == 'RECOVERED' for key in mapped if key in checked)
        confirmed_repairs += repaired
        original_gap_total += original_gaps
        mapped_original_gap_total += len(mapped)
        unchecked = len(keys) - len(checked)
        years[str(year)] = {
            'original_aggregate_missing_split_windows': original_gaps,
            'original_gap_keys_identifiable': len(mapped),
            'confirmed_repairs_of_identifiable_original_gaps': repaired,
            'expected_candidate_windows': len(keys),
            'checked_windows': len(checked),
            'usable_provider_windows': by_status['RECOVERED'],
            'provider_empty_or_stale': by_status['PROVIDER_EMPTY_OR_STALE'],
            'provider_error_retryable': by_status['PROVIDER_ERROR_RETRYABLE'],
            'unchecked_windows': unchecked,
            'aggregate_missing_count_difference': by_status['PROVIDER_EMPTY_OR_STALE'] - original_gaps if not unchecked else None,
        }
    full = remaining == 0 and counts['PROVIDER_ERROR_RETRYABLE'] == 0
    report = {
        'status': 'AGGREGATE_RECONCILIATION_COMPLETE_IDENTITY_UNVERIFIED' if full and mapped_original_gap_total < original_gap_total
                  else 'RECONCILIATION_COMPLETE' if full else 'PROVISIONAL_COVERAGE_RECONCILIATION',
        'source_sha256': source_hash,
        'expected_candidate_windows': len(expected),
        'checked_windows': len(records),
        'unchecked_windows': remaining,
        'usable_provider_windows': counts['RECOVERED'],
        'provider_empty_or_stale': counts['PROVIDER_EMPTY_OR_STALE'],
        'provider_error_retryable': counts['PROVIDER_ERROR_RETRYABLE'],
        'original_aggregate_missing_split_windows': original_gap_total,
        'original_gap_keys_identifiable': mapped_original_gap_total,
        'original_gap_keys_unmapped': original_gap_total - mapped_original_gap_total,
        'confirmed_repairs_of_identifiable_original_gaps': confirmed_repairs,
        'years': years,
        'limitations': [
            'RECOVERED means the new provider query returned usable bars; it does not establish that the original replay lacked them.',
            'Original aggregate missing counts cannot be mapped to tickers without original candidate_audit rows.',
            'Matching aggregate missing counts do not prove that the same individual windows are missing.',
            'This is not a strategy backtest; profitability, borrow availability and fills remain unverified.',
        ],
    }
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + '.tmp')
        temp.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
        temp.replace(path)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', default='outputs/backtest/hybrid-37386241124')
    p.add_argument('--recovery', default='outputs/backtest/obsidian-recovery')
    p.add_argument('--output', default='outputs/backtest/obsidian-coverage-reconciliation.json')
    args = p.parse_args()
    print(json.dumps(run(args.source, args.recovery, args.output), indent=2))
