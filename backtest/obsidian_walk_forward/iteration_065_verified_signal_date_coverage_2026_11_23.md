# OBSIDIAN iteration 065 — authenticated archive signal-date coverage audit (2026-11-23)

RESEARCH ONLY. Continued after iteration 064 on authorized branch `research/obsidian-early-rug-20261025`. No SMG authentication, orders, private data, live Portfolio Desk, protected baseline, main, deployment, alerts or workflow execution.

## Prerequisite review
Read `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md` (blob 45d49fb811827d5d614d05b30d7fac8a7bd5d771), `backtest/FAST_DUMP_RANK_RESULTS.md` (617d7606b11b92e0ccc87bfc70f44eb7544102d6), `backtest/FIRM_TIMING_VALIDATION.md` (88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178), discovery playbook (c3b0873774cab2afc352d542d98db5e6565af032), prospective proof gate (7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79), diagnostic cycles 1–2 negative control (9a9ba45a4485bed1d924e99d50c5a905b04e71de), iteration 064 (5ae632d68e06137d89e3c89247e08bdde3e0cda1), and unchanged original ranker `backtest/target_rank_research.py` (e574c908eeb5fafbf918200296b01eeaf8dafbdd).

## Actual execution and input provenance
Downloaded artifact `11378995592` from GitHub Actions run `37386241124` into the isolated execution container at `/mnt/data/obsidian-original-11378995592.zip`. Independently computed SHA256 `a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e` (matches registered value); Python `ZipFile.testzip()` returned `None` (no ZIP CRC failure). Read the archived JSON/GZIP directly without modifying source or using outcomes for tuning.

New independently computed coverage facts:
- `firm-timing-inputs.json.gz` session calendar includes **89** 2025 dates from August 1 through December 5 inclusive; it does **not** include December 8–31.
- `2025-hybrid-signals.json` has **63** date keys from September 8 through December 4, totaling **90** event records. Relative to those 89 packet sessions, **26** have no hybrid-signal date key. Absence of a key does not prove no eligible opportunities, no market events, or a complete eligible universe.
- `2023-hybrid-signals.json`: 61 date keys, September 8–December 4, **7** event records.
- `2024-hybrid-signals.json`: 62 date keys, September 9–December 4, **48** event records.
- The unchanged ranker restricts simulation to September 8–December 5 each year. These archived dates are historical, already inspected, not fresh validation.

Reproduction commands for the verified coverage computation:
```bash
sha256sum /mnt/data/obsidian-original-11378995592.zip
python - <<'PY'
import zipfile,json,gzip
z=zipfile.ZipFile('/mnt/data/obsidian-original-11378995592.zip')
assert z.testzip() is None
p=json.loads(gzip.decompress(z.read('firm-timing-inputs.json.gz')))
s=[d for d in p['sessions'] if '2025-08-01'<=d<='2025-12-31']
for y in (2023,2024,2025):
    e=json.loads(z.read(f'{y}-hybrid-signals.json'))
    print(y,len(e),min(e),max(e),sum(map(len,e.values())))
print('2025 packet sessions',len(s),min(s),max(s))
print('2025 missing signal-date keys',len(set(s)-set(json.loads(z.read('2025-hybrid-signals.json')))))
PY
```

## Blocker and disposition
Shell `git ls-remote https://github.com/Dirtyhandgernades/Dudebot.git refs/heads/research/obsidian-early-rug-20261025` failed `Could not resolve host: github.com`. GitHub connector can read source but a complete pinned checkout has not been assembled into the same isolated runtime as the verified archive. Therefore **the unchanged 54-configuration ranker was not executed**, and no baseline match, P&L, ending equity, challenger test, verified fills, or new holdout evidence is claimed. Synthetic starting balance remains $100,000. No hypothesis change registered; original baseline must be reproduced before challenger testing. Promotion **UNVALIDATED**.

Next bounded repair: reconstruct a complete pinned checkout in the isolated container (rather than another partial dependency inventory), verify source hashes, stage the five archived inputs at `outputs/backtest/hybrid-37386241124`, run `python -m backtest.target_rank_research` unchanged and reconcile all 54 normal/stress/positions outputs against the archived report. Do not confuse this reproduction with an Aug–Dec full-universe or fresh prospective test.
