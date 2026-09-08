"""Historical replay and reference comparison. No delivery or live-state writes.

Input packets are point-in-time research records, never the reference labels.
This module deliberately cannot infer complete universe coverage from packets.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import date, datetime, time as daytime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from bs4 import BeautifulSoup

from .market import calculate, calendar, session_bounds
from .models import Candidate, Config, HaltCheck
from .providers import Alpaca
from .rules import EntityList, evaluate, market_confirmation, structural, years_ago
from .transport import Http

UTC = timezone.utc
START = date(2022, 7, 29)
END = date(2025, 7, 28)


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone-aware timestamp required')
    return result.astimezone(UTC)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    temp.replace(path)


def decision_time(day, cfg):
    zone = timezone(timedelta(hours=-8)) if cfg.notification_timezone == 'fixed_UTC_minus_08' else ZoneInfo('America/Los_Angeles')
    now = datetime.combine(day, daytime(12), zone).astimezone(UTC)
    bounds = session_bounds(day)
    # Match the production dispatch gate, including the closing instant.
    return now if bounds and bounds[0] <= now < bounds[1] + timedelta(minutes=5) else None


def prior_sessions(day, count):
    if count < 1 or count > 252:
        raise ValueError('Comparison window must be 1..252 sessions')
    return [s.date() for s in calendar(day.year).sessions_in_range(
        str(day - timedelta(days=count * 3 + 30)), str(day - timedelta(days=1)))][-count:]


def public_at(doc):
    if doc.get('accepted_at'):
        return stamp(doc['accepted_at'])
    # A date alone becomes usable at the NEXT calendar day's midnight New York.
    return datetime.combine(date.fromisoformat(doc['filed_at']) + timedelta(days=1),
                            daytime(), ZoneInfo('America/New_York')).astimezone(UTC)


def packet_errors(packet, candidate, now):
    errors = []
    mapping = packet.get('mapping', {})
    try:
        valid_mapping = (mapping['ticker'] == candidate.ticker and
            str(int(mapping['cik'])) == str(int(candidate.cik)) and
            mapping['exchange'] == candidate.exchange and
            date.fromisoformat(mapping['valid_from']) <= now.date() < date.fromisoformat(mapping['valid_to']) and
            stamp(mapping['known_at']) <= now and bool(mapping['source_url']) and
            bool(mapping['share_class']) and bool(mapping['original_listing_source']))
    except (KeyError, ValueError):
        valid_mapping = False
    if not valid_mapping:
        errors.append('UNVERIFIED_HISTORICAL_SYMBOL_CIK_SHARE_CLASS')
    docs = {d['url']: d for d in packet.get('documents', [])}
    evidence = list(candidate.evidence.values()) + [m.evidence for m in candidate.matches]
    for proof in evidence:
        doc = docs.get(proof.url)
        if not doc:
            errors.append('MISSING_SOURCE_DOCUMENT'); continue
        if public_at(doc) > now or date.fromisoformat(doc['filed_at']) != proof.filed_at:
            errors.append('FILING_NOT_PUBLIC_AT_DECISION')
        soup = BeautifulSoup(doc.get('raw_text', ''), 'html.parser')
        for element in soup(['script', 'style', 'ix:header']):
            element.decompose()
        normalized = ' '.join(soup.get_text(' ', strip=True).split())
        if (hashlib.sha256(doc.get('raw_text', '').encode()).hexdigest() != proof.document_sha256 or
                proof.quote not in normalized):
            errors.append('EVIDENCE_PROVENANCE_MISMATCH')
    # All context documents must also obey the cutoff, even if not quoted.
    if any(public_at(d) > now for d in docs.values()):
        errors.append('FUTURE_CONTEXT_DOCUMENT')
    if not packet.get('filing_review_source') or stamp(packet.get('filing_review_through', '1900-01-01T00:00:00Z')) != now:
        errors.append('INCOMPLETE_POINT_IN_TIME_FILING_REVIEW')
    if packet.get('corporate_actions_verified') is not True or not packet.get('corporate_action_source'):
        errors.append('CORPORATE_ACTION_REVIEW')
    return sorted(set(errors))


def historical_halt(packet, now):
    record = packet.get('halt', {})
    status = 'UNKNOWN'
    source = record.get('source_url', '')
    if record.get('status') in {'CLEAR', 'HALTED'} and source and record.get('historical_archive') is True:
        if stamp(record['from']) <= now < stamp(record['through']):
            status = record['status']
    return HaltCheck(checked_at=now, status=status, reason='Historical archive coverage; missing coverage remains UNKNOWN', source_url=source)


def replay_packet(packet, cfg, entities, market):
    now = stamp(packet['decision_at'])
    candidate = Candidate.model_validate(packet['candidate'])
    row = {'decision_at': now.isoformat(), 'ticker': candidate.ticker,
           'candidate_key': candidate.key, 'pipeline': candidate.pipeline,
           'status': 'DATA_GAP', 'reasons': [], 'input_sha256': fingerprint(packet)}
    if decision_time(now.date(), cfg) != now:
        row['reasons'] = ['OUTSIDE_PERMITTED_NOON_DECISION']; return row
    errors = packet_errors(packet, candidate, now)
    if errors:
        row['reasons'] = errors; return row
    if candidate.pipeline == 'DIRECT_OFFERING' and candidate.event_date < now.date() - timedelta(days=cfg.direct_offering_backfill_days):
        row.update(status='EXCLUDED', reasons=['DIRECT_OFFERING_OUTSIDE_BACKFILL']); return row
    halt = historical_halt(packet, now)
    structure = structural(candidate, cfg, entities, now)
    snapshot = None
    if structure.status == 'STRUCTURAL_MATCH' and halt.status != 'HALTED':
        effective = now - timedelta(minutes=cfg.market_data_delay_minutes)
        try:
            rows = market.bars(candidate.ticker, effective - timedelta(days=150), effective, asof=now.date())
            snapshot = calculate(rows, effective, cfg, 'https://data.alpaca.markets/v2/stocks/bars', candidate.ipo_date)
            snapshot.feed = cfg.market_feed
            snapshot.declared_delay_minutes = cfg.market_data_delay_minutes
        except Exception as exc:
            row['reasons'] = ['MARKET_DATA_UNAVAILABLE:' + type(exc).__name__]; return row
    result = evaluate(candidate, cfg, entities, now, snapshot, halt)
    row.update(status=result.status, reasons=result.reasons, evaluation=result.model_dump(mode='json'))
    if halt.status == 'UNKNOWN' and structure.status == 'STRUCTURAL_MATCH':
        # No fabricated CLEAR record. Reuse just the production market rules.
        diagnostic = market_confirmation(structure, cfg, now, snapshot)
        row['other_criteria_status'] = diagnostic.status
        row['other_criteria_reasons'] = diagnostic.reasons
        if diagnostic.status == 'QUALIFIED':
            row['status'] = 'MATCH_EXCEPT_UNKNOWN_HALT'
    return row


def compare(events, decisions, lookback=20):
    output = []
    matched_alerts = set()
    for event in events:
        day = date.fromisoformat(event['event_date'])
        window = set(prior_sessions(day, lookback))
        relevant = [(i, r) for i, r in enumerate(decisions) if r['ticker'] == event['ticker'] and stamp(r['decision_at']).date() in window]
        hits = [(i, r) for i, r in relevant if r['status'] == 'QUALIFIED']
        hits.sort(key=lambda pair: pair[1]['decision_at'])
        tentative = [r for _, r in relevant if r['status'] == 'MATCH_EXCEPT_UNKNOWN_HALT']
        same_day = [r for r in decisions if r['ticker'] == event['ticker'] and stamp(r['decision_at']).date() == day and r['status'] == 'QUALIFIED']
        first = hits[0][1] if hits else None
        matched_alerts.update(i for i, _ in hits)
        reasons = sorted({reason for _, r in relevant for reason in r['reasons']})
        state = 'DETECTED_PRIOR' if hits else 'UNVERIFIED_HALT_MATCH' if tentative else 'SAME_DAY_TIMING_UNKNOWN' if same_day else 'NOT_EVALUABLE'
        if not hits:
            reasons.append('HISTORICAL_UNIVERSE_COVERAGE_NOT_ESTABLISHED')
        if not relevant:
            reasons.append('NO_REPLAY_RECORDS_IN_LOOKBACK')
        # A five-letter event symbol is a rule conflict, NOT proof of its earlier name.
        output.append(dict(event, result=state,
            first_prior_alert=first['decision_at'] if first else '',
            lead_calendar_days=(day - stamp(first['decision_at']).date()).days if first else '',
            lead_trading_sessions=len([d for d in window if d >= stamp(first['decision_at']).date()]) if first else '',
            pipeline=first['pipeline'] if first else '', prior_alert_count=len(hits),
            same_day_alert_count=len(same_day), halt_unverified_match_count=len(tentative),
            evaluated_candidate_decisions=len(relevant),
            event_symbol_exclusion='FIVE_LETTER_TICKER' if re.fullmatch('[A-Z]{5}', event['ticker']) else '',
            reasons=';'.join(sorted(set(reasons))),
            evidence_json=json.dumps(first.get('evaluation', {}) if first else {}, sort_keys=True)))
    extras = [r for i, r in enumerate(decisions) if r['status'] == 'QUALIFIED' and i not in matched_alerts]
    return output, extras


class CachedMarket:
    """Atomic caches keyed by all request parameters; failed calls aren't cached."""
    def __init__(self, market, folder):
        self.market, self.folder = market, folder

    def bars(self, ticker, start, end, *, asof):
        from .models import Bar
        query = dict(ticker=ticker, start=start.isoformat(), end=end.isoformat(), asof=str(asof),
                     feed=self.market.feed, adjustment='split', timeframe='1Min')
        path = self.folder / (fingerprint(query) + '.json')
        if path.exists():
            payload = json.loads(path.read_text())
            if payload['query'] != query:
                raise ValueError('Cache query mismatch')
            return [Bar.model_validate(b) for b in payload['bars']]
        rows = self.market.bars(ticker, start, end, asof=asof)
        write_json(path, dict(query=query, retrieved_at=datetime.now(UTC).isoformat(), bars=[r.model_dump(mode='json') for r in rows]))
        return rows


