from datetime import datetime,timezone
from types import SimpleNamespace

from smg.learning import outcome_rows,record_scan,review
from smg.live_selection import select
from smg.storage import Store


def test_firm_priority_and_daily_miss_reason_are_preserved(tmp_path):
    now=datetime(2026,9,21,20,tzinfo=timezone.utc)
    def candidate(ticker,pipeline):
        return SimpleNamespace(ticker=ticker,pipeline=pipeline,reviewed_at=now,is_acquisition_corp=False)
    firms=[candidate('F'+str(i),'FIRM_WATCH') for i in range(4)]
    broad=[candidate('V'+str(i),'VOLATILITY_WATCH') for i in range(3)]
    cfg=SimpleNamespace(firm_live_shortlist_size=3,broad_shortlist_size=1,strict_live_shortlist_size=0)
    selected,counts=select(broad+firms,['F2'],cfg)
    assert [c.ticker for c in selected]==['F2','F0','F1','V0']
    assert counts=={'firm':3,'volatility':1,'strict':0}
    store=Store(tmp_path/'state.sqlite')
    evaluation=SimpleNamespace(candidate=firms[0],status='REVIEW_REQUIRED',
        reasons=['UNKNOWN_ISSUER_CLASSIFICATION'],snapshot=None,shortability=None)
    record_scan(store,firms,[evaluation],now)
    bars={'F0':{'2026-09-21':{'c':10},'2026-09-22':{'c':7}},
          'F1':{'2026-09-21':{'c':10},'2026-09-22':{'c':7}}}
    rows=outcome_rows(store,bars,'2026-09-21','2026-09-22')
    assert next(r for r in rows if r['ticker']=='F0')['scan_reasons']==['UNKNOWN_ISSUER_CLASSIFICATION']
    assert next(r for r in rows if r['ticker']=='F0')['outcome']=='MISSED_20PCT_CLOSE_DROP'
    assert next(r for r in rows if r['ticker']=='F1')['scan_status']=='NOT_SELECTED_FOR_SCAN'
    assert next(r for r in rows if r['ticker']=='F3')['outcome']=='DATA_GAP'


def test_sent_alert_is_not_counted_as_miss(tmp_path):
    store=Store(tmp_path/'state.sqlite')
    store.put('watch_census:2026-09-21',{'firm_symbols':['ABC']})
    store.put('trade_alert_history:2026-09-21:ABC',{'ticker':'ABC','status':'SENT'})
    bars={'ABC':{'2026-09-21':{'c':10},'2026-09-22':{'c':7}}}
    assert outcome_rows(store,bars,'2026-09-21','2026-09-22')[0]['outcome']=='FLAGGED_20PCT_CLOSE_DROP'


def test_firm_reason_wins_when_both_lanes_watched_same_ticker(tmp_path):
    store=Store(tmp_path/'two-lanes.sqlite')
    store.put('watch_census:2026-09-21',{'firm_symbols':['ABC']})
    for lane,reason in [('FIRM_WATCH','UNKNOWN_ISSUER_CLASSIFICATION'),
                        ('VOLATILITY_WATCH','VOLATILITY_REVERSAL_NOT_CONFIRMED')]:
        store.put('scan_day:2026-09-21:'+lane+':ABC',{'ticker':'ABC','pipeline':lane,
            'status':'REVIEW_REQUIRED','reasons':[reason]})
    bars={'ABC':{'2026-09-21':{'c':10},'2026-09-22':{'c':7}}}
    row=outcome_rows(store,bars,'2026-09-21','2026-09-22')[0]
    assert row['pipeline']=='FIRM_WATCH'
    assert row['scan_reasons']==['UNKNOWN_ISSUER_CLASSIFICATION']


def test_annual_filing_can_supply_missing_issuer_classification(tmp_path):
    from smg.live_firms import LiveFirmDiscovery
    class Sec:
        def document(self,url):
            return {'text':'We manufacture and sell industrial products across North America.',
                    'url':url,'sha256':'fixture'}
    discovery=LiveFirmDiscovery(Sec(),SimpleNamespace(entities={}),Store(tmp_path/'issuer.sqlite'),
        SimpleNamespace(filings_max_downloads_per_run=2))
    filings=[{'form':'10-K','date':'2026-03-01','url':'https://www.sec.gov/Archives/test'}]
    classification,proof=discovery.issuer_classification(filings)
    assert classification is False and proof['url']==filings[0]['url']
    assert discovery.issuer_classification(filings)[0] is False
    assert discovery.downloads==1


def test_missed_firm_moves_up_research_queue_without_becoming_a_trade(tmp_path):
    store=Store(tmp_path/'review.sqlite')
    store.put('watch_census:2026-09-21',{'firm_symbols':['WCT']})
    class Http:
        def json(self,url,**kwargs):
            return {'bars':{'WCT':[{'t':'2026-09-21T20:00:00Z','c':10},
                                   {'t':'2026-09-22T20:00:00Z','c':7}]}}
    result=review(store,Http(),{},datetime(2026,9,22,23,35,tzinfo=timezone.utc))
    assert result['research_priority_symbols']==['WCT']
    assert store.get('learning_priority')['firm_symbols']==['WCT']
    assert result['reviews'][0]['misses'][0]['scan_status']=='NOT_SELECTED_FOR_SCAN'
