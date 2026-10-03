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


def test_dated_review_or_hard_exclusion_is_not_reported_as_missing_discovery(tmp_path):
    days=['2025-09-08','2025-09-09']
    (tmp_path/'firm-timing-inputs.json.gz').write_bytes(gzip.compress(json.dumps({'sessions':days,'firm_dates':{}}).encode()))
    for strategy in ['LIVE_FIRM_TIMING_SHORT','FIRM_EXHAUSTION_RESEARCH']:
        (tmp_path/f'2025-{strategy}.json').write_text(json.dumps({'trades':[],'signal_events':[],'net_profit':0,'closed_trades':0}))
    records=[{'ticker':'ABC','decision_at':days[0]+'T00:00:00Z','status':'REVIEW_REQUIRED','reasons':['UNKNOWN_ISSUER_CLASSIFICATION']},
             {'ticker':'DEF','decision_at':days[0]+'T00:00:00Z','status':'EXCLUDED','reasons':['ACQUISITION_CORPORATION']}]
    transactions=[{'transaction_type':'SHORT SELL','ticker':t,'date':days[1]} for t in ['ABC','DEF','GHI']]
    for report in compare(tmp_path,transactions,records).values():
        rows={r['ticker']:r for r in report['rows']}
        assert rows['ABC']['comparison_result']=='FIRM_FOUND_ISSUER_CLASSIFICATION_UNRESOLVED'
        assert rows['DEF']['comparison_result']=='HARD_EXCLUDED_BY_DATED_SOURCE'
        assert rows['GHI']['comparison_result']=='FIRM_DISCOVERY_ABSENT'
        assert report['watched_before_friend_entry']==0
