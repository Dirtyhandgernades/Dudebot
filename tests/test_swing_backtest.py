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

def test_fast_dump_score_uses_only_signal_history():
    _,bars=fixture();history=list(bars.values())[:22]
    history[-1]={**history[-1],'c':8,'h':9,'l':7,'v':200}
    assert dump_structure_score(history)>=80

def test_borrow_execution_is_reported_separately_from_detection():
    events=[{'ticker':'ABC','signal_date':'2025-01-02','planned_entry_date':'2025-01-03'},
            {'ticker':'XYZ','signal_date':'2025-01-02','planned_entry_date':'2025-01-03'}]
    observations=[{'subject':'ABC','observed_at':'2025-01-02T19:00:00+00:00','value':
        {'tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'}}]
    result=borrow_metrics(events,observations)
    assert result['detected']==2 and result['executable']==1 and result['unavailable']==1 and result['rejected']==0
