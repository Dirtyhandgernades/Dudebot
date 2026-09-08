"""Synthetic software tests only. No historical detections are asserted."""
import csv
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from smg.backtest import (compare, decision_time, historical_halt, main,
                          packet_errors, prior_sessions, public_at, replay_packet)
from smg.demo import candidate, snapshot, NOW
from smg.models import Bar, Config, HaltCheck
from smg.market import session_bounds
from smg.providers import Alpaca
from smg.rules import EntityList, evaluate

UTC = timezone.utc
ENTITIES = EntityList(yaml.safe_load(Path('config/entities.yaml').read_text()))


def packet():
    c = candidate()
    raw = 'Synthetic test source document with sufficient provenance text.'
    sha = hashlib.sha256(raw.encode()).hexdigest()
    for e in list(c.evidence.values()) + [m.evidence for m in c.matches]:
        e.document_sha256 = sha
        e.quote = raw
    now = NOW.replace(second=0)
    c.reviewed_at = now
    return dict(decision_at=now.isoformat(), candidate=c.model_dump(mode='json'),
        documents=[dict(url=c.matches[0].evidence.url, filed_at='2026-07-15', raw_text=raw)],
        mapping=dict(ticker=c.ticker, cik=c.cik, exchange=c.exchange,
            valid_from='2026-07-15', valid_to='2027-01-01', known_at='2026-07-15T10:00:00Z',
            source_url='https://example.com/synthetic-mapping', share_class='ordinary', original_listing_source='synthetic'),
        filing_review_source='synthetic index', filing_review_through=now.isoformat(),
        corporate_actions_verified=True, corporate_action_source='synthetic action archive')


class Market:
    def bars(self, ticker, start, end, *, asof):
        self.asof = asof
        self.end = end
        rows = []
        for day in prior_sessions(end.date(), 60):
            if day < date(2026, 7, 15):
                continue
            opening, closing = session_bounds(day)
            rows.extend([Bar(start=opening, close=10, high=10, low=10, volume=100),
                         Bar(start=closing-timedelta(minutes=1), close=10, high=10, low=10, volume=10)])
        rows.append(Bar(start=end-timedelta(minutes=1), close=20, high=20, low=20, volume=300))
        # A future partial minute must not affect the result.
        rows.append(Bar(start=end, close=999, high=999, low=999, volume=999999))
        return rows


def record(day, status='QUALIFIED', ticker='ABCD'):
    return dict(decision_at=day+'T20:00:00+00:00', ticker=ticker, status=status,
                pipeline='RECENT_IPO', candidate_key='ipo', reasons=[])


def test_noon_fixed_pst_and_delay():
    p = packet(); market = Market()
    result = replay_packet(p, Config(surge_return_min_pct=12), ENTITIES, market)
    assert market.end.hour == 19 and market.end.minute == 44
    assert market.asof == date(2026, 9, 8)
    assert result['status'] == 'MATCH_EXCEPT_UNKNOWN_HALT'
    assert result['evaluation']['halt']['status'] == 'UNKNOWN'


@pytest.mark.parametrize('day', [date(2024, 7, 4), date(2024, 11, 29)])
def test_holiday_and_early_close_have_no_noon_decision(day):
    assert decision_time(day, Config()) is None


def test_winter_and_summer_fixed_clock():
    assert decision_time(date(2024, 1, 3), Config()).hour == 20
    assert decision_time(date(2024, 7, 3), Config()) is None
    assert decision_time(date(2024, 7, 5), Config()).hour == 20


def test_date_only_availability_is_next_day_new_york():
    assert public_at({'filed_at':'2024-07-05'}) == datetime(2024, 7, 6, 4, tzinfo=UTC)
    assert public_at({'filed_at':'2024-01-03'}) == datetime(2024, 1, 4, 5, tzinfo=UTC)


def test_future_acceptance_and_context_block():
    from smg.models import Candidate
    p = packet(); p['documents'][0]['accepted_at'] = '2026-09-09T00:00:00Z'
    errors = packet_errors(p, Candidate.model_validate(p['candidate']), NOW)
    assert 'FILING_NOT_PUBLIC_AT_DECISION' in errors
    assert 'FUTURE_CONTEXT_DOCUMENT' in errors


