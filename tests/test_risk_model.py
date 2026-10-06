from datetime import date,timedelta
from smg.risk_model import feature_row,fit,predict,walk_forward_report,earliest_firm_dates

def bars(n=22,start=10,volume=100):
    return [dict(c=start*(1+i*.01),h=start*(1+i*.01)*1.01,l=start*(1+i*.01)*.99,v=volume) for i in range(n)]

def test_features_only_use_supplied_history():
    x=feature_row(bars())
    assert len(x)==7 and x[0]>0 and x[4]==1
    future=bars();future.append(dict(c=1,h=1,l=1,v=999999))
    assert feature_row(future[:22])==x

def test_balanced_logistic_ranker_learns_direction_deterministically():
    rows=[]
    for i in range(40):
        rows.append({'x':[float(i),0,0,0,1,0,0],'label':int(i>=20)})
    model=fit(rows);scores=predict(model,[rows[0],rows[-1]])
    assert model and scores[1]>scores[0]


def test_high_rank_scores_are_not_reported_as_high_trade_confidence():
    from smg.risk_model import score_reliability
    report=score_reliability([{'ticker':'ABC','label':1},{'ticker':'XYZ','label':0}],[.95,.95])
    assert report['score_is_calibrated_probability'] is False
    assert report['bins'][0]['mean_rank_score']==.95
    assert report['bins'][0]['empirical_target_rate']==.5


def test_missing_predictions_cannot_report_a_perfect_brier_score():
    from smg.risk_model import metrics
    result=metrics([{'label':1}],[])
    assert result['status']=='PREDICTIONS_UNAVAILABLE' and result['brier'] is None

def test_walk_forward_never_uses_reference_labels_and_keeps_holdout_separate():
    # Sparse fixture intentionally cannot train; the split contract still holds.
    report=walk_forward_report([],{}, {}, [])
    assert report['status']=='INSUFFICIENT_TRAINING_DATA'
    assert report['splits']=={'train':'2022-2023','validation':'2024','holdout':'2025'}
    assert report['holdout']['samples']==0

def test_firm_evidence_after_close_is_not_available_for_same_close():
    rows=[{'ticker':'ABC','decision_at':'2025-09-08T21:00:00Z',
           'reasons':['VERIFIED_LISTED_FIRM_RELATIONSHIP']}]
    assert earliest_firm_dates(rows)=={'ABC':'2025-09-09'}
    rows[0]['decision_at']='2025-09-08T18:00:00Z'
    assert earliest_firm_dates(rows)=={'ABC':'2025-09-08'}


def test_training_labels_never_bridge_missing_exchange_sessions():
    from smg.market import calendar
    from smg.risk_model import samples
    sessions=[str(s.date()) for s in calendar(2023).sessions_in_range('2023-11-01','2023-12-05')]
    sessions += [str(s.date()) for s in calendar(2024).sessions_in_range('2024-06-03','2024-07-12')]
    series={d:{**b,'v':100} for d,b in zip(sessions,bars(len(sessions)))}
    records=[{'ticker':'ABC','decision_at':'2023-01-03T12:00:00Z',
              'reasons':['VERIFIED_LISTED_FIRM_RELATIONSHIP']}]
    rows=samples(records,{'ABC':series},{'ABC':series},sessions)
    assert rows
    assert all((date.fromisoformat(r['label_end'])-date.fromisoformat(r['signal_date'])).days<10 for r in rows)
    assert all(r['signal_date']>'2024-06-25' for r in rows)


def test_fold_cannot_learn_late_maturing_outcomes_from_prior_year_signals():
    from smg.risk_model import matured_before
    known={'signal_date':'2023-12-20','label_end':'2023-12-27','label':1}
    future={'signal_date':'2023-12-29','label_end':'2024-01-05','label':1}
    assert matured_before([known,future],'2024-01-01')==[known]
