# OBSIDIAN iteration 054 — 2026-11-23 — research only

Previous iteration: 053. Branch: research/obsidian-early-rug-20261025.

## Source inspection
Read the checked-in continuous protocol, discovery proposal, prospective proof gate, iteration 053 checker and iteration 052 negative-control test using GitHub connector. FAST_DUMP_RANK_RESULTS.md and FIRM_TIMING_VALIDATION.md were not found at repository root; the protocol cites them and the discovery proposal points to backtest/FAST_DUMP_RANK_RESULTS.md. No historical report figures were reclassified as a fresh run.

## One bounded repair
Added test_iteration_054_required_field_guard.py, targeting the *new* 053 checker instead of the intentionally failing 052 regression against the obsolete 049 checker. Three tests: a valid 54-configuration synthetic fixture passes; omission of exit_reason fails even when the CSV cell is empty; explicit null remains serializable. These are synthetic integrity fixtures, not strategy evidence.

## Execution blocker
Container network lookup of raw.githubusercontent.com failed (curl exit 6). GitHub connector can fetch source and commit new files, but cannot mount those files into the isolated Python environment. Accordingly the exact checked-in tests were **not executed**, and no original ranker execution or historical P&L is claimed. Reproduction still requires full pinned branch checkout, compatible dependencies, and the SHA256-verified artifact 11378995592 in the same environment.

## Outcome
2025-08-01 to 2025-12-31 target; $100,000 independent synthetic starting capital. New net P&L, ending equity, baseline/challenger and stress metrics: unavailable. Previously recorded gaps: no August hybrid decisions; 17 late-December sessions absent. No fresh prospective windows verified. No challenger registered; promotion UNVALIDATED.

## Reproduction command (when files are actually colocated)
python -m unittest discover -s backtest/obsidian_walk_forward -p 'test_iteration_054_required_field_guard.py' -v

Do not run target_rank_research until original source and archive checksum are verified. No protected, live, or production changes.
