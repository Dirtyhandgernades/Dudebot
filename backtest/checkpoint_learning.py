"""Learn from matched delayed checkpoint candles, never future entry features."""
import argparse
import gzip
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np
from smg.action_learning import fit_policy, policy_scores
from smg.risk_model import feature_row, matured_before
from smg.exposure import POLICY
from smg.swing_backtest import simulate
from backtest.repair_study import held_issuer, independent_rows
from backtest.multiyear_study import YEARS, hold_outcome, consistency, timing_audit, write
from backtest.entry_failure_audit import OFFSETS, validate_event

CURRENT_FEATURES = ('change_from_prior_close', 'close_location', 'upper_wick',
                    'red_candle', 'below_prior_low', 'lower_high', 'failed_recent_high')


def checkpoint_x(packet, event, day):
    chart = event.get('observed_chart')
    if not isinstance(chart, dict) or any(k not in chart for k in CURRENT_FEATURES):
        return None
    if (any(type(chart[k]) not in (int, float) for k in CURRENT_FEATURES[:3]) or
            any(type(chart[k]) is not bool for k in CURRENT_FEATURES[3:])):
        return None
    i = packet['sessions'].index(day); series = packet['split'].get(event['ticker'], {})
    history = [series.get(d) for d in packet['sessions'][i-22:i]]
    if len(history) != 22 or not all(history):
        return None
    base = feature_row(history)
    if base is None:
        return None
    x = base + [float(chart[k]) for k in CURRENT_FEATURES]
    return x if all(np.isfinite(v) for v in x) else None


def issuer_before(packet, event):
    at = datetime.fromisoformat(event['decision_at']); ciks = set()
    for row in packet['records']:
        if row.get('ticker') != event['ticker'] or not row.get('cik'):
            continue
        stamp = datetime.fromisoformat(row['decision_at'].replace('Z', '+00:00'))
        if stamp <= at:
            ciks.add(str(int(row['cik'])))
    return next(iter(ciks)) if len(ciks) == 1 else None


def models_before(rows, packet, year):
    earlier = independent_rows([r for r in matured_before(rows, f'{year}-01-01', f'{year-2}-01-01') if not r['held_issuer']])
    models = {}; counts = {}
    for hold in (1, 2, 3):
        train = [{**r, **hold_outcome(r, packet, hold)} for r in earlier]
        models[hold] = fit_policy(train); counts[hold] = len(train)
    return models, counts


def eligible(score):
    return (all(np.isfinite(score[k]) for k in ('return_rank', 'profitability_rank', 'tail_loss_rank')) and
            score['return_rank'] > 0 and score['profitability_rank'] >= .5 and score['tail_loss_rank'] <= .25)


