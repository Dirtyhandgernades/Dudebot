"""Cached entry/exit attribution and fixed confirmation tests; no live writes.

Future closes diagnose a trade only after simulation. They never choose an
entry, exit horizon, filter, or size. All filters and failures are retained.
"""
import argparse
import gzip
import hashlib
import json
import math
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from smg.entry_features import confirmed
from smg.exposure import POLICY
from smg.market import session_bounds
from smg.swing_backtest import simulate
from backtest.multiyear_study import YEARS, consistency, timing_audit, write

POLICIES = ('BASELINE', 'NO_CONTINUING_PUMP', 'OBSERVED_CONFIRMATION',
            'PRIOR_LOW_BREAK', 'FAILED_HIGH_REJECTION')
OFFSETS = (15, 5)


def keep(event, policy):
    if policy not in POLICIES:
        raise ValueError('Unknown frozen confirmation policy')
    if policy == 'BASELINE':
        return True
    chart = event.get('observed_chart')
    if not isinstance(chart, dict):
        return False
    numbers = ('change_from_prior_close', 'close_location', 'upper_wick')
    if any(type(chart.get(k)) not in (int, float) or not math.isfinite(chart[k]) for k in numbers):
        return False
    if not 0 <= chart['close_location'] <= 1 or not 0 <= chart['upper_wick'] <= 1:
        return False
    if any(type(chart.get(k)) is not bool for k in ('below_prior_low', 'red_candle', 'failed_recent_high')):
        return False
    if policy == 'NO_CONTINUING_PUMP':
        return chart['change_from_prior_close'] <= 0
    if policy == 'OBSERVED_CONFIRMATION':
        return confirmed(chart)
    if policy == 'PRIOR_LOW_BREAK':
        return chart['below_prior_low']
    return (chart['failed_recent_high'] and chart['red_candle'] and
            chart['close_location'] <= .35 and chart['upper_wick'] >= .35 and
            chart['change_from_prior_close'] <= .02)


def validate_event(event, day):
    at = datetime.fromisoformat(event['decision_at'])
    cutoff = datetime.fromisoformat(event['data_cutoff'])
    complete = datetime.fromisoformat(event['last_complete_at'])
    bounds = session_bounds(date.fromisoformat(day))
    if (not all(s.tzinfo is not None for s in (at, cutoff, complete)) or
            not bounds or not bounds[0] <= at < bounds[1] or
            at - cutoff < timedelta(minutes=16) or
            not bounds[0] < complete <= cutoff or
            cutoff - complete > timedelta(minutes=5)):
        raise ValueError('Invalid preclose or delayed-data timestamps')


def future_diagnostic(trade, event, packet):
    """Retrospective attribution, explicitly excluded from entry selection."""
    days = packet['sessions']; i = days.index(trade['entry_date'])
    series = packet['split'].get(trade['ticker'], {})
    base = series.get(trade['entry_date'], {}).get('c')
    future = days[i+1:i+11]
    available = [d for d in future if d in series]
    known3 = bool(base and len(future) >= 3 and all(d in series for d in future[:3]))
    known10 = bool(base and len(future) == 10 and len(available) == 10)
    first = next((d for d in available if series[d]['c'] / base <= .8 + 1e-10), None) if base else None
    first_n = days.index(first) - i if first else None
    if not known3:
        category = 'THREE_SESSION_PRICE_WINDOW_UNKNOWN'
    elif first_n is not None and first_n <= 3:
        category = 'DROP_HIT_POLICY_LOSS' if trade['pnl'] <= 0 else 'DROP_HIT_POLICY_PROFIT'
    elif not known10:
        category = 'NO_THREE_SESSION_DROP_LATER_WINDOW_UNKNOWN'
    elif first_n is not None:
        category = 'DROP_OUTSIDE_THREE_SESSION_HORIZON'
    else:
        category = 'NO_20PCT_LOWER_CLOSE_WITHIN_TEN_SESSIONS'
    exits = {}
    if base:
        for n, d in enumerate(future[:3], 1):
            if d not in series:
                exits[str(n)] = None
                continue
            ratio = series[d]['c'] / base
            elapsed = (date.fromisoformat(d) - date.fromisoformat(trade['entry_date'])).days
            exits[str(n)] = trade['notional'] * (1-ratio) - trade['entry_fee'] - trade['notional']*ratio*.003 - 5 - trade['notional']*.1*elapsed/365
    quote = event.get('decision_price')
    return {'ticker': trade['ticker'], 'entry_date': trade['entry_date'],
            'exit_date': trade['exit_date'], 'pnl': trade['pnl'], 'notional': trade['notional'],
            'decision_at': event.get('decision_at'), 'source_policy': event.get('source_policy'),
            'observed_chart': event.get('observed_chart'), 'category': category,
            'first_20pct_lower_close': first, 'sessions_to_first_20pct_lower_close': first_n,
            'three_session_prices_known': known3, 'ten_session_prices_known': known10,
            'closing_fill_vs_decision_quote_pct': 100*(trade['entry_price']/quote-1) if quote else None,
            'fixed_exit_counterfactual_pnl': exits,
            'counterfactual_is_not_portfolio_or_entry_rule': True,
            'maximum_adverse_closing_move_first3_pct': max(0, max((100*(series[d]['c']/base-1) for d in future[:3] if d in series), default=0)) if base else None}


