import json
import unittest
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from backtest import obsidian_free_quant_feed as m

NOW=datetime(2026,10,29,18,10,tzinfo=timezone.utc)

class FakeReader:
    maximum=24
    def __init__(self,fail_sip=False):self.used=0;self.receipts=[];self.fail_sip=fail_sip;self.calls=[]
    def get(self,url,params=None,headers=None):
        self.used+=1;self.calls.append((url,params));r=dict(retrieved_at=NOW.isoformat(),error=None,http_status=200)
        if 'snapshots' in url:
            payload={'AAPL':{'latestTrade':{'t':(NOW-timedelta(seconds=5)).isoformat(),'p':100},
                             'latestQuote':{'t':(NOW-timedelta(seconds=500)).isoformat(),'bp':99,'ap':101}}}
        elif '/bars' in url:
            if self.fail_sip:r['error']='HTTP_403';self.receipts.append(r);return None,r
            payload={'bars':{'AAPL':[{'t':(NOW-timedelta(minutes=19)).isoformat(),'c':99,'v':20}]}}
        else:
            self.receipts.append(r);return b'<rss><channel/></rss>',r
        self.receipts.append(r);return json.dumps(payload).encode(),r

class FeedTests(unittest.TestCase):
    def test_independent_trade_quote_clocks_and_future(self):
        snap={'latestTrade':{'p':10,'t':(NOW-timedelta(seconds=5)).isoformat()},
              'latestQuote':{'bp':9,'ap':11,'t':(NOW-timedelta(seconds=90)).isoformat()}}
        r=m.market_record(snap,NOW)
        self.assertEqual(r['trade']['status'],'FRESH_SINGLE_VENUE')
        self.assertEqual(r['quote']['status'],'STALE_SINGLE_VENUE')
        snap['latestTrade']['t']=(NOW+timedelta(seconds=1)).isoformat()
        self.assertEqual(m.market_record(snap,NOW)['trade']['status'],'FUTURE')
    def test_missing_invalid_crossed_and_stale(self):
        self.assertEqual(m.market_record(None,NOW)['status'],'MISSING_IEX_SNAPSHOT')
        for price in [True,0,-1,float('nan')]:
            self.assertEqual(m.market_record({'latestTrade':{'p':price,'t':NOW.isoformat()}},NOW)['trade']['status'],'INVALID')
        r=m.market_record({'latestQuote':{'bp':11,'ap':9,'t':NOW.isoformat()}},NOW)
        self.assertEqual(r['quote']['status'],'CROSSED_QUOTE')
    def test_whole_denominator_delayed_is_never_live_or_halt_clear(self):
        f=FakeReader()
        with patch.dict('os.environ',{'ALPACA_API_KEY':'fixture','ALPACA_SECRET_KEY':'fixture'},clear=True):
            r=m.collect(['AAPL','JDZG'],reader=f,clock=NOW)
        self.assertEqual(r['coverage']['denominator'],2)
        self.assertEqual(r['rows'][1]['iex']['status'],'MISSING_IEX_SNAPSHOT')
        self.assertEqual(r['rows'][0]['sip']['minimum_delay_minutes'],17)
        self.assertIsNotNone(r['rows'][0]['sip']['latest_completed_bar'])
        for row in r['rows']:
            self.assertFalse(row['halt']['executable_halt_clearance'])
            self.assertFalse(row['trade_authorized'])
        params=next(p for url,p in f.calls if '/bars' in url)
        self.assertEqual(datetime.fromisoformat(params['end']),NOW-timedelta(minutes=18))
        self.assertNotIn('fixture',json.dumps(r))
    def test_403_does_not_fallback_to_paid_or_iex_as_sip(self):
        with patch.dict('os.environ',{'ALPACA_API_KEY':'x','ALPACA_SECRET_KEY':'y'},clear=True):
            r=m.collect(['AAPL'],reader=FakeReader(True),clock=NOW)
        self.assertEqual(r['rows'][0]['sip']['error'],'HTTP_403')
        self.assertIsNone(r['rows'][0]['sip']['latest_completed_bar'])
    def test_filing_publication_no_future_and_no_polarity_inference(self):
        p={'filings':{'recent':{'form':['8-K','8-K'],'accessionNumber':['0000000001-26-000001']*2,
          'primaryDocument':['report.htm']*2,'acceptanceDateTime':[(NOW-timedelta(hours=1)).isoformat(),(NOW+timedelta(hours=1)).isoformat()]}}}
        rows=m.filing_records(p,'AAPL','1',NOW,NOW)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['counterevidence_status'],'UNREVIEWED')
        self.assertFalse(rows[0]['actual_issuance_or_sale_verified'])
    def test_filing_shapes_and_path_traversal(self):
        p={'filings':{'recent':{'form':['8-K'],'accessionNumber':['0000000001-26-000001'],
           'primaryDocument':['../bad'],'acceptanceDateTime':[NOW.isoformat()]}}}
        self.assertEqual(m.filing_records(p,'AAPL','1',NOW,NOW),[])
    def test_duplicate_and_protected_clock_rejected(self):
        with self.assertRaises(ValueError):m.collect(['AAPL','AAPL'],clock=NOW)
        with self.assertRaises(ValueError):m.collect(['AAPL'],clock=NOW.replace(hour=19,minute=50))
    def test_transport_budget_and_rate_stop_secret_safe(self):
        class Response:status_code=429;content=b'error'
        class Session:
            calls=0
            def get(self,*a,**kw):self.calls+=1;return Response()
        s=Session();r=m.Reader(s,maximum=2)
        r.get('https://data.alpaca.markets/one');raw,receipt=r.get('https://data.alpaca.markets/two')
        self.assertEqual(s.calls,1);self.assertIsNone(raw)
        self.assertEqual(receipt['error'],'BUDGET_OR_PROVIDER_STOP')
    def test_missing_credentials_still_returns_unknown_rows(self):
        with patch.dict('os.environ',{},clear=True):r=m.collect(['AAPL'],reader=FakeReader(),clock=NOW)
        self.assertEqual(r['rows'][0]['iex']['error'],'ALPACA_CREDENTIALS_ABSENT')
        self.assertEqual(r['rows'][0]['catalysts']['status'],'SEC_USER_AGENT_ABSENT')

