"""Research-only, fail-closed staging of the pinned original ranker input archive.

Run from the root of an isolated checkout of the authorized research branch.
Never downloads, executes trading code, or overwrites files.
"""
import argparse
import hashlib
from pathlib import Path
import zipfile

ZIP_SHA = 'a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e'
MEMBERS = {
 'firm-timing-inputs.json.gz':'e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb',
 'discovery-decisions.json':'71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737',
 '2023-hybrid-signals.json':'2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee',
 '2024-hybrid-signals.json':'c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b',
 '2025-hybrid-signals.json':'8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42',
}

def digest(b): return hashlib.sha256(b).hexdigest()

def stage(archive, dest):
    if archive.is_symlink() or not archive.is_file(): raise ValueError('archive absent or symlink')
    if dest.is_symlink() or (dest.exists() and (not dest.is_dir() or any(dest.iterdir()))):
        raise ValueError('destination must be absent or empty, never overwrite')
    if digest(archive.read_bytes()) != ZIP_SHA: raise ValueError('original archive SHA256 mismatch')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None: raise ValueError('ZIP CRC mismatch')
        names = z.namelist()
        for name in MEMBERS:
            matches=[n for n in names if n == name or n.endswith('/'+name)]
            if len(matches)!=1: raise ValueError(f'ambiguous/missing member {name}: {matches}')
            info=z.getinfo(matches[0]); mode=info.external_attr >> 16
            if (mode & 0o170000) == 0o120000: raise ValueError('symlink member')
            if digest(z.read(info)) != MEMBERS[name]: raise ValueError(f'member hash mismatch: {name}')
        dest.mkdir(parents=True,exist_ok=True)
        for name in MEMBERS:
            source=next(n for n in names if n==name or n.endswith('/'+name))
            with (dest/name).open('xb') as out: out.write(z.read(source))
    return {name: MEMBERS[name] for name in MEMBERS}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('archive',type=Path)
    parser.add_argument('--dest',type=Path,default=Path('outputs/backtest/hybrid-37386241124'))
    args=parser.parse_args()
    for name,sha in stage(args.archive,args.dest).items(): print(name,sha)
