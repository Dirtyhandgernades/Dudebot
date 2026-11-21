# Iteration 013 — input materialization and position audit (2026-11-21)
Research only; append-only after 012. Read the protocol, FAST_DUMP, FIRM_TIMING, discovery proposal, prospective gate, negative control, iteration 012 and ranker on authorized branch.

Actual isolated computation: downloaded both Actions ZIPs into /mnt/data. Original artifact 11378995592 (run 37386241124) SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e matches expected; unzip -tq passed. Extracted only five required files to isolated outputs/backtest/hybrid-37386241124. SHA256:
- 2023-hybrid-signals.json 2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee
- 2024-hybrid-signals.json c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b
- 2025-hybrid-signals.json 8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42
- discovery-decisions.json 71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737
- firm-timing-inputs.json.gz e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb

Preserved output artifact 14691551088 (run 44864565861, commit 95d4d059092c51d9e8ee5b0df1589ff22b12785d) SHA256 95f916cdc1d988f752a49f14c38852c1f9876c5ddfd535bb915c19f840ea1ba1 matches. New actual Python check: for each of 54 target-rank-2026-10-05/*-trades.csv members, parse csv.DictReader and paired JSON trades array; compare length and each ordered CSV field to str(JSON field), mapping None to empty. Result: 655 rows, zero mismatches across all 54 normal/stress configurations. This is internal archived position consistency, not independent execution.

Next blocker: source tree not mounted in isolated filesystem. Connector fetch yields source text; exact dependency closure must be transferred and verified rather than replacing imports with stubs. Direct module Git blob IDs: intraday_replay 2aa2a4e2d3155325b45b34ab4da7358afaad96d3; models abe350d577439fa870c73d354b2628cb4bfb22d0; risk_model 00f3e1085bc9875355d9203038e09f8dcbb09e2c; swing_backtest d32a81bd2e74cf6305ef7de3476b3b33d0c659a2; confirmation_comparison 1f22966bfceaf88318ea4e20b53e3db76f499d80. Transitive imports include backtest, cli, game_firm_replay, market, transport, game_rules; requirements.txt returned 404; inspect pyproject.toml and source tree next. Local numpy 2.3.5 is available, original version not yet verified. Reproduction target python -m backtest.target_rank_research, unchanged source, offline. Do not rerun archived CSV consistency checks merely for another report.

Starting capital $100k per season; no new P&L, ending balance or challenger. Aug–Dec coverage and fresh windows still unresolved; promotion UNPROVEN. No live actions or workflow changes.