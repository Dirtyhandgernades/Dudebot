from datetime import date,timedelta
import pytest
from smg.swing_backtest import PERIODS,borrow_metrics,dump_structure_score,frozen_cohort,signal,simulate

def test_walk_forward_periods_are_fixed_before_outcomes():
    assert PERIODS == [('2023-09-08','2023-12-05'),('2024-09-08','2024-12-05'),('2025-09-08','2025-12-05')]

def fixture():
    days=[str(date(2025,1,1)+timedelta(days=i)) for i in range(30)]
    bars={day:dict(c=10,h=10.1,l=9.9,v=100) for day in days}
    return days,bars

def test_cohort_never_uses_future_record_or_price_outcome():
    rows=[dict(cik='1',ticker='ABC',decision_at='2025-07-28T19:00:00Z',reasons=['VERIFIED_LISTED_FIRM_RELATIONSHIP'],firm_and_price_match=False),
          dict(cik='1',ticker='FUTR',decision_at='2025-09-09T19:00:00Z',reasons=['VERIFIED_LISTED_FIRM_RELATIONSHIP'])]
    assert frozen_cohort(rows)==['ABC']

def test_short_accounting_charges_both_sides_and_borrow():
    days,bars=fixture();bars[days[23]]={**bars[days[23]],'c':8}
    result=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],hold=1)
    assert result['closed_trades']==0  # No failure signal on constant prior prices.
    result=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],hold=1,strategy='FIRM_BASELINE_SHORT')
    expected=2000-30-24-10-10000*.1/365
    assert result['net_profit']==pytest.approx(expected,abs=.01)
    assert result['trades'][0]['signal_date']==days[21]
    assert result['trades'][0]['entry_date']==days[22]
    assert result['gross_20pct_winners']==1

def test_smg_cash_interest_applies_daily_positive_and_negative_rates():
    days,bars=fixture()
    bars[days[23]]={**bars[days[23]],'c':8}
    positive=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],hold=1,
                       strategy='PUMP_FAILURE_SHORT',smg_cash_interest=True)
    assert positive['interest_pnl']==pytest.approx(100000*.0075/365,abs=.01)
    leveraged=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],hold=1,
                        strategy='FIRM_BASELINE_SHORT',smg_cash_interest=True,buying_power=150000,
                        position_target=150000,signal_share_sizing=False)
    assert leveraged['interest_pnl']<0
    assert leveraged['negative_cash_rate']==pytest.approx(.07)

def test_missing_exit_cannot_become_a_winning_survivor_or_zero_loss():
    days,bars=fixture();del bars[days[23]]
    result=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],hold=1,strategy='FIRM_BASELINE_SHORT')
    assert result['ending_balance'] is None
    assert result['unresolved_open_positions']==1 and result['closed_trades']==0

def test_split_is_not_a_short_windfall_and_raw_gate_is_used():
    days,bars=fixture();raw={d:dict(b) for d,b in bars.items()}
    raw[days[23]]['c']=5  # Adjusted series stays flat across a 2:1 split.
    result=simulate({'ABC':raw},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],hold=1,strategy='FIRM_BASELINE_SHORT')
    assert result['trades'][0]['gross_return_pct']==0 and result['net_profit']<0
    raw[days[21]]['c']=3
    assert simulate({'ABC':raw},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],strategy='FIRM_BASELINE_SHORT')['closed_trades']==0

def test_future_fill_bar_cannot_create_a_signal_and_capital_is_not_reused():
    days,bars=fixture();bars[days[22]]={**bars[days[22]],'c':20,'h':20,'v':10000}
    result=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[23],strategy='BREAKOUT_LONG')
    assert result['closed_trades']==0
    _,flat=fixture();symbols=[f'S{i:02}' for i in range(20)]
    result=simulate({s:flat for s in symbols},{s:flat for s in symbols},symbols,days,start=days[22],end=days[25],hold=7,strategy='FIRM_BASELINE_SHORT')
    assert result['closed_trades']==10
    assert sum(t['notional']+t['entry_fee'] for t in result['trades'])<=100000

def test_breakout_needs_price_and_volume_confirmation():
    _,bars=fixture();history=list(bars.values())[:22]
    assert signal(history)==['FIRM_BASELINE_SHORT']
    history[-1]={**history[-1],'c':11,'h':11,'v':250}
    assert 'BREAKOUT_LONG' in signal(history)

