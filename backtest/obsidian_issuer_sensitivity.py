"""Leave one issuer out of the frozen diagnostic denominator at a time."""
import argparse
import hashlib
import json
from pathlib import Path


def rates(rows):
    events = [r for r in rows if r['outcomes']['3']['favorable'] >= .20 - 1e-10]
    hits = sum(r['selected']['baseline'] for r in events)
    alerts = sum(r['selected']['baseline'] for r in rows)
    return dict(hits=hits, alerts=alerts, events=len(events),
                event_issuers=len({r['ticker'] for r in events}),
                precision=hits / alerts if alerts else None,
                recall=hits / len(events) if events else None)


def summarize(records):
    rows = [r for r in records if r['outcomes']['3'] is not None]
    symbols = sorted({r['ticker'] for r in rows})
    omissions = [rates([r for r in rows if r['ticker'] != symbol]) for symbol in symbols]
    bounds = {}
    for metric in ('precision', 'recall'):
        values = [r[metric] for r in omissions if r[metric] is not None]
        bounds[metric] = dict(low=min(values, default=None), high=max(values, default=None),
                              undefined=len(symbols)-len(values))
    return dict(evaluable=len(rows), censored=len(records)-len(rows), issuers=len(symbols),
                full=rates(rows), omission_ranges=bounds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    data = parser.parse_args().source.read_bytes()
    manifest = Path('backtest/evidence/2026-11-21/iterations-016-018/metrics.json')
    if hashlib.sha256(data).hexdigest() != json.loads(manifest.read_text())['raw_result_sha256']:
        raise ValueError('Unexpected iteration 018 input')
    print(json.dumps({y:summarize(v['diagnostics']) for y,v in json.loads(data)['years'].items()},indent=2))
