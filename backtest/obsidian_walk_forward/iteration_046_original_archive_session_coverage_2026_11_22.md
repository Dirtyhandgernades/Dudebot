# OBSIDIAN iteration 046 — 2026-11-22 — original archive recovered; session/signal coverage measured

RESEARCH_ONLY_NOT_AN_ORDER. Continuation of iteration 045. No SMG account/vault access, orders, production workflows, protected baselines, alerts, deployment, or main changes. This is an input-coverage audit, NOT a strategy execution or validation.

## Read and provenance
Read the authorized-branch protocol, FAST_DUMP_RANK_RESULTS, FIRM_TIMING_VALIDATION, discovery playbook, prospective proof gate, diagnostic negative control, and iteration 045. Downloaded the original GitHub Actions artifact **11378995592** from run **37386241124** via the GitHub connector into a disposable container. Local ZIP file was 11,294,854 bytes; locally computed SHA256 **a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e**, exactly matching the registered original. Read the five baseline-required members directly from this ZIP, without changing bytes:

- firm-timing-inputs.json.gz SHA256 e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb
- discovery-decisions.json SHA256 71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737
- 2023-hybrid-signals.json SHA256 2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee
- 2024-hybrid-signals.json SHA256 c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b
- 2025-hybrid-signals.json SHA256 8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42

## Actual computation: Aug–Dec 2025 date coverage
Used installed exchange_calendars XNYS sessions_in_range('2025-08-01','2025-12-31') to count 106 exchange sessions. Compared the archive's `sessions` array and dated keys of `2025-hybrid-signals.json`. These are availability counts, not verified price/eligibility/complete-universe coverage.

| Month | Exchange sessions | Archived session keys | Dated hybrid signal keys |
|---|---:|---:|---:|
| Aug | 21 | 21 | 0 |
| Sep | 21 | 21 | 17 |
| Oct | 23 | 23 | 23 |
| Nov | 19 | 19 | 19 |
| Dec | 22 | 5 | 4 |
| **Total** | **106** | **89** | **63** |

Hybrid signals contain 90 candidate rows across 63 dated keys (2025-09-08 through 2025-12-04). The archive's global sessions extend through 2025-12-05. Missing global session keys are **17 XNYS sessions, Dec 8–31**. August is NOT wholly absent from the archive: 21 global calendar keys are present, but there are **zero August hybrid signal-date keys**, so August decision coverage is not demonstrated. Sep 1–5 have no hybrid keys. No full-universe denominator, independent official EOD authentication, historical SMG eligibility or shortability established.

## Execution and disposition
No unchanged original ranker executed: the complete pinned checkout at e7989871cbc66f1a06a1867f1a23066e1f57fa6b and transitive dependencies were not co-located with the archive in this container; direct github.com DNS unavailable. No new strategy outputs or P&L; synthetic start $100,000; ending equity, baseline/challenger PF/drawdown/stress unavailable. Historical +$103,258.54 aggressive and +$73,815.54 lower-exposure figures remain *previously inspected conditional reports*, not newly reproduced results. All 2023–25 previously inspected; no fresh holdout and no registered challenger until original reproduction.

## Next bounded step
Use the pinned full checkout and recovered archive in the same isolated environment; run the existing 036/037 checksum preflights and 038 fail-closed guard; execute `python -m backtest.target_rank_research` unchanged **once**, reconcile all 54 configurations against FAST_DUMP_RANK_RESULTS. If successful, prioritize missing August decision evidence and 17 late-December sessions before any Aug–Dec replay or fresh challenger. Never promote automatically. **Promotion UNVALIDATED.**