def test_rapid_pump_failure_requires_stronger_pump_and_breakdown():
    _,bars=fixture();history=list(bars.values())[:22]
    history[-1]={**history[-1],'c':8,'h':9,'l':7,'v':200}
    assert 'RAPID_PUMP_FAILURE_SHORT' not in signal(history)
    for i,b in enumerate(history[:-1]):b['c']=6+i*.25;b['h']=b['c']+.1;b['l']=b['c']-.1
    history[-1]={**history[-1],'c':8,'h':8.5,'l':7,'v':200}
    assert 'RAPID_PUMP_FAILURE_SHORT' in signal(history)

def test_combined_collapse_requires_multiple_confirmations():
    _, bars = fixture()
    history = list(bars.values())[:22]
    for i, bar in enumerate(history[:-1]):
        bar['c'] = 6 + i * .12
        bar['h'] = bar['c'] + .1
        bar['l'] = bar['c'] - .1
    history[-1] = {**history[-1], 'c': 7.5, 'h': 7.7, 'l': 6.8, 'v': 200}
    assert 'COMBINED_COLLAPSE_SHORT' in signal(history)

def test_fast_dump_score_uses_only_signal_history():
    _,bars=fixture();history=list(bars.values())[:22]
    history[-1]={**history[-1],'c':8,'h':9,'l':7,'v':200}
    assert dump_structure_score(history)>=80

def test_revised_live_policy_uses_prior_signal_and_dated_firm_evidence():
    from smg.models import Config
    days,bars=fixture()
    for day in days[21:]:bars[day]=dict(c=8,h=8.1,l=7.9,v=200)
    bars[days[25]]=dict(c=6,h=6.1,l=5.9,v=200)
    args=dict(start=days[22],end=days[25],hold=3,strategy='LIVE_FIRM_TIMING_SHORT',
              firm_cfg=Config(surge_return_min_pct=12),firm_dates={'ABC':days[21]})
    result=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,**args)
    assert result['closed_trades']==1
    assert result['trades'][0]['entry_date']==days[22]
    assert result['trades'][0]['exit_date']==days[25]
    assert result['trades'][0]['timing_trigger']=='FIRM_BREAKDOWN_SHORT'
    assert result['borrow_execution']['unavailable']==1
    args['firm_dates']={'ABC':days[23]}
    assert simulate({'ABC':bars},{'ABC':bars},['ABC'],days,**args)['closed_trades']==0
    args['firm_dates']={'ABC':days[21]};bars[days[21]]['v']=70
    assert simulate({'ABC':bars},{'ABC':bars},['ABC'],days,**args)['closed_trades']==0

def test_live_policy_cannot_run_without_public_firm_evidence():
    days,bars=fixture()
    with pytest.raises(ValueError):
        simulate({'ABC':bars},{'ABC':bars},['ABC'],days,strategy='LIVE_FIRM_TIMING_SHORT')

def test_documented_rename_preserves_true_return_across_adjustment_units():
    from smg.swing_backtest import stitch_rename
    change=dict(old_symbol='OLD',new_symbol='NEW',effective_date='2025-10-10',
                published_at='2025-10-09T12:00:00Z',action='rename_only')
    data={'raw':{'OLD':{'2025-10-09':dict(c=10)},'NEW':{'2025-10-10':dict(c=8)}},
          'split':{'OLD':{'2025-10-09':dict(c=10)},'NEW':{'2025-10-10':dict(c=1)}}}
    assert stitch_rename(data,change)['status']=='STITCHED_RENAME'
    assert data['split']['OLD']['2025-10-10']['c']==8
    assert data['raw']['OLD']['2025-10-10']['c']==8
    assert '2025-10-09' not in data['raw']['NEW']
    with pytest.raises(ValueError):stitch_rename(data,{**change,'action':'merger'})

@pytest.mark.parametrize('missing',[True,False])
def test_missing_marks_or_insolvency_cannot_finance_new_entries(missing):
    from smg.models import Config
    days,a=fixture();b={d:dict(v) for d,v in a.items()}
    for day in days[21:]:a[day]=dict(c=8,h=8.1,l=7.9,v=200)
    for day in days[22:]:b[day]=dict(c=8,h=8.1,l=7.9,v=200)
    if missing:del a[days[23]]
    else:
        for day in days[23:]:a[day]=dict(c=80,h=80.1,l=79.9,v=200)
    result=simulate({'ABC':a,'XYZ':b},{'ABC':a,'XYZ':b},['ABC','XYZ'],days,
        start=days[22],end=days[25],hold=3,strategy='LIVE_FIRM_TIMING_SHORT',
        position_target=30000,buying_power=150000,firm_cfg=Config(surge_return_min_pct=12),
        firm_dates={'ABC':days[21],'XYZ':days[22]})
    assert {t['ticker'] for t in result['trades']}=={'ABC'}
    reason='NEW_ENTRY_BLOCKED_UNVALUED_CAPITAL' if missing else 'NEW_ENTRY_BLOCKED_NONPOSITIVE_EQUITY'
    assert result['gaps'][reason]>=1
    assert result['account_insolvent'] is (not missing)
    if not missing:
        assert result['financial_status']=='ACCOUNT_INSOLVENT_MARGIN_RULES_UNMODELED'

