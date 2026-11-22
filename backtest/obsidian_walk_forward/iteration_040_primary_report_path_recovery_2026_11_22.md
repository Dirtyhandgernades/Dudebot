# OBSIDIAN iteration 040 — 2026-11-22 — primary baseline report paths recovered

RESEARCH_ONLY_NOT_AN_ORDER. Append-only continuation of iteration 039. No orders, account access, live desk, protected baselines, deployment, alerts or main changes.

## Verified primary documents
Read on the authorized branch: `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md` (Git blob 45d49fb811827d5d614d05b30d7fac8a7bd5d771), `backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md` (c3b0873774cab2afc352d542d98db5e6565af032), `backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md` (7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79), and diagnostic negative control `backtest/OBSIDIAN_DIAGNOSTIC_REPLAY_CYCLES_1_2_2026_11_20.md` (9a9ba45a4485bed1d924e99d50c5a905b04e71de).

**Concrete repair:** the earlier 404s were incorrect root-level paths, not absent reports. Enumerated the branch's `backtest/` directory through GitHub contents and recovered and read:
- `backtest/FAST_DUMP_RANK_RESULTS.md` blob `617d7606b11b92e0ccc87bfc70f44eb7544102d6`.
- `backtest/FIRM_TIMING_VALIDATION.md` blob `88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178`.

## Primary baseline reference now independently reopened
Original ranker report: top-half $50k target/30% equity cap, 3-session hold, $100k independent start; 2023/2024/2025 modeled net +$18,658.11 / +$39,124.52 / +$103,258.54, stress +$16,487.95 / +$25,305.11 / +$64,020.56, drawdown 3.059% / 25.691% / 19.966%, closed trades 3 / 16 / 36. These are **previously inspected archived report numbers, not newly computed P&L or executable SMG fills**. The lower-exposure $30k target/25% cap top-half variant reported +$15,587.70 / +$37,403.93 / +$73,815.54, stress +$13,809.62 / +$26,795.01 / +$48,528.08. Original report says all 54 cases at `outputs/backtest/target-rank-2026-10-05`; `python -m backtest.target_rank_research` is the reproduction command.

Firm-timing negative comparison remains separate: 2025 revised three-session firm policy -$189,510.63 conditional modeled P&L, with an SMX loss of $167,915.33. It is not the original ranker and must not replace it.

## Blockers and next step
This iteration did **not** execute the original ranker: no co-located pinned source/dependencies and verified archive bytes in this container. Archive source run 37386241124, artifact 11378995592, expected SHA256 `a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e`; verify again before use. Next bounded repair is to co-locate the original archive, unchanged ranker and dependencies in a disposable execution environment; run preflight/staging/guard and then the ranker once, reconciling 54 cases including positions, normal and stress. No challenger registered yet. August and Dec 6–31 2025 are still unverified/missing. 2023–25 are not untouched holdouts.

Synthetic initial capital $100,000; **newly computed** ending equity, net/stress return, PF, drawdown and benchmark: unavailable. No promotion evidence; status UNVALIDATED.