def test_changed_symbol_cannot_borrow_current_mapping():
    from smg.models import Candidate
    p = packet(); p['mapping']['valid_from'] = '2026-09-09'
    assert 'UNVERIFIED_HISTORICAL_SYMBOL_CIK_SHARE_CLASS' in packet_errors(p, Candidate.model_validate(p['candidate']), NOW)


def test_delisted_mapping_ends_exclusively():
    from smg.models import Candidate
    p = packet(); p['mapping']['valid_to'] = '2026-09-08'
    assert 'UNVERIFIED_HISTORICAL_SYMBOL_CIK_SHARE_CLASS' in packet_errors(p, Candidate.model_validate(p['candidate']), NOW)


def test_unknown_action_status_suppresses_qualification():
    p = packet(); p['corporate_actions_verified'] = False
    r = replay_packet(p, Config(), ENTITIES, Market())
    assert r['status'] == 'DATA_GAP' and 'CORPORATE_ACTION_REVIEW' in r['reasons']


def test_halt_archive_must_cover_decision():
    p = packet(); p['halt'] = dict(status='CLEAR', historical_archive=True,
        source_url='https://example.com/archive', **{'from':'2026-09-08T19:00:00Z','through':'2026-09-08T20:00:00Z'})
    assert historical_halt(p, NOW.replace(second=0)).status == 'UNKNOWN'


def test_past_current_rss_is_not_historical_clear():
    p = packet(); p['halt'] = dict(status='CLEAR', source_url='https://nasdaqtrader.com/rss')
    assert historical_halt(p, NOW).status == 'UNKNOWN'


def test_same_day_and_after_drop_never_advance_detection():
    events = [dict(event_id='a', ticker='ABCD', event_date='2024-02-05')]
    rows, extra = compare(events, [record('2024-02-05'), record('2024-02-06')])
    assert rows[0]['result'] == 'SAME_DAY_TIMING_UNKNOWN'
    assert rows[0]['first_prior_alert'] == '' and len(extra) == 2


def test_repeated_events_and_20_session_boundary():
    events = [dict(event_id='a', ticker='ABCD', event_date='2024-02-05'),
              dict(event_id='b', ticker='ABCD', event_date='2024-02-06')]
    first = prior_sessions(date(2024, 2, 5), 20)[0]
    rows, _ = compare(events, [record(str(first))])
    assert rows[0]['result'] == 'DETECTED_PRIOR'
    assert rows[0]['lead_trading_sessions'] == 20
    assert rows[1]['result'] == 'NOT_EVALUABLE'


def test_unknown_halts_and_missing_records_are_not_hits_or_misses():
    events = [dict(event_id='a', ticker='ABCD', event_date='2024-02-05')]
    assert compare(events, [record('2024-02-02', 'MATCH_EXCEPT_UNKNOWN_HALT')])[0][0]['result'] == 'UNVERIFIED_HALT_MATCH'
    assert compare(events, [])[0][0]['result'] == 'NOT_EVALUABLE'


def test_drop_labels_cannot_change_comparison():
    a = dict(event_id='a', ticker='ABCD', event_date='2024-02-05', reported_drop_pct='-99')
    b = dict(a, reported_drop_pct='-1')
    left = compare([a], [record('2024-02-02')])[0][0]
    right = compare([b], [record('2024-02-02')])[0][0]
    left.pop('reported_drop_pct'); right.pop('reported_drop_pct')
    assert left == right


def test_asof_and_split_adjustment_sent_to_alpaca():
    class HTTP:
        def json(self, url, **kwargs):
            assert kwargs['params']['asof'] == '2024-01-03'
            assert kwargs['params']['adjustment'] == 'split'
            assert kwargs['params']['feed'] == 'sip'
            return {'bars':{}}
    market = Alpaca(HTTP(), 'fake', 'fake')
    market.bars('OLD', NOW-timedelta(days=150), NOW, asof=date(2024, 1, 3))


