# OBSIDIAN iteration 058 — verified original archive colocated (2026-11-23)

RESEARCH ONLY. Branch research/obsidian-early-rug-20261025. Continued from iteration 057; no production or SMG access.

## Actual execution
Downloaded GitHub Actions run 37386241124 artifact 11378995592 via GitHub connector into isolated container path /mnt/data/pre-close-firm-37386241124.zip. Computed SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, exactly matching registered hash. ZIP integrity test passed; 30 members listed. Extracted five required authentic members, without overwriting, into /mnt/data/obsidian_iteration_058/outputs/backtest/hybrid-37386241124/.

Member SHA256:
- firm-timing-inputs.json.gz: e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb
- discovery-decisions.json: 71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737
- 2023-hybrid-signals.json: 2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee
- 2024-hybrid-signals.json: c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b
- 2025-hybrid-signals.json: 8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42

Fetched source backtest/target_rank_research.py on authorized branch, blob SHA e574c908eeb5fafbf918200296b01eeaf8dafbdd. Read registered protocol, playbook, proof gate, diagnostic negative control, backtest/FAST_DUMP_RANK_RESULTS.md and backtest/FIRM_TIMING_VALIDATION.md.

## Boundary and blockers
This is **staging only**, not a new backtest. Original ranker and its smg dependencies have not yet been assembled and executed in the isolated container; original 54 outputs remain unreproduced. The extracted inputs are available for this iteration only unless explicitly persisted. Aug hybrid signals and late-December coverage are incomplete. Synthetic starting balance $100,000; no newly computed equity, P&L, stress or challenger metrics. All historical seasons previously inspected; no fresh holdout. Promotion unvalidated.

## Next bounded action
Fetch exact branch source and required smg dependencies into isolated read-only source tree, verify code hashes, execute unmodified python -m backtest.target_rank_research only when original inputs and dependencies colocated; compare 54 outputs and positions to archived report. Do not edit original ranker or launch workflow. No challenger hypothesis registered.
