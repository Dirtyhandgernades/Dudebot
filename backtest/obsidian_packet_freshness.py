"""Measure every packet row's actual source ages without granting execution."""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def audit(packet, observed_at):
    if observed_at.utcoffset() is None:
        raise ValueError('Aware observation time required')
    symbols = packet['requested_symbols']
    rows = packet['rows']
    if len(rows) != len(symbols) or {r['ticker'] for r in rows} != set(symbols) or len(set(symbols)) != len(symbols):
        raise ValueError('Incomplete or duplicate source roster')
    result = []
    counts = Counter()
    for row in rows:
        iex = row.get('iex', {})
        sip = row.get('sip', {})
        measurements = {}
        for key, value in (
            ('iex_trade', iex.get('trade', {}).get('source_timestamp')),
            ('iex_quote', iex.get('quote', {}).get('source_timestamp')),
            ('sip_bar_end', (sip.get('latest_completed_bar') or {}).get('bar_end')),
            ('sip_safe_asof', sip.get('safe_asof')),
        ):
            try:
                source = datetime.fromisoformat(value.replace('Z', '+00:00'))
                age = (observed_at-source).total_seconds()
                if source.utcoffset() is None or age < 0:
                    raise ValueError()
                measurements[key] = dict(source_at=source.isoformat(), age_seconds=age)
                counts[key+'_available'] += 1
            except (AttributeError, TypeError, ValueError):
                measurements[key] = dict(source_at=value, age_seconds=None)
                counts[key+'_unknown_or_future'] += 1
        counts['halt_'+row.get('halt', {}).get('status', 'UNKNOWN')] += 1
        result.append(dict(ticker=row['ticker'], measurements=measurements,
                           original_iex_status=iex.get('status'), original_sip_status=sip.get('status')))
    return dict(observed_at=observed_at.isoformat(), roster_count=len(rows), counts=dict(counts),
                rows=result, execution_freshness_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.packet.read_text()), datetime.now(timezone.utc))
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
