import pytest
from smg.exposure import budget,range_fraction,reserve,POLICY
from smg.storage import Store
from smg.trade_card import position_guide


def test_unknown_range_and_extreme_volatility_cannot_raise_size():
    known=budget(100000,150000,50000,.08)
    unknown=budget(100000,150000,50000,None)
    extreme=budget(100000,150000,50000,1.)
    assert known['ceiling']==8000 and unknown['ceiling']==2000 and extreme['ceiling']==1000
    assert not known['loss_is_capped']
    assert range_fraction([{'h':10,'l':11,'c':10}]) is None
    assert budget(100000,150000,50000,float('nan'))==unknown


def test_gross_budget_and_order_fee_reserve_bind_before_fills():
    plan=position_guide(10,99,True,True,observed_range=.01,reserved=59000)
    assert plan['reserved_capital']<=1000 and plan['shares']>=10
    assert position_guide(10,99,True,True,observed_range=.01,reserved=60000)['shares']==0
    for bad in (float('nan'),-1,float('inf')):
        with pytest.raises(ValueError):budget(100000,150000,50000,reserved=bad)


def test_reservations_survive_weekends_ambiguous_sends_and_policy_versions(tmp_path):
    store=Store(tmp_path/'s.db');days=['2026-10-07','2026-10-08','2026-10-09','2026-10-12','2026-10-13']
    reserve(store,'ABC',days[0],8000,days,'old')
    assert reserve(store,'ABC',days[3],None,days,'new')[1]['policy_id']=='old'
    assert reserve(store,'ABC',days[4],None,days,'new')==(0,None)
    # Passing a short date inventory next month cannot resurrect old claims.
    assert reserve(store,'XYZ','2026-11-09',None,['2026-11-09'],'new')==(0,None)


def test_protected_share_count_cannot_use_future_closes_and_losses_are_not_clipped():
    from tests.test_swing_backtest import fixture
    from smg.swing_backtest import simulate
    days,bars=fixture();args=dict(start=days[22],end=days[23],hold=1,strategy='FIRM_BASELINE_SHORT',
        position_target=50000,buying_power=150000,signal_share_sizing=True,risk_controls=True,
        decision_price_buffer=1.2,exposure_policy=POLICY)
    old=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,**args)
    bars[days[23]]={**bars[days[23]],'c':100,'h':101}
    new=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,**args)
    assert old['trades'][0]['shares']==new['trades'][0]['shares']
    assert new['trades'][0]['pnl']<-new['trades'][0]['exposure_envelope']['stress_loss_budget']


def test_stopped_short_cannot_reenter_immediately():
    from tests.test_swing_backtest import fixture
    from smg.swing_backtest import simulate
    days,bars=fixture()
    for d in days[23:]:bars[d]={**bars[d],'c':12,'h':13,'l':11}
    r=simulate({'ABC':bars},{'ABC':bars},['ABC'],days,start=days[22],end=days[27],
        hold=3,strategy='FIRM_BASELINE_SHORT',position_target=50000,buying_power=150000,
        signal_share_sizing=True,risk_controls=True,decision_price_buffer=1.2,exposure_policy=POLICY)
    assert r['gaps']['EXPOSURE_STOP_COOLDOWN']>=1
    assert len(r['trades'])==1


def test_shared_delivery_capacity_persists_before_uncertain_discord_requests(tmp_path):
    from tests.test_ranked_firm import evaluate,NOW
    from tests.test_delivery import FakeHttp,URL
    from smg.notify import DiscordSender
    from smg.models import Config
    store=Store(tmp_path/'capacity.db');http=FakeHttp(fail=True);checkpoints=[]
    sender=DiscordSender(http,URL,store,lambda s:checkpoints.append(s.get('paper_exposure_reservations')),clock=lambda:NOW)
    sender._valid_trade=lambda *args:True  # Market gates have separate integration fixtures.
    items=[]
    for i in range(30):
        e=evaluate();e.candidate.ticker='A'+str(i).zfill(3);items.append(e)
    receipt=sender.send_new(items,Config())
    rows=store.get('paper_exposure_reservations')
    assert sum(r['capital'] for r in rows.values())<=60000
    assert len(http.calls)<30 and receipt['status']=='DELIVERY_UNCERTAIN'
    assert checkpoints[0] and len(checkpoints[0])==len(http.calls)
    e=items[0].model_copy(deep=True);e.status='QUALIFIED'
    e.snapshot.monthly_return=999  # Changing phase cannot bypass an active reservation.
    assert sender.send_new([e],Config())=='NO_NEW_TRADES'
    assert len(store.get('paper_exposure_reservations'))==len(rows)
