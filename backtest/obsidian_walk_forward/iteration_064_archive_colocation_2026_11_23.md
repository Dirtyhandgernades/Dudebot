# OBSIDIAN iteration 064 — archive colocated in current isolated runtime (2026-11-23)

RESEARCH ONLY. Continuation of iteration 063. Authorized branch `research/obsidian-early-rug-20261025`. No SMG authentication, orders, private account/vault data, Portfolio Desk, frozen baseline, deployment, workflow execution, or main changes.

## Sources reviewed
Read `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md` (blob 45d49fb811827d5d614d05b30d7fac8a7bd5d771), `backtest/FAST_DUMP_RANK_RESULTS.md` (617d7606b11b92e0ccc87bfc70f44eb7544102d6), `backtest/FIRM_TIMING_VALIDATION.md` (88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178), `backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md` (c3b0873774cab2afc352d542d98db5e6565af032), `backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md` (7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79), diagnostic cycles 1–2 (9a9ba45a4485bed1d924e99d50c5a905b04e71de; NEGATIVE CONTROL ONLY), iteration 063 (2573df4a1a352b03e5259ba397348c97631f99d5), and unchanged `backtest/target_rank_research.py` (e574c908eeb5fafbf918200296b01eeaf8dafbdd).

## Actual new repair
Downloaded Actions artifact 11378995592 from run 37386241124 into this runtime at `/mnt/data/github-actions-artifact-11378995592.zip`. Computed SHA256 **a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e**, exactly the registered digest. ZIP test: no errors, 30 entries. Extracted the five exact original inputs with exclusive file creation to isolated `/mnt/data/obsidian064/outputs/backtest/hybrid-37386241124/`:

| Member | SHA256 |
|---|---|
| firm-timing-inputs.json.gz | e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb |
| discovery-decisions.json | 71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737 |
| 2023-hybrid-signals.json | 2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee |
| 2024-hybrid-signals.json | c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b |
| 2025-hybrid-signals.json | 8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42 |

Checked installed Python package presence: numpy, pandas, pydantic, exchange_calendars, lxml, requests, PyYAML and bs4 all import-discoverable. No complete repository checkout was present in this isolated container, and GitHub hostname resolution remained unavailable via shell. The GitHub connector can fetch individual source files, but the complete verified source closure has not yet been assembled here. No original ranker execution or output reconciliation is claimed. Note that runtime staging may not persist across future automation runs; the archive is retrievable again by connector.

## Research state and next step
Synthetic initial balance $100,000; new P&L and ending equity NOT COMPUTED. No baseline/challenger metrics or fresh holdout evidence. August 2025 hybrid signals and late December remain uncovered. Next step: assemble pinned full checkout in the same isolated runtime as the verified archive; run unchanged `python -m backtest.target_rank_research`, reconcile all 54 output cases (normal, stress, positions) against the original report. Do not introduce a challenger until original baseline matches. Promotion UNVALIDATED.
