from datetime import datetime, timezone

import pytest

from backtest.obsidian_packet_freshness import audit


def test_delayed_label_does_not_hide_actual_old_source():
    packet = dict(requested_symbols=['TEST'], rows=[dict(ticker='TEST', iex={},
        sip=dict(status='FRESH_AT_ASOF', safe_asof='2026-11-23T20:00:00Z',
                 latest_completed_bar=dict(bar_end='2026-11-23T19:59:00Z')))])
    result = audit(packet, datetime(2026, 11, 23, 20, 30, tzinfo=timezone.utc))
    assert result['rows'][0]['measurements']['sip_bar_end']['age_seconds'] == 1860
    assert result['counts']['iex_trade_unknown_or_future'] == 1
    assert not result['execution_freshness_verified']
    packet['rows'].append(packet['rows'][0])
    with pytest.raises(ValueError, match='roster'):
        audit(packet, datetime.now(timezone.utc))
