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


if __name__=='__main__':unittest.main()
