from datetime import datetime, timezone

import pytest

from backtest.obsidian_independent_quote_halt import parse_nasdaq_halts, SAFE_SYMBOL


def test_source_unit_symbol_preserved_without_becoming_trade_universe_symbol():
    source = b'''<rss><channel><item><IssueSymbol>ALUB=</IssueSymbol>
    <HaltDate>11/20/2026</HaltDate><HaltTime>10:00:00</HaltTime>
    <ReasonCode>T1</ReasonCode></item></channel></rss>'''
    rows = parse_nasdaq_halts(source, datetime(2026, 11, 20, 20, tzinfo=timezone.utc))
    assert rows[0]['ticker'] == 'ALUB='
    assert not SAFE_SYMBOL.fullmatch('ALUB=')
    with pytest.raises(ValueError, match='INVALID_SYMBOL'):
        parse_nasdaq_halts(source.replace(b'ALUB=', b'ALUB=='), datetime.now(timezone.utc))
