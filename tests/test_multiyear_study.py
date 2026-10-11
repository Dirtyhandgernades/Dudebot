from datetime import date
import pytest
from smg.market import calendar
from smg.swing_backtest import simulate
from smg.intraday_replay import decision_window,STRATEGY
from backtest.multiyear_study import hold_outcome,allocation,consistency,YEARS,full_sessions


def fixture():
    days=[str(d.date()) for d in calendar(2025).sessions_in_range('2025-08-01','2025-10-03')]
    bars={d:{'o':10,'h':10.1,'l':9.9,'c':10,'v':100} for d in days}
    return {'sessions':days,'raw':{'ABC':bars},'split':{'ABC':bars},'first_dates':{'ABC':days[0]}}


def test_research_holding_period_counts_sessions_and_never_exits_at_a_known_low():
    p=fixture();entry='2025-09-12';_,_,decision,cutoff=decision_window(entry)
    event={'ticker':'ABC','decision_at':decision.isoformat(),'data_cutoff':cutoff.isoformat(),'decision_price':10,'timing_trigger':STRATEGY,'dump_structure_score':25}
    def run(hold_map):
        return simulate(p['raw'],p['split'],['ABC'],p['sessions'],start=entry,end='2025-09-19',hold=3,strategy=STRATEGY,
            intraday_signals={entry:[event]},firm_dates=p['first_dates'],signal_share_sizing=True,research_hold_by_entry=hold_map)
    assert run(None)['trades'][0]['exit_date']=='2025-09-17'
    assert run({entry+':ABC':1})['trades'][0]['exit_date']=='2025-09-15'
    assert run({entry+':ABC':2})['trades'][0]['exit_date']=='2025-09-16'
    with pytest.raises(ValueError):run({entry+':ABC':4})


def test_shorter_training_outcomes_still_require_matured_three_session_window():
    p=fixture();row={'ticker':'ABC','entry_date':'2025-09-12'}
    assert hold_outcome(row,p,1)['exit_date']=='2025-09-15'
    assert hold_outcome(row,p,1)['label_end']=='2025-09-17'
    p['split']['ABC'].pop('2025-09-17')
    assert hold_outcome(row,p,1)['policy_net_return'] is None


def test_positive_rank_with_high_loss_risk_cannot_get_a_larger_research_allocation():
    score={'return_rank':.4,'profitability_rank':.8,'tail_loss_rank':.1}
    assert allocation(score,[.1,.3])==1
    assert allocation({**score,'return_rank':.2},[.1,.3])==.6
    assert allocation({**score,'return_rank':.05},[.1,.3])==.2
    assert allocation({**score,'tail_loss_rank':.5},[.1,.3]) is None
    assert allocation({**score,'return_rank':float('nan')},[.1,.3]) is None


def test_one_good_season_and_interest_without_trades_cannot_pass_consistency():
    metric={'net_profit':100,'interest_pnl':100,'closed_trades':0,'max_observed_drawdown_pct':0,'account_insolvent':False}
    rows=[{'year':y,'variant':'X','status':'EVALUATED','base':metric,'stress':metric} for y in YEARS]
    report=consistency(rows)['X']
    assert not report['passed_all_years'] and not report['season_target_achieved_all_years']
    assert not consistency(rows[1:])['X']['passed_all_years']


def test_year_calendars_have_no_missing_summer_or_duplicate_boundary_sessions():
    days=full_sessions(2016,2025)
    assert days==sorted(set(days)) and '2016-01-04' in days and '2025-12-31' in days
    assert '2020-07-04' not in days and '2020-07-06' in days


def test_holding_and_allocation_heads_cannot_train_on_future_labels_or_held_issuers(monkeypatch):
    from backtest.multiyear_study import training_heads
    p=fixture();row={'ticker':'ABC','signal_date':'2025-09-12','entry_date':'2025-09-12','label_end':'2025-09-17',
                    'held_issuer':False,'issuer_cik':'1','x':[0]*14,'policy_net_return':0}
    captured=[]
    monkeypatch.setattr('backtest.multiyear_study.fit_policy',lambda rows:captured.append(rows))
    rows=[row,{**row,'label_end':'2026-01-02'},{**row,'held_issuer':True},{**row,'signal_date':'2023-09-12'}]
    _,_,counts=training_heads(rows,p,2026)
    assert counts=={1:1,2:1,3:1} and all(len(r)==1 for r in captured)
