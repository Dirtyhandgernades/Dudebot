# OBSIDIAN iteration 043 — 2026-11-22 — independently recovered and staged original archive

RESEARCH_ONLY_NOT_AN_ORDER. Continuation of iteration 042. No SMG authentication, orders, private/vault data, production automation, protected baseline, deployment, alerts or main changes.

## Primary source review
Read from authorized branch the registered continuous walk-forward protocol (blob 45d49fb811827d5d614d05b30d7fac8a7bd5d771), FAST_DUMP_RANK_RESULTS (617d7606b11b92e0ccc87bfc70f44eb7544102d6), FIRM_TIMING_VALIDATION (88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178), discovery playbook proposal (c3b0873774cab2afc352d542d98db5e6565af032), prospective proof gate (7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79), and diagnostic cycles 1–2 (9a9ba45a4485bed1d924e99d50c5a905b04e71de) as negative control. Also read prior iteration 042 and original ranker (e574c908eeb5fafbf918200296b01eeaf8dafbdd).

## Actual material repair
Downloaded the original artifact through authenticated GitHub repository connector, NOT SMG, into an isolated container as /mnt/data/pre-close-firm-37386241124.zip. Independently ran sha256sum on actual local bytes: a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, exactly registered; 11,294,854 bytes, 30 ZIP members. Verified ZIP listing and SHA256 of all five required members, then extracted only those five verified files into new, non-overwriting directory /mnt/data/obsidian_iteration043/outputs/backtest/hybrid-37386241124:

- firm-timing-inputs.json.gz (11,118,396 bytes): e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb
- discovery-decisions.json (713,142 bytes): 71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737
- 2023-hybrid-signals.json (5,209 bytes): 2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee
- 2024-hybrid-signals.json (28,252 bytes): c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b
- 2025-hybrid-signals.json (51,454 bytes): 8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42

Python code executed: zipfile.ZipFile(...), z.read(name), hashlib.sha256(...), assert digest==expected, Path.mkdir(exist_ok=False), Path.write_bytes(...). All five assertions passed. This is real byte verification and staging, NOT strategy execution.

## Outstanding blocker / next step
Pinned original source checkout and all transitive dependencies have NOT been co-located with staged inputs; GitHub direct DNS unavailable in container. The unchanged original 54-configuration ranker was NOT run. Next bounded step: assemble branch-pinned source and dependencies in same disposable environment, run existing guard, execute python -m backtest.target_rank_research once, reconcile 54 portfolio outputs, costs, stress, positions and report values. Do not rerun diagnostic substitute or register challenger before reconciliation. Archive in this ephemeral container may not survive next automation turn; GitHub artifact remains accessible. No input or code modification.

## Performance / promotion
$100,000 independent synthetic starting balance. No newly computed equity, P&L, stress return, trades, or paired challenger. Historical 2025 aggressive +$103,258.54 and lower-exposure +$73,815.54 are earlier retrospective report figures only, not reproduced this iteration. Aug and Dec 6–31 2025 still unverified, no full-universe denominator or SMG short permissions. Promotion UNVALIDATED.