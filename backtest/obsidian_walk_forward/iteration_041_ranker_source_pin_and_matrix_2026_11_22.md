# OBSIDIAN iteration 041 — 2026-11-22 — original ranker source-pin and run-matrix audit

RESEARCH_ONLY_NOT_AN_ORDER. Append-only continuation of iteration 040. No SMG authentication, orders, account/vault data, live automation, protected baselines, deployment, alerts, or main changes.

## Primary documents read from authorized branch
- backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md — Git blob 45d49fb811827d5d614d05b30d7fac8a7bd5d771
- backtest/FAST_DUMP_RANK_RESULTS.md — 617d7606b11b92e0ccc87bfc70f44eb7544102d6
- backtest/FIRM_TIMING_VALIDATION.md — 88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178
- backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md — c3b0873774cab2afc352d542d98db5e6565af032
- backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md — 7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79
- backtest/OBSIDIAN_DIAGNOSTIC_REPLAY_CYCLES_1_2_2026_11_20.md (negative control) — 9a9ba45a4485bed1d924e99d50c5a905b04e71de

## Concrete new source-level audit
Read unchanged backtest/target_rank_research.py (Git blob e574c908eeb5fafbf918200296b01eeaf8dafbdd) and the five directly imported research modules from the authorized branch:
- smg/intraday_replay.py — 2aa2a4e2d3155325b45b34ab4da7358afaad96d3
- smg/models.py — abe350d577439fa870c73d354b2628cb4bfb22d0
- smg/risk_model.py — 00f3e1085bc9875355d9203038e09f8dcbb09e2c
- smg/swing_backtest.py — d32a81bd2e74cf6305ef7de3476b3b33d0c659a2
- backtest/confirmation_comparison.py — 1f22966bfceaf88318ea4e20b53e3db76f499d80

The original source's static loop produces exactly **54** portfolio cases: three years (2023, 2024, 2025) x [top_half (2 targets x 2 costs), top_quartile (2x2), top_decile (2x2), confirmed_top_quartile (2x2), top_half_30pct (1 target x 2 costs)] = 3 x 18. Additionally it writes 3 model JSON files, 54 portfolio JSON files, 54 trades CSV files and a summary JSON if every run succeeds. This is a source-derived expected-output inventory, **not an execution**.

The source explicitly reads five archived inputs under outputs/backtest/hybrid-37386241124: firm-timing-inputs.json.gz, discovery-decisions.json, and 2023/2024/2025-hybrid-signals.json. It writes fixed filenames to outputs/backtest/target-rank-2026-10-05. Reproduction command: python -m backtest.target_rank_research; run only after checksum preflight, isolated source assembly, and iteration 038 no-overwrite guard.

## Availability and result status
Local container /mnt/data has no archived ZIP or checkout; github.com DNS resolution failed (gaierror: Temporary failure in name resolution). GitHub connector successfully reads the branch's UTF-8 source, but cannot itself establish a co-located executable checkout/archive. Archive to reverify: Actions run 37386241124, artifact 11378995592, SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e. No attempt to claim that prior downloads persist. No baseline rerun, no challenger, no fresh holdout, no new P&L.

Historical reference (not newly computed): original 2025 aggressive 50k/30% +$103,258.54 net, +$64,020.56 stress; lower-exposure 30k/25% +$73,815.54 net, +$48,528.08 stress. Synthetic initial capital $100,000. Newly computed ending equity and all promotion metrics: unavailable. August and Dec 6-31 2025 missing/unverified; 2023-25 already inspected.

## Next bounded action
Assemble the pinned modules and transitive dependencies with the checksum-verified ZIP in one disposable checkout, run archive preflight and staging, run the guard, execute the original unmodified ranker once, and reconcile all 54 outputs against FAST_DUMP_RANK_RESULTS.md including positions, base and stress. Do not register a challenger before that reconciliation. Promotion UNVALIDATED.
