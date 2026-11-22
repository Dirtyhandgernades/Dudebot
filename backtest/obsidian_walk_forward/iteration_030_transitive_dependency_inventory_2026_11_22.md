# OBSIDIAN iteration 030 — transitive dependency and environment inventory (2026-11-22)

RESEARCH ONLY. Authorized branch `research/obsidian-early-rug-20261025`. Append-only continuation after iteration 029. No trading, SMG authentication, vault access, baseline modification, or production change.

## Verified reading and provenance
Read `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md`, `backtest/FAST_DUMP_RANK_RESULTS.md`, `backtest/FIRM_TIMING_VALIDATION.md`, `backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md`, `backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md`, `backtest/OBSIDIAN_DIAGNOSTIC_REPLAY_CYCLES_1_2_2026_11_20.md`, and iteration 029 manifest. The ranker source remains blob `e574c908eeb5fafbf918200296b01eeaf8dafbdd`. All historical seasons are previously inspected; no new holdout.

## Newly fetched and pinned second-level dependencies
| File | Git blob | Important additional local imports |
|---|---|---|
| smg/backtest.py | 1779ecf369d976684252a7d458564702d2ada649 | providers, rules, firm_first, market, models, transport |
| smg/cli.py | 036b90a4ac2d11c0e4088fac106b5e746a43e251 | rules, storage, providers, extraction, discovery, runner, notify |
| smg/game_firm_replay.py | 34b9c30d366c2c5f83f11cc3e6bf0c76aa6141df | firm_first, firm_search, rules, source_replay, market, swing_backtest |
| smg/market.py | 845865aad5ed1ec1d69f9b5d050ef661cb0c65b4 | models |
| smg/transport.py | 7c2e876144cab9c41b9d13c546cc93a30e2e4258 | none |
| smg/game_rules.py | 76451c59bb2c54837f76c135b0b150f87a14d69c | none |
| pyproject.toml | 6becde9c8ad62e0816591736dafae792a7cc1730 | package dependency specification |

The repository `pyproject.toml` specifies Python >=3.11,<3.14; requests >=2.32,<3; pydantic >=2.10,<3; PyYAML >=6,<7; beautifulsoup4 >=4.12,<5; lxml >=6,<7; exchange-calendars >=4.9,<5; pandas >=2.2,<4; numpy >=1.26,<3. No `requirements.txt` exists at root (404). These are ranges, not an exact historical lockfile. This inventory is a verified incremental repair of the dependency manifest, NOT completed recursive closure or proof of reproducibility.

## Authentic input and execution boundary
Original GitHub Actions run 37386241124, artifact 11378995592, expected ZIP SHA256 `a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e`. Artifact-producing commit `b8fbd035543611f49992d6df3b619af7a6ddf548` differs from current research source; compatibility not established. No artifact ZIP was transferred into a Python runtime in this iteration; no SHA256 was independently recalculated now. Do not call the old published 54 results a new run.

## Results
No backtest execution, no new trade-level outcomes, no computed net return, stress return, equity, or challenger. Independent synthetic initial capital specified $100,000, but ending equity unavailable. No new hypothesis tested. Promotion UNVALIDATED.

## Next bounded step
Fetch/pin remaining local imports: `smg/providers.py`, `smg/rules.py`, `smg/firm_first.py`, `smg/storage.py`, `smg/extraction.py`, `smg/discovery.py`, `smg/runner.py`, `smg/notify.py`, `smg/firm_search.py`, `smg/source_replay.py`; recurse only if additional imports appear. Check archive-producer commit for source differences; then co-locate original source and verified ZIP in isolated read-only input directory, run unmodified `python -m backtest.target_rank_research` and compare all 54 configurations to the archived report. No challenger until exact baseline reproduction.
