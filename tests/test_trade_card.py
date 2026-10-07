from datetime import datetime,timedelta,timezone
from smg.trade_card import position_guide,embed,strength
from smg.drop_probability import outcome,build,estimate,independent
from tests.test_ranked_firm import evaluate,NOW


def reference_rows(n=40):
    return [{'ticker':str(i),'cik':str(i),'entry_date':'2025-10-01','label_end':'2025-10-06',
             'rank_score':.6,'day_1':int(i%10==0),'day_2':int(i%5==0),
             'day_3':int(i%4==0),'severe_50pct_day_3':int(i%20==0)} for i in range(n)]


def test_probability_is_empirical_monotonic_and_missing_data_is_unknown():
    data=estimate(build(reference_rows()),.6)
    assert data['status']=='ESTIMATED_HISTORICAL_REFERENCE' and data['samples']==40
    targets=data['targets']
    assert targets['day_1']['estimate']<targets['day_2']['estimate']<targets['day_3']['estimate']
    assert targets['day_3']['estimate']==10.5/41
    assert targets['day_3']['wilson_95'][0]<.25<targets['day_3']['wilson_95'][1]
    assert estimate(build(reference_rows(10)),.6)['status']=='INSUFFICIENT_DATA'


def test_probability_labels_use_post_entry_closes_not_intraday_lows():
    days=['2025-11-04','2025-11-05','2025-11-06','2025-11-07']
    split={'TEST':{d:{'c':v,'l':.01} for d,v in zip(days,[10,10,9,7])}}
    row={'ticker':'TEST','entry_date':days[0]}
    labels=outcome(row,split,split)
    assert [labels[f'day_{h}'] for h in (1,2,3)]==[0,0,1]
    del split['TEST'][days[2]]
    assert outcome(row,split,split) is None


def test_same_issuer_rename_cannot_double_count_overlapping_labels():
    rows=reference_rows(2);rows[0]['cik']=rows[1]['cik']='1'
    assert len(independent(rows))==1


def test_strength_cannot_alone_unlock_maximum_size_and_unknown_quotes_allocate_zero():
    regular=position_guide(10,90,True,True)
    probability={'status':'ESTIMATED_HISTORICAL_REFERENCE','samples':50,
                 'targets':{'day_3':{'estimate':.60,'wilson_95':[.4,.75]},'severe_50pct_day_3':{'estimate':.15}}}
    strong=position_guide(10,90,True,True,probability=probability)
    assert strong['shares']>regular['shares'] and strong['capital']<30000
    assert strong['shares']==2492 and strong['capital']==24920
    assert position_guide(None,99,True,True)['shares']==0
    assert position_guide(10,99,True,False)['shares']==0
    assert position_guide(10000,99,True,True)['shares']==0
    assert position_guide(10,99,True,True,available_bp=100)['shares']==0


def test_simple_card_separates_score_probability_hold_and_exact_shares():
    e=evaluate();e.ranking_evidence['drop_probability']=estimate(build(reference_rows()),.6)
    card=embed(e,NOW);fields={f['name']:f['value'] for f in card['fields']}
    assert 'Strength score' in fields and '/100' in fields['Strength score']
    assert '1d ' in fields['Estimated drop probability'] and '40 past episodes' in fields['Estimated drop probability']
    assert '1–3 trading sessions' in fields['Drop window / hold']
    assert 'shares' in fields['Suggested paper position'] and 'Closing fill' in fields['Suggested paper position']
    watched=embed(e,NOW,practice=True)
    assert '0 shares' in next(f['value'] for f in watched['fields'] if f['name']=='Suggested paper position')


def test_future_news_cannot_add_strength_points():
    e=evaluate();first=strength(e,NOW)
    e.ranking_evidence['sentiment']={'observed_at':(NOW+timedelta(days=1)).isoformat(),
        'value':{'providers':{'news':{'status':'AVAILABLE','latest_source_timestamp':NOW.isoformat(),'headline_score':-999}}}}
    assert strength(e,NOW)['score']==first['score']
