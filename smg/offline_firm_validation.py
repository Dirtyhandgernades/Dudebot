"""Reproduce firm-policy diagnostics from cached inputs, without API requests.

Reference lists are opened only after the simulations have finished and are
used for reporting overlap, never for selecting symbols or choosing rules.
"""
import argparse
import csv
import gzip
import json
from pathlib import Path
from .models import Config
from .swing_backtest import PERIODS, simulate


def rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--reference', default='backtest/reference_events.csv')
    parser.add_argument('--friend-transactions')
    args = parser.parse_args()
    data = json.loads(gzip.decompress(Path(args.inputs).read_bytes()))
    cfg = Config(**data['config'])
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    runs = []
    for start, end in PERIODS:
        for strategy, hold in [('LIVE_FIRM_TIMING_SHORT', 3),
                               ('LIVE_FIRM_TIMING_SHORT', 1),
                               ('ADAPTIVE_COLLAPSE_SHORT', 3)]:
            result = simulate(data['raw'], data['split'], data['cohorts'][start]['short'],
                              data['sessions'], start=start, end=end, hold=hold,
                              strategy=strategy, position_target=30000, buying_power=150000,
                              firm_dates=data['firm_dates'], firm_cfg=cfg)
            result.update(period_start=start, period_end=end)
            filename = f'{start}-{strategy}-hold-{hold}.json'
            (out / filename).write_text(json.dumps(result, indent=2), encoding='utf-8')
            runs.append(result)
    # Evaluation-only comparisons: none of these labels reach simulate().
    references = rows(args.reference)
    friends = rows(args.friend_transactions) if args.friend_transactions else []
    reference_tickers = {r['ticker'].upper() for r in references}
    friend_shorts = {r['ticker'].upper() for r in friends if r['transaction_type']=='SHORT SELL'}
    friend_longs = {r['ticker'].upper() for r in friends if r['transaction_type']=='BUY'}
    primary = next(r for r in runs if r['period_start']=='2025-09-08'
                   and r['strategy']=='LIVE_FIRM_TIMING_SHORT' and r['hold_sessions']==3)
    traded = {t['ticker'] for t in primary['trades']}
    cohort = set(data['cohorts']['2025-09-08']['short'])
    game_events = [r for r in references if '2025-09-08'<=r['event_date']<='2025-12-05']
    indices = {day:i for i,day in enumerate(data['sessions'])}
    prior_event_matches = []
    for event in game_events:
        event_index = indices.get(event['event_date'])
        if event_index is None:
            continue
        previous = [s for s in primary['signal_events']
                    if s['ticker']==event['ticker'] and s['signal_date'] in indices
                    and 1<=event_index-indices[s['signal_date']]<=5]
        if previous:
            prior_event_matches.append({**event, 'prior_signal_dates':sorted({s['signal_date'] for s in previous})})
    comparison = dict(
        comparison_only=True, selection_uses_reference_tickers=False,
        frozen_cohort_size=len(cohort), closed_unique_tickers=len(traded),
        reference_events_total=len(references), reference_events_in_game=len(game_events),
        reference_ticker_overlap=sorted(traded & reference_tickers),
        prior_1_to_5_session_event_matches=prior_event_matches,
        friend_short_tickers=len(friend_shorts), friend_short_overlap=sorted(traded & friend_shorts),
        friend_long_overlap=sorted(traded & friend_longs),
        friend_short_tickers_outside_frozen_cohort=sorted(friend_shorts-cohort),
        friend_short_tickers_in_cohort_without_closed_trade=sorted((friend_shorts & cohort)-traded),
    )
    (out/'list-comparison.json').write_text(json.dumps(comparison, indent=2), encoding='utf-8')
    fields=['ticker','side','signal_date','entry_date','exit_date','shares','entry_price',
            'notional','timing_trigger','dump_structure_score','pnl','return_pct','gross_return_pct',
            'friend_short_ticker_overlap','friend_long_ticker_overlap','reference_ticker_overlap',
            'historical_borrow_status']
    with (out/'2025-firm-trades.csv').open('w', newline='', encoding='utf-8') as handle:
        writer=csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for trade in primary['trades']:
            writer.writerow({**{k:trade[k] for k in fields if k in trade},
                             'friend_short_ticker_overlap':trade['ticker'] in friend_shorts,
                             'friend_long_ticker_overlap':trade['ticker'] in friend_longs,
                             'reference_ticker_overlap':trade['ticker'] in reference_tickers,
                             'historical_borrow_status':'UNAVAILABLE'})
    small=[{k:v for k,v in r.items() if k not in ('trades','signal_events','daily_equity','unresolved_positions')}
           for r in runs]
    (out/'results-summary.json').write_text(json.dumps(small, indent=2), encoding='utf-8')
    print(json.dumps({'results':[{k:r[k] for k in ('period_start','strategy','hold_sessions',
                       'net_profit','closed_trades','account_insolvent')} for r in runs],
                      'comparison':comparison}, indent=2))


if __name__=='__main__':
    main()
