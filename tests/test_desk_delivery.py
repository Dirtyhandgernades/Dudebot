import hashlib
import json
import zipfile
from datetime import datetime, timezone

import pytest

from backtest.obsidian_board_intake import intake
from backtest.obsidian_desk_delivery import deliver


def fixture(root, run=1, source='2026-11-23T20:20:00+00:00'):
    directory = root / f'intake-{run}'
    directory.mkdir()
    packet = json.dumps(dict(requested_symbols=['TEST'], finished_at=source)).encode()
    board = dict(source_packet_sha256=hashlib.sha256(packet).hexdigest(), source_packet_at=source,
                 denominator=1, requested_symbols=['TEST'], rows=[dict(ticker='TEST')],
                 created_at=source, classification_counts={'BLOCKED': 1}, recommendations=[])
    archive = directory / 'artifact-2.zip'
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr(f'outputs/backtest/free-quant-{run}.json', packet)
        zipped.writestr(f'outputs/backtest/free-quant-board-{run}.json', json.dumps(board))
    receipt = intake(archive, hashlib.sha256(archive.read_bytes()).hexdigest(), run,
                     datetime(2026, 11, 23, 20, 25, tzinfo=timezone.utc))
    receipt.update(run_identity_verified=True, artifact_id=2, intent='synthetic-test-intent')
    (directory / 'receipt.json').write_text(json.dumps(receipt))
    vault = root / 'vault'
    (vault / '08 System').mkdir(parents=True, exist_ok=True)
    (vault / '08 System/registry.json').write_text('{}')
    (vault / 'START HERE.md').write_text('Synthetic vault')
    return directory, vault, receipt


def test_delivery_preserves_source_receipt_bytes_and_original_delivery_clock(tmp_path):
    directory, vault, receipt = fixture(tmp_path)
    first = deliver(directory, vault)
    again = deliver(directory, vault)
    assert first == again
    assert first['intake_received_at'] == receipt['received_at']
    assert first['source_packet_at'] == receipt['source_packet_at']
    assert not first['decision_review_completed']
    assert not first['submission_authorized']
    destination = vault / first['directory']
    assert (destination / 'intake-receipt.json').read_bytes() == (directory / 'receipt.json').read_bytes()
    assert (destination / 'artifact.zip').read_bytes() == (directory / 'artifact-2.zip').read_bytes()
    assert not (vault / '08 System/.research-board-delivery.lock').exists()


@pytest.mark.parametrize('fault', ['archive', 'receipt', 'identity'])
def test_corrupt_or_unverified_input_never_publishes_a_pointer(tmp_path, fault):
    directory, vault, receipt = fixture(tmp_path)
    if fault == 'archive':
        (directory / 'artifact-2.zip').write_bytes(b'tampered')
    elif fault == 'receipt':
        receipt['source_packet_at'] = '2026-11-23T20:21:00+00:00'
    else:
        receipt['run_identity_verified'] = False
    (directory / 'receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        deliver(directory, vault)
    assert not (vault / '08 System/latest-research-board.json').exists()


def test_older_artifact_is_archived_without_replacing_newer_latest(tmp_path):
    new, vault, _ = fixture(tmp_path, 2, '2026-11-23T20:22:00+00:00')
    first = deliver(new, vault)
    old, _, _ = fixture(tmp_path, 1)
    delivered = deliver(old, vault)
    assert not delivered['latest_updated']
    latest = json.loads((vault / '08 System/latest-research-board.json').read_text())
    assert latest['run_id'] == first['run_id'] == 2


def test_delivery_refuses_tampered_saved_content(tmp_path):
    directory, vault, _ = fixture(tmp_path)
    first = deliver(directory, vault)
    (vault / first['directory'] / 'board.json').write_text('tampered')
    with pytest.raises(ValueError, match='EXISTING_DELIVERY_CONTENT_MISMATCH'):
        deliver(directory, vault)


def test_missing_vault_is_not_recreated(tmp_path):
    directory, _, _ = fixture(tmp_path)
    missing = tmp_path / 'missing'
    with pytest.raises(ValueError, match='EXISTING_DESK_VAULT_REQUIRED'):
        deliver(directory, missing)
    assert not missing.exists()
