"""Bounded April-June historical training candles, separate from game tests."""
import argparse
import gzip
import json
from pathlib import Path
from backtest.balanced_checkpoints import SymbolBars
from backtest.intraday_checkpoint_study import run
from backtest.multiyear_study import write


class PairedWarmupBars:
    """Finish individual raw/split pairs; don't stall an entire year's batch."""
    def __init__(self, base, period_budget=None):
        self.base = base; self.period_budget = period_budget; self.pairs = {}; self.gaps = {}

    @property
    def requests(self): return self.base.requests

    def get(self, symbols, start, end, mode):
        key = (start.isoformat(), end.isoformat())
        if key not in self.pairs:
            self.pairs[key] = {}; missing = []
            period_ceiling = min(self.base.provider.max_requests, self.requests+self.period_budget) if self.period_budget is not None else self.base.provider.max_requests
            for ticker in sorted(symbols):
                limit = self.base.provider.max_requests
                # Partial pairs remain unknown, while completed single-symbol
                # pages survive for the next equally budgeted daily pass.
                self.base.provider.max_requests = min(limit, period_ceiling)
                try:
                    raw = self.base.get([ticker], start, end, 'raw')
                    split = self.base.get([ticker], start, end, 'split')
                except RuntimeError as exc:
                    if str(exc) != 'REQUEST_BUDGET': raise
                    missing.append(ticker)
                else:
                    self.pairs[key][ticker] = {'raw': raw.get(ticker, []), 'split': split.get(ticker, [])}
                finally:
                    self.base.provider.max_requests = limit
            self.gaps[start.date().isoformat()] = {'unavailable_symbol_pairs': len(missing), 'symbols': missing,
                                                   'reason': 'BUDGET_OR_INCOMPLETE_CACHE_NOT_NO_SETUP'}
        return {ticker: rows[mode] for ticker, rows in self.pairs[key].items()}


def collect(packet, out, budget):
    if not 0 <= budget <= 100: raise ValueError('Warmup request budget must be within0–100')
    client = PairedWarmupBars(SymbolBars('backtest/runtime/multiyear-warmup-minutes', max_requests=budget),
                             period_budget=max(2,budget//7))
    rows = []
    for offset in (15, 5):
        report = run(packet, client, out/str(offset), train_window_years=2,
                     years=tuple(range(2018, 2025)), policies=['PRECLOSE_ONLY'],
                     preclose_offset_minutes=offset, season_start='04-01', season_end='06-30')
        rows.append(report)
    result = {'status': 'BOUNDED_OFFSEASON_TRAINING_COLLECTION', 'period': ['04-01', '06-30'],
              'years': list(range(2018, 2025)), 'request_budget': budget, 'provider_requests': client.requests,
              'new_page_quota_per_year': max(2,budget//7),
              'reports': rows, 'training_only': True, 'live_changed': False,
              'intraday_symbol_coverage_gaps': client.gaps,
              'limits': ['Budget-limited periods stay unavailable; no empty cache invented',
                         'Same dated firm discovery and prior-year candidate rank as game study',
                         'Spring data never scored as fall-season profit; labels mature before test year',
                         'Incomplete source/price/borrow/eligibility coverage remains unknown']}
    write(out/'collection.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--packet', required=True)
    parser.add_argument('--out', default='reports/multiyear/warmup'); parser.add_argument('--max-requests', type=int, default=20)
    args = parser.parse_args(); packet = json.loads(gzip.decompress(Path(args.packet).read_bytes()))
    report = collect(packet, Path(args.out), args.max_requests)
    print(json.dumps({'status': report['status'], 'provider_requests': report['provider_requests']}))


if __name__ == '__main__': main()
