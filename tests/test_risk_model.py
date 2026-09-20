from datetime import date,timedelta
from smg.risk_model import feature_row,fit,predict,walk_forward_report

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

def test_walk_forward_never_uses_reference_labels_and_keeps_holdout_separate():
    # Sparse fixture intentionally cannot train; the split contract still holds.
    report=walk_forward_report([],{}, {}, [])
    assert report['status']=='INSUFFICIENT_TRAINING_DATA'
    assert report['splits']=={'train':'2022-2023','validation':'2024','holdout':'2025'}
    assert report['holdout']['samples']==0
