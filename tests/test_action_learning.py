from datetime import datetime,timezone
import json
from smg.action_learning import policy_outcome,fit_policy,policy_scores,forward_review
from smg.storage import Store
from backtest.action_policy_study import choose_rows


def bars():
    return {'TEST':{'2025-11-04':{'c':10},'2025-11-05':{'c':12},'2025-11-06':{'c':13},'2025-11-07':{'c':1}}}


def test_dump_label_can_be_positive_while_actual_delayed_stop_loses():
    result=policy_outcome({'ticker':'TEST','entry_date':'2025-11-04'},bars())
    assert result['dump_20pct_occurs']==1 and result['policy_net_return']<-.30
    assert result['exit_date']=='2025-11-06' and result['exit_reason']=='STOP_FROM_PRIOR_CLOSE'


def test_missing_future_price_is_unknown_and_not_a_zero_return():
    data=bars();del data['TEST']['2025-11-06']
    result=policy_outcome({'ticker':'TEST','entry_date':'2025-11-04'},data)
    assert result['policy_net_return'] is None and result['status']=='OUTCOME_UNAVAILABLE'


def test_predictions_and_actions_do_not_depend_on_evaluation_labels():
    rows=[{'x':[i/40,(i%3)/3],'policy_net_return':.1 if i%3 else -.4,
           'policy_profitable':int(bool(i%3)),'tail_loss':int(not i%3),'dump_20pct_occurs':int(bool(i%3)),
           'label_end':'2024-12-01'} for i in range(40)]
    model=fit_policy(rows);test=[{'x':[.2,.4],'policy_net_return':-100}]
    first=policy_scores(model,test);test[0]['policy_net_return']=100
    assert policy_scores(model,test)==first
    selected=choose_rows(test,[{'return_rank':.3,'profitability_rank':.8,'tail_loss_rank':.1}],.02,'RETURN_PROFIT_AND_TAIL')
    assert len(selected)==1
    rejected=choose_rows(test,[{'return_rank':.3,'profitability_rank':.8,'tail_loss_rank':.8}],.02,'RETURN_PROFIT_AND_TAIL')
    assert rejected==[]


def test_forward_learning_reads_only_existing_ledger_without_mutating_weights(tmp_path):
    path=tmp_path/'state.sqlite';store=Store(path);store.put('forward_contract:fixture',{'weights':[1,2]});store.db.close()
    before=path.read_bytes();result=forward_review(path,datetime(2026,10,6,23,tzinfo=timezone.utc))
    assert result['status']=='NO_FORECASTS_YET' and result['provider_requests']==0
    assert path.read_bytes()==before


def test_early_price_history_aligns_units_and_rejects_raw_revision():
    from backtest.extend_training_inputs import align_early_history
    packet={'raw':{'TEST':{'2022-06-01':{'c':10}}},'split':{'TEST':{'2022-06-01':{'c':5}}}}
    extra={'raw':{'TEST':{'2022-05-31':{'c':12},'2022-06-01':{'c':10}}},
           'split':{'TEST':{'2022-05-31':{'c':3},'2022-06-01':{'c':2.5}}}}
    result=align_early_history(packet,extra)
    assert result['added_raw_symbol_days']==1 and packet['split']['TEST']['2022-05-31']['c']==6
    extra['raw']['TEST']['2022-06-01']['c']=100
    assert align_early_history(packet,extra)['alignment_gaps'][0]['reason']=='RAW_HISTORY_REVISION_REQUIRES_REVIEW'


def test_rename_alignment_preserves_price_times_volume_and_is_idempotent():
    from smg.history_identity import repair_legacy_volume
    packet={'renames':[{'status':'STITCHED_RENAME','old_symbol':'OLD','new_symbol':'NEW',
                       'effective_date':'2025-10-03','adjusted_scale':.1}],
            'split':{'OLD':{'2025-10-03':{'c':25,'v':50,'vw':250}},'NEW':{'2025-10-03':{'c':25,'v':50,'vw':250}}}}
    repair_legacy_volume(packet)
    assert packet['split']['NEW']['2025-10-03']['v']==500
    assert packet['split']['NEW']['2025-10-03']['vw']==25
    repair_legacy_volume(packet)
    assert packet['split']['NEW']['2025-10-03']['v']==500


def test_augmented_context_does_not_read_future_prices_or_trade_market_proxy():
    from backtest.extend_training_inputs import augment_rows
    from backtest.repair_study import build_rows
    from tests.test_repair_study import packet
    data,days=packet();data['split']['SPY']={d:{'c':100+i,'h':101+i,'l':99+i,'v':100} for i,d in enumerate(days)}
    row=next(r for r in build_rows(data,[])[0] if r['signal_date']==days[30])
    before=augment_rows([row],data,{})[0]['x']
    data['split']['SPY'][days[31]]['c']=100000
    assert augment_rows([row],data,{})[0]['x']==before
    assert len(before)==32 and all(r['ticker']!='SPY' for r in build_rows(data,[])[0])
