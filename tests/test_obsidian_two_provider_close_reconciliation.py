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

    def test_malformed_http_status_is_censored_not_exception(self):
        for bad in (None, True, False, '200', [], {}, 0, 600):
            with self.subTest(status=repr(bad)):
                r = receipt({'status': 'OK', 'symbol': 'AAPL',
                             'from': '2026-10-27', 'close': '100'}, status=bad)
                self.assertEqual(m.category(r), 'MALFORMED_HTTP_STATUS')
                row = m.observation('MASSIVE', 'AAPL', '2026-10-27', r)
                self.assertEqual(row['validation_status'], 'BLOCKED')
                self.assertIsNone(row['price'])

    def test_unexpected_vendor_success_status_cannot_count_as_bar(self):
        for provider, original in [('MASSIVE', massive()), ('TWELVE_DATA', twelve())]:
            for bad in (None, 'partial', 'success', 'OK' if provider == 'TWELVE_DATA' else 'ok'):
                with self.subTest(provider=provider, status=bad):
                    r = copy.deepcopy(original)
                    if bad is None:
                        r['payload'].pop('status')
                    else:
                        r['payload']['status'] = bad
                    row = m.observation(provider, 'AAPL', '2026-10-27', r)
                    self.assertEqual(row['provider_error_category'], 'UNEXPECTED_PROVIDER_STATUS')
                    self.assertEqual(row['validation_status'], 'BLOCKED')
                    self.assertIsNone(row['price'])

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
                self.assertEqual(params['start_date'], m.SESSIONS[0])
                self.assertEqual(params['end_date'], m.SESSIONS[-1])
                self.assertNotIn('outputsize', params)
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
        with patch.object(m,'_open_no_redirect',side_effect=OSError('credential-value')):
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
        with patch.object(m,'_open_no_redirect',return_value=FakeResponse()):
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



    def test_bounded_date_window_is_stable_and_explicit(self):
        self.assertEqual(m._bounded_request_window(('AAPL', 'MSFT'),
                         ('2026-10-27', '2026-10-28')),
                         ('2026-10-27', '2026-10-28'))
        self.assertEqual(m._bounded_request_window(('AAPL',),
                         ('2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30')),
                         ('2026-10-27', '2026-10-30'))

    def test_invalid_date_or_request_budget_fails_before_network(self):
        invalid = [
            (('AAPL',), ('2026-10-28', '2026-10-27')),
            (('AAPL',), ('2026-10-27', '2026-10-27')),
            (('AAPL',), ('2026-10-27', '2026-11-30')),
            (('AAPL',), ('2026-10-99',)),
            (('AAPL', 'MSFT'), ('2026-10-27', '2026-10-28', '2026-10-29')),
            (('AAPL', 'AAPL'), ('2026-10-27',)),
            (('AAPL', 'MSFT', 'GOOG'), ('2026-10-27',)),
            (('AAPL/SECRET',), ('2026-10-27',)),
        ]
        with patch.object(m, 'get') as get:
            for symbols, sessions in invalid:
                with self.subTest(symbols=symbols, sessions=sessions):
                    with self.assertRaises(ValueError):
                        m.reconcile(symbols=symbols, sessions=sessions)
            get.assert_not_called()

    def test_date_filtered_batch_keeps_exact_requested_days_only(self):
        def fake(url, params, token):
            if 'twelvedata' in url:
                self.assertEqual(params['start_date'], '2026-10-27')
                self.assertEqual(params['end_date'], '2026-10-28')
                self.assertNotIn('outputsize', params)
                r = twelve([
                    {'datetime': '2026-10-26', 'close': '50'},
                    {'datetime': '2026-10-27', 'close': '100'},
                    {'datetime': '2026-10-28', 'close': '101'},
                    {'datetime': '2026-10-29', 'close': '75'},
                ])
                r['payload']['meta']['symbol'] = params['symbol']
                return r
            return massive(url.rsplit('/', 1)[-1], url.split('/')[-2])
        with patch.object(m, 'get', side_effect=fake) as get, patch.dict(
                'os.environ', {'MASSIVE_API_KEY': 'fixture', 'TWELVE_DATA_API_KEY': 'fixture'}):
            result = m.reconcile()
        self.assertEqual(get.call_count, 6)
        self.assertEqual(result['total_ticker_dates'], 4)
        self.assertEqual(result['valid_twelve_data_bars'], 4)
        self.assertEqual({row['session'] for row in result['rows']},
                         {'2026-10-27', '2026-10-28'})
        self.assertFalse(result['official_exchange_close_verified'])
        self.assertFalse(result['outcome_scoring_eligible'])


    def test_redirects_cannot_relabel_another_source_as_vendor(self):
        # Even an apparently benign same-origin 302 is not independently
        # authenticated and must not silently turn into a different provider.
        req = m.request.Request('https://api.massive.com/v1/open-close/AAPL/2026-10-27?apiKey=canary')
        handler = m._NoRedirectHandler()
        self.assertIsNone(handler.redirect_request(
            req, None, 302, 'Found',
            {'Location': 'https://other-provider.example/echo?apiKey=canary'},
            'https://other-provider.example/echo?apiKey=canary'))
        self.assertIsNone(handler.redirect_request(
            req, None, 301, 'Moved',
            {'Location': '/new-location'}, 'https://api.massive.com/new-location'))

    def test_redirect_response_is_censored_without_leaking_location(self):
        secret = 'canary-token-redirect'
        class RedirectResponse:
            code = 302
            headers = {'Location': 'https://other-provider.example/?apiKey=' + secret}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                return b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":100}'
        with patch.object(m, '_open_no_redirect', return_value=RedirectResponse()) as opened:
            fetched = m.get('https://api.massive.com/v1/open-close/AAPL/2026-10-27',
                            {'apiKey': secret}, secret)
        opened.assert_called_once()
        row = m.observation('MASSIVE', 'AAPL', '2026-10-27', fetched)
        self.assertEqual(row['provider_error_category'], 'UNTRUSTED_REDIRECT')
        self.assertEqual(row['validation_status'], 'BLOCKED')
        self.assertIsNone(row['price'])
        self.assertNotIn(secret, json.dumps(row))
        self.assertNotIn('other-provider.example', json.dumps(row))


    def test_ambiguous_vendor_json_keys_and_nonfinite_constants_are_censored(self):
        # A last-key-wins JSON decoder could turn a provider error into OK,
        # change the security identity, or overwrite a close. The body hash
        # remains a complete-byte receipt hash, NOT official-close proof.
        import hashlib
        class RawResponse:
            code = 200
            headers = {}
            def __init__(self, raw): self.raw = raw
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                self_limit = limit
                self_raw = self.raw
                if self_limit != 150001:
                    raise AssertionError("unexpected read budget")
                return self_raw

        bodies = [
            b'{"status":"error","status":"OK","symbol":"AAPL","from":"2026-10-27","close":100}',
            b'{"status":"OK","symbol":"AAPL","symbol":"MSFT","from":"2026-10-27","close":100}',
            b'{"status":"ok","meta":{"symbol":"AAPL","symbol":"MSFT"},"values":[]}',
            b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":100,"close":80}',
            b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":NaN}',
            b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":Infinity}',
            b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":-Infinity}',
        ]
        for raw in bodies:
            with self.subTest(raw=raw), patch.object(
                    m, '_open_no_redirect', return_value=RawResponse(raw)):
                fetched = m.get('https://api.massive.com/v1/open-close',
                                {'apiKey': 'fixture'}, 'fixture')
                self.assertEqual(fetched['http_status'], 200)
                self.assertEqual(fetched['body_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertIsNone(fetched['payload'])
                self.assertEqual(m.category(fetched), 'MALFORMED_RESPONSE')
                row = m.observation('MASSIVE', 'AAPL', '2026-10-27', fetched)
                self.assertEqual(row['validation_status'], 'BLOCKED')
                self.assertIsNone(row['price'])
                self.assertFalse(row['raw_body_retained'])

    def test_oversized_provider_body_never_claims_complete_response_hash(self):
        # A 150001-byte bounded read is only a prefix of an unknown body.
        # It must be censored without retaining a misleading SHA256.
        class Oversized:
            code = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                self_limit = limit
                if self_limit != 150001:
                    raise AssertionError("unexpected read budget")
                return b'{' + b'x' * 150000
        with patch.object(m, '_open_no_redirect', return_value=Oversized()):
            fetched = m.get('https://api.massive.com/v1/open-close',
                            {'apiKey': 'canary'}, 'canary')
        self.assertEqual(fetched['error'], 'RESPONSE_BODY_TOO_LARGE')
        self.assertTrue(fetched['body_truncated'])
        self.assertIsNone(fetched['body_sha256'])
        self.assertIsNone(fetched['payload'])
        row = m.observation('MASSIVE', 'AAPL', '2026-10-27', fetched)
        self.assertEqual(row['provider_error_category'], 'RESPONSE_BODY_TOO_LARGE')
        self.assertTrue(row['response_body_truncated'])
        self.assertIsNone(row['raw_response_hash'])
        self.assertEqual(row['validation_status'], 'BLOCKED')

    def test_exact_boundary_body_is_complete_and_hashable(self):
        import hashlib
        raw = b'{"status":"OK"}'
        raw += b' ' * (150000 - len(raw))
        class Boundary:
            code = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                self_limit = limit
                if self_limit != 150001:
                    raise AssertionError("unexpected read budget")
                return raw
        with patch.object(m, '_open_no_redirect', return_value=Boundary()):
            fetched = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
        self.assertFalse(fetched['body_truncated'])
        self.assertIsNone(fetched['error'])
        self.assertEqual(fetched['body_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(fetched['payload'], {'status': 'OK'})

    def test_oversized_429_still_stops_paid_request_budget(self):
        blocked = dict(http_status=429, error='RESPONSE_BODY_TOO_LARGE',
                       payload=None, body_truncated=True, body_sha256=None,
                       headers={}, retrieved_at='2026-10-31T16:00:00Z')
        with patch.object(m, 'get', return_value=blocked) as get:
            budget = m.Budget(4)
            self.assertEqual(budget.fetch('url', {}, 'token')['error'],
                             'RESPONSE_BODY_TOO_LARGE')
            self.assertEqual(budget.fetch('url', {}, 'token')['error'], 'RATE_LIMIT')
        get.assert_called_once()


    def test_http_denial_category_survives_oversized_or_malformed_body(self):
        # Preserve the real provider access/quota blocker, without treating
        # an incomplete response as hashable or as a valid price observation.
        for status, reason in [(401, 'AUTHENTICATION'),
                               (403, 'ENTITLEMENT_OR_ACCESS'),
                               (429, 'RATE_LIMIT')]:
            for body_error in ('RESPONSE_BODY_TOO_LARGE', 'MALFORMED_RESPONSE'):
                with self.subTest(status=status, body_error=body_error):
                    blocked = receipt(None, status)
                    blocked.update(error=body_error, payload=None, body_sha256=None,
                                   body_truncated=body_error == 'RESPONSE_BODY_TOO_LARGE')
                    self.assertEqual(m.category(blocked), reason)
                    row = m.observation('MASSIVE', 'AAPL', '2026-10-27', blocked)
                    self.assertEqual(row['provider_error_category'], reason)
                    self.assertEqual(row['response_body_truncated'],
                                     body_error == 'RESPONSE_BODY_TOO_LARGE')
                    self.assertIsNone(row['raw_response_hash'])
                    self.assertIsNone(row['price'])
                    self.assertEqual(row['validation_status'], 'BLOCKED')
                    with patch.object(m, 'get', return_value=blocked) as get:
                        budget = m.Budget(4)
                        budget.fetch('url', {}, 'fixture')
                        self.assertEqual(budget.fetch('url', {}, 'fixture')['error'], reason)
                    get.assert_called_once()




    def test_ambiguous_provider_errors_stop_remaining_paid_requests(self):
        # No second paid request after an unknown or malformed provider
        # response that could hide quota/entitlement denial.
        cases = [
            ({'status': 'error', 'code': '429'}, 'MALFORMED_RESPONSE'),
            ({'status': 'error', 'code': 499}, 'PROVIDER_ERROR'),
            ({'status': 'partial'}, 'UNEXPECTED_PROVIDER_STATUS'),
            ({}, 'UNEXPECTED_PROVIDER_STATUS'),
            (None, 'MALFORMED_RESPONSE'),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                first = receipt(payload)
                with patch.object(m, 'get', return_value=first) as fetch:
                    budget = m.Budget(4)
                    self.assertEqual(m.category(budget.fetch('url', {}, 'token')), expected)
                    self.assertEqual(budget.fetch('url', {}, 'token')['error'],
                                     'UNVERIFIABLE_PROVIDER_RESPONSE')
                    self.assertEqual(budget.used, 1)
                fetch.assert_called_once()
        oversized = receipt(None)
        oversized.update(error='RESPONSE_BODY_TOO_LARGE', body_truncated=True)
        with patch.object(m, 'get', return_value=oversized) as fetch:
            budget = m.Budget(4)
            budget.fetch('url', {}, 'token')
            self.assertEqual(budget.fetch('url', {}, 'token')['error'],
                             'UNVERIFIABLE_PROVIDER_RESPONSE')
        fetch.assert_called_once()

    def test_zero_padded_remaining_quota_stops_paid_requests(self):
        for remaining in ('0', '00', '0000'):
            with self.subTest(remaining=remaining):
                first = massive()
                first['headers'] = {'x-ratelimit-remaining': remaining}
                with patch.object(m, 'get', return_value=first) as fetch:
                    budget = m.Budget(4)
                    budget.fetch('url', {}, 'token')
                    self.assertEqual(budget.fetch('url', {}, 'token')['error'],
                                     'RATE_LIMIT')
                    self.assertEqual(budget.used, 1)
                fetch.assert_called_once()


if __name__=='__main__':unittest.main()
