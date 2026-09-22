from types import SimpleNamespace
from smg.broad_discovery import firm_shortlist,market_features,shortlist

def bars(close=10,volume=100):
    rows=[]
    for i in range(22):
        c=close*(1+i*.02);rows.append({'t':f'2026-01-{i+1:02}T21:00:00Z','c':c,'h':c*1.05,'l':c*.95,'v':volume})
    rows[-1]['c']=rows[-2]['l']*.95;rows[-1]['v']=200
    return rows

def cfg(size=8):
    return SimpleNamespace(broad_min_monthly_return_pct=12,broad_min_daily_range_pct=8,broad_min_volume_ratio=1,
        broad_shortlist_size=size,firm_live_shortlist_size=size)

def test_daily_prefilter_requires_failure_and_volume_after_pump_or_volatility():
    f=market_features(bars())
    assert f['failed_previous_low'] and f['volume_ratio_20']==2 and f['average_range_5_pct']>8
    item={'ticker':'ABC','features':f,'known_firm':False}
    assert shortlist({'ABC':item},cfg())==[item]
    quiet={**f,'failed_previous_low':False,'return_1_pct':0,'drawdown_21_pct':-1}
    assert shortlist({'ABC':{**item,'features':quiet}},cfg())==[]

def test_shortlist_is_bounded_and_known_firm_is_only_a_bonus():
    base=market_features(bars())
    rows={f'S{i}':{'ticker':f'S{i}','features':dict(base),'known_firm':i==3} for i in range(5)}
    selected=shortlist(rows,cfg(2))
    assert len(selected)==2 and selected[0]['ticker']=='S3'

def test_firm_live_shortlist_is_bounded_by_current_market_activity():
    base=market_features(bars())
    rows={f'S{i}':{'ticker':f'S{i}','features':dict(base,volume_ratio_20=i+1),'known_firm':True} for i in range(5)}
    assert firm_shortlist(rows,set(rows),cfg(2))==['S4','S3']
