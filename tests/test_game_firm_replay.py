from smg.game_firm_replay import lead_metrics


def test_prior_alert_and_prior_position_are_not_same_day_detections():
    sessions=['2025-09-08','2025-09-09','2025-09-10','2025-09-11']
    bars={s:dict(c=c) for s,c in zip(sessions,[10,10,7,7])}
    result={'signal_events':[{'ticker':'ABC','signal_date':sessions[1]}],
            'trades':[{'ticker':'ABC','entry_date':sessions[2],'exit_date':sessions[3]}]}
    report=lead_metrics(result,{'ABC':bars},{'ABC':bars},sessions,sessions[0],sessions[-1])
    assert report['events']==1 and report['events_with_prior_signal']==1
    assert report['events_with_position_open_before_drop']==0
    result['signal_events'][0]['signal_date']=sessions[2]
    assert lead_metrics(result,{'ABC':bars},{'ABC':bars},sessions,sessions[0],sessions[-1])['events_with_prior_signal']==0


def test_below_three_dollar_events_do_not_inflate_eligible_recall():
    sessions=['2025-09-08','2025-09-09']
    bars={sessions[0]:dict(c=2),sessions[1]:dict(c=1)}
    report=lead_metrics({'signal_events':[],'trades':[]},{'ABC':bars},{'ABC':bars},sessions,*sessions)
    assert report['events']==0 and report['event_recall'] is None


def test_symbol_without_any_provider_bars_is_a_gap_not_a_crash():
    sessions=['2025-09-08','2025-09-09']
    result=lead_metrics({'signal_events':[],'trades':[]},{'GONE':{}},{'GONE':{}},sessions,*sessions)
    assert result['missing_symbol_day_outcomes']==1
    assert result['event_recall'] is None


def test_classification_context_is_dated_and_never_clears_known_spacs():
    from smg.game_firm_replay import dated_records
    from smg.rules import EntityList
    from test_live_firms import watch,ENTRIES,CFG
    from datetime import timedelta
    past=watch();later=past.model_copy(deep=True)
    later.reviewed_at+=timedelta(days=10)
    later.is_acquisition_corp=None;later.evidence.pop('is_acquisition_corp')
    rows=dated_records([later,past],CFG,EntityList(ENTRIES))
    assert rows[-1]['status']=='STRUCTURAL_MATCH'
    future=past.model_copy(deep=True);future.reviewed_at+=timedelta(days=20)
    assert dated_records([later,future],CFG,EntityList(ENTRIES))[0]['status']=='REVIEW_REQUIRED'
    past.is_acquisition_corp=True
    later.is_acquisition_corp=False
    assert dated_records([past,later],CFG,EntityList(ENTRIES))[-1]['status']=='EXCLUDED'