def legacy_audit(folder):
    path = folder / '2025-09-08-LIVE_FIRM_TIMING_SHORT-primary.json'
    if not path.exists():
        return {'status': 'LEGACY_ARTIFACT_UNAVAILABLE'}
    data = json.loads(path.read_text(encoding='utf-8'))
    return {'status': 'ARCHIVED_LEGACY_SIMULATION', 'artifact': str(path),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'net_profit': data['net_profit'], 'ending_balance': data['ending_balance'],
            'hold_sessions_per_trade': data.get('hold_sessions'), 'closed_trades': data['closed_trades'],
            'entry_dates': [min(t['entry_date'] for t in data['trades']), max(t['entry_date'] for t in data['trades'])],
            'largest_losses': sorted(data['trades'], key=lambda t: t['pnl'])[:5],
            'interpretation': 'Season simulation with individual three-session holds; not one three-session account loss or a live executed account. Legacy price/identity assumptions are not re-certified here.'}


def run(packet, checkpoints, out, legacy=None):
    plan = {'id': 'firm-entry-failure-2026-10-11-v1', 'years': list(YEARS),
            'offsets_before_close_minutes': list(OFFSETS), 'policies': list(POLICIES),
            'holds': [1, 2, 3], 'allocation': POLICY, 'live_changed': False,
            'provider_requests': 0, 'hindsight_in_selection': False,
            'longs': 'REVIEW_ONLY; cannot infer a long from a losing short',
            'input_sha256': hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()}
    write(out/'experiment.json', plan)
    results = []; ledgers = []; diagnostics = []; source_counts = []
    if legacy:
        write(out/'legacy-loss-audit.json', legacy_audit(legacy))
    for offset in OFFSETS:
        for year in YEARS:
            source = checkpoints / str(offset) / f'{year}-PRECLOSE_ONLY-signals.json'
            if source.exists():
                events = json.loads(source.read_text(encoding='utf-8'))
                for day, group in events.items():
                    for event in group:
                        validate_event(event, day)
            else:
                events = None
            source_counts.append({'year': year, 'offset': offset,
                                  'status': 'AVAILABLE' if events is not None else 'UNKNOWN',
                                  'sha256': hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else None,
                                  'events': sum(map(len, events.values())) if events is not None else None})
            for policy in POLICIES:
                chosen = {day: [e for e in group if keep(e, policy)] for day, group in events.items()} if events is not None else None
                for hold in (1, 2, 3):
                    name = f'{policy}_H{hold}_PRECLOSE_{offset}'
                    row = {'year': year, 'variant': name, 'status': 'EVALUATED' if chosen is not None else 'DATA_OR_TRAINING_UNAVAILABLE'}
                    if chosen is None:
                        results.append(row); continue
                    symbols = sorted({e['ticker'] for group in chosen.values() for e in group})
                    for case, bps, borrow in (('base', 30, .1), ('stress', 100, 1.)):
                        result = simulate(packet['raw'], packet['split'], symbols, packet['sessions'],
                            start=f'{year}-09-08', end=f'{year}-12-05', hold=hold,
                            strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH', firm_dates=packet['first_dates'],
                            intraday_signals=chosen, signal_share_sizing=True, risk_controls=True,
                            position_target=50000, buying_power=150000,
                            max_position_equity_fraction=POLICY['max_position_fraction'],
                            decision_price_buffer=1.2, smg_cash_interest=True,
                            cost_bps=bps, borrow_rate=borrow, exposure_policy=POLICY)
                        write(out/'portfolios'/f'{year}-{name}-{case}.json', result)
                        row[case] = {k: result[k] for k in ('net_profit', 'ending_balance', 'interest_pnl', 'closed_trades', 'max_observed_drawdown_pct', 'account_insolvent', 'gaps')}
                        ledgers.extend({**t, 'year': year, 'variant': name, 'cost_case': case} for t in timing_audit(result, packet))
                        if policy == 'BASELINE' and hold == 3 and case == 'base':
                            lookup = {(d, e['ticker']): e for d, group in events.items() for e in group}
                            diagnostics.extend({**future_diagnostic(t, lookup[(t['entry_date'], t['ticker'])], packet), 'year': year, 'offset': offset} for t in result['trades'])
                    results.append(row)
        print(json.dumps({'stage': 'confirmation_complete', 'offset': offset, 'portfolios': len(results)*2}), flush=True)
    write(out/'trade-ledger.json', ledgers)
    write(out/'entry-exit-attribution.json', diagnostics)
    report = {'status': 'FIXED_CONFIRMATION_RESEARCH_COMPLETE', 'experiment': plan,
              'results': results, 'consistency': consistency(results), 'source_counts': source_counts,
              'baseline_attribution_counts': dict(Counter(t['category'] for t in diagnostics)),
              'holding_overruns': sum(t['holding_policy_overrun'] for t in ledgers),
              'provider_requests': 0, 'live_changed': False, 'automatic_promotion': False,
              'limits': ['Prior-ranked partial firm universe; cannot measure full-market missed dumps',
                         'Historical borrow/cap/halts/SMG eligibility remain unknown; conditional paper profits',
                         'Future closes and hypothetical fixed exits are attribution only, never selection',
                         'Both timing controls are retained; no retrospective best exit per trade',
                         'No20pctlowerclose within10sessions is not proof the company never dumps or is legitimate',
                         'Inspected years are not untouched holdouts; prospective validation required']}
    write(out/'summary.json', report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--checkpoints', required=True)
    parser.add_argument('--out', default='reports/multiyear/entry-audit')
    parser.add_argument('--legacy')
    args = parser.parse_args()
    packet = json.loads(gzip.decompress(Path(args.packet).read_bytes()))
    report = run(packet, Path(args.checkpoints), Path(args.out), Path(args.legacy) if args.legacy else None)
    print(json.dumps({'status': report['status'], 'passing_consistency': sum(c['passed_all_years'] for c in report['consistency'].values()), 'holding_overruns': report['holding_overruns']}))


if __name__ == '__main__':
    main()
