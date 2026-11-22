"""Iteration 038: fail-closed pre-execution guard for ORIGINAL Dudebot ranker.

Run from a disposable research-branch checkout, after iteration 037 staging.
Does not execute the ranker, write files, or access any account/network.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

EXPECTED = {
    "firm-timing-inputs.json.gz": "e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb",
    "discovery-decisions.json": "71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737",
    "2023-hybrid-signals.json": "2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee",
    "2024-hybrid-signals.json": "c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b",
    "2025-hybrid-signals.json": "8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42",
}
RANKER_GIT_BLOB = "e574c908eeb5fafbf918200296b01eeaf8dafbdd"
BRANCH = "research/obsidian-early-rug-20261025"

def fail(message):
    raise SystemExit("BLOCKED: " + message)

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) != 2:
        fail("usage: python backtest/obsidian_walk_forward/iteration_038_original_execution_guard_2026_11_22.py CHECKOUT")
    root = Path(sys.argv[1]).resolve(strict=True)
    if not root.is_dir():
        fail("checkout is not a directory")
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    try:
        if git("rev-parse", "--show-toplevel") != str(root):
            fail("checkout must be repository root")
        if git("symbolic-ref", "--short", "HEAD") != BRANCH:
            fail("unexpected branch")
        if git("status", "--porcelain", "--untracked-files=no"):
            fail("tracked source tree has modifications")
    except (subprocess.CalledProcessError, FileNotFoundError):
        fail("cannot verify checkout and branch")
    ranker = root / "backtest/target_rank_research.py"
    if not ranker.is_file() or ranker.is_symlink():
        fail("original ranker missing or symlinked")
    try:
        if git("hash-object", "backtest/target_rank_research.py") != RANKER_GIT_BLOB:
            fail("original ranker blob mismatch")
    except subprocess.CalledProcessError:
        fail("ranker blob hash unavailable")
    source = root / "outputs/backtest/hybrid-37386241124"
    if not source.is_dir() or source.is_symlink():
        fail("verified staged source directory missing or symlinked")
    for name, expected in EXPECTED.items():
        p = source / name
        if not p.is_file() or p.is_symlink() or digest(p) != expected:
            fail("missing or mismatched input: " + name)
    output = root / "outputs/backtest/target-rank-2026-10-05"
    if output.exists() or output.is_symlink():
        fail("ranker output directory already exists; original ranker would overwrite files")
    print("PASS: unchanged original ranker and five staged inputs; output path unused")
    print("NOT A BACKTEST. Inspect dependencies and environment before a one-time isolated execution.")
    print("Candidate command from checkout root: python -m backtest.target_rank_research")

if __name__ == "__main__":
    main()
