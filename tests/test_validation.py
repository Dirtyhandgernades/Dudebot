from smg.validation import independent_rows,fit_calibration,calibrated_scores,reliability,missed_dumps


def test_calibration_rejects_single_class_and_does_not_confuse_rank_with_probability():
    rows=[{'ticker':str(i),'label':int(i<10),'label_end':'2024-01-10','signal_date':'2024-01-02'} for i in range(100)]
    model=fit_calibration(rows,[.95]*100)
    estimates=calibrated_scores(model,[.95]*100)
    assert .08<sum(estimates)/100<.12
    assert reliability(rows,estimates)['confidence_sizing_enabled'] is False
    assert fit_calibration([dict(r,label=1) for r in rows],[.95]*100) is None


def test_calibration_windows_do_not_duplicate_overlapping_ticker_outcomes():
    a={'ticker':'ABC','signal_date':'2024-01-02','label_end':'2024-01-08'}
    b={'ticker':'ABC','signal_date':'2024-01-03','label_end':'2024-01-09'}
    c={'ticker':'ABC','signal_date':'2024-01-10','label_end':'2024-01-17'}
    assert independent_rows([c,b,a])==[a,c]


def test_missed_audit_never_counts_after_drop_signals_as_advance_detection():
    days=['2025-09-08','2025-09-09','2025-09-10','2025-09-11']
    bars={d:{'c':10 if i<3 else 7} for i,d in enumerate(days)}
    packet={'sessions':days,'raw':{'ABC':bars},'split':{'ABC':bars},'firm_dates':{'ABC':days[0]}}
    result=missed_dumps(packet,{days[-1]:[{'ticker':'ABC'}]},{days[-1]:[{'ticker':'ABC'}]},
                        {'trades':[]},days[0],days[-1])
    assert result['events']==1
    assert result['events_with_prior_selected_signal']==0

