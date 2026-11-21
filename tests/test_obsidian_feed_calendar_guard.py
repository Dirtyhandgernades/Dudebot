import unittest
from datetime import datetime
from unittest.mock import Mock

from backtest.obsidian_free_quant_feed import collect


class CalendarGuardTests(unittest.TestCase):
    def test_protected_windows_and_exchange_holiday_make_no_requests(self):
        for stamp in (
            '2026-11-23T20:45:00+00:00',
            '2026-11-23T20:58:00+00:00',
            '2026-11-27T17:45:00+00:00',
            '2026-11-27T17:58:00+00:00',
            '2026-11-26T18:00:00+00:00',
        ):
            with self.subTest(stamp=stamp):
                reader = Mock()
                with self.assertRaisesRegex(ValueError, 'OUTSIDE_RESEARCH'):
                    collect(['AAPL'], reader=reader, clock=datetime.fromisoformat(stamp))
                self.assertEqual(reader.mock_calls, [])