def test_borrow_execution_is_reported_separately_from_detection():
    events=[{'ticker':'ABC','signal_date':'2025-01-02','planned_entry_date':'2025-01-03'},
            {'ticker':'XYZ','signal_date':'2025-01-02','planned_entry_date':'2025-01-03'}]
    observations=[{'subject':'ABC','observed_at':'2025-01-03T19:00:00+00:00','value':
        {'tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'}}]
    result=borrow_metrics(events,observations)
    assert result['detected']==2 and result['executable']==1 and result['unavailable']==1 and result['rejected']==0


def test_stop_is_next_close_and_does_not_fabricate_a_stop_price():
    days,bars=fixture()
    bars[days[23]]={**bars[days[23]],'c':12}
    bars[days[24]]={**bars[days[24]],'c':20}
    result=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[25],hold=3,
                    strategy='FIRM_BASELINE_SHORT',risk_controls=True,signal_share_sizing=True)
    trade=result['trades'][0]
    assert trade['exit_date']==days[24]
    assert trade['exit_reason']=='STOP_SIGNAL_PREVIOUS_CLOSE'
    assert trade['gross_return_pct']==-100


def test_share_quantity_does_not_know_the_future_fill_price():
    days,bars=fixture();raw={d:dict(b) for d,b in bars.items()}
    args=dict(start=days[22],end=days[23],hold=1,strategy='FIRM_BASELINE_SHORT',
              position_target=15000,buying_power=150000,signal_share_sizing=True)
    first=simulate({'ABC':raw},{'ABC':raw},['ABC'],days,**args)['trades'][0]
    raw[days[22]]['c']=15
    second=simulate({'ABC':raw},{'ABC':raw},['ABC'],days,**args)['trades'][0]
    assert first['shares']==second['shares']==1500
    assert second['notional']==22500


def test_exhaustion_research_requires_a_pump_and_upper_wick():
    from smg.swing_backtest import firm_exhaustion_trigger
    from smg.models import Config
    _,bars=fixture();history=list(bars.values())[:22]
    history[-1]=dict(o=12,c=12,h=13,l=11,v=200)
    assert firm_exhaustion_trigger(history,Config(surge_return_min_pct=12))=='FIRM_EXHAUSTION_RESEARCH'
    history[-1]['o']=13
    assert firm_exhaustion_trigger(history,Config(surge_return_min_pct=12)) is None

def test_borrow_evidence_after_entry_close_and_provider_errors_are_unavailable():
    events=[{'ticker':'ABC','signal_date':'2025-01-02','planned_entry_date':'2025-01-03'}]
    late={'subject':'ABC','observed_at':'2025-01-03T22:00:00+00:00','value':
          {'tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'}}
    failed={'subject':'ABC','observed_at':'2025-01-03T19:00:00+00:00','value':
            {'status':'UNAVAILABLE','error_type':'ProviderError'}}
    assert borrow_metrics(events,[late])['unavailable']==1
    assert borrow_metrics(events,[failed])['unavailable']==1
    hard={**failed,'value':{'status':'CURRENT','tradable':True,'shortable':True,'borrow_status':'hard_to_borrow'}}
    assert borrow_metrics(events,[hard])['rejected']==1

def test_firm_watch_lead_report_starts_after_public_firm_evidence():
    from smg.risk_model import firm_watch_lead_report
    days,bars=fixture();bars[days[24]]={**bars[days[24]],'c':7}
    records=[{'ticker':'ABC','decision_at':days[23]+'T12:00:00Z',
              'reasons':['VERIFIED_LISTED_FIRM_RELATIONSHIP']}]
    result=firm_watch_lead_report(records,{'ABC':bars},{'ABC':bars},days,
        [(days[22],days[24])],{days[22]:{'short':['ABC']}})['periods'][0]
    assert result['firm_watch_days']==2
    assert result['five_session_drop_windows']==1
    assert result['timing_trigger_days']==0
    assert result['distinct_drop_events']==1
    assert result['events_previously_on_firm_watch']==1
    assert result['events_with_prior_timing_trigger']==0
    assert result['event_rows'][0]['firm_watch_lead_sessions']==1
