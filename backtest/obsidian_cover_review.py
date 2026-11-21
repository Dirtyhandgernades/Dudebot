"""Monday desk diagnostic for discretionary short covers, using completed sessions."""
from collections import Counter
from datetime import date
import gzip
import hashlib
import json
from math import isfinite
from pathlib import Path


def review(reason, bars):
    if reason not in {'TIME_LIMIT', 'TAKE_PROFIT_SIGNAL_PREVIOUS_CLOSE'}:
        return 'PRESERVE_EXISTING_EXIT'
    if len(bars) != 3 or any(not b or any(type(b.get(k)) not in (int,float) or
            not isfinite(b[k]) or b[k] <= 0 for k in ('c','h')) or b['c'] > b['h'] for b in bars):
        return 'INSUFFICIENT_DATA'
    first, second, third = bars
    if all(first[k] > second[k] > third[k] for k in ('c','h')):
        return 'CONTINUATION_REVIEW'
    if all(first[k] < second[k] < third[k] for k in ('c','h')):
        return 'REVERSAL_REVIEW'
    return 'MIXED_EVIDENCE'


def run(target='CONTINUATION_REVIEW'):
    root = Path('outputs/backtest')
    source = root/'hybrid-37386241124/firm-timing-inputs.json.gz'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != 'e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb':
        raise ValueError('Source mismatch')
    with gzip.open(source) as handle:
        packet = json.load(handle)
    sessions = packet['sessions']
    results = []
    for year in (2023,2024,2025):
        for cost in ('base','stress'):
            ledger = root/f'target-rank-2026-10-05/{year}-top_half_30pct-50000-{cost}.json'
            baseline = json.loads(ledger.read_bytes())
            decisions = Counter()
            changes = []
            unknown = 0
            higher_cover = 0
            for trade in baseline['trades']:
                i = sessions.index(trade['exit_date'])
                series = packet['split'][trade['ticker']]
                decision = review(trade['exit_reason'], [series.get(d) for d in sessions[i-3:i]])
                decisions[decision] += 1
                if decision != target:
                    continue
                if i+1 >= len(sessions) or sessions[i+1] > f'{year}-12-05' or sessions[i+1] not in series:
                    unknown += 1
                    continue
                day, following = sessions[i:i+2]
                days = (date.fromisoformat(following)-date.fromisoformat(day)).days
                diff = (series[day]['c']-series[following]['c'])/trade['adjusted_entry']
                higher_cover += int(diff < 0)
                gain = trade['notional']*(diff*(1+baseline['cost_bps_each_way']/10000)
                                          - baseline['borrow_rate']*days/365)
                changes.append(gain)
            results.append(dict(year=year,cost=cost,original_profit=baseline['net_profit'],
                                ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),
                                decisions=dict(decisions),evaluated=len(changes),unknown=unknown,
                                higher_cover_price=higher_cover, worse_net=sum(x<0 for x in changes),
                                improved=sum(x>0 for x in changes),incremental_net_on_known=round(sum(changes),2),
                                worst_increment=round(min(changes),2) if changes else None))
    return dict(source_sha256=digest,paired_fixed_positions=results)


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=['CONTINUATION_REVIEW','REVERSAL_REVIEW'], default='CONTINUATION_REVIEW')
    print(json.dumps(run(parser.parse_args().group),indent=2))
