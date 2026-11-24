"""Deliver a verified research artifact to the existing private desk vault.

Preserves original clocks. Delivery is not a desk review or trade permission.
"""
import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_board_intake import intake


def atomic(path, raw):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode('utf-8')


def preserve(path, raw):
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('EXISTING_DELIVERY_CONTENT_MISMATCH')
    else:
        atomic(path, raw)


def deliver(directory, vault):
    directory, vault = Path(directory), Path(vault)
    system = vault / '08 System'
    if not (system / 'registry.json').is_file() or not (vault / 'START HERE.md').is_file():
        raise ValueError('EXISTING_DESK_VAULT_REQUIRED')
    raw_receipt = (directory / 'receipt.json').read_bytes()
    receipt = json.loads(raw_receipt)
    if receipt.get('run_identity_verified') is not True or receipt.get('intake_verified') is not True:
        raise ValueError('VERIFIED_RETRIEVAL_REQUIRED')
    run = receipt['run_id']
    archive = directory / f'artifact-{receipt["artifact_id"]}.zip'
    checked = intake(archive, receipt['artifact_sha256'], run,
                     datetime.fromisoformat(receipt['received_at']))
    if any(receipt.get(key) != value for key, value in checked.items()):
        raise ValueError('INTAKE_RECEIPT_CONTENT_MISMATCH')
    with zipfile.ZipFile(archive) as zipped:
        packet = zipped.read(f'outputs/backtest/free-quant-{run}.json')
        board_raw = zipped.read(f'outputs/backtest/free-quant-board-{run}.json')
    board = json.loads(board_raw)
    lock = system / '.research-board-delivery.lock'
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        destination = vault / '07 Sources' / 'Research Board' / f'run-{run}'
        destination.mkdir(parents=True, exist_ok=True)
        for name, raw in [('artifact.zip', archive.read_bytes()), ('packet.json', packet),
                          ('board.json', board_raw), ('intake-receipt.json', raw_receipt)]:
            preserve(destination / name, raw)
        delivery_path = destination / 'delivery.json'
        identity = dict(run_id=run, source_packet_at=receipt['source_packet_at'],
                        intake_received_at=receipt['received_at'],
                        artifact_sha256=receipt['artifact_sha256'],
                        packet_sha256=receipt['packet_sha256'], board_sha256=receipt['board_sha256'],
                        intake_receipt_sha256=hashlib.sha256(raw_receipt).hexdigest(),
                        roster_count=receipt['roster_count'], decision_review_completed=False,
                        submission_authorized=False, scope='RESEARCH_ONLY',
                        directory=str(destination.relative_to(vault)).replace('\\', '/'))
        if delivery_path.exists():
            result = json.loads(delivery_path.read_bytes())
            if any(result.get(key) != value for key, value in identity.items()):
                raise ValueError('EXISTING_DELIVERY_IDENTITY_MISMATCH')
            datetime.fromisoformat(result['delivered_at'])
        else:
            result = dict(identity, delivered_at=datetime.now(timezone.utc).isoformat())
            preserve(delivery_path, encoded(result))
        latest_path = system / 'latest-research-board.json'
        previous = json.loads(latest_path.read_bytes()) if latest_path.exists() else None
        if previous and datetime.fromisoformat(previous['source_packet_at']) > datetime.fromisoformat(result['source_packet_at']):
            return dict(result, latest_updated=False)
        if previous and previous['source_packet_at'] == result['source_packet_at'] and previous != result:
            raise ValueError('CONFLICTING_DESK_BOARD_AT_SAME_SOURCE_TIME')
        note = ('# Research board delivery\n\nRESEARCH ONLY. Receipt is not a completed desk review or trade authorization.\n\n'
                f"Source packet: {result['source_packet_at']}\n\nOriginal local intake: {result['intake_received_at']}\n\n"
                f"First vault delivery: {result['delivered_at']}\n\nRun: {run}; roster: {result['roster_count']}.\n\n"
                f"Classifications: {json.dumps(board.get('classification_counts', {}), sort_keys=True)}.\n\n"
                f"Research recommendations: {len(board.get('recommendations', []))}. These are not approved orders.\n\n"
                f"Packet and board: `{result['directory']}`. Receipt/hash details: `08 System/latest-research-board.json`.\n\n"
                'Recheck actual source ages and the current session before use. Original timestamps have not been refreshed. '
                'The 139-name research watchlist is separate from the complete persistent vault registry. '
                'Join current account/pending orders, review eligibility, thesis, corporate actions, halt status and authorization. '
                'Keep uncertain submissions locked until platform reconciliation.\n')
        dashboard = vault / '00 Dashboard' / 'Research Board.md'
        dashboard.parent.mkdir(parents=True, exist_ok=True)
        atomic(dashboard, note.encode('utf-8'))
        atomic(latest_path, encoded(result))
        return dict(result, latest_updated=True)
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--intake', required=True, type=Path)
    parser.add_argument('--vault', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(deliver(args.intake, args.vault)))


if __name__ == '__main__':
    main()