def collect_indexes(state, start, end, max_quarters=2):
    """Independent SEC leads, including delisted issuers; no current ticker filter.

    Leads are not candidates: mapping, original terms and context review remain
    required. Index completion must never be equated with screening coverage.
    """
    agent = os.environ.get('SEC_USER_AGENT', '')
    if '@' not in agent:
        return {'status': 'NOT_RUN', 'reason': 'SEC_USER_AGENT_NOT_CONFIGURED'}
    state.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(state / 'indexes.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS quarters (period TEXT PRIMARY KEY, source TEXT, sha256 TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS leads (path TEXT PRIMARY KEY, cik TEXT, name TEXT, form TEXT, filed_at TEXT)')
    http = Http(); completed = 0; periods = []
    # Older IPOs plus pre-window context; indexed independently of labels.
    since = years_ago(start, 3) - timedelta(days=150)
    for year in range(since.year, end.year + 1):
        for quarter in range(1, 5):
            first = date(year, 3 * quarter - 2, 1)
            last = date(year + (quarter == 4), 1 if quarter == 4 else quarter * 3 + 1, 1) - timedelta(days=1)
            if first <= end and last >= since:
                periods.append((year, quarter))
    try:
        for year, quarter in periods:
            period = f'{year}Q{quarter}'
            if db.execute('SELECT 1 FROM quarters WHERE period=?', (period,)).fetchone():
                continue
            if completed >= max_quarters:
                break
            url = f'https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx'
            raw = http.text(url, headers={'User-Agent': agent})
            if 'CIK|Company Name|Form Type|Date Filed|Filename' not in raw:
                raise ValueError('INVALID_SEC_INDEX')
            with db:
                for line in raw.splitlines():
                    parts = line.split('|')
                    if len(parts) != 5 or not parts[0].isdigit():
                        continue
                    cik, name, form, filed_at, path = parts
                    if form in {'424B3', '424B4', '424B5', '8-K', '6-K', '10-K', '20-F'} and str(since) <= filed_at <= str(end):
                        db.execute('INSERT OR IGNORE INTO leads VALUES (?,?,?,?,?)', (path, cik, name, form, filed_at))
                db.execute('INSERT INTO quarters VALUES (?,?,?)', (period, url, hashlib.sha256(raw.encode()).hexdigest()))
            completed += 1
        return {'status': 'INDEX_COLLECTION_ONLY', 'quarters_done': db.execute('SELECT count(*) FROM quarters').fetchone()[0],
                'quarters_expected': len(periods), 'leads': db.execute('SELECT count(*) FROM leads').fetchone()[0],
                'screened_candidates': None, 'universe_complete': False}
    finally:
        db.close()


