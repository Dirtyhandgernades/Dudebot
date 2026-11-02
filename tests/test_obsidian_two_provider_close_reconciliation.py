import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from backtest import obsidian_two_provider_close_reconciliation as m


def receipt(payload=None, status=200):
    return dict(http_status=status, payload=payload, body_sha256='fixture',
                retrieved_at='2026-10-29T17:00:00+00:00',
                requested_at='2026-10-29T16:59:59+00:00', headers={})


def massive(day='2026-10-27', symbol='AAPL', close=100):
    return receipt(dict(status='OK', symbol=symbol, **{'from': day}, close=close))


def twelve(bars=None):
    return receipt(dict(status='ok', meta=dict(symbol='AAPL', exchange='NASDAQ'),
                        values=bars if bars is not None else [dict(datetime='2026-10-27', close='100')]))


class ReconciliationTests(unittest.TestCase):
    def test_official_close_proof_inventory_preserved_for_missing_and_matching_bars(self):
        # Numeric vendor agreement is not an official close, and no collected
        # third-source evidence must never be reported as no conflict.
        with patch.dict("os.environ", {}, clear=True):
            missing = m.reconcile()
        self.assertEqual(missing["official_close_censored_count"], 4)
        self.assertEqual(missing["official_close_eligible_count"], 0)
        self.assertEqual(missing["third_source_conflict_inventory_count"], 0)
        self.assertEqual(missing["third_source_conflict_inventory_status"], "NOT_COLLECTED")
        self.assertEqual(len(missing["official_close_proof_requirements"]), 8)
        for row in missing["rows"]:
            self.assertEqual(row["missing_official_close_proofs"],
                             missing["official_close_proof_requirements"])
            self.assertEqual(row["official_close_evidence_status"], "CENSORED_UNVERIFIED")
            self.assertEqual(row["third_source_conflict_status"], "NOT_COLLECTED")
            self.assertFalse(row["eligible_official_close"])

        def fake(url, params, token):
            if "twelvedata" in url:
                r = twelve([{"datetime": d, "close": "100"} for d in m.SESSIONS])
                r["payload"]["meta"]["symbol"] = params["symbol"]
                return r
            return massive(url.rsplit("/", 1)[-1], url.split("/")[-2])
        with patch.object(m, "get", side_effect=fake), patch.dict(
                "os.environ", {"MASSIVE_API_KEY": "fixture", "TWELVE_DATA_API_KEY": "fixture"}):
            paired = m.reconcile()
        self.assertEqual(paired["both_bar_count"], 4)
        self.assertEqual(paired["official_close_censored_count"], 4)
        self.assertEqual(paired["official_close_eligible_count"], 0)
        self.assertEqual(paired["third_source_conflict_inventory_count"], 0)
        for row in paired["rows"]:
            self.assertTrue(row["diagnostic_numeric_agreement_only"])
            self.assertEqual(row["comparison_status"], "IDENTITY_UNVERIFIED")
            self.assertEqual(row["missing_official_close_proofs"],
                             paired["official_close_proof_requirements"])
            self.assertEqual(row["third_source_conflict_status"], "NOT_COLLECTED")
            self.assertFalse(row["eligible_official_close"])

    def test_unreviewed_vendor_numeric_conflicts_are_not_silently_reported_as_zero(self):
        # The authenticated-identity comparison is intentionally unavailable,
        # but real numeric vendor disagreements still need an explicit,
        # separately labeled diagnostic count and difference.
        def fake(url, params, token):
            if "twelvedata" in url:
                r = twelve([{"datetime": d, "close": "100"} for d in m.SESSIONS])
                r["payload"]["meta"]["symbol"] = params["symbol"]
                return r
            day = url.rsplit("/", 1)[-1]
            symbol = url.split("/")[-2]
            return massive(day, symbol, close="100.02" if day == "2026-10-27" else "100")
        with patch.object(m, "get", side_effect=fake), patch.dict(
                "os.environ", {"MASSIVE_API_KEY": "fixture", "TWELVE_DATA_API_KEY": "fixture"}):
            result = m.reconcile()
        self.assertEqual(result["total_ticker_dates"], 4)
        self.assertEqual(result["both_bar_count"], 4)
        self.assertEqual(result["conflict_count"], 0)  # No authenticated identity review.
        self.assertEqual(result["vendor_bar_numeric_conflict_unverified_identity_count"], 2)
        self.assertEqual(result["vendor_bar_numeric_agreement_unverified_identity_count"], 2)
        self.assertEqual(result["official_close_eligible_count"], 0)
        self.assertEqual(result["third_source_conflict_inventory_count"], 0)
        for row in result["rows"]:
            self.assertEqual(row["comparison_status"], "IDENTITY_UNVERIFIED")
            self.assertEqual(row["official_close_evidence_status"], "CENSORED_UNVERIFIED")
            self.assertEqual(len(row["missing_official_close_proofs"]), 8)
            if row["session"] == "2026-10-27":
                self.assertTrue(row["vendor_bar_numeric_conflict_unverified_identity"])
                self.assertEqual(row["vendor_bar_numeric_difference_usd_unverified_identity"], "0.02")
            else:
                self.assertFalse(row["vendor_bar_numeric_conflict_unverified_identity"])
                self.assertEqual(row["vendor_bar_numeric_difference_usd_unverified_identity"], "0")

        with patch.dict("os.environ", {}, clear=True):
            absent = m.reconcile()
        self.assertEqual(absent["vendor_bar_numeric_conflict_unverified_identity_count"], 0)
        self.assertEqual(absent["vendor_bar_numeric_agreement_unverified_identity_count"], 0)
        self.assertTrue(all(row["vendor_bar_numeric_conflict_unverified_identity"] is None
                            and row["vendor_bar_numeric_difference_usd_unverified_identity"] is None
                            for row in absent["rows"]))

    def pair(self):
        return (m.observation('MASSIVE', 'AAPL', '2026-10-27', massive()),
                m.observation('TWELVE_DATA', 'AAPL', '2026-10-27', twelve()))

    def identity(self):
        return dict(ticker='AAPL', session_date='2026-10-27', security_id='reviewed-id',
                    identity_verified=True, exchange_verified=True, corporate_actions_verified=True,
                    corporate_action_changed=False, source_receipts=['fixture-review'])

    def test_diagnostic_agreement_requires_two_recognized_distinct_vendor_organizations(self):
        # A copied vendor response, alias or missing organization cannot be
        # laundered into a two-organization diagnostic comparison merely by
        # supplying external identity-review flags.
        a, b = self.pair()
        reviewed = self.identity()
        self.assertEqual(m.compare(a, b, reviewed), ("VENDOR_BAR_AGREEMENT_NOT_OFFICIAL", "0"))
        self.assertEqual(m.compare(b, a, reviewed), ("VENDOR_BAR_AGREEMENT_NOT_OFFICIAL", "0"))
        for org_a, org_b in [("MASSIVE", "MASSIVE"),
                             ("TWELVE_DATA", "TWELVE_DATA"),
                             ("MASSIVE", "POLYGON"),
                             ("MASSIVE", None),
                             (None, None)]:
            with self.subTest(org_a=org_a, org_b=org_b):
                x, y = dict(a), dict(b)
                x["provider_organization"] = org_a
                y["provider_organization"] = org_b
                self.assertEqual(m.compare(x, y, reviewed),
                                 ("PROVIDER_ORGANIZATION_NOT_DISTINCT_OR_UNRECOGNIZED", None))
        # Recognized names alone do NOT change official outcome eligibility.
        self.assertFalse(a["identity_verified"])
        self.assertFalse(b["identity_verified"])

    def test_self_attested_review_flags_cannot_be_official_close_agreement(self):
        # A source_receipts list containing only caller-supplied strings is
        # not independent authentication of official exchange closes.
        a, b = self.pair()
        forged = self.identity()
        forged['source_receipts'] = ['self-attested-review-only']
        status, difference = m.compare(a, b, forged)
        self.assertEqual(status, 'VENDOR_BAR_AGREEMENT_NOT_OFFICIAL')
        self.assertEqual(difference, '0')
        self.assertNotIn(status, {'AGREE', 'DISAGREE'})
        b['price'] = '100.01'
        status, difference = m.compare(a, b, forged)
        self.assertEqual(status, 'VENDOR_BAR_CONFLICT_NOT_OFFICIAL')
        self.assertEqual(difference, '0.01')
        self.assertNotIn(status, {'AGREE', 'DISAGREE'})

    def test_matching_requires_reviewed_identity(self):
        a, b = self.pair()
        self.assertEqual(m.compare(a, b)[0], 'IDENTITY_UNVERIFIED')
        self.assertEqual(m.compare(a, b, self.identity()), ('VENDOR_BAR_AGREEMENT_NOT_OFFICIAL', '0'))

    def test_exact_decimal_tolerance_and_disagreement(self):
        a, b = self.pair()
        b['price'] = '100.005'
        self.assertEqual(m.compare(a, b, self.identity())[0], 'VENDOR_BAR_AGREEMENT_NOT_OFFICIAL')
        b['price'] = '100.005001'
        self.assertEqual(m.compare(a, b, self.identity())[0], 'VENDOR_BAR_CONFLICT_NOT_OFFICIAL')

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
            self.assertNotEqual(m.compare(a, other, self.identity())[0], 'VENDOR_BAR_AGREEMENT_NOT_OFFICIAL')

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

    def test_duplicate_or_invalid_remaining_quota_headers_fail_closed(self):
        # A last-header-wins dict can turn '0, 9' into nine apparently
        # remaining paid calls. Preserve no selected ambiguous quota value.
        from email.message import Message

        class FakeResponse:
            code = 200
            def __init__(self, values):
                self.headers = Message()
                self.headers.add_header("Content-Type", "application/json")
                for value in values:
                    self.headers.add_header("X-RateLimit-Remaining", value)
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                return b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":100}'

        for values in (("0", "9"), ("0", "0"), ("not-numeric",), ("0, 9",)):
            with self.subTest(values=values), patch.object(
                    m, "_open_no_redirect", side_effect=lambda req: FakeResponse(values)) as opened:
                budget = m.Budget(4)
                first = budget.fetch("https://api.massive.com/v1/open-close", {}, "fixture")
                self.assertEqual(first["error"], "UNVERIFIED_QUOTA_HEADER")
                self.assertTrue(first["quota_header_unverified"])
                self.assertNotIn("x-ratelimit-remaining", first["headers"])
                self.assertIsNotNone(first["body_sha256"])
                self.assertEqual(m.category(first), "UNVERIFIED_QUOTA_HEADER")
                row = m.observation("MASSIVE", "AAPL", "2026-10-27", first)
                self.assertTrue(row["response_quota_header_unverified"])
                self.assertEqual(row["validation_status"], "BLOCKED")
                self.assertIsNone(row["price"])
                self.assertEqual(budget.fetch("url", {}, "fixture")["error"],
                                 "UNVERIFIABLE_PROVIDER_RESPONSE")
                opened.assert_called_once()
        for values, expected in [(("0",), "RATE_LIMIT"), (("2",), None), ((), None)]:
            with self.subTest(valid_values=values), patch.object(
                    m, "_open_no_redirect", side_effect=lambda req: FakeResponse(values)):
                budget = m.Budget(4)
                first = budget.fetch("https://api.massive.com/v1/open-close", {}, "fixture")
                self.assertIsNone(first["error"])
                self.assertFalse(first["quota_header_unverified"])
                self.assertEqual(budget.stopped, expected)

    def test_ambiguous_quota_preserves_full_censored_cohort(self):
        from email.message import Message

        class FakeResponse:
            code = 200
            def __init__(self):
                self.headers = Message()
                self.headers.add_header("Content-Type", "application/json")
                self.headers.add_header("X-RateLimit-Remaining", "0")
                self.headers.add_header("X-RateLimit-Remaining", "99")
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                return b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":100}'

        with patch.object(m, "_open_no_redirect", side_effect=lambda req: FakeResponse()) as opened, \
                patch.dict("os.environ", {"MASSIVE_API_KEY": "fixture",
                                           "TWELVE_DATA_API_KEY": "fixture"}):
            result = m.reconcile()
        self.assertEqual(opened.call_count, 2)
        self.assertEqual(result["total_ticker_dates"], 4)
        self.assertEqual(result["missing_pair_count"], 4)
        self.assertEqual(result["both_bar_count"], 0)
        self.assertEqual(result["official_close_eligible_count"], 0)
        self.assertTrue(all(not row["eligible_official_close"] for row in result["rows"]))

    def test_vendor_json_exponent_overflow_and_underflow_are_censored(self):
        # Python's standard JSON float decoder otherwise turns these exact
        # source claims into infinity or zero, even in nested sideband fields.
        class FakeResponse:
            code = 200
            headers = {'Content-Type': 'application/json'}
            def __init__(self, raw): self.raw = raw
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n): return self.raw[:n]

        for exponent in ('1e309', '1e-400', '-1e-400'):
            raw = ('{"status":"OK","symbol":"AAPL","from":"2026-10-27",'
                   '"close":100,"nested":{"vendor_numeric":' + exponent + '}}').encode()
            with self.subTest(exponent=exponent), patch.object(
                    m, '_open_no_redirect', return_value=FakeResponse(raw)):
                r = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
                self.assertIsNone(r['payload'])
                self.assertEqual(m.category(r), 'MALFORMED_RESPONSE')
                self.assertIsNotNone(r['body_sha256'])
                row = m.observation('MASSIVE', 'AAPL', '2026-10-27', r)
                self.assertEqual(row['validation_status'], 'BLOCKED')
                self.assertIsNone(row['price'])

        valid = (b'{"status":"OK","symbol":"AAPL","from":"2026-10-27",'
                 b'"close":1.25e2,"nested":{"vendor_numeric":0.0}}')
        with patch.object(m, '_open_no_redirect', return_value=FakeResponse(valid)):
            r = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
        self.assertIsNone(m.category(r))
        self.assertEqual(r['payload']['close'], 125.0)

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
                     'X-RateLimit-Reset':'token='+secret,
                     'Content-Type':'application/json'}
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

    def test_twelve_missing_or_out_of_scope_exchange_is_censored(self):
        # A symbol echo is insufficient: do not compare OTC or unverified
        # exchange bars against a Nasdaq/NYSE listed security, and do not
        # silently treat NYSE American as NYSE in the frozen cohort.
        for venue in (None, "", "OTC", "NYSE American", "NYSE ARCA", "UNKNOWN"):
            with self.subTest(exchange=venue):
                r = twelve()
                if venue is None:
                    r["payload"]["meta"].pop("exchange")
                else:
                    r["payload"]["meta"]["exchange"] = venue
                row = m.observation("TWELVE_DATA", "AAPL", "2026-10-27", r)
                self.assertEqual(row["provider_error_category"],
                                 "EXCHANGE_UNVERIFIED_OR_OUT_OF_SCOPE")
                self.assertEqual(row["validation_status"], "BLOCKED")
                self.assertIsNone(row["price"])
                self.assertIsNone(row["exchange"])
                a = m.observation("MASSIVE", "AAPL", "2026-10-27", massive())
                self.assertEqual(m.compare(a, row)[0], "UNAVAILABLE")
        for venue in ("NASDAQ", "NYSE"):
            with self.subTest(eligible_exchange=venue):
                r = twelve()
                r["payload"]["meta"]["exchange"] = venue
                row = m.observation("TWELVE_DATA", "AAPL", "2026-10-27", r)
                self.assertEqual(row["validation_status"], "VALID_VENDOR_BAR")
                self.assertEqual(row["exchange"], venue)

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
            headers = {"Content-Type": "application/json"}
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
            headers = {"Content-Type": "application/json"}
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
            headers = {"Content-Type": "application/json"}
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



    def test_provider_specific_status_mismatch_stops_paid_budget(self):
        # A status accepted by the generic classifier can be wrong for the
        # actual provider. Reject it before another paid request.
        for returned, expected in [('ok', 'OK'), ('OK', 'ok')]:
            with self.subTest(returned=returned, expected=expected):
                first = receipt({'status': returned})
                with patch.object(m, 'get', return_value=first) as fetch:
                    budget = m.Budget(4)
                    initial = budget.fetch('url', {}, 'fixture', expected_status=expected)
                    self.assertEqual(m.category(initial), 'UNEXPECTED_PROVIDER_STATUS')
                    self.assertEqual(budget.fetch('url', {}, 'fixture',
                                                  expected_status=expected)['error'],
                                     'UNVERIFIABLE_PROVIDER_RESPONSE')
                    self.assertEqual(budget.used, 1)
                fetch.assert_called_once()

    def test_reconcile_wrong_massive_status_censors_fixed_denominator(self):
        def fake(url, params, token):
            if 'twelvedata' in url:
                response = twelve([{'datetime': day, 'close': '100'} for day in m.SESSIONS])
                response['payload']['meta']['symbol'] = params['symbol']
                return response
            response = massive(url.rsplit('/', 1)[-1], url.split('/')[-2])
            response['payload']['status'] = 'ok'
            return response
        with patch.object(m, 'get', side_effect=fake) as fetch, patch.dict(
                'os.environ', {'MASSIVE_API_KEY': 'fixture',
                               'TWELVE_DATA_API_KEY': 'fixture'}):
            result = m.reconcile()
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(result['request_budget']['massive_used'], 1)
        self.assertEqual(result['total_ticker_dates'], 4)
        self.assertEqual(result['both_bar_count'], 0)
        self.assertEqual(result['missing_pair_count'], 4)
        self.assertEqual(result['rows'][0]['providers']['MASSIVE']['provider_error_category'],
                         'UNEXPECTED_PROVIDER_STATUS')
        self.assertTrue(all(
            row['providers']['MASSIVE']['provider_error_category'] in
            {'UNEXPECTED_PROVIDER_STATUS', 'UNVERIFIABLE_PROVIDER_RESPONSE'}
            for row in result['rows']))
        self.assertFalse(result['official_exchange_close_verified'])
        self.assertFalse(result['outcome_scoring_eligible'])


    def test_json_content_type_missing_wrong_or_duplicate_fails_closed(self):
        # HTTP 200 plus parseable JSON is insufficient if the server did not
        # provide one unambiguous JSON media type. Preserve a bounded hash,
        # but never treat the payload as a valid vendor daily bar.
        from email.message import Message
        raw = b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":100}'

        class Response:
            def __init__(self, types, code=200):
                self.code = code
                self.headers = Message()
                for value in types:
                    self.headers.add_header("Content-Type", value)
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                self_limit = limit
                if self_limit != 150001: raise AssertionError("bounded read changed")
                return raw

        for types in ((), ("text/plain",), ("application/octet-stream",),
                      ("application/json", "application/json"),
                      ("application/json", "text/html")):
            with self.subTest(types=types), patch.object(
                    m, "_open_no_redirect", return_value=Response(types)):
                got = m.get("https://api.massive.com/v1/open-close", {}, "fixture")
            self.assertEqual(got["error"], "UNVERIFIED_JSON_CONTENT_TYPE")
            self.assertTrue(got["content_type_unverified"])
            self.assertIsNone(got["payload"])
            self.assertIsNotNone(got["body_sha256"])
            self.assertEqual(m.category(got), "UNVERIFIED_JSON_CONTENT_TYPE")
            row = m.observation("MASSIVE", "AAPL", "2026-10-27", got)
            self.assertEqual(row["validation_status"], "BLOCKED")
            self.assertTrue(row["response_content_type_unverified"])
            self.assertIsNone(row["price"])
            with patch.object(m, "get", return_value=got) as fetch:
                budget = m.Budget(4)
                budget.fetch("url", {}, "fixture", expected_status="OK")
                self.assertEqual(budget.fetch("url", {}, "fixture")["error"],
                                 "UNVERIFIABLE_PROVIDER_RESPONSE")
                fetch.assert_called_once()

        with patch.object(m, "_open_no_redirect",
                          return_value=Response(("application/json; charset=utf-8",))):
            valid = m.get("https://api.massive.com/v1/open-close", {}, "fixture")
        self.assertIsNone(valid["error"])
        self.assertFalse(valid["content_type_unverified"])
        self.assertEqual(valid["payload"]["close"], 100)

        # An explicit HTTP authorization denial takes precedence over a
        # missing media type; the budget still stops on that first request.
        with patch.object(m, "_open_no_redirect", return_value=Response((), 403)):
            denied = m.get("https://api.massive.com/v1/open-close", {}, "fixture")
        self.assertEqual(m.category(denied), "ENTITLEMENT_OR_ACCESS")

    def test_declared_http_length_mismatch_censors_complete_hash_and_budget(self):
        # A valid-looking JSON prefix cannot establish a complete receipt
        # when Content-Length contradicts the bytes actually received.
        import hashlib
        raw = b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":100}'
        class FakeResponse:
            code = 200
            def __init__(self, declared):
                self.headers = {"Content-Length": declared, "Content-Type": "application/json"}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                self_limit = limit
                if self_limit != 150001: raise AssertionError("read bound changed")
                return raw
        for declared in (str(len(raw) - 1), str(len(raw) + 1),
                         "malformed", "12, 12"):
            with self.subTest(declared=declared), patch.object(
                    m, '_open_no_redirect', return_value=FakeResponse(declared)):
                r = m.get('https://api.massive.com/v1/open-close',
                          {'apiKey': 'fixture'}, 'fixture')
                self.assertEqual(r['http_status'], 200)
                self.assertEqual(r['error'], 'RESPONSE_LENGTH_MISMATCH')
                self.assertTrue(r['body_length_mismatch'])
                self.assertIsNone(r['body_sha256'])
                self.assertIsNone(r['payload'])
                row = m.observation('MASSIVE', 'AAPL', '2026-10-27', r)
                self.assertEqual(row['provider_error_category'],
                                 'RESPONSE_LENGTH_MISMATCH')
                self.assertTrue(row['response_length_mismatch'])
                self.assertIsNone(row['raw_response_hash'])
                self.assertIsNone(row['price'])
                with patch.object(m, 'get', return_value=r) as get:
                    budget = m.Budget(4)
                    budget.fetch('url', {}, 'fixture', expected_status='OK')
                    self.assertEqual(budget.fetch('url', {}, 'fixture')['error'],
                                     'UNVERIFIABLE_PROVIDER_RESPONSE')
                    self.assertEqual(budget.used, 1)
                get.assert_called_once()
        with patch.object(m, '_open_no_redirect',
                          return_value=FakeResponse(str(len(raw)))):
            good = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
        self.assertFalse(good['body_length_mismatch'])
        self.assertIsNone(good['error'])
        self.assertEqual(good['body_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(good['payload']['close'], 100)

    def test_duplicate_content_length_headers_are_not_silently_collapsed(self):
        # HTTP Message.get() exposes only the first of multiple headers.
        # Identical duplicates are still ambiguous receipt framing.
        from email.message import Message
        raw = b'{"status":"OK","symbol":"AAPL","from":"2026-10-27","close":100}'

        class RawResponse:
            code = 200
            def __init__(self, lengths):
                self.headers = Message()
                self.headers.add_header("Content-Type", "application/json")
                for length in lengths:
                    self.headers.add_header("Content-Length", length)
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                self_limit = limit
                if self_limit != 150001:
                    raise AssertionError("unexpected read budget")
                return raw

        valid = str(len(raw))
        for declarations in ((valid, valid), (valid, str(len(raw) + 5))):
            with self.subTest(declarations=declarations), patch.object(
                    m, '_open_no_redirect', return_value=RawResponse(declarations)):
                got = m.get('https://api.massive.com/v1/open-close',
                            {'apiKey': 'fixture'}, 'fixture')
                self.assertEqual(got['error'], 'RESPONSE_LENGTH_MISMATCH')
                self.assertTrue(got['body_length_mismatch'])
                self.assertIsNone(got['payload'])
                self.assertIsNone(got['body_sha256'])
                self.assertEqual(
                    m.observation('MASSIVE', 'AAPL', '2026-10-27', got)['validation_status'],
                    'BLOCKED')
        with patch.object(m, '_open_no_redirect',
                          return_value=RawResponse((valid,))):
            good = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
        self.assertIsNone(good['error'])
        self.assertEqual(good['payload']['close'], 100)


    def test_same_day_vendor_daily_bar_censored_until_request_after_16_et(self):
        # Oct 27 is EDT (20:00Z cutoff); Nov 2 is EST (21:00Z).
        # Response completion after close cannot rescue a preclose request.
        for day, before, boundary, after in [
            ('2026-10-27', '2026-10-27T19:59:59Z',
             '2026-10-27T20:00:00Z', '2026-10-27T20:00:01Z'),
            ('2026-11-02', '2026-11-02T20:59:59Z',
             '2026-11-02T21:00:00Z', '2026-11-02T21:00:01Z'),
        ]:
            for requested in (before, boundary, None, 'bad',
                              day + 'T23:59:59'):
                with self.subTest(day=day, requested=requested):
                    r = massive(day=day)
                    r['requested_at'] = requested
                    r['retrieved_at'] = after
                    row = m.observation('MASSIVE', 'AAPL', day, r)
                    self.assertEqual(row['provider_error_category'],
                                     'SESSION_NOT_COMPLETE_AT_REQUEST_OR_TIMESTAMP_UNVERIFIED')
                    self.assertEqual(row['validation_status'], 'BLOCKED')
                    self.assertIsNone(row['price'])
                    self.assertFalse(row['identity_verified'])
            r = massive(day=day)
            r['requested_at'] = after
            r['retrieved_at'] = after
            row = m.observation('MASSIVE', 'AAPL', day, r)
            self.assertEqual(row['validation_status'], 'VALID_VENDOR_BAR')
            self.assertFalse(row['identity_verified'])

    def test_request_start_timestamp_not_vendor_body_controls_completion(self):
        # No timestamp from the vendor payload can replace a missing local
        # request-start receipt. This gate does not prove official closes.
        r = massive()
        r['payload']['retrieved_at'] = '2026-10-29T00:00:00Z'
        r.pop('requested_at')
        row = m.observation('MASSIVE', 'AAPL', '2026-10-27', r)
        self.assertEqual(row['provider_error_category'],
                         'SESSION_NOT_COMPLETE_AT_REQUEST_OR_TIMESTAMP_UNVERIFIED')
        self.assertEqual(row['validation_status'], 'BLOCKED')
        self.assertIsNone(row['price'])

    def test_vendor_receipt_requires_monotonic_local_timestamps(self):
        # A forged or broken local receipt cannot be a valid vendor bar even
        # when the payload claims the right ticker, session and close.
        session_block = 'SESSION_NOT_COMPLETE_AT_REQUEST_OR_TIMESTAMP_UNVERIFIED'
        receipt_block = 'RECEIPT_TIMESTAMP_ORDER_UNVERIFIED'
        cases = [
            (None, '2026-10-29T17:00:00Z', session_block),
            ('2026-10-29T16:59:59Z', None, receipt_block),
            ('2026-10-29T16:59:59', '2026-10-29T17:00:00Z', session_block),
            ('2026-10-29T16:59:59Z', '2026-10-29T17:00:00', receipt_block),
            ('2026-10-29T17:00:01Z', '2026-10-29T17:00:00Z', receipt_block),
            ('bad', '2026-10-29T17:00:00Z', session_block),
        ]
        for started, finished, expected in cases:
            with self.subTest(started=started, finished=finished):
                r = massive()
                r['requested_at'] = started
                r['retrieved_at'] = finished
                r['payload']['retrieved_at'] = '2026-10-30T12:00:00Z'
                row = m.observation('MASSIVE', 'AAPL', '2026-10-27', r)
                self.assertEqual(row['provider_error_category'], expected)
                self.assertEqual(row['validation_status'], 'BLOCKED')
                self.assertIsNone(row['price'])
                self.assertFalse(row['identity_verified'])

    def test_receipt_timestamp_order_compares_instants_not_clock_strings(self):
        r = massive()
        # 12:59 -04:00 is 16:59Z; 17:00Z follows one minute later.
        r['requested_at'] = '2026-10-29T12:59:00-04:00'
        r['retrieved_at'] = '2026-10-29T17:00:00Z'
        self.assertEqual(m.observation('MASSIVE', 'AAPL', '2026-10-27',
                                       r)['validation_status'], 'VALID_VENDOR_BAR')
        r['retrieved_at'] = '2026-10-29T12:58:59-04:00'
        self.assertEqual(m.observation('MASSIVE', 'AAPL', '2026-10-27',
                                       r)['provider_error_category'],
                         'RECEIPT_TIMESTAMP_ORDER_UNVERIFIED')

    def test_published_2026_full_closures_and_weekends_fail_before_paid_requests(self):
        # NYSE 2026 published holiday list, plus Saturday/Sunday. A vendor
        # bar on one of these dates is not a regular-session closing price.
        closed = ('2026-01-01', '2026-01-19', '2026-02-16',
                  '2026-04-03', '2026-05-25', '2026-06-19',
                  '2026-07-03', '2026-09-07', '2026-11-26',
                  '2026-12-25', '2026-10-31', '2026-11-01')
        with patch.object(m, 'get') as get:
            for day in closed:
                with self.subTest(day=day):
                    with self.assertRaisesRegex(ValueError,
                            'CLOSED_OR_UNVERIFIED_EXCHANGE_SESSION'):
                        m.reconcile(symbols=('AAPL',), sessions=(day,))
                    row = m.observation('MASSIVE', 'AAPL', day, massive(day=day))
                    self.assertEqual(row['provider_error_category'],
                                     'CLOSED_OR_UNVERIFIED_EXCHANGE_SESSION')
                    self.assertEqual(row['validation_status'], 'BLOCKED')
                    self.assertIsNone(row['price'])
            get.assert_not_called()

    def test_static_calendar_is_not_proof_and_early_close_cutoff_stays_conservative(self):
        for day in ('2026-10-12', '2026-10-27', '2026-11-11',
                    '2026-11-27', '2026-12-24'):
            with self.subTest(day=day):
                self.assertEqual(m._bounded_request_window(('AAPL',), (day,)),
                                 (day, day))
        # Thanksgiving Friday 2026 closes at 13:00 ET, but a request
        # starting at 15:59 ET is conservatively blocked until after 16:00.
        r = massive(day='2026-11-27')
        r['requested_at'] = '2026-11-27T20:59:59Z'
        r['retrieved_at'] = '2026-11-27T21:00:02Z'
        self.assertEqual(m.observation('MASSIVE', 'AAPL', '2026-11-27', r)[
            'provider_error_category'],
            'SESSION_NOT_COMPLETE_AT_REQUEST_OR_TIMESTAMP_UNVERIFIED')
        r['requested_at'] = '2026-11-27T21:00:01Z'
        row = m.observation('MASSIVE', 'AAPL', '2026-11-27', r)
        self.assertEqual(row['validation_status'], 'VALID_VENDOR_BAR')
        self.assertFalse(row['identity_verified'])
        self.assertEqual(row['price_type'], 'VENDOR_DAILY_OHLC_CLOSE')
        self.assertFalse(m.reconcile(symbols=('AAPL',), sessions=('2026-10-27',))[
            'official_exchange_close_verified'])

    def test_unknown_year_fails_closed_without_calendar_rollover(self):
        with patch.object(m, 'get') as get:
            with self.assertRaisesRegex(ValueError,
                    'CLOSED_OR_UNVERIFIED_EXCHANGE_SESSION'):
                m.reconcile(symbols=('AAPL',), sessions=('2027-01-04',))
            get.assert_not_called()
        row = m.observation('MASSIVE', 'AAPL', '2027-01-04',
                            massive(day='2027-01-04'))
        self.assertEqual(row['provider_error_category'],
                         'CLOSED_OR_UNVERIFIED_EXCHANGE_SESSION')
        self.assertIsNone(row['price'])


    def test_transport_and_redirect_failures_stop_same_run_provider_budget(self):
        # A network failure or HTTP redirect cannot establish source origin.
        # Neither may trigger more paid requests to that provider in the
        # same bounded diagnostic, while the exact first error is retained.
        for initial, expected in [
            (dict(error='NETWORK_UNAVAILABLE', http_status=None,
                  payload=None, headers={}), 'NETWORK_UNAVAILABLE'),
            (receipt({'status': 'OK'}, status=302), 'UNTRUSTED_REDIRECT'),
        ]:
            with self.subTest(error=expected), patch.object(
                    m, 'get', return_value=initial) as fetch:
                budget = m.Budget(4)
                first = budget.fetch('url', {}, 'fixture', expected_status='OK')
                second = budget.fetch('url', {}, 'fixture', expected_status='OK')
                self.assertEqual(m.category(first), expected)
                self.assertEqual(second['error'], expected)
                self.assertEqual(budget.stopped, expected)
                self.assertEqual(budget.used, 1)
                fetch.assert_called_once()

    def test_http_400_bad_request_stops_provider_but_preserves_other_budget(self):
        # Invalid endpoint/query parameters should not cause a series of
        # repeated paid requests to the same failing provider. A separate
        # provider must retain its own request budget and the frozen four
        # symbol/session slots remain censored, not deleted.
        with patch.object(m, 'get', return_value=receipt({'status': 'error'}, 400)) as fetch:
            budget = m.Budget(4)
            first = budget.fetch('url', {}, 'fixture')
            self.assertEqual(m.category(first), 'BAD_REQUEST')
            self.assertEqual(budget.fetch('url', {}, 'fixture')['error'], 'BAD_REQUEST')
            self.assertEqual(budget.used, 1)
        fetch.assert_called_once()

        def fake(url, params, token):
            if 'twelvedata' in url:
                result = twelve([{'datetime': day, 'close': '100'} for day in m.SESSIONS])
                result['payload']['meta']['symbol'] = params['symbol']
                return result
            return receipt({'status': 'error'}, 400)

        with patch.object(m, 'get', side_effect=fake) as fetch, patch.dict(
                'os.environ', {'MASSIVE_API_KEY': 'fixture',
                               'TWELVE_DATA_API_KEY': 'fixture'}):
            result = m.reconcile()
        self.assertEqual(fetch.call_count, 3)  # 1 Massive + 2 Twelve.
        self.assertEqual(result['request_budget']['massive_used'], 1)
        self.assertEqual(result['request_budget']['twelve_data_used'], 2)
        self.assertEqual(result['total_ticker_dates'], 4)
        self.assertEqual(result['official_close_censored_count'], 4)
        self.assertEqual(result['official_close_eligible_count'], 0)
        self.assertEqual(result['missing_pair_count'], 4)
        self.assertEqual(result['rows'][0]['providers']['MASSIVE']['provider_error_category'],
                         'BAD_REQUEST')
        self.assertTrue(all(row['providers']['MASSIVE']['provider_error_category']
                            in {'BAD_REQUEST'} for row in result['rows']))
        self.assertFalse(result['outcome_scoring_eligible'])

    def test_provider_5xx_stops_same_run_without_erasing_denominator(self):
        # Provider-side 5xx must not burn the remaining bounded request budget.
        # Other providers still receive their own requests and every original
        # ticker/session stays present and officially censored.
        for status in (500, 502, 503, 504):
            with self.subTest(status=status):
                failure = receipt({"status": "error"}, status=status)
                with patch.object(m, "get", return_value=failure) as fetch:
                    budget = m.Budget(4)
                    first = budget.fetch("url", {}, "fixture", expected_status="OK")
                    second = budget.fetch("url", {}, "fixture", expected_status="OK")
                    self.assertEqual(m.category(first), "SERVER_ERROR")
                    self.assertEqual(second["error"], "SERVER_ERROR")
                    self.assertEqual(budget.used, 1)
                    fetch.assert_called_once()

        def fake(url, params, token):
            if "twelvedata" in url:
                good = twelve([{"datetime": day, "close": "100"} for day in m.SESSIONS])
                good["payload"]["meta"]["symbol"] = params["symbol"]
                return good
            return receipt({"status": "error"}, status=503)

        with patch.object(m, "get", side_effect=fake) as fetch, patch.dict(
                "os.environ", {"MASSIVE_API_KEY": "fixture",
                               "TWELVE_DATA_API_KEY": "fixture"}):
            result = m.reconcile()
        self.assertEqual(fetch.call_count, 3)  # 2 Twelve; only 1 Massive.
        self.assertEqual(result["request_budget"]["massive_used"], 1)
        self.assertEqual(result["total_ticker_dates"], 4)
        self.assertEqual(result["official_close_censored_count"], 4)
        self.assertEqual(result["official_close_eligible_count"], 0)
        self.assertEqual(result["missing_pair_count"], 4)
        self.assertTrue(all(
            row["providers"]["MASSIVE"]["provider_error_category"] == "SERVER_ERROR"
            for row in result["rows"]))
        self.assertFalse(result["outcome_scoring_eligible"])

    def test_transport_read_and_header_errors_fail_closed_without_crashing(self):
        # Transport exceptions must not be confused with malformed JSON,
        # leaving status/body uninitialized and losing the fixed denominator.
        class BrokenResponse:
            code = 200
            def __init__(self, failure, stage):
                self.failure, self.stage = failure, stage
                self.headers = {} if stage == 'read' else self
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                if self.stage == 'read':
                    raise self.failure
                return b'{"status":"OK"}'
            def get_all(self, name):
                raise self.failure

        errors = (ValueError('bad stream'),
                  UnicodeDecodeError('utf-8', bytes([255]), 0, 1, 'invalid'),
                  RecursionError('broken decoder'))
        for stage in ('read', 'headers'):
            for failure in errors:
                with self.subTest(stage=stage, error=type(failure).__name__), patch.object(
                        m, '_open_no_redirect',
                        return_value=BrokenResponse(failure, stage)):
                    got = m.get('https://api.massive.com/v1/open-close',
                                {'apiKey': 'canary'}, 'canary')
                    self.assertEqual(got['error'], 'NETWORK_UNAVAILABLE')
                    self.assertIsNone(got['http_status'])
                    self.assertIsNone(got['body_sha256'])
                    self.assertEqual(m.category(got), 'NETWORK_UNAVAILABLE')
                    self.assertNotIn('canary', json.dumps(got))
                    with patch.object(m, 'get', return_value=got) as fetch:
                        budget = m.Budget(4)
                        self.assertEqual(m.category(budget.fetch('url', {}, 'fixture')),
                                         'NETWORK_UNAVAILABLE')
                        self.assertEqual(budget.fetch('url', {}, 'fixture')['error'],
                                         'NETWORK_UNAVAILABLE')
                        fetch.assert_called_once()

    def test_transport_failure_keeps_original_four_row_denominator(self):
        # A missing Massive transport receipt must not erase the remaining
        # original issuer/session rows or invent an official-close result.
        def fake(url, params, token):
            if 'twelvedata' in url:
                r = twelve([{'datetime': d, 'close': '100'} for d in m.SESSIONS])
                r['payload']['meta']['symbol'] = params['symbol']
                return r
            return dict(error='NETWORK_UNAVAILABLE', http_status=None,
                        payload=None, headers={})
        with patch.object(m, 'get', side_effect=fake) as fetch, patch.dict(
                'os.environ', {'MASSIVE_API_KEY': 'fixture',
                               'TWELVE_DATA_API_KEY': 'fixture'}):
            result = m.reconcile()
        self.assertEqual(fetch.call_count, 3)  # Two Twelve requests, one Massive.
        self.assertEqual(result['request_budget']['massive_used'], 1)
        self.assertEqual(result['total_ticker_dates'], 4)
        self.assertEqual(result['official_close_censored_count'], 4)
        self.assertEqual(result['official_close_eligible_count'], 0)
        self.assertEqual(result['missing_pair_count'], 4)
        self.assertTrue(all(row['providers']['MASSIVE']['provider_error_category']
                            == 'NETWORK_UNAVAILABLE' for row in result['rows']))


    def test_reconcile_rejects_future_or_incomplete_session_before_paid_requests(self):
        # Even an otherwise valid scheduled weekday must not be queried as
        # a completed daily close before the conservative 16:00 ET cutoff.
        # Oct 30 uses EDT; Nov 2 follows the DST change and uses EST.
        cases = [
            (('2026-10-30',), '2026-10-30T19:59:59Z'),
            (('2026-10-30',), '2026-10-30T20:00:00Z'),
            (('2026-11-02',), '2026-11-01T13:00:00Z'),
            (('2026-11-02',), '2026-11-02T20:59:59Z'),
            (('2026-11-02',), '2026-11-02T21:00:00Z'),
            (('2026-10-30', '2026-11-02'), '2026-11-01T13:00:00Z'),
            (('2026-10-30',), '2026-11-01T13:00:00'),
            (('2026-10-30',), 'invalid-timestamp'),
        ]
        for sessions, now in cases:
            with self.subTest(sessions=sessions, now=now), patch.object(
                    m, 'utcnow', return_value=now), patch.object(
                    m, 'get') as fetch, patch.dict(
                    'os.environ', {'MASSIVE_API_KEY': 'fixture',
                                   'TWELVE_DATA_API_KEY': 'fixture'}):
                with self.assertRaisesRegex(
                        ValueError, 'SESSION_NOT_COMPLETE_AT_DIAGNOSTIC_START'):
                    m.reconcile(symbols=('AAPL',), sessions=sessions)
                fetch.assert_not_called()

        # After the real 16:00 ET cutoff, the same requested session may
        # enter a diagnostic but remains entirely censored without evidence.
        with patch.object(m, 'utcnow', return_value='2026-11-01T13:00:00Z'), patch.dict(
                'os.environ', {}, clear=True), patch.object(m, 'get') as fetch:
            result = m.reconcile(symbols=('AAPL',), sessions=('2026-10-30',))
        fetch.assert_not_called()
        self.assertEqual(result['captured_at_utc'], '2026-11-01T13:00:00Z')
        self.assertEqual(result['total_ticker_dates'], 1)
        self.assertEqual(result['official_close_censored_count'], 1)
        self.assertEqual(result['official_close_eligible_count'], 0)
        self.assertFalse(result['outcome_scoring_eligible'])

    def test_vendor_daily_session_label_is_not_original_exchange_source_timestamp(self):
        # Massive "from" and Twelve Data "datetime" are date-only labels.
        # Neither is an original exchange auction/source event timestamp.
        for provider, raw in (
                ("MASSIVE", massive()),
                ("TWELVE_DATA", twelve())):
            with self.subTest(provider=provider):
                row = m.observation(provider, "AAPL", "2026-10-27", raw)
                self.assertEqual(row["validation_status"], "VALID_VENDOR_BAR")
                self.assertEqual(row["vendor_session_label"], "2026-10-27")
                self.assertIsNone(row["source_timestamp"])
                self.assertEqual(row["source_timestamp_evidence_status"],
                                 "NOT_PROVIDED_BY_VENDOR_DAILY_BAR")
                self.assertFalse(row["identity_verified"])
        # Even fully populated diagnostic bars do not discharge the
        # original-exchange timestamp requirement or permit outcome scoring.
        def fake(url, params, token):
            if "twelvedata" in url:
                r = twelve([{"datetime": d, "close": "100"} for d in m.SESSIONS])
                r["payload"]["meta"]["symbol"] = params["symbol"]
                return r
            return massive(url.rsplit("/", 1)[-1], url.split("/")[-2])
        with patch.object(m, "get", side_effect=fake), patch.dict(
                "os.environ", {"MASSIVE_API_KEY": "fixture",
                               "TWELVE_DATA_API_KEY": "fixture"}):
            result = m.reconcile()
        self.assertEqual(result["both_bar_count"], 4)
        self.assertEqual(result["official_close_eligible_count"], 0)
        for item in result["rows"]:
            for vendor in item["providers"].values():
                self.assertIsNone(vendor["source_timestamp"])
                self.assertEqual(vendor["vendor_session_label"], item["session"])
                self.assertEqual(vendor["source_timestamp_evidence_status"],
                                 "NOT_PROVIDED_BY_VENDOR_DAILY_BAR")
            self.assertIn("ORIGINAL_EXCHANGE_SOURCE_TIMESTAMP_NOT_AUTHENTICATED",
                          item["missing_official_close_proofs"])

    def test_vendor_json_fraction_preserves_exact_source_digits_at_tolerance(self):
        # Python json.loads normally rounds 100.0050000000000001 to 100.005,
        # turning a genuine diagnostic >$0.005 disagreement into agreement.
        class FakeResponse:
            code = 200
            headers = {'Content-Type': 'application/json'}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                return (b'{"status":"OK","symbol":"AAPL","from":"2026-10-27",'
                        b'"close":100.0050000000000001,"sideband":0.0}')

        with patch.object(m, '_open_no_redirect', return_value=FakeResponse()):
            raw = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
        self.assertIsNone(raw['error'])
        self.assertEqual(str(raw['payload']['close']), '100.0050000000000001')
        a = m.observation('MASSIVE', 'AAPL', '2026-10-27', raw)
        b = m.observation('TWELVE_DATA', 'AAPL', '2026-10-27', twelve())
        self.assertEqual(a['price'], '100.0050000000000001')
        self.assertEqual(m.compare(a, b, self.identity()),
                         ('VENDOR_BAR_CONFLICT_NOT_OFFICIAL', '0.0050000000000001'))
        self.assertFalse(a['identity_verified'])
        self.assertIsNone(a['source_timestamp'])

    def test_vendor_json_extreme_and_overprecise_auxiliary_values_still_censor(self):
        class FakeResponse:
            code = 200
            headers = {'Content-Type': 'application/json'}
            def __init__(self, extra): self.extra = extra
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                return ('{"status":"OK","symbol":"AAPL","from":"2026-10-27",'
                        '"close":100,"aux":' + self.extra + '}').encode()
        for extra in ('1e309', '1e-400', '0.' + '1' * 101):
            with self.subTest(extra=extra[:20]), patch.object(
                    m, '_open_no_redirect', return_value=FakeResponse(extra)):
                raw = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
                self.assertIsNone(raw['payload'])
                self.assertEqual(m.category(raw), 'MALFORMED_RESPONSE')
                self.assertEqual(m.observation('MASSIVE', 'AAPL', '2026-10-27',
                                               raw)['validation_status'], 'BLOCKED')

    def test_vendor_decimal_more_than_28_digits_still_flags_conflict(self):
        # Decimal's default 28-digit arithmetic can itself round the final
        # fractional difference to exactly $0.005. Preserve source digits
        # during BOTH diagnostic comparison and full cohort reconciliation.
        fraction = '100.00500000000000000000000000000000000000001'
        class FakeResponse:
            code = 200
            headers = {'Content-Type': 'application/json'}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                return ('{"status":"OK","symbol":"AAPL","from":"2026-10-27",'
                        '"close":' + fraction + '}').encode()
        with patch.object(m, '_open_no_redirect', return_value=FakeResponse()):
            raw = m.get('https://api.massive.com/v1/open-close', {}, 'fixture')
        a = m.observation('MASSIVE', 'AAPL', '2026-10-27', raw)
        b = m.observation('TWELVE_DATA', 'AAPL', '2026-10-27', twelve())
        expected = '0.00500000000000000000000000000000000000001'
        self.assertEqual(a['price'], fraction)
        self.assertEqual(m.compare(a, b, self.identity()),
                         ('VENDOR_BAR_CONFLICT_NOT_OFFICIAL', expected))
        self.assertFalse(a['identity_verified'])

        def fake(url, params, token):
            if 'twelvedata' in url:
                r = twelve([{'datetime': day, 'close': '100'} for day in m.SESSIONS])
                r['payload']['meta']['symbol'] = params['symbol']
                return r
            r = massive(url.rsplit('/', 1)[-1], url.split('/')[-2],
                        close=fraction if url.endswith('2026-10-27') else '100')
            return r
        with patch.object(m, 'get', side_effect=fake), patch.dict(
                'os.environ', {'MASSIVE_API_KEY': 'fixture',
                               'TWELVE_DATA_API_KEY': 'fixture'}):
            result = m.reconcile()
        self.assertEqual(result['vendor_bar_numeric_conflict_unverified_identity_count'], 2)
        self.assertEqual(result['official_close_eligible_count'], 0)
        for row in result['rows']:
            if row['session'] == '2026-10-27':
                self.assertEqual(row['vendor_bar_numeric_difference_usd_unverified_identity'],
                                 expected)
                self.assertTrue(row['vendor_bar_numeric_conflict_unverified_identity'])

if __name__=='__main__':unittest.main()
