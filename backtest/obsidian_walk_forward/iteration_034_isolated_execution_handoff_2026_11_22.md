# OBSIDIAN iteration 034 — isolated execution handoff (2026-11-22)

RESEARCH ONLY. Continuation of iteration 033. Authorized branch `research/obsidian-early-rug-20261025`; no orders, SMG credentials, protected baselines, production automation, alerts, or promotion.

## Required source review
Read `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md`, `backtest/FAST_DUMP_RANK_RESULTS.md`, `backtest/FIRM_TIMING_VALIDATION.md`, `backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md`, `backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md`, and diagnostic cycles 1–2 only as a negative control. Read iteration 033 verified archive manifest. 2023–25 remain inspected retrospective seasons.

## Actual current-run environment check
Attempted read-only `git ls-remote https://github.com/Dirtyhandgernades/Dudebot.git refs/heads/research/obsidian-early-rug-20261025` in the isolated execution container. Failed before contacting GitHub: `Could not resolve host: github.com`. Container `/mnt/data` has no archived ZIP or extracted packet; previous iteration's container paths are not mounted in this execution. GitHub connector can read repository text but does not automatically place those bytes in the isolated Python container. Thus no honest executable baseline reproduction was possible here. The previous iteration's checksum verification is historical evidence, not a new checksum computation.

## One feasible repair: reproducible isolated-run recipe
The following procedure is a *manual handoff, not a completed run*. It must be executed only in a network-capable isolated runner with access to the original artifact archive, no SMG credentials, no production checkout, and no writes to the repository. Use a pinned commit corresponding to the verified research-branch source snapshot (not the artifact-producing commit). Do not use an unreviewed floating branch head.

1. Copy GitHub Actions artifact `11378995592` (run `37386241124`) into a fresh temporary directory. Verify SHA-256 equals `a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e` before extraction.
2. Extract exactly `firm-timing-inputs.json.gz`, `discovery-decisions.json`, `2023-hybrid-signals.json`, `2024-hybrid-signals.json`, and `2025-hybrid-signals.json` into `outputs/backtest/hybrid-37386241124/` beneath a disposable working directory. Reject path traversal, symlinks, duplicate names, unexpected entries and mismatched individual hashes from iteration 033.
3. Assemble a read-only snapshot of the unchanged ranker and pinned transitive dependencies from the authorized branch, with an isolated Python environment satisfying the pinned `pyproject.toml`. Verify ranker Git blob `e574c908eeb5fafbf918200296b01eeaf8dafbdd` and dependency hashes from iterations 029–031. Never install or execute production services or workflows.
4. From the disposable working directory run `python -m backtest.target_rank_research`. Its output directory is hard-coded as `outputs/backtest/target-rank-2026-10-05`; do not run from a production checkout.
5. Inventory output files and their SHA-256, record Python/package versions, command, exit code and all 54 configuration results. Compare each normal/stress result and position-level trade rows to `backtest/FAST_DUMP_RANK_RESULTS.md`; mismatches must be reported, not patched into the original code. Preserve immutable original inputs and append a separate reproduction manifest.

This recipe addresses the missing executable-environment handoff, but does not repair the runner's DNS or transfer the archive. Do not describe it as execution.

## Status
Synthetic initial capital: $100,000 (specification only). New computed net P&L, ending equity, stress returns, baseline/challenger comparison: unavailable. Aug 2025 and Dec 6–31, 2025 point-in-time signal coverage remains missing. No new hypothesis until original 54-case reproduction. Promotion UNVALIDATED.
