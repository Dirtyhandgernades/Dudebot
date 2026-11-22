# OBSIDIAN iteration 042 — 2026-11-22 — artifact availability and reproducibility blocker

RESEARCH_ONLY_NOT_AN_ORDER. Append-only continuation of iteration 041. No SMG login, private/vault data, orders, production automation, alerts, protected baselines, deployment, or main edits.

## Primary-source review
Read from authorized branch: backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md (blob 45d49fb811827d5d614d05b30d7fac8a7bd5d771); backtest/FAST_DUMP_RANK_RESULTS.md (617d7606b11b92e0ccc87bfc70f44eb7544102d6); backtest/FIRM_TIMING_VALIDATION.md (88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178); backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md (c3b0873774cab2afc352d542d98db5e6565af032); backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md (7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79); and backtest/OBSIDIAN_DIAGNOSTIC_REPLAY_CYCLES_1_2_2026_11_20.md (9a9ba45a4485bed1d924e99d50c5a905b04e71de), negative control only. Reviewed iteration 041 ledger (b0d56b8c068d42ac1699c9023e637a11868c9907).

## New direct artifact metadata verification
Queried GitHub Actions run 37386241124 through authenticated repository connector (metadata read only), 2026-11-22. The original input artifact is **currently available and not expired**:
- ID: 11378995592; name: pre-close-firm-37386241124
- Size: 11,294,854 bytes
- GitHub-reported digest: sha256:a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e
- Created 2026-10-05T23:04:09Z; expires **2027-01-03T23:03:15Z**; expired=false
- Producing workflow head: main at b8fbd035543611f49992d6df3b619af7a6ddf548 (not the later research-branch ranker)
- Artifact metadata URL: https://api.github.com/repos/Dirtyhandgernades/Dudebot/actions/artifacts/11378995592

This verifies **current server-side availability and published digest**, not independent byte hashing, ZIP extraction, source compatibility, or a new execution. The source code/archived inputs must still be assembled in the same isolated filesystem. GitHub connector file reference alone is not a locally mounted executable input.

## Bounded repair outcome and blockers
Material gap clarified: archive expiration is **not** the blocker through the December 4 research cutoff; the blocker is co-location of the exact archive bytes with the pinned research-branch source/dependencies in a disposable execution environment. Prior iteration 035 downloaded and verified ZIP bytes but this run cannot assume that container persists. Avoid another source-only dry run or repeated notes masquerading as performance. If a future run can materialize the ZIP and pinned source together, first run existing iteration 036 preflight, iteration 037 stage, iteration 038 no-overwrite guard, then exactly once `python -m backtest.target_rank_research`, reconcile 54 configurations against FAST_DUMP_RANK_RESULTS.md. No change to the original ranker.

## Performance and gate
Synthetic capital $100,000; no new execution, fills, daily equity, P&L, challenger, or independent holdout. Historical 2025 aggressive +$103,258.54 net / +$64,020.56 stress and lower exposure +$73,815.54 net / +$48,528.08 stress remain retrospective report numbers only. Aug and late-Dec 2025 coverage unresolved; exact SMG eligibility/borrow unverified. No hypothesis change registered until original reproduction. Promotion: UNVALIDATED.