def run(packet, checkpoints, out):
    plan = {'id': 'matched-checkpoint-learning-2026-10-11-v1', 'years': list(YEARS),
            'offsets': list(OFFSETS), 'current_features': list(CURRENT_FEATURES),
            'prior_features': 'Seven completed daily price/volume features',
            'training': 'Same-offset earlier two-year matured signals; nonoverlapping issuer windows; held issuers excluded',
            'variants': ['MATCHED_NET_H1', 'MATCHED_NET_H2', 'MATCHED_NET_H3', 'MATCHED_NET_ADAPTIVE'],
            'selection': 'Prior expected net return>0, profitability rank>=.5, tail rank<=.25',
            'adaptive': 'Largest prior expected return minus .25*tail rank; tie favors shorter hold',
            'exposure': POLICY, 'provider_requests': 0, 'live_changed': False,
            'automatic_promotion': False, 'scores_are_probabilities': False}
    write(out/'experiment.json', plan); results = []; ledgers = []; model_counts = []
    for offset in OFFSETS:
        events_by_year = {}; samples = []; missing = 0
        for year in YEARS:
            source = checkpoints / str(offset) / f'{year}-PRECLOSE_ONLY-signals.json'
            if not source.exists(): continue
            events_by_year[year] = json.loads(source.read_text(encoding='utf-8'))
            for day, group in events_by_year[year].items():
                for event in group:
                    validate_event(event, day); x = checkpoint_x(packet, event, day)
                    if x is None: missing += 1; continue
                    cik = issuer_before(packet, event)
                    # Ambiguous historical identity is not a ticker-based independent issuer.
                    if cik is None: missing += 1; continue
                    row = {'ticker': event['ticker'], 'entry_date': day, 'signal_date': day,
                           'x': x, 'issuer_cik': cik, 'held_issuer': held_issuer(event['ticker'], cik)}
                    outcome = hold_outcome(row, packet, 3)
                    if outcome.get('policy_net_return') is not None:
                        samples.append({**row, **outcome})
        for year in YEARS:
            models, counts = models_before(samples, packet, year)
            model_counts.append({'year': year, 'offset': offset, 'independent_training_counts': counts,
                                 'unknown_feature_or_identity_events': missing})
            write(out/'models'/f'{year}-{offset}.json', {'models': models, 'counts': counts})
            events = events_by_year.get(year)
            for hold in (1, 2, 3, None):
                variant = f'MATCHED_NET_H{hold}_PRECLOSE_{offset}' if hold else f'MATCHED_NET_ADAPTIVE_PRECLOSE_{offset}'
                row = {'year': year, 'variant': variant, 'status': 'EVALUATED'}
                if events is None or not all(models.values()):
                    row['status'] = 'DATA_OR_TRAINING_UNAVAILABLE'; results.append(row); continue
                chosen = defaultdict(list); holds = {}; decisions = []
                for day, group in events.items():
                    for event in group:
                        x = checkpoint_x(packet, event, day)
                        if x is None or issuer_before(packet, event) is None: continue
                        scores = {n: policy_scores(m, [{'x': x}])[0] for n, m in models.items()}
                        kept = {n: score for n, score in scores.items() if eligible(score)}
                        selected = hold if hold else max(kept, key=lambda n: (kept[n]['return_rank']-.25*kept[n]['tail_loss_rank'], -n)) if kept else None
                        action = selected is not None and selected in kept
                        decisions.append({'ticker': event['ticker'], 'decision_at': event['decision_at'], 'scores': scores,
                                          'kept': action, 'hold': selected, 'confidence_is_uncalibrated': True})
                        if action:
                            chosen[day].append(event); holds[day+':'+event['ticker']] = selected
                symbols = sorted({e['ticker'] for group in chosen.values() for e in group})
                for case, bps, borrow in (('base', 30, .1), ('stress', 100, 1.)):
                    result = simulate(packet['raw'], packet['split'], symbols, packet['sessions'],
                        start=f'{year}-09-08', end=f'{year}-12-05', hold=hold or 3,
                        strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH', firm_dates=packet['first_dates'],
                        intraday_signals=chosen, signal_share_sizing=True, risk_controls=True,
                        position_target=50000, buying_power=150000, max_position_equity_fraction=POLICY['max_position_fraction'],
                        decision_price_buffer=1.2, smg_cash_interest=True, cost_bps=bps, borrow_rate=borrow,
                        exposure_policy=POLICY, research_hold_by_entry=holds)
                    write(out/'portfolios'/f'{year}-{variant}-{case}.json', result)
                    row[case] = {k: result[k] for k in ('net_profit', 'ending_balance', 'interest_pnl', 'closed_trades', 'max_observed_drawdown_pct', 'account_insolvent', 'gaps')}
                    ledgers.extend({**t, 'year': year, 'variant': variant, 'cost_case': case} for t in timing_audit(result, packet))
                write(out/'decisions'/f'{year}-{variant}.json', decisions); results.append(row)
        print(json.dumps({'stage': 'matched_candle_learning', 'offset': offset, 'sample_rows': len(samples)}), flush=True)
    write(out/'trade-ledger.json', ledgers)
    report = {'status': 'MATCHED_CHECKPOINT_RESEARCH_COMPLETE', 'experiment': plan, 'results': results,
              'consistency': consistency(results), 'training_coverage': model_counts, 'provider_requests': 0,
              'live_changed': False, 'automatic_promotion': False,
              'limits': ['Partial prior-ranked cohort; no full-market missed-dump denominator',
                        'Unknown historical borrow/cap/halts/game eligibility; conditional paper only',
                        'Early years lacking matched checkpoint training remain unavailable',
                        'Uncalibrated ranks; no confidence-based size increase',
                        'Inspected years are research diagnostics, not fresh validation']}
    write(out/'summary.json', report); return report


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--packet', required=True); parser.add_argument('--checkpoints', required=True)
    parser.add_argument('--out', default='reports/multiyear/checkpoint-learning'); args = parser.parse_args()
    packet = json.loads(gzip.decompress(Path(args.packet).read_bytes()))
    run(packet, Path(args.checkpoints), Path(args.out))


if __name__ == '__main__': main()
