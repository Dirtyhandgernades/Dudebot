import hashlib
import json
import zipfile
from datetime import datetime, timezone

import pytest

from backtest.obsidian_board_intake import intake, delivery_check


@pytest.mark.parametrize('fault', [None, 'roster', 'source', 'duplicate', 'future'])
def test_intake_checks_source_binding_and_complete_roster(tmp_path, fault):
    at = '2026-11-23T20:20:00+00:00'
    raw = json.dumps(dict(requested_symbols=['TEST'], finished_at=at)).encode()
    board = dict(source_packet_sha256=hashlib.sha256(raw).hexdigest(), source_packet_at=at, denominator=1,
                 requested_symbols=['TEST'], rows=[dict(ticker='TEST')], created_at=at)
    if fault == 'roster':
        board['rows'] = []
    if fault == 'source':
        board['source_packet_sha256'] = 'wrong'
    if fault == 'future':
        board['created_at'] = '2026-11-24T20:20:00+00:00'
    path = tmp_path / 'artifact.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('outputs/backtest/free-quant-1.json', raw)
        name = 'outputs/backtest/free-quant-board-1.json'
        archive.writestr(name, json.dumps(board))
        if fault == 'duplicate':
            archive.writestr(name, json.dumps(board))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    received = datetime(2026, 11, 23, 20, 21, tzinfo=timezone.utc)
    if fault:
        with pytest.raises(ValueError):
            intake(path, digest, 1, received)
    else:
        result = intake(path, digest, 1, received)
        assert result['roster_count'] == 1
        assert result['packet_age_seconds'] == 60
        assert not result['decision_review_completed']
    with pytest.raises(ValueError, match='HASH'):
        intake(path, 'wrong', 1, received)


@pytest.mark.parametrize('source,received,expected', [
    ('2026-11-23T20:20:00+00:00', '2026-11-23T20:21:00+00:00', []),
    ('2026-11-23T20:34:00+00:00', '2026-11-23T20:36:00+00:00', ['DELIVERY_LATE']),
    ('2026-11-23T20:20:00+00:00', '2026-11-23T20:34:00+00:00', ['PACKET_STALE_OR_FUTURE']),
    ('2026-11-22T20:20:00+00:00', '2026-11-23T20:21:00+00:00',
     ['PACKET_STALE_OR_FUTURE', 'SOURCE_SESSION_MISMATCH']),
])
def test_receipt_deadline_and_source_age(source, received, expected):
    receipt = dict(intake_verified=True, source_packet_at=source, received_at=received)
    result = delivery_check(receipt, datetime(2026, 11, 23, 20, 35, tzinfo=timezone.utc), 300)
    assert result['blockers'] == expected
    assert result['delivery_eligible'] == (not expected)
    assert not result['decision_review_completed']

