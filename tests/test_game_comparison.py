import gzip,json
from smg.game_comparison import compare


def test_ticker_overlap_after_friend_entry_is_not_aligned_detection(tmp_path):
    days=['2025-09-08','2025-09-09','2025-09-10','2025-09-11']
    packet={'sessions':days,'firm_dates':{'ABC':days[0]}}
    (tmp_path/'firm-timing-inputs.json.gz').write_bytes(gzip.compress(json.dumps(packet).encode()))
    trade={'ticker':'ABC','entry_date':days[3],'pnl':50}
    result={'trades':[trade],'signal_events':[],'net_profit':50,'closed_trades':1}
    for strategy in ['LIVE_FIRM_TIMING_SHORT','FIRM_EXHAUSTION_RESEARCH']:
        (tmp_path/f'2025-{strategy}.json').write_text(json.dumps(result))
    reports=compare(tmp_path,[{'transaction_type':'SHORT SELL','ticker':'ABC','date':days[2]}])
    for report in reports.values():
        assert report['watched_before_friend_entry']==1
        assert report['ticker_trade_overlap']==1
        assert report['entry_aligned_tickers']==0
        assert report['selection_uses_friend_inputs'] is False
