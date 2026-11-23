from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from backtest.obsidian_free_quant_feed import collect
from tests.test_obsidian_free_quant_feed import FakeReader


def test_explicit_weekend_mode_retains_closed_session_and_no_authorization():
    reader = FakeReader()
    now = datetime(2026, 11, 22, 18, tzinfo=timezone.utc)
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match='OUTSIDE_RESEARCH'):
            collect(['AAPL'], reader=reader, clock=now)
        assert reader.calls == []
        packet = collect(['AAPL'], reader=reader, clock=now, off_session_research=True)
    assert packet['market_session_state'] == 'OUTSIDE_REGULAR_SESSION'
    assert packet['off_session_research'] is True
    assert packet['trade_authorized'] is False


def test_research_mode_cannot_override_protected_decision_window():
    with pytest.raises(ValueError, match='OUTSIDE_RESEARCH'):
        collect(['AAPL'], reader=FakeReader(),
                clock=datetime(2026, 11, 23, 20, 50, tzinfo=timezone.utc), off_session_research=True)
