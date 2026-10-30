import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from backtest import obsidian_two_provider_close_reconciliation as m


def receipt(payload=None, status=200):
    return dict(http_status=status, payload=payload, body_sha256='fixture',
                retrieved_at='2026-10-29T17:00:00+00:00', headers={})


def massive(day='2026-10-27', symbol='AAPL', close=100):
    return receipt(dict(status='OK', symbol=symbol, **{'from': day}, close=close))


def twelve(bars=None):
    return receipt(dict(status='ok', meta=dict(symbol='AAPL', exchange='NASDAQ'),
                        values=bars if bars is not None else [dict(datetime='2026-10-27', close='100')]))


class ReconciliationTests(unittest.TestCase):
    def pair(self):
        return (m.observation('MASSIVE', 'AAPL', '2026-10-27', massive()),
                m.observation('TWELVE_DATA', 'AAPL', '2026-10-27', twelve()))

    def identity(self):
        return dict(ticker='AAPL', session_date='2026-10-27', security_id='reviewed-id',
                    identity_verified=True, exchange_verified=True, corporate_actions_verified=True,
                    corporate_action_changed=False, source_receipts=['fixture-review'])

    def test_matching_requires_reviewed_identity(self):
        a, b = self.pair()
        self.assertEqual(m.compare(a, b)[0], 'IDENTITY_UNVERIFIED')
        self.assertEqual(m.compare(a, b, self.identity()), ('AGREE', '0'))

    def test_exact_decimal_tolerance_and_disagreement(self):
        a, b = self.pair()
        b['price'] = '100.005'
        self.assertEqual(m.compare(a, b, self.identity())[0], 'AGREE')
        b['price'] = '100.005001'
        self.assertEqual(m.compare(a, b, self.identity())[0], 'DISAGREE')

    def test_reverse_split_unknown_and_adjustment_mismatch(self):
        a, b = self.pair()
        for changed in (True, None):
            evidence = self.identity(); evidence['corporate_action_changed'] = changed
            self.assertEqual(m.compare(a, b, evidence)[0], 'CORPORATE_ACTION_AMBIGUITY')
        b['adjustment_basis'] = 'SPLIT_ADJUSTED'
        self.assertEqual(m.compare(a, b, self.identity())[0], 'PRICE_BASIS_MISMATCH')

    def test_identity_date_and_price_type_mismatch(self):
        a, b = self.pair()
        for field, value in [('ticker', 'OTHER'), ('session_date', '2026-10-28'),
                             ('price_type', 'OFFICIAL_AUCTION')]:
            other = dict(b); other[field] = value
            self.assertNotEqual(m.compare(a, other, self.identity())[0], 'AGREE')

    def test_duplicate_missing_and_malformed_bars(self):
        for bars, reason in [([], 'SESSION_MISSING'),
                             ([{'datetime':'2026-10-28','close':'100'}], 'SESSION_MISSING'),
                             ([{'datetime':'2026-10-27','close':'100'}]*2, 'DUPLICATE_SESSION'),
                             ([None], 'MALFORMED_BARS')]:
            self.assertEqual(m.observation('TWELVE_DATA','AAPL','2026-10-27',twelve(bars))['provider_error_category'], reason)

    def test_invalid_prices_and_symbol_date_echo(self):
        for value in (True, None, 'nan', 'Infinity', -1, 0, 'bad'):
            self.assertEqual(m.observation('MASSIVE','AAPL','2026-10-27',massive(close=value))['provider_error_category'], 'INVALID_PRICE')
        for response, reason in [(massive(symbol='WRONG'),'IDENTITY_MISMATCH'),
                                 (massive(day='2026-10-28'),'SESSION_MISMATCH')]:
            self.assertEqual(m.observation('MASSIVE','AAPL','2026-10-27',response)['provider_error_category'],reason)

    def test_http_and_network_errors(self):
        for status, reason in [(400,'BAD_REQUEST'),(401,'AUTHENTICATION'),(403,'ENTITLEMENT_OR_ACCESS'),
                               (429,'RATE_LIMIT'),(500,'SERVER_ERROR')]:
            self.assertEqual(m.category(receipt({'message':'secret'},status)), reason)
        self.assertEqual(m.category({'error':'NETWORK_UNAVAILABLE'}),'NETWORK_UNAVAILABLE')
        self.assertEqual(m.category(receipt([])),'MALFORMED_RESPONSE')
        self.assertEqual(m.category(receipt({'status':'error','code':429})),'RATE_LIMIT')

    def test_rate_limit_stops_requests_and_retains_headers(self):
        r = receipt({},429); r['headers']={'retry-after':'60'}
        with patch.object(m,'get',return_value=r) as get:
            budget=m.Budget(4)
            first=budget.fetch('url',{},'token')
            second=budget.fetch('url',{},'token')
        self.assertEqual(get.call_count,1)
        self.assertEqual(second['error'],'RATE_LIMIT')
        self.assertEqual(first['headers']['retry-after'],'60')

    def test_header_exhaustion_and_hard_budget(self):
        for headers, reason in [({'x-ratelimit-remaining':'0'},'RATE_LIMIT'),({},'REQUEST_BUDGET_EXHAUSTED')]:
            r=massive();r['headers']=headers
            with patch.object(m,'get',return_value=r) as get:
                budget=m.Budget(1);budget.fetch('url',{},'token')
                self.assertEqual(budget.fetch('url',{},'token')['error'],reason)
                self.assertEqual(get.call_count,1)

    def test_bounded_batch_complete_denominator_and_no_secret_echo(self):
        def fake(url,params,token):
            if 'twelvedata' in url:
                self.assertEqual(params['adjust'],'none')
                r=twelve([{'datetime':d,'close':'100'} for d in m.SESSIONS])
                r['payload']['meta']['symbol']=params['symbol']
                return r
            return massive(url.rsplit('/',1)[-1],url.split('/')[-2])
        with patch.object(m,'get',side_effect=fake) as get, patch.dict('os.environ',{'MASSIVE_API_KEY':'secret-fixture','TWELVE_DATA_API_KEY':'secret-fixture'}):
            result=m.reconcile()
        self.assertEqual(get.call_count,6)
        self.assertEqual(result['both_bar_count'],4)
        self.assertEqual(result['valid_same_session_pairs'],0)
        self.assertEqual(result['identity_blocked_count'],4)
        self.assertNotIn('secret-fixture',json.dumps(result))
        self.assertFalse(result['outcome_scoring_eligible'])

    def test_missing_secrets_and_write_once_before_network(self):
        with patch.dict('os.environ',{},clear=True):
            result=m.reconcile()
        self.assertEqual(result['missing_pair_count'],4)
        self.assertEqual(result['request_budget']['massive_used'],0)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'existing.json';path.write_text('original')
            with patch.object(m,'OUT',path), patch.object(m,'get') as get:
                with self.assertRaises(FileExistsError):m.main()
                get.assert_not_called()
            self.assertEqual(path.read_text(),'original')

    def test_transport_does_not_emit_network_exception(self):
        with patch.object(m.request,'urlopen',side_effect=OSError('credential-value')):
            r=m.get('https://example.com',{},'credential-value')
        self.assertNotIn('credential-value',json.dumps(r))
        self.assertEqual(r['error'],'NETWORK_UNAVAILABLE')


    def test_provider_body_and_untrusted_headers_never_enter_artifact(self):
        secret='canary-token-in-provider-response'
        class FakeResponse:
            code=200
            headers={'Retry-After':'60', 'X-RateLimit-Remaining':'2',
                     'X-RateLimit-Reset':'token='+secret}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                return json.dumps({'status':'error', 'message':'echo '+secret,
                                   'apiKey':secret}).encode('utf-8')
        with patch.object(m.request,'urlopen',return_value=FakeResponse()):
            fetched=m.get('https://api.massive.com/v1/open-close',
                          {'apiKey':secret}, secret)
        self.assertNotIn('redacted_response_body',fetched)
        self.assertEqual(fetched['headers'],{'retry-after':'60','x-ratelimit-remaining':'2'})
        normalized=m.observation('MASSIVE','AAPL','2026-10-27',fetched)
        self.assertNotIn('redacted_response_body',normalized)
        self.assertNotIn(secret,json.dumps(normalized))
        self.assertEqual(normalized['provider_error_category'],'PROVIDER_ERROR')
        self.assertEqual(normalized['raw_response_hash'],fetched['body_sha256'])
        self.assertFalse(normalized['raw_body_retained'])

    def test_untrusted_legacy_receipt_body_not_copied_to_normalized_result(self):
        r=massive()
        r['redacted_response_body']='vendor secret echoed in error text'
        row=m.observation('MASSIVE','AAPL','2026-10-27',r)
        self.assertNotIn('redacted_response_body',row)
        self.assertNotIn('vendor secret',json.dumps(row))



    def test_untrusted_vendor_error_shapes_do_not_abort(self):
        for payload, expected in [
            ({'status': []}, 'MALFORMED_RESPONSE'),
            ({'status': {'bad': True}}, 'MALFORMED_RESPONSE'),
            ({'status': 'error', 'code': []}, 'MALFORMED_RESPONSE'),
            ({'status': 'ERROR', 'code': {'bad': 429}}, 'MALFORMED_RESPONSE'),
            ({'status': 'error', 'code': 429}, 'RATE_LIMIT'),
        ]:
            with self.subTest(payload=payload):
                r = receipt(payload)
                self.assertEqual(m.category(r), expected)
                self.assertEqual(
                    m.observation('MASSIVE', 'AAPL', '2026-10-27', r)['provider_error_category'],
                    expected)

    def test_extreme_finite_vendor_prices_censored_without_losing_rows(self):
        for value in ('1e999999', '1e-999999'):
            self.assertIsNone(m.price(value))
            self.assertEqual(
                m.observation('MASSIVE', 'AAPL', '2026-10-27',
                              massive(close=value))['provider_error_category'], 'INVALID_PRICE')
        def fake(url, params, token):
            if 'twelvedata' in url:
                r = twelve([{'datetime': d, 'close': '100'} for d in m.SESSIONS])
                r['payload']['meta']['symbol'] = params['symbol']
                return r
            return massive(url.rsplit('/', 1)[-1], url.split('/')[-2], close='1e999999')
        with patch.object(m, 'get', side_effect=fake), patch.dict(
                'os.environ', {'MASSIVE_API_KEY': 'fixture', 'TWELVE_DATA_API_KEY': 'fixture'}):
            result = m.reconcile()
        self.assertEqual(result['total_ticker_dates'], 4)
        self.assertEqual(result['missing_pair_count'], 4)
        self.assertEqual(result['both_bar_count'], 0)
        self.assertFalse(result['outcome_scoring_eligible'])

    def test_malformed_exchange_metadata_is_censored(self):
        for bad in ([], {}, 123):
            r = twelve()
            r['payload']['meta']['exchange'] = bad
            row = m.observation('TWELVE_DATA', 'AAPL', '2026-10-27', r)
            self.assertEqual(row['provider_error_category'], 'MALFORMED_METADATA')
            self.assertEqual(row['validation_status'], 'BLOCKED')


if __name__=='__main__':unittest.main()
