# OBSIDIAN iteration 033 — independent archived-input recovery (2026-11-22)

RESEARCH ONLY. Continuation after iteration 032 on authorized branch research/obsidian-early-rug-20261025. No SMG authentication, orders, vault/private data, protected baselines, deployment, alerts or main changes.

## Required reading
Read backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md, backtest/FAST_DUMP_RANK_RESULTS.md, backtest/FIRM_TIMING_VALIDATION.md, backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md, backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md, backtest/OBSIDIAN_DIAGNOSTIC_REPLAY_CYCLES_1_2_2026_11_20.md (negative control), and iteration 032 provenance note.

## New independently executed recovery
Downloaded original GitHub Actions run 37386241124 artifact 11378995592 using GitHub artifact download connector to an isolated local runtime at /mnt/data/github-actions-artifact-11378995592.zip. Independently computed archive SHA-256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, exactly matching registered archive SHA-256. Opened ZIP and extracted ONLY the five original input files to /mnt/data/obsidian_iteration_033/outputs/backtest/hybrid-37386241124/ using exclusive creation (no existing file overwritten).

| Extracted input | Bytes | SHA-256 |
|---|---:|---|
| firm-timing-inputs.json.gz | 11118396 | e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb |
| discovery-decisions.json | 713142 | 71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737 |
| 2023-hybrid-signals.json | 5209 | 2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee |
| 2024-hybrid-signals.json | 28252 | c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b |
| 2025-hybrid-signals.json | 51454 | 8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42 |

Read/decompressed JSON inputs successfully. Packet has keys sessions, config, firm_dates, cohorts, raw, split. There are 521 cached session entries from 2022-06-01 to 2025-12-05; 415 raw and 415 split ticker keys; cohorts 2023-09-08, 2024-09-08, 2025-09-08. Hybrid signal coverage: 2023 61 day keys / 7 events (Sep 8–Dec 4); 2024 62 / 48 (Sep 9–Dec 4); 2025 63 / 90 (Sep 8–Dec 4). These counts are artifact observations, not an independently authenticated full market calendar or complete eligible universe. Missing Aug 2025 and Dec 6–31 coverage remains an explicit blocker.

## Ranker schema compatibility (partial)
Unmodified research-branch backtest/target_rank_research.py (Git blob e574c908eeb5fafbf918200296b01eeaf8dafbdd) expects exactly the five files extracted, and packet keys raw/split/sessions/firm_dates/config/cohorts. Those names exist in extracted archive. This establishes top-level structural compatibility, NOT executable or semantic compatibility. Ranker output is 54 portfolio configurations (3 years x [four policies x two targets + one policy x one target] x two costs). It writes outputs/backtest/target-rank-2026-10-05, so execute only from an isolated working directory with read-only pinned source, never in production checkout.

## Remaining blockers and next bounded step
Need assemble all verified pinned research-branch source dependencies in isolated working directory, resolve package versions, run unmodified python -m backtest.target_rank_research, compare 54 portfolio outputs including normal/stress/trade positions to backtest/FAST_DUMP_RANK_RESULTS.md. No such execution in iteration 033. No new P&L or ending equity; $100,000 is experiment starting capital, not an observed balance. No challenger or hypothesis registered until original baseline matches. Existing 2023–25 results remain inspected retrospective tests, not holdouts. Promotion UNVALIDATED.