@pytest.mark.parametrize('gain,qualified,low', [(11.99,False,False),(12,True,True),(17.5,True,True),(20,True,True),(23,True,True),(23.01,True,False),(25,True,False)])
def test_user_surge_band_boundaries(gain, qualified, low):
    cfg = Config(surge_return_min_pct=12, ipo_low_priority_surge_max_pct=23)
    snap = snapshot(); snap.monthly_return = gain
    halt = HaltCheck(checked_at=NOW, status='CLEAR', reason='test', source_url='https://example.com')
    result = evaluate(candidate(), cfg, ENTITIES, NOW, snap, halt)
    assert (result.status == 'QUALIFIED') == qualified
    assert ('LOW_PRIORITY_MONTHLY_SURGE' in result.reasons) == low


def test_audit_reports_null_detection_counts(tmp_path, monkeypatch):
    for key in ['ALPACA_API_KEY','ALPACA_SECRET_KEY','SEC_USER_AGENT','SURGE_RETURN_MIN_PCT']:
        monkeypatch.delenv(key, raising=False)
    assert main(['audit','--output',str(tmp_path)]) == 2
    summary = json.loads((tmp_path/'summary.json').read_text())
    assert summary['reference_events'] == 230 and summary['reference_symbols'] == 137
    assert summary['actual_detected_events'] is None and summary['actual_misses'] is None
    with (tmp_path/'event_comparison.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 230 and all(r['result'] == 'NOT_EVALUABLE' for r in rows)


def test_independent_filing_audit_resumes_without_current_universe(tmp_path, monkeypatch):
    import sqlite3
    from smg.historical_discovery import audit_filings
    db = sqlite3.connect(tmp_path/'indexes.sqlite')
    db.execute('CREATE TABLE leads (path TEXT PRIMARY KEY, cik TEXT, name TEXT, form TEXT, filed_at TEXT)')
    db.execute('INSERT INTO leads VALUES (?,?,?,?,?)',('edgar/data/1/test.txt','1','Historical Delisted Issuer','424B4','2024-01-03'))
    db.commit(); db.close()
    monkeypatch.setenv('SEC_USER_AGENT','test test@example.com')
    calls=[]
    def fetch(self,url,**kwargs):
        calls.append(url)
        return '<html><body>This document has no recognized transaction.</body></html>'
    monkeypatch.setattr('smg.historical_discovery.Http.text',fetch)
    first, records = audit_filings(tmp_path,date(2022,7,29),date(2025,7,28),{})
    second, again = audit_filings(tmp_path,date(2022,7,29),date(2025,7,28),{})
    assert len(calls)==1 and records==again
    assert first['pipelines']['RECENT_IPO']['audited_filings']==1
    assert second['downloaded_this_run']==0
    assert records[0]['status']=='NO_TRANSACTION_RECOGNIZED_BY_PARSER'
    assert second['screening_detections'] is None


def test_reference_market_samples_are_prior_delayed_and_cached(tmp_path,monkeypatch):
    from smg.backtest import audit_reference_market
    monkeypatch.setenv('ALPACA_API_KEY','fake'); monkeypatch.setenv('ALPACA_SECRET_KEY','fake')
    calls=[]
    def bars(self,ticker,start,end,*,asof):
        calls.append((ticker,start,end,asof))
        return []
    monkeypatch.setattr('smg.backtest.Alpaca.bars',bars)
    events=[dict(event_id='one',ticker='OLD',event_date='2024-02-05',reported_drop_pct='-99')]
    first=audit_reference_market(events,Config(),tmp_path)
    second=audit_reference_market(events,Config(),tmp_path)
    assert first==second and len(calls)==1
    assert calls[0][3]==date(2024,2,2)
    assert calls[0][1]==datetime(2024,2,2,19,39,tzinfo=UTC)
    assert calls[0][2]==datetime(2024,2,2,19,43,tzinfo=UTC)
    assert first[0]['status']=='NO_BARS_IN_SAMPLED_INTERVAL'
    assert 'reported_drop_pct' not in json.dumps(first)
