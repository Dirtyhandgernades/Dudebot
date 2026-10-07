from datetime import datetime,timedelta,timezone
from smg.entry_features import before_news,context,chart,confirmed
from smg.rules import EntityList
from backtest.entry_quality import model_before,gates

NOW=datetime(2025,12,3,20,40,tzinfo=timezone.utc)


def test_intraday_news_and_firm_evidence_cannot_use_later_content_or_edits():
    old={'headline':'trial update','created_at':(NOW-timedelta(hours=2)).isoformat(),'updated_at':(NOW-timedelta(hours=1)).isoformat()}
    future={**old,'updated_at':(NOW+timedelta(minutes=1)).isoformat()}
    assert before_news([old,future],NOW)==[old]
    entries=EntityList({'underwriter':{'High-Suspicion Focus Group':['Cathay Securities']}}).entries
    match={'name':'Cathay Securities','role':'underwriter','evidence':{'url':'https://example.com'}}
    rows=[{'decision_at':(NOW+timedelta(minutes=1)).isoformat(),'firm_matches':[match]}]
    assert context(rows,NOW,entries)==({},[])


def test_partial_confirmation_is_not_inferred_from_a_future_daily_close():
    history=[{'o':10,'h':11,'l':9,'c':10,'v':100}]*22
    partial={'o':10.5,'h':12,'l':9,'c':9.5}
    result=chart(history,partial)
    assert confirmed(result)
    assert not confirmed(chart(history,{**partial,'c':11.5}))
    assert chart(history,None) is None


def test_model_cannot_use_unmatured_or_held_issuer_outcomes():
    rows=[{'ticker':'A','signal_date':'2024-12-20','entry_date':'2024-12-23','label_end':'2024-12-27',
           'policy_net_return':.1,'held_issuer':False,'issuer_cik':'1','x':[0]*14},
          {'ticker':'B','signal_date':'2024-12-30','entry_date':'2024-12-31','label_end':'2025-01-06',
           'policy_net_return':.9,'held_issuer':False,'issuer_cik':'2','x':[0]*14},
          {'ticker':'C','signal_date':'2024-12-20','entry_date':'2024-12-23','label_end':'2024-12-27',
           'policy_net_return':.9,'held_issuer':True,'issuer_cik':'3','x':[0]*14}]
    model,threshold,train=model_before(rows,'2025-01-01','2023-01-01')
    assert model is None and threshold is None and [r['ticker'] for r in train]==['A']


def test_missing_chart_and_unknown_profit_cannot_pass_promotion_gate():
    metric={'net_profit':None,'closed_trades':2,'max_observed_drawdown_pct':0}
    rows=[{'corpus':'x','year':2025,'policy':'BASELINE','base':metric,'stress':metric,'status':'EVALUATED'},
          {'corpus':'x','year':2025,'policy':'CHART_CONFIRMED','base':metric,'stress':metric,'status':'CHART_DATA_UNAVAILABLE'}]
    result=gates(rows)['CHART_CONFIRMED']
    assert result['passed_historical'] is False and result['aggregate_stress_improvement'] is None
    assert 'CHART_DATA_UNAVAILABLE' in result['checks'][0]['failures']
