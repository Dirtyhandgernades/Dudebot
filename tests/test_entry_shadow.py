import json
from smg.storage import Store
from smg.entry_shadow import capture,review,contract
from tests.test_ranked_firm import evaluate,NOW
from datetime import timedelta


def setup(tmp_path):
    root=tmp_path;folder=root/'config';folder.mkdir()
    spec={'id':'trial','parent_policy':'fixture','published_at':(NOW-timedelta(minutes=1)).isoformat(),
          'source_sha256':{},'live_enabled':False,'automatic_promotion':False,'return_head':{'model':None}}
    (folder/'entry_quality_trial.json').write_text(json.dumps(spec))
    store=Store(root/'s.db');e=evaluate();facts=e.ranking_evidence['ranked_firm']
    e.ranking_evidence['entry_research']={'x':facts['features']+[0]*7}
    store.put('ranked_evaluation:a',e.model_dump(mode='json'))
    return root,store,e,spec


def test_first_paper_decision_is_immutable_and_not_a_live_promotion(tmp_path):
    root,store,e,spec=setup(tmp_path)
    assert capture(store,root,NOW)['captured']==1
    old=store.items('entry_quality_decision:')[0][1]
    e.ranking_evidence['entry_research']['x'][-1]=1
    store.put('ranked_evaluation:a',e.model_dump(mode='json'))
    assert capture(store,root,NOW)['captured']==0
    assert store.items('entry_quality_decision:')[0][1]==old
    assert old['paper_only'] is True


def test_future_completed_prices_do_not_create_a_matured_outcome(tmp_path):
    from smg.market import calendar
    root,store,e,spec=setup(tmp_path);capture(store,root,NOW)
    days=[str(d.date()) for d in calendar(NOW.year).sessions_in_range(str(NOW.date()),str((NOW+timedelta(days=10)).date()))][:4]
    series={d:{'c':v} for d,v in zip(days,[10,5,5,5])}
    store.put('ranked_daily_history',{'raw':{e.candidate.ticker:series},'split':{e.candidate.ticker:series}})
    result=review(store,root,NOW)
    assert result['matured_nonoverlapping']==0 and result['unknown_outcomes']==1
    assert result['automatic_promotion'] is False
    assert not store.items('entry_quality_outcome:')


def test_trial_cannot_enable_promotion_or_use_future_prior_features(tmp_path):
    import pytest
    root,store,e,spec=setup(tmp_path)
    e.ranking_evidence['ranked_firm']['feature_dates'][-1]=str(NOW.date())
    store.put('ranked_evaluation:a',e.model_dump(mode='json'))
    assert capture(store,root,NOW)['captured']==0
    spec['automatic_promotion']=True
    (root/'config/entry_quality_trial.json').write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='CANNOT_PROMOTE'):contract(root)
