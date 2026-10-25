"""Fail-closed cached historical replay integrity audit.

Run: python -m backtest.obsidian_data_audit --source outputs/backtest/hybrid-37386241124
Exit code 2 on missing/corrupt/partial inputs. No network, orders, or Discord.
"""
import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

YEARS = (2023, 2024, 2025)
REQUIRED_PACKET_KEYS = ('config', 'sessions', 'raw', 'split', 'cohorts', 'firm_dates')


class ReplayDataError(RuntimeError):
    pass


def load_checked(source):
    source = Path(source)
    packet_path = source / 'firm-timing-inputs.json.gz'
    if not packet_path.is_file():
        raise ReplayDataError(f'MISSING_PACKET: {packet_path}')
    try:
        data = packet_path.read_bytes()
        packet = json.loads(gzip.decompress(data))
    except (OSError, ValueError, EOFError) as exc:
        raise ReplayDataError(f'CORRUPT_PACKET: {exc}') from exc
    if not isinstance(packet, dict):
        raise ReplayDataError('PACKET_NOT_OBJECT')
    missing = [k for k in REQUIRED_PACKET_KEYS if k not in packet]
    if missing:
        raise ReplayDataError(f'MISSING_PACKET_KEYS: {missing}')
    sessions = packet['sessions']
    if not isinstance(sessions, list) or sessions != sorted(set(sessions)):
        raise ReplayDataError('INVALID_SESSIONS_NOT_STRICTLY_ORDERED')
    report = {
        'packet_sha256': hashlib.sha256(data).hexdigest(),
        'packet_bytes': len(data),
        'session_count': len(sessions),
        'years': {},
        'warnings': [],
    }
    for year in YEARS:
        start, end = f'{year}-09-08', f'{year}-12-05'
        expected = [day for day in sessions if start <= day < end]
        if not expected:
            raise ReplayDataError(f'NO_SESSIONS: {year}')
        cohort = packet['cohorts'].get(start)
        if not isinstance(cohort, dict) or 'short' not in cohort:
            raise ReplayDataError(f'MISSING_COHORT: {start}')
        signal_path = source / f'{year}-hybrid-signals.json'
        audit_path = source / f'{year}-intraday-audit.json'
        for p in (signal_path, audit_path):
            if not p.is_file():
                raise ReplayDataError(f'MISSING_INPUT: {p}')
        try:
            signals = json.loads(signal_path.read_text(encoding='utf-8'))
            audit = json.loads(audit_path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise ReplayDataError(f'INVALID_INPUT: {year}: {exc}') from exc
        if not isinstance(signals, dict):
            raise ReplayDataError(f'INVALID_SIGNALS: {year}')
        missing_days = sorted(set(expected) - set(signals))
        if missing_days:
            raise ReplayDataError(f'MISSING_SCAN_DAYS: {year}: {missing_days[:12]} (total {len(missing_days)})')
        if not isinstance(audit, dict) or 'gaps' not in audit:
            raise ReplayDataError(f'MISSING_AUDIT_GAPS: {year}')
        missing_bars = Counter()
        events = 0
        for day in expected:
            rows = signals[day]
            if not isinstance(rows, list):
                raise ReplayDataError(f'INVALID_DAY_EVENTS: {day}')
            for event in rows:
                events += 1
                ticker = event.get('ticker') if isinstance(event, dict) else None
                if not ticker or not event.get('decision_at') or not event.get('data_cutoff'):
                    raise ReplayDataError(f'INVALID_EVENT: {day}: {event}')
                if not str(event['decision_at']).startswith(day):
                    raise ReplayDataError(f'DECISION_DATE_MISMATCH: {day}: {ticker}')
                if event['data_cutoff'] >= event['decision_at']:
                    raise ReplayDataError(f'FUTURE_DATA_CUTOFF: {day}: {ticker}')
                if not packet['raw'].get(ticker, {}).get(day):
                    missing_bars['raw_entry_day'] += 1
                if not packet['split'].get(ticker, {}).get(day):
                    missing_bars['split_entry_day'] += 1
        report['years'][str(year)] = {
            'expected_scan_days': len(expected),
            'observed_scan_days': len(expected),
            'candidate_events': events,
            'missing_event_day_bars': dict(missing_bars),
            'source_audit_gaps': audit['gaps'],
            'signal_sha256': hashlib.sha256(signal_path.read_bytes()).hexdigest(),
            'audit_sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        }
        if missing_bars:
            report['warnings'].append(f'{year}: event day bars missing {dict(missing_bars)}')
        if audit['gaps']:
            report['warnings'].append(f'{year}: upstream coverage gaps reported')
    return packet, report


def run(source, output):
    _, report = load_checked(source)
    report['status'] = 'PASS_WITH_COVERAGE_WARNINGS' if report['warnings'] else 'PASS'
    if output:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='outputs/backtest/hybrid-37386241124')
    parser.add_argument('--output', default='outputs/backtest/obsidian-data-audit.json')
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.source, args.output), indent=2))
    except ReplayDataError as exc:
        print(json.dumps({'status': 'FAIL', 'error': str(exc)}), file=sys.stderr)
        sys.exit(2)
