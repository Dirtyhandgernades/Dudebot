"""Verify a downloaded research artifact and record actual local intake."""
import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def intake(archive, expected_sha256, run_id, received_at):
    data = Path(archive).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('ARTIFACT_HASH_MISMATCH')
    if received_at.utcoffset() is None:
        raise ValueError('AWARE_RECEIPT_REQUIRED')
    with zipfile.ZipFile(archive) as zipped:
        packet_name = f'outputs/backtest/free-quant-{run_id}.json'
        board_name = f'outputs/backtest/free-quant-board-{run_id}.json'
        if any(zipped.namelist().count(name) != 1 for name in (packet_name, board_name)):
            raise ValueError('MISSING_OR_DUPLICATE_PACKET_BOARD')
        raw = zipped.read(packet_name)
        board_raw = zipped.read(board_name)
    packet, board = json.loads(raw), json.loads(board_raw)
    packet_hash = hashlib.sha256(raw).hexdigest()
    if board.get('source_packet_sha256') != packet_hash:
        raise ValueError('BOARD_SOURCE_HASH_MISMATCH')
    symbols = packet['requested_symbols']
    board_symbols = [row['ticker'] for row in board['rows']]
    if (len(symbols) != len(set(symbols)) or len(board_symbols) != len(set(board_symbols))
            or set(symbols) != set(board_symbols) or board['denominator'] != len(symbols)
            or board['requested_symbols'] != symbols):
        raise ValueError('INCOMPLETE_BOARD_DENOMINATOR')
    source_at = datetime.fromisoformat(packet['finished_at'])
    board_at = datetime.fromisoformat(board['created_at'])
    if not source_at <= board_at <= received_at:
        raise ValueError('INVALID_SOURCE_BOARD_RECEIPT_CLOCK')
    return dict(run_id=run_id, received_at=received_at.isoformat(), source_packet_at=source_at.isoformat(),
                board_created_at=board_at.isoformat(), artifact_sha256=expected_sha256,
                packet_sha256=packet_hash, board_sha256=hashlib.sha256(board_raw).hexdigest(),
                roster_count=len(symbols), packet_age_seconds=(received_at-source_at).total_seconds(),
                intake_verified=True, decision_review_completed=False, submission_authorized=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--run-id', required=True, type=int)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    result = intake(args.archive, args.sha256, args.run_id, datetime.now(timezone.utc))
    with args.receipt.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)


if __name__ == '__main__':
    main()
