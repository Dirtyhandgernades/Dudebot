# OBSIDIAN iteration 052 — required-field omission negative control (2026-11-23)

RESEARCH ONLY. Branch `research/obsidian-early-rug-20261025`. No SMG access, private data, production, main, frozen baseline, or Portfolio Desk changes.

## Source evidence
Read `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md`, `backtest/FAST_DUMP_RANK_RESULTS.md`, `backtest/FIRM_TIMING_VALIDATION.md`, the trade-discovery playbook, prospective proof gate, and diagnostic negative control. Inspected unchanged `backtest/target_rank_research.py` (Git blob `e574c908eeb5fafbf918200296b01eeaf8dafbdd`), iteration 049 checker (blob `a9d1a268372a74b7fd1bd635f1fca4cb90ade9b9`), iteration 050 tests (blob `afef41c30364aab8a3d51ea9164caf63ef2c70bb`) and iteration 051 note.

## Concrete new defect / bounded computation
The iteration 049 checker compares `row.get(field)` to `csv_cell(trade.get(field))`. If a required key is **absent** from the JSON trade, `trade.get(field)` returns `None`. Python's original `csv.DictWriter` writes that missing field as an empty CSV cell. The checker therefore considers both sides equal, and can return PASS even though the required JSON key was absent. Executed a local standard-library `csv.DictWriter` / `csv.DictReader` demonstration with `exit_reason` omitted: the CSV cell was `''` and the current equality expression returned `True`. This is a checker integrity defect, not a trading result. The demonstration does not establish an actual historical portfolio has missing keys.

Registered an append-only regression `backtest/obsidian_walk_forward/test_iteration_052_missing_trade_field.py` on this branch (commit `a506ef50643aafaf2b930da065b418c9c0993cad`). It constructs all 54 synthetic configurations with one required field omitted in one JSON trade, and requires BLOCKED. **The newly checked-in test has not been executed.** Under the inspected iteration 049 logic it is expected to fail until a separate append-only checker repair is introduced. Do not silently weaken or remove the negative control.

## Execution / promotion
Original ranker still not reproduced in this iteration: pinned complete checkout and verified archived input ZIP not co-located in an executable environment. No new historical P&L or ending equity computed. Synthetic initial balance $100,000. August hybrid signals and 17 late-December sessions remain missing in previously inspected archived data. No challenger registered. Promotion UNVALIDATED; 0 verified genuinely fresh test windows.

## Next bounded action
Run the exact checked-in new regression; implement a separate versioned checker rejecting absent required trade keys, and re-run all checker regressions. Then co-locate pinned source and verified artifact 11378995592 for the original unmodified 54-configuration reproduction. No strategy changes before reconciliation.
