"""Dispatch the existing hosted research collector once per local date."""
import argparse
import fcntl
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = 'Dirtyhandgernades/Dudebot'
BRANCH = 'research/obsidian-early-rug-20261025'
WORKFLOW = 'obsidian-free-quant-feed.yml'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'status'])
    parser.add_argument('--state', required=True, type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    args.state.mkdir(parents=True, exist_ok=True)
    day = datetime.now(ZoneInfo('America/Chicago')).date()
    receipt = args.state / (day.isoformat() + '.json')
    with (args.state/'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.command == 'status':
            print(receipt.read_text() if receipt.exists() else 'No dispatch recorded today')
            return
        if receipt.exists():
            print(receipt.read_text())
            if json.loads(receipt.read_text())['status'] != 'dispatch_accepted':
                raise SystemExit('Previous dispatch requires reconciliation')
            return
        # Check host access before reserving the dispatch. Never repeat an ambiguous POST.
        subprocess.run(['gh','api',f'repos/{REPO}/actions/workflows/{WORKFLOW}','--silent'],check=True,timeout=30)
        def record(status):
            temp = receipt.with_suffix('.tmp')
            temp.write_text(json.dumps(dict(date=str(day), repo=REPO, branch=BRANCH,
                                            workflow=WORKFLOW, status=status))+'\n')
            temp.replace(receipt)
        record('dispatch_pending_or_unknown')
        subprocess.run(['gh','workflow','run',WORKFLOW,'--repo',REPO,'--ref',BRANCH],check=True,timeout=45)
        record('dispatch_accepted')
        print(receipt.read_text())


if __name__ == '__main__':
    main()
