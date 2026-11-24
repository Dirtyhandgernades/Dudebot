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


def test_preferred_share_row_does_not_discard_unrelated_common_share_halt():
    def item(symbol):
        return (b'<item><IssueSymbol>' + symbol + b'</IssueSymbol>'
                b'<HaltDate>11/24/2026</HaltDate><HaltTime>09:00:00</HaltTime>'
                b'<ReasonCode>T1</ReasonCode></item>')

    source = b'<rss><channel>' + item(b'GPMT-A') + item(b'JDZG') + b'</channel></rss>'
    rows = parse_nasdaq_halts(source, datetime(2026, 11, 24, 15, tzinfo=timezone.utc))
    assert [row['ticker'] for row in rows] == ['GPMT-A', 'JDZG']
    assert all(row['halt_state_at_receipt'] == 'HALT_REPORTED_WITHOUT_VERIFIED_RESUME'
               for row in rows)
    assert not SAFE_SYMBOL.fullmatch('GPMT-A')
    for invalid in (b'GPMT-', b'GPMT--A', b'GPMT-A/OTHER'):
        with pytest.raises(ValueError, match='INVALID_SYMBOL'):
            parse_nasdaq_halts(source.replace(b'GPMT-A', invalid), datetime.now(timezone.utc))
