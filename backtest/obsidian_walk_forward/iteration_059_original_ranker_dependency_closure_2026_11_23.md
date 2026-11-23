# OBSIDIAN iteration 059 — original ranker dependency-closure inventory (2026-11-23)

RESEARCH ONLY — branch `research/obsidian-early-rug-20261025`. Continues iteration 058. No SMG account, credentials, live desk, orders, production workflow, protected baseline or main touched.

## Verified directly this iteration
Read `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md`, `backtest/FAST_DUMP_RANK_RESULTS.md`, `backtest/FIRM_TIMING_VALIDATION.md`, `backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md`, `backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md`, diagnostic negative control, iteration 058 audit and original `backtest/target_rank_research.py` from the authorized branch. The original ranker is Git blob `e574c908eeb5fafbf918200296b01eeaf8dafbdd`; it writes 54 configuration results (18/year), plus CSVs, three models and a summary. Original simulation scope is Sep 8–Dec 5 per year, not full Aug–Dec. This inventory is NOT a rerun.

Read exact source and identified initial import closure:
| module | Git blob SHA |
|---|---|
| smg/intraday_replay.py | 2aa2a4e2d3155325b45b34ab4da7358afaad96d3 |
| smg/models.py | abe350d577439fa870c73d354b2628cb4bfb22d0 |
| smg/risk_model.py | 00f3e1085bc9875355d9203038e09f8dcbb09e2c |
| smg/swing_backtest.py | d32a81bd2e74cf6305ef7de3476b3b33d0c659a2 |
| backtest/confirmation_comparison.py | 1f22966bfceaf88318ea4e20b53e3db76f499d80 |
| smg/backtest.py | 1779ecf369d976684252a7d458564702d2ada649 |
| smg/cli.py | 036b90a4ac2d11c0e4088fac106b5e746a43e251 |
| smg/game_firm_replay.py | 34b9c30d366c2c5f83f11cc3e6bf0c76aa6141df |
| smg/market.py | 845865aad5ed1ec1d69f9b5d050ef661cb0c65b4 |
| smg/transport.py | 7c2e876144cab9c41b9d13c546cc93a30e2e4258 |
| smg/game_rules.py | 76451c59bb2c54837f76c135b0b150f87a14d69c |

Import-time dependency caveat: `smg.intraday_replay` imports `smg.cli`, which imports scanning/provider modules; `smg.game_firm_replay` imports source parsing and firm search. These require additional transitive modules even though the research runner itself does not contact services. External imports observed: numpy, pydantic, pandas, exchange_calendars, requests, yaml, bs4. Never import in a production environment; execute only in isolated offline environment with no secrets/network.

## Actual execution / blockers
Container filesystem checked: `/mnt/data` was empty at iteration start; iteration 058's staged ZIP and inputs were **not persisted into this container**. `git ls-remote https://github.com/Dirtyhandgernades/Dudebot.git refs/heads/research/obsidian-early-rug-20261025` failed with `Could not resolve host: github.com`. GitHub connector can read individual UTF-8 source files, but cannot place the binary Actions archive into this container. No original 54-case execution attempted because required authenticated archive bytes and full source closure are not colocated. Do not interpret previous iteration's staged files as present now.

Archive identity registered in iteration 058 (not reverified in this container): Actions run 37386241124 / artifact 11378995592, expected ZIP SHA256 `a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e`. Its five member hashes are recorded in iteration 058. Need to recheck ZIP and member hashes on any new execution host.

## Reproduction next step
On a network-enabled isolated offline-execution host, obtain exact branch checkout and authentic artifact; verify ZIP and five members against iteration 058; ensure all transitive imports and pinned dependencies load without side effects; stage `outputs/backtest/hybrid-37386241124`; run unchanged `python -m backtest.target_rank_research`; reconcile all 54 normal/stress/position outputs to `FAST_DUMP_RANK_RESULTS.md`. Do not rerun simplified diagnostic. Do not launch GitHub Actions or alter protected/live files.

## Result and gate
Starting independent synthetic balance $100,000. New net P&L, ending equity, drawdown, profit factor, precision/recall and baseline/challenger comparisons: **not computed**. No new validation window or challenger registered. August hybrid signals and 17 late-December sessions remain unverified/missing. Existing 2023–25 years are already inspected. Promotion **UNVALIDATED**.
