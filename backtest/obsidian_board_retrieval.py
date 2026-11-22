"""Retrieve one explicitly identified research run through authenticated gh."""
import argparse
import json
import subprocess
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backtest.obsidian_board_intake import intake

REPO = 'Dirtyhandgernades/Dudebot'
BRANCH = 'research/obsidian-early-rug-20261025'


def validate_run(run, run_id, intent):
    if not isinstance(run.get('repository'), dict):
        raise ValueError('RUN_IDENTITY_MISMATCH')
    if (run.get('id') != run_id or run.get('display_title') != intent
            or run.get('head_branch') != BRANCH or run.get('event') != 'workflow_dispatch'
            or run.get('path') != '.github/workflows/obsidian-free-quant-feed.yml'
            or run.get('repository', {}).get('full_name') != REPO):
        raise ValueError('RUN_IDENTITY_MISMATCH')
    if run.get('status') != 'completed':
        return False
    if run.get('conclusion') != 'success':
        raise ValueError('COLLECTION_RUN_FAILED')
    return True


def api(path):
    return subprocess.check_output(['gh', 'api', f'repos/{REPO}/{path}'], timeout=45)


def retrieve(run_id, intent, directory):
    run = json.loads(api(f'actions/runs/{run_id}'))
    if not validate_run(run, run_id, intent):
        return dict(status='WAITING_FOR_RUN', run_id=run_id, intent=intent)
    listing = json.loads(api(f'actions/runs/{run_id}/artifacts'))
    name = f'obsidian-free-quant-{run_id}'
    artifacts = [a for a in listing['artifacts'] if a['name'] == name and not a['expired']]
    if len(artifacts) != 1:
        raise ValueError('MISSING_OR_AMBIGUOUS_ARTIFACT')
    artifact = artifacts[0]
    digest = artifact.get('digest', '')
    if not digest.startswith('sha256:') or len(digest) != 71:
        raise ValueError('ARTIFACT_DIGEST_UNAVAILABLE')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / f'artifact-{artifact["id"]}.zip'
    if not archive.exists():
        payload = api(f'actions/artifacts/{artifact["id"]}/zip')
        # Atomic publication preserves incomplete temporary downloads for diagnosis.
        with tempfile.NamedTemporaryFile(dir=directory, suffix='.partial', delete=False) as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
            temporary = Path(output.name)
        os.link(temporary, archive)
        temporary.unlink()
    receipt_path = directory / 'receipt.json'
    if receipt_path.exists():
        saved = json.loads(receipt_path.read_text())
        if (saved.get('run_id') != run_id or saved.get('intent') != intent
                or saved.get('artifact_id') != artifact['id']):
            raise ValueError('EXISTING_RECEIPT_IDENTITY_MISMATCH')
        verified = intake(archive, digest[7:], run_id, datetime.fromisoformat(saved['received_at']))
        if any(saved.get(key) != value for key, value in verified.items()):
            raise ValueError('EXISTING_RECEIPT_CONTENT_MISMATCH')
        return saved
    receipt = intake(archive, digest[7:], run_id, datetime.now(timezone.utc))
    receipt.update(intent=intent, artifact_id=artifact['id'], run_identity_verified=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=directory, suffix='.receipt-partial',
                                     encoding='utf-8', delete=False) as output:
        json.dump(receipt, output, indent=2)
        output.flush()
        os.fsync(output.fileno())
        temporary = Path(output.name)
    os.link(temporary, receipt_path)
    temporary.unlink()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True, type=int)
    parser.add_argument('--intent', required=True)
    parser.add_argument('--directory', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(retrieve(args.run_id, args.intent, args.directory)))


if __name__ == '__main__':
    main()
