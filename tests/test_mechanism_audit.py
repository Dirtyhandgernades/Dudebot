from datetime import date,datetime,timedelta,timezone
from collections import defaultdict
from smg.market import calendar
from smg.mechanism_audit import patterns,audit,news_before,roles_before


def test_price_family_has_no_future_inputs_and_broad_watch_is_not_entry():
    bars=[{'o':10,'c':10,'h':10.1,'l':9.9,'v':100} for _ in range(22)]
    bars[-1]={'o':14,'c':14,'h':14.1,'l':13.9,'v':50}
    before=patterns(bars)
    assert before==['RAMP_WATCH_NO_VOLUME_GATE']
    all_bars=bars+[{'o':1,'c':1,'h':1,'l':1,'v':10000}]
    assert patterns(all_bars[:22])==before


def test_news_revision_after_signal_cannot_be_used_as_prior_evidence():
    rows=[{'created_at':'2025-11-06T12:00:00Z','updated_at':'2025-11-07T12:00:00Z','headline':'later revised'},
          {'created_at':'2025-11-06T12:00:00Z','updated_at':'2025-11-06T13:00:00Z','headline':'known'}]
    assert [r['headline'] for r in news_before(rows,'2025-11-06')]==['known']


def test_documented_former_auditor_is_not_current_before_publication():
    rows=defaultdict(list,DTCK=[{'ticker':'DTCK','decision_at':'2023-01-01T00:00:00Z','source_url':'fixture',
        'firm_matches':[{'name':'OneStop Assurance PAC','role':'auditor','relationship':'current'}]}])
    assert roles_before(rows,'DTCK','2024-08-29')[0]['relationship_at_source']=='current'
    assert roles_before(rows,'DTCK','2025-11-06')[0]['relationship_at_source'].startswith('FORMER_PARTY_DOCUMENTED')


def test_audit_reference_roster_cannot_select_an_independent_warning():
    days=[str(s.date()) for s in calendar(2025).sessions_in_range('2025-08-01','2025-10-01')]
    bars={d:{'o':10,'c':10,'h':10.1,'l':9.9,'v':100} for d in days}
    bars[days[22]]={'o':14,'c':14,'h':17,'l':13,'v':400}
    result=audit({'raw':{'AUDT':bars},'split':{'AUDT':bars}},days,['AUDT'],set(),{'AUDT':days[0]},[],{},days[21],days[-1])
    assert all(r['warning_days']==0 for r in result['pattern_comparison'])


def test_longer_ramp_watch_needs_observed_history_and_does_not_call_a_dump_date():
    from smg.mechanism_audit import longer_ramp_watch
    history=[{'c':10+i*.1} for i in range(63)]
    assert longer_ramp_watch(history)
    assert not longer_ramp_watch(history[:30])
    history[-1]={'c':5}
    assert not longer_ramp_watch(history)


def test_verified_late_notice_cannot_backfill_new_symbol_into_the_game():
    import json
    from pathlib import Path
    from datetime import datetime
    change=json.loads((Path(__file__).resolve().parents[1]/'backtest/issuer_lineage.json').read_text())['changes'][0]
    assert change['old_symbol']=='MCTR' and change['new_symbol']=='TJGC'
    assert change['effective_date']>'2025-12-05'
    assert datetime.fromisoformat(change['published_at'].replace('Z','+00:00')).date().isoformat()>change['effective_date']
