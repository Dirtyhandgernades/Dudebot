# OBSIDIAN iteration 029 — pinned direct dependency manifest (2026-11-22)

RESEARCH ONLY; authorized branch research/obsidian-early-rug-20261025. Continuation after iteration 028. No orders, credentials, production changes or strategy promotion.

## Source inspection and bounded repair
Read original protocol, FAST_DUMP_RANK_RESULTS.md, FIRM_TIMING_VALIDATION.md, proposed v2 playbook, prospective proof gate and diagnostic negative control. Fetched unmodified backtest/target_rank_research.py (Git blob e574c908eeb5fafbf918200296b01eeaf8dafbdd) and its five direct local imports from the authorized branch:

| File | Git blob |
|---|---|
| smg/intraday_replay.py | 2aa2a4e2d3155325b45b34ab4da7358afaad96d3 |
| smg/models.py | abe350d577439fa870c73d354b2628cb4bfb22d0 |
| smg/risk_model.py | 00f3e1085bc9875355d9203038e09f8dcbb09e2c |
| smg/swing_backtest.py | d32a81bd2e74cf6305ef7de3476b3b33d0c659a2 |
| backtest/confirmation_comparison.py | 1f22966bfceaf88318ea4e20b53e3db76f499d80 |

The five imports have additional dependencies; an isolated reproduction requires at least smg.backtest, smg.cli, smg.game_firm_replay, smg.market, smg.transport, smg.game_rules, plus numpy and pydantic. This is a direct-import inspection, NOT a complete recursive manifest or proof of compatible package versions. Preserve original code; do not stub or simplify the simulator.

## Archive and run boundary
Artifact 11378995592 from workflow 37386241124, expected ZIP SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, previously inventoried in iteration 028. No ZIP byte transfer or local checksum verification this iteration. Producer commit b8fbd035543611f49992d6df3b619af7a6ddf548 differs from current research-branch code; compatibility unproven. Ranker reads five archived inputs from outputs/backtest/hybrid-37386241124 and writes outputs/backtest/target-rank-2026-10-05. Do not execute until source, dependency closure and archive are co-located in isolated scratch environment and inputs hashed. Exact reproduction means matching all 54 configurations, normal/stress and trade positions, not copying reported numbers.

## Results and disposition
No independent baseline run, new trade ledger, fresh validation window, P&L, or ending equity calculated. $100,000 is the specified independent synthetic starting capital, not a computed result. The 2023–25 results are previously inspected and cannot serve as untouched holdouts. No challenger hypothesis is authorized before baseline reproduction. Promotion UNVALIDATED.

## Next bounded action
Recursively fetch and pin remaining dependency imports, resolve requirements and check source compatibility against artifact producer commit, then checksum and unpack authentic archive in same isolated environment. No re-running diagnostic negative control as primary baseline.
