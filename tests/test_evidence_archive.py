from datetime import datetime,timezone
from smg.evidence_archive import parse_finra,halt_events,select_share_fact,market_cap_proxy
from smg.storage import Store

NOW=datetime(2025,9,8,19,tzinfo=timezone.utc)

def test_finra_short_volume_is_parsed_and_labeled_without_overclaiming():
    text='Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n20250905|ABC|400|10|1000|Q\n# rows|1||||\n'
    rows=parse_finra(text,{'ABC'})
    assert rows['ABC']['short_volume_ratio']==.4
    assert 'borrow' not in rows['ABC'] and 'short_interest' not in rows['ABC']

def test_halt_history_keeps_resumed_events():
    xml='<rss><channel><item><IssueSymbol>ABC</IssueSymbol><HaltDate>09/08/2025</HaltDate><ReasonCode>T1</ReasonCode><ResumptionTradeTime>13:00:00</ResumptionTradeTime></item></channel></rss>'
    row=halt_events(xml)[0]
    assert row['symbol']=='ABC' and row['reason_code']=='T1' and row['resumption_trade_time']=='13:00:00'

def test_share_fact_is_point_in_time_and_cap_is_a_proxy():
    facts={'facts':{'dei':{'EntityCommonStockSharesOutstanding':{'units':{'shares':[
        {'end':'2025-06-30','filed':'2025-08-01','val':10_000_000,'form':'10-Q','accn':'old'},
        {'end':'2025-09-30','filed':'2025-11-01','val':99_000_000,'form':'10-Q','accn':'future'}]}}}}}
    fact=select_share_fact(facts,NOW)
    assert fact['val']==10_000_000 and fact['accn']=='old'
    cap=market_cap_proxy(facts,4,NOW)
    assert cap['market_cap_proxy']==40_000_000 and 'proxy' not in cap['status'].lower()

def test_observation_archive_is_append_only_and_queryable(tmp_path):
    store=Store(tmp_path/'state.sqlite')
    store.observe('market_borrow','abc',NOW,'https://example.com',{'price':4})
    store.observe('market_borrow','abc',NOW,'https://example.com',{'price':999})
    assert store.latest_observation('market_borrow','ABC')['value']['price']==4
    assert len(store.observations('market_borrow','ABC'))==1