if __name__=='__main__':unittest.main()

class PassageTests(unittest.TestCase):
    def test_negated_adverse_words_remain_unreviewed_evidence(self):
        text='There is no substantial doubt about our going concern. The offering was terminated.'
        adverse=m.passages(text,('going concern','offering'))
        counter=m.passages(text,('no substantial doubt','terminated'))
        self.assertEqual(len(adverse),2)
        self.assertEqual(len(counter),2)
        self.assertTrue(all(row['review_required'] for row in adverse+counter))
    def test_naive_or_missing_publication_is_not_evidence(self):
        p={'filings':{'recent':{'form':['8-K'],'accessionNumber':['0000000001-26-000001'],
             'primaryDocument':['doc.htm'],'acceptanceDateTime':['2026-10-29T12:00:00']}}}
        self.assertEqual(m.filing_records(p,'AAPL','1',NOW,NOW),[])

class RotationTests(unittest.TestCase):
    def test_new_priority_symbols_and_no_repeating_completed_batch(self):
        state={'version':1,'symbols':{'AAPL':{'last_attempted_at':NOW.isoformat()}}}
        batch=m.sec_batch(['AAPL','CBRS','MSFT','RAPP','SPTX'],3,state,['CBRS','RAPP','SPTX'])
        self.assertEqual(batch,['CBRS','RAPP','SPTX'])
        packet={'rows':[{'ticker':s,'catalysts':{'status':'RECENT_FILING_METADATA_COLLECTED_REVIEW_REQUIRED'}} for s in batch],
                'sec_rotation':{'selected_symbols':batch},'requested_symbols':['AAPL','CBRS','MSFT','RAPP','SPTX'],
                'finished_at':(NOW+timedelta(seconds=1)).isoformat()}
        new=m.update_rotation(state,packet)
        self.assertEqual(m.sec_batch(packet['requested_symbols'],2,new,['CBRS','RAPP','SPTX']),['MSFT','AAPL'])
        self.assertEqual(state['symbols'].keys(),{'AAPL'})
    def test_every_name_gets_a_turn_and_wraps(self):
        symbols=['AAA','BBB','CCC','DDD','EEE'];state={'version':1,'symbols':{}};seen=set()
        for i in range(3):
            batch=m.sec_batch(symbols,2,state)
            packet={'rows':[{'ticker':s,'catalysts':{'status':'RECENT_FILING_METADATA_COLLECTED_REVIEW_REQUIRED'}} for s in batch],
                    'sec_rotation':{'selected_symbols':batch},'requested_symbols':symbols,
                    'finished_at':(NOW+timedelta(seconds=i)).isoformat()}
            seen.update(batch);state=m.update_rotation(state,packet)
        self.assertEqual(seen,set(symbols))
    def test_unavailable_credentials_and_host_budget_do_not_burn_turn(self):
        state={'version':1,'symbols':{}}
        for status in ('SEC_USER_AGENT_ABSENT','BUDGET_OR_PROVIDER_STOP','SEC_MAP_SOURCE_HTTP_403'):
            packet={'rows':[{'ticker':'AAPL','catalysts':{'status':status}}],
                    'sec_rotation':{'selected_symbols':['AAPL']},'requested_symbols':['AAPL'],'finished_at':NOW.isoformat()}
            self.assertEqual(m.update_rotation(state,packet)['symbols'],{})
    def test_malformed_rotation_is_rejected(self):
        for state in ({}, {'version':1,'symbols':{'AAPL':{'last_attempted_at':'bad'}}}):
            with self.assertRaises(ValueError):m.sec_batch(['AAPL'],8,state)
