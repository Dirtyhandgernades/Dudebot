"""Research-only, stdlib preflight for original Dudebot archived inputs.

Run in a disposable checkout of research/obsidian-early-rug-20261025.
Does not execute ranker, alter existing inputs, or access SMG.
Usage: python backtest/obsidian_walk_forward/iteration_036_archive_preflight_2026_11_22.py /path/to/pre-close-firm.zip
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ARCHIVE_SHA = "a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e"
EXPECTED = {
    "firm-timing-inputs.json.gz": "e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb",
    "discovery-decisions.json": "71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737",
    "2023-hybrid-signals.json": "2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee",
    "2024-hybrid-signals.json": "c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b",
    "2025-hybrid-signals.json": "8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42",
}
def digest(data):
    return hashlib.sha256(data).hexdigest()
def main():
    if len(sys.argv) != 2:
        raise SystemExit("Pass exactly one local ZIP path")
    archive = Path(sys.argv[1])
    if not archive.is_file():
        raise SystemExit("BLOCKED: archive not present in this execution environment")
    if archive.stat().st_size != 11294854:
        raise SystemExit("BLOCKED: archive byte count mismatch")
    with archive.open("rb") as f:
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    if h.hexdigest() != ARCHIVE_SHA:
        raise SystemExit("BLOCKED: archive SHA256 mismatch")
    with zipfile.ZipFile(archive) as z:
        members = z.namelist()
        matches = {}
        for expected, sha in EXPECTED.items():
            candidates = [m for m in members if Path(m).name == expected and not m.endswith("/")]
            if len(candidates) != 1:
                raise SystemExit(f"BLOCKED: expected exactly one {expected}, found {len(candidates)}")
            info = z.getinfo(candidates[0])
            if info.file_size > 100_000_000:
                raise SystemExit(f"BLOCKED: unexpected uncompressed size for {expected}")
            actual = digest(z.read(info))
            if actual != sha:
                raise SystemExit(f"BLOCKED: {expected} SHA256 mismatch")
            matches[expected] = {"archive_member": candidates[0], "sha256": actual, "bytes": info.file_size}
    print(json.dumps({"status":"VERIFIED_INPUTS_ONLY_NOT_A_BACKTEST",
                      "archive_sha256":ARCHIVE_SHA,"archive_members":len(members),
                      "inputs":matches}, indent=2))
    print("NEXT: stage these five verified bytes in a NEW disposable checkout at "
          "outputs/backtest/hybrid-37386241124; verify source/dependencies before "
          "running unchanged ranker. Do not overwrite existing outputs.")
if __name__ == "__main__":
    main()
