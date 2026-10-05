import pytest
from datetime import datetime,timedelta
from types import SimpleNamespace
from smg.intraday_replay import decision_window,partial_bar,candidates,signal_event,hybrid_event,STRATEGY
from smg.market import calendar
from smg.swing_backtest import simulate


def packet():
    days=[str(s.date()) for s in calendar(2025).sessions_in_range('2025-09-01','2025-11-10')]
    bars={d:dict(o=10,c=10,h=10.1,l=9.9,v=100) for d in days}
    return {'sessions':days,'firm_dates':{'ABC':'2025-01-01'},'raw':{'ABC':{d:dict(b) for d,b in bars.items()}},'split':{'ABC':bars}}


def test_future_incomplete_extended_and_stale_bars_do_not_inform_partial_day():
    opened,_,decision,cutoff=decision_window('2025-11-06')
    start=cutoff.replace(minute=15)
    good={'t':start.isoformat(),'o':14,'h':17,'l':13,'c':14,'v':400}
    future={**good,'t':(start+timedelta(minutes=5)).isoformat(),'c':1000,'h':1000,'v':100000}
    extended={**good,'t':(opened-timedelta(minutes=5)).isoformat(),'v':100000}
    result=partial_bar([good,future,extended],opened,cutoff)
    assert result['c']==14 and result['h']==17 and result['v']==400
    stale={**good,'t':(start-timedelta(minutes=20)).isoformat()}
    assert partial_bar([stale],opened,cutoff) is None


def test_half_day_decision_follows_session_close_and_preserves_delay():
    opened,closed,decision,cutoff=decision_window('2025-11-28')
    assert closed-decision==timedelta(minutes=20)
    assert decision-cutoff==timedelta(minutes=16)
    assert closed.hour==18 and decision.hour==17 and decision.minute==40


def test_today_final_close_cannot_change_preselection_or_chart_signal():
    d=packet();day='2025-11-06';cfg=SimpleNamespace(surge_return_min_pct=12)
    _,_,_,cutoff=decision_window(day)
    partial={'o':14,'h':17,'l':13,'c':14,'v':400,'last_complete_at':cutoff.replace(minute=20).isoformat()}
    before=candidates(d,day);event=signal_event(d,'ABC',day,partial,partial,cfg)
    assert event is not None
    d['raw']['ABC'][day]['c']=.1;d['split']['ABC'][day].update(c=.1,h=1000,v=100000)
    assert candidates(d,day)==before
    assert signal_event(d,'ABC',day,partial,partial,cfg)==event
    assert signal_event(d,'ABC',day,partial,{**partial,'c':3},cfg) is None


def test_same_day_share_order_uses_observed_price_not_unknown_closing_price():
    d=packet();day='2025-11-06';end='2025-11-07';_,_,decision,cutoff=decision_window(day)
    event={'ticker':'ABC','decision_at':decision.isoformat(),'data_cutoff':cutoff.isoformat(),
           'decision_price':5,'timing_trigger':STRATEGY,'dump_structure_score':25}
    result=simulate(d['raw'],d['split'],['ABC'],d['sessions'],start=day,end=end,
                    strategy=STRATEGY,firm_dates=d['firm_dates'],intraday_signals={day:[event]},
                    buying_power=150000,position_target=30000,risk_controls=True,signal_share_sizing=True)
    assert result['closed_trades']==1
    trade=result['trades'][0]
    assert trade['entry_date']==day and trade['signal_date']==day
    assert trade['shares']==5000 and trade['notional']==50000
    event['data_cutoff']=decision.isoformat()
    with pytest.raises(ValueError):
        simulate(d['raw'],d['split'],['ABC'],d['sessions'],start=day,end=end,
                 strategy=STRATEGY,firm_dates=d['firm_dates'],intraday_signals={day:[event]},signal_share_sizing=True)


def test_hybrid_prior_pattern_is_rejected_after_dump_or_resumed_squeeze():
    d=packet();day='2025-11-06';cfg=SimpleNamespace(surge_return_min_pct=12)
    prior=d['sessions'][d['sessions'].index(day)-1]
    d['split']['ABC'][prior].update(o=14,c=14,h=17,l=13,v=400)
    _,_,_,cutoff=decision_window(day)
    partial={'o':14,'h':14.1,'l':13.9,'c':14,'v':100,'last_complete_at':cutoff.replace(minute=20).isoformat()}
    event=hybrid_event(d,'ABC',day,partial,partial,cfg)
    assert event['source_policy']=='PRIOR_CLOSE_EXHAUSTION_REVALIDATED_PRICE'
    assert event['pattern_date']==prior
    for price in [12,18]:
        changed={**partial,'c':price,'o':price,'h':price+.1,'l':price-.1}
        assert hybrid_event(d,'ABC',day,changed,changed,cfg) is None


def test_confirmation_filter_cannot_read_the_future_fill_or_outcome():
    from smg.intraday_replay import confirmed_hybrid_events
    d=packet();day='2025-11-06';events={day:[{'ticker':'ABC','decision_price':10.1}]}
    before,audit=confirmed_hybrid_events(d,events)
    assert len(before[day])==1 and audit['RETAINED']==1
    d['raw']['ABC'][day]['c']=1000
    d['split']['ABC']['2025-11-07']['c']=.01
    assert confirmed_hybrid_events(d,events)==(before,audit)
    events[day][0]['decision_price']=10.3
    after,audit=confirmed_hybrid_events(d,events)
    assert after[day]==[] and audit['CONTINUING_UP_MOVE']==1


def test_preclose_position_scale_reduces_decision_share_order():
    d=packet();day='2025-11-06';end='2025-11-07';_,_,decision,cutoff=decision_window(day)
    event={'ticker':'ABC','decision_at':decision.isoformat(),'data_cutoff':cutoff.isoformat(),
           'decision_price':5,'timing_trigger':STRATEGY,'dump_structure_score':25,'position_scale':.5}
    args=dict(start=day,end=end,strategy=STRATEGY,firm_dates=d['firm_dates'],
              intraday_signals={day:[event]},buying_power=150000,position_target=30000,
              risk_controls=True,signal_share_sizing=True)
    result=simulate(d['raw'],d['split'],['ABC'],d['sessions'],**args)
    assert result['trades'][0]['shares']==3000
    assert result['trades'][0]['position_scale']==.5
    for invalid in (float('nan'),-1,2):
        event['position_scale']=invalid
        with pytest.raises(ValueError):simulate(d['raw'],d['split'],['ABC'],d['sessions'],**args)


def test_drop_timing_counts_exact_twenty_percent_and_censors_missing_outcomes():
    from backtest.confirmation_comparison import drop_timing
    d=packet();entry='2025-11-06';next_day='2025-11-07'
    d['split']['ABC'][next_day]['c']=8
    result={'trades':[{'ticker':'ABC','entry_date':entry,'adjusted_entry':10}]}
    timing=drop_timing(result,d,'2025-11-10')
    assert timing['1']['drop_20pct_at_close']==1
    del d['split']['ABC'][next_day]
    timing=drop_timing(result,d,'2025-11-10')
    assert timing['1']['assessable_entries']==0 and timing['1']['unavailable_or_season_end']==1
