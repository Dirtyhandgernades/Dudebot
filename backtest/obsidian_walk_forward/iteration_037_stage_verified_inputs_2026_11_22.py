"""Research-only atomic staging of the five checksum-verified original inputs.

Usage: python backtest/obsidian_walk_forward/iteration_037_stage_verified_inputs_2026_11_22.py ARCHIVE.zip CHECKOUT
Fails closed on missing/invalid archive, existing destination, or unsafe paths.
Never executes ranker, accesses accounts, or touches production.
"""
import hashlib
import importlib.util
import os
import pathlib
import sys
import tempfile
import zipfile

EXPECTED_ARCHIVE = "a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e"
EXPECTED = {
    "firm-timing-inputs.json.gz": "e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb",
    "discovery-decisions.json": "71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737",
    "2023-hybrid-signals.json": "2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee",
    "2024-hybrid-signals.json": "c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b",
    "2025-hybrid-signals.json": "8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: stage_verified_inputs.py ARCHIVE.zip CHECKOUT")
    archive = pathlib.Path(sys.argv[1]).resolve(strict=True)
    checkout = pathlib.Path(sys.argv[2]).resolve(strict=True)
    if not checkout.is_dir() or not (checkout / "backtest" / "target_rank_research.py").is_file():
        raise SystemExit("BLOCKED: target is not an assembled ranker checkout")
    dest = checkout / "outputs/backtest/hybrid-37386241124"
    if dest.exists() or dest.is_symlink():
        raise SystemExit("BLOCKED: destination already exists; never overwrite")
    if archive.stat().st_size != 11294854:
        raise SystemExit("BLOCKED: archive size mismatch")
    with archive.open("rb") as f:
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != EXPECTED_ARCHIVE:
        raise SystemExit("BLOCKED: archive hash mismatch")
    verified = {}
    with zipfile.ZipFile(archive) as z:
        for name, expected_hash in EXPECTED.items():
            matches = [i for i in z.infolist() if not i.is_dir() and pathlib.PurePosixPath(i.filename).name == name]
            if len(matches) != 1 or matches[0].file_size > 100_000_000:
                raise SystemExit("BLOCKED: missing, duplicate or oversized " + name)
            data = z.read(matches[0])
            if sha(data) != expected_hash:
                raise SystemExit("BLOCKED: input hash mismatch " + name)
            verified[name] = data
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive destination creation prevents overwriting prior work.
    dest.mkdir(mode=0o700)
    try:
        for name, data in verified.items():
            with (dest / name).open("xb") as f:
                f.write(data)
        for name, data in verified.items():
            if sha((dest / name).read_bytes()) != sha(data):
                raise RuntimeError("staged verification failed")
    except Exception:
        # Leave partial directory visible for inspection; never silently replace it.
        raise
    print("VERIFIED_INPUTS_STAGED_NOT_A_BACKTEST", str(dest))
    for name in sorted(verified):
        print(name, len(verified[name]), sha(verified[name]))
    print("NEXT: verify pinned source/dependencies, then run original module once in disposable checkout.")

if __name__ == "__main__":
    main()