def probe_market(cfg):
    """One-minute historical SIP access check, not a strategy replay."""
    if not all(os.environ.get(k) for k in ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY']):
        return {'status':'NOT_RUN', 'reason':'ALPACA_CREDENTIALS_NOT_CONFIGURED'}
    market = Alpaca(Http(), os.environ['ALPACA_API_KEY'], os.environ['ALPACA_SECRET_KEY'], cfg.market_feed, cfg.market_data_delay_minutes)
    start = datetime(2024, 1, 3, 19, 43, tzinfo=UTC)
    try:
        bars = market.bars('AAPL', start, start, asof=start.date())
        return {'status':'ACCESS_VERIFIED' if bars else 'EMPTY_RESPONSE', 'symbol':'AAPL',
                'time':start.isoformat(), 'bar_count':len(bars), 'feed':cfg.market_feed,
                'purpose':'Authentication and historical access only; not a screening result'}
    except Exception as exc:
        return {'status':'FAILED', 'error_type':type(exc).__name__, 'http_status':getattr(exc,'status',None)}


def audit_reference_market(events, cfg, state, budget=250):
    """Targeted data-availability audit, wholly separate from screening.

    Five minutes before the last eligible prior noon are sampled. This cannot
    establish RVOL, a 21-session return, full history, or a strategy detection.
    """
    records = []
    configured = all(os.environ.get(k) for k in ['ALPACA_API_KEY','ALPACA_SECRET_KEY'])
    market = Alpaca(Http(),os.environ.get('ALPACA_API_KEY',''),os.environ.get('ALPACA_SECRET_KEY',''),cfg.market_feed,cfg.market_data_delay_minutes)
    cache = state / 'reference-market-samples'
    started = time.monotonic(); calls = 0; access_failed = False
    for event in events:
        day = date.fromisoformat(event['event_date'])
        eligible = [decision_time(d,cfg) for d in prior_sessions(day,20)]
        now = next((t for t in reversed(eligible) if t is not None),None)
        record = dict(event_id=event['event_id'],ticker=event['ticker'],event_date=event['event_date'],
                      status='NOT_SAMPLED',sample_end='',bar_count=None,source_url='https://data.alpaca.markets/v2/stocks/bars')
        if now:
            cutoff = now-timedelta(minutes=cfg.market_data_delay_minutes)
            query = dict(ticker=event['ticker'],asof=str(now.date()),start=(cutoff-timedelta(minutes=5)).isoformat(),
                         end=(cutoff-timedelta(minutes=1)).isoformat(),feed=cfg.market_feed,adjustment='split')
            path = cache / (fingerprint(query)+'.json')
            result = json.loads(path.read_text()) if path.exists() else None
            if result is None and configured and not access_failed and calls<budget and time.monotonic()-started<300:
                try:
                    bars = market.bars(event['ticker'],stamp(query['start']),stamp(query['end']),asof=now.date())
                    result = dict(status='BARS_AVAILABLE_IN_SAMPLE' if bars else 'NO_BARS_IN_SAMPLED_INTERVAL',
                                  sample_end=query['end'],bar_count=len(bars),query=query)
                    write_json(path,result)
                except Exception as exc:
                    result = dict(status='PROVIDER_ERROR',error_type=type(exc).__name__,http_status=getattr(exc,'status',None))
                    access_failed = getattr(exc,'status',None) in {401,403,429}
                calls+=1
            if result:
                record.update(result)
        records.append(record)
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['audit', 'collect-indexes', 'replay'])
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--start', type=date.fromisoformat, default=START)
    parser.add_argument('--end', type=date.fromisoformat, default=END)
    parser.add_argument('--lookback', type=int, default=20)
    parser.add_argument('--packets', type=Path)
    parser.add_argument('--output', type=Path, default=Path('backtest/reports'))
    parser.add_argument('--max-records', type=int, default=25)
    parser.add_argument('--max-quarters', type=int, default=2)
    args = parser.parse_args(argv)
    if args.start > args.end or not 1 <= args.max_records <= 1000 or not 1 <= args.max_quarters <= 32 or not 1 <= args.lookback <= 252:
        parser.error('Invalid window or run budget')
    cfg_raw = yaml.safe_load((args.root / 'config/strategy.yaml').read_text())
    if os.environ.get('SURGE_RETURN_MIN_PCT', '').strip():
        cfg_raw['surge_return_min_pct'] = os.environ['SURGE_RETURN_MIN_PCT']
    cfg = Config.model_validate(cfg_raw)
    entries = yaml.safe_load((args.root / 'config/entities.yaml').read_text())
    reference = args.root / 'backtest/reference_events.csv'
    with reference.open(newline='', encoding='utf-8-sig') as stream:
        events = list(csv.DictReader(stream))
    if any(not args.start <= date.fromisoformat(e['event_date']) <= args.end for e in events):
        parser.error('Replay window must contain every reference event')
    state = args.root / 'backtest/runtime' / fingerprint({'start':str(args.start),'end':str(args.end)})[:16]
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    secrets = {key: bool(os.environ.get(key, '').strip()) for key in ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'SEC_USER_AGENT']}
    packets = []
    if args.packets:
        packets = [json.loads(line) for line in args.packets.read_text(encoding='utf-8').splitlines() if line.strip()]
    run_key = fingerprint({'cfg':cfg.model_dump(),'entities':entries,'packets':packets,'engine':Path(__file__).read_text(),
                           'rules':Path(__file__).with_name('rules.py').read_text(),'market':Path(__file__).with_name('market.py').read_text(),
                           'providers':Path(__file__).with_name('providers.py').read_text()})
    checkpoint = state / ('replay-' + run_key + '.json')
    decisions = json.loads(checkpoint.read_text()) if args.command == 'replay' and checkpoint.exists() else []
    # Retry provider failures on resume; preserve deterministic research gaps.
    decisions = [r for r in decisions if not any(x.startswith('MARKET_DATA_UNAVAILABLE:') for x in r['reasons'])]
    issues = ['HISTORICAL_UNIVERSE_AND_FILING_COVERAGE_NOT_ESTABLISHED', 'REFERENCE_DROP_TIMES_NOT_SUPPLIED']
    if cfg.surge_return_min_pct is None:
        issues.append('IPO_SURGE_THRESHOLD_NOT_SET')
    collection = None
    provider_access = None
    source_audit = None
    market_samples = []
    if args.command == 'collect-indexes':
        provider_access = probe_market(cfg)
        try:
            collection = collect_indexes(state, args.start, args.end, args.max_quarters)
        except Exception as exc:
            collection = {'status': 'INCOMPLETE', 'reason': type(exc).__name__}
        from .historical_discovery import audit_filings
        source_audit, research = audit_filings(state,args.start,args.end,entries)
        write_json(out / 'filing_research.json', research)
        market_samples = audit_reference_market(events,cfg,state)
        write_json(out / 'reference_market_samples.json',market_samples)
    if args.command == 'replay' and packets and secrets['ALPACA_API_KEY'] and secrets['ALPACA_SECRET_KEY']:
        market = CachedMarket(Alpaca(Http(), os.environ['ALPACA_API_KEY'], os.environ['ALPACA_SECRET_KEY'], cfg.market_feed, cfg.market_data_delay_minutes), state / 'bars')
        done = {r['input_sha256'] for r in decisions}; count = 0; started = time.monotonic()
        for packet in packets:
            if fingerprint(packet) in done:
                continue
            if not args.start <= stamp(packet['decision_at']).date() <= args.end:
                raise ValueError('Packet outside declared replay window')
            if count >= args.max_records or time.monotonic() - started > 480:
                break
            result = replay_packet(packet, cfg, EntityList(entries), market)
            decisions.append(result); done.add(result['input_sha256']); count += 1
            write_json(checkpoint, decisions)
    if not packets:
        issues.append('NO_POINT_IN_TIME_RESEARCH_PACKETS')
    for key, present in secrets.items():
        if not present:
            issues.append(key + '_NOT_CONFIGURED_LOCALLY')
    comparison, extras = compare(events, decisions, args.lookback)
    samples_by_event = {r['event_id']:r for r in market_samples}
    for row in comparison:
        sample = samples_by_event.get(row['event_id'],{})
        row['market_sample_status'] = sample.get('status','NOT_SAMPLED')
        row['market_sample_end'] = sample.get('sample_end','')
        row['market_sample_bar_count'] = sample.get('bar_count','')
    with (out / 'event_comparison.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparison[0])); writer.writeheader(); writer.writerows(comparison)
    write_json(out / 'decisions.json', decisions)
    write_json(out / 'extra_alerts.json', extras)
    hits = [r for r in comparison if r['result'] == 'DETECTED_PRIOR']
    summary = {'status': 'INCOMPLETE' if decisions else 'NOT_RUN', 'start':str(args.start),'end':str(args.end),
        'reference_events':len(events),'reference_symbols':len({e['ticker'] for e in events}),
        'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(), 'config':cfg.model_dump(),
        'lookback_trading_sessions':args.lookback, 'universe_complete':False,
        'evaluated_candidate_decisions':len(decisions), 'packets_supplied':len(packets),
        'actual_detected_events':len(hits) if decisions else None,
        'actual_detected_symbols':len({r['ticker'] for r in hits}) if decisions else None,
        'actual_misses':None, 'detection_rate':None,
        'comparison_counts':dict(Counter(r['result'] for r in comparison)),
        'extra_alert_records':len(extras) if decisions else None,
        'repeat_alert_records':sum(max(0, n - 1) for n in Counter(r['candidate_key'] for r in decisions if r['status']=='QUALIFIED').values()) if decisions else None,
        'event_symbol_rule_conflicts':sum(bool(r['event_symbol_exclusion']) for r in comparison),
        'issues':issues,'local_credentials_present':secrets,'index_collection':collection,'provider_access':provider_access,'source_audit':source_audit,
        'reference_market_sample_counts':dict(Counter(r['status'] for r in market_samples)),'run_key':run_key}
    write_json(out / 'summary.json', summary)
    print(json.dumps({k:summary[k] for k in ['status','reference_events','reference_symbols','evaluated_candidate_decisions','actual_detected_events','actual_misses','issues','provider_access','index_collection','source_audit','reference_market_sample_counts']}))
    return 2 if summary['status'] == 'NOT_RUN' else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('Backtest error: ' + type(exc).__name__, file=sys.stderr)
        sys.exit(1)
