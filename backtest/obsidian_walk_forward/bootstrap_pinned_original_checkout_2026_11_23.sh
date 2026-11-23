#!/usr/bin/env bash
# Research-only checkout bootstrap. Does not run strategy, authenticate, or change production.
set -euo pipefail
REPO_URL="https://github.com/Dirtyhandgernades/Dudebot.git"
PIN="09e985643380e564f71ef31b70983bc264f3941c"
BRANCH="research/obsidian-early-rug-20261025"
EXPECTED_RANKER_BLOB="e574c908eeb5fafbf918200296b01eeaf8dafbdd"
EXPECTED_ARCHIVE_SHA256="a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e"
if [[ $# -ne 2 ]]; then echo "Usage: $0 EMPTY_DESTINATION VERIFIED_ARTIFACT_ZIP" >&2; exit 2; fi
DEST="$1"; ZIP="$2"
[[ -f "$ZIP" ]] || { echo "Archive missing" >&2; exit 2; }
echo "$EXPECTED_ARCHIVE_SHA256  $ZIP" | sha256sum -c -
[[ ! -e "$DEST" ]] || { echo "Destination exists; refusing overwrite" >&2; exit 2; }
git clone --no-checkout --single-branch --branch "$BRANCH" "$REPO_URL" "$DEST"
git -C "$DEST" checkout --detach "$PIN"
[[ "$(git -C "$DEST" rev-parse HEAD)" == "$PIN" ]]
[[ "$(git -C "$DEST" rev-parse HEAD:backtest/target_rank_research.py)" == "$EXPECTED_RANKER_BLOB" ]] || { echo "Original ranker blob mismatch" >&2; exit 3; }
git -C "$DEST" status --porcelain
python - "$ZIP" <<'PY'
import sys,zipfile
z=zipfile.ZipFile(sys.argv[1])
assert z.testzip() is None
required={'firm-timing-inputs.json.gz','discovery-decisions.json','2023-hybrid-signals.json','2024-hybrid-signals.json','2025-hybrid-signals.json'}
assert required.issubset(set(z.namelist()))
print('Verified archive and complete pinned source checkout; ranker NOT executed')
PY
echo "Pinned research checkout ready. Do not run without isolated read-only input staging and output reconciliation."
