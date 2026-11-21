# Iteration 001 — original input recovery, November 20 2026
Research only. No account access, orders, production changes or promotion.
Recovered and extracted original run 37386241124 artifact 11378995592. Local SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e matches original. Compressed packet SHA256 e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb. Archive contains 30 files; packet has 415 raw/split securities, 521 sessions from 2022-06-01 to 2025-12-05 (not continuous across years), 2025 Aug 1–Dec 5 89 sessions. Original hybrid signals cover Sep 8/9–Dec 4 only; no August or post-Dec5 signal coverage. Discovery decisions present. VERB last bar Aug29, BREA Oct2, neither successor resolved.
## Actual computation: archive signal audit (not a ranker rerun)
For each original hybrid event, check 22 preceding session split bars, raw entry close >=3, and complete entry plus next three session split-close chain. Count any subsequent close <=80% of entry close, >=120%, >=150%; mean gross short return at third close. No fills, no chosen strategy changes. All 145 events pass 22-bar availability and raw floor; 3 censored. Archived calendar continuity across multi-year gaps still needs independent validation.
| Year | Signals | Evaluable | >=20% fall | >=20% rise | >=50% rise | Mean gross short 3d |
|---|---:|---:|---:|---:|---:|---:|
|2023|7|7|2|2|1|-9.1124%|
|2024|48|48|9|6|1|7.4949%|
|2025|90|87|12|4|0|6.2887%|
2025 source split 50 intraday exhaustion, 40 prior-close exhaustion revalidated; 2024 30/18, 2023 5/2. Counts are event-days, not independent issuers or actual SMG executions.
## Actual computation: archived unranked hybrid ledger audit
Read existing portfolio results, recomputed profit factor and closed-trade P&L excluding three largest winners. This is not new simulation and not original trained ranker. Starting balance $100k.
| Year | Archived normal net | Stress net | Normal PF | Stress PF | Normal trade P&L less top3 | Stress less top3 |
|---|---:|---:|---:|---:|---:|---:|
|2023|13581.32|9477.13|1.952|1.612|-11692.59|-13596.52|
|2024|-11058.53|-27725.98|.857|.671|-50862.66|-65490.77|
|2025|75015.03|36346.18|2.323|1.524|21499.95|-11517.27|
Top3 removal uses closed-trade P&L only, not counterfactual portfolio recalc or interest-inclusive equity. This reinforces why original ranker reproduction matters: unranked hybrid is different.
## Reproduction blocker / source checkpoint
Container git ls-remote failed DNS resolution. Connector fetch_file succeeds but returns text in separate tool runtime, not filesystem. Need byte-exact source materialization (repository checkout or source archive, or individually copied source verified by git blob hashes), recursively including dependencies; no stubbed financial logic. Direct imports retrieved:
backtest/target_rank_research.py e574c908eeb5fafbf918200296b01eeaf8dafbdd
smg/intraday_replay.py 2aa2a4e2d3155325b45b34ab4da7358afaad96d3
smg/models.py abe350d577439fa870c73d354b2628cb4bfb22d0
smg/risk_model.py 00f3e1085bc9875355d9203038e09f8dcbb09e2c
smg/swing_backtest.py d32a81bd2e74cf6305ef7de3476b3b33d0c659a2
backtest/confirmation_comparison.py 1f22966bfceaf88318ea4e20b53e3db76f499d80
Further local imports include smg/backtest.py, cli.py, game_firm_replay.py, market.py, transport.py, game_rules.py; recurse before running. Check package initializers and dependency versions. Isolated input extraction path outputs/backtest/hybrid-37386241124. Next action source materialization with blob verification, then python -m backtest.target_rank_research unchanged; compare 54 outputs. No challenger registered/evaluated until baseline reproduced. No new P&L claim. Existing historical periods not fresh. No promotion.