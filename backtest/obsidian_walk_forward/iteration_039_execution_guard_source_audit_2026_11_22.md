# OBSIDIAN iteration 039 — 2026-11-22 — execution guard audit and runtime availability

RESEARCH_ONLY_NOT_AN_ORDER. Append-only continuation of iteration 038. No production, portfolio desk, protected baseline, credentials, or trading changes.

## Read and verified
Read the continuous protocol, proposed discovery playbook, original prospective proof gate, diagnostic negative control, unchanged `backtest/target_rank_research.py`, and iteration 038 execution guard on the authorized branch. Root-level `FAST_DUMP_RANK_RESULTS.md` and `FIRM_TIMING_VALIDATION.md` returned 404 at the tested paths; their conclusions are summarized in the protocol, but the underlying reports were not independently reread in this iteration. Do not represent them as newly verified.

Original ranker blob: `e574c908eeb5fafbf918200296b01eeaf8dafbdd`. Iteration 038 guard blob: `e2060865a878255a8be78c64ab55f902a020977e`.

## One bounded concrete verification
Inspected the unchanged ranker's output statements against the iteration 038 guard: the ranker writes to `outputs/backtest/target-rank-2026-10-05` using `mkdir(parents=True,exist_ok=True)`, then writes year-model JSON, per-case JSON and trades CSV, and summary JSON. The guard checks this **exact same directory** and rejects any preexisting output directory. Thus the output collision safeguard targets the actual fixed output path; this is a source-level verification, **not a successful runtime test**.

## Runtime blocker and disposition
The current disposable container has Git available but no repository checkout or archive under `/mnt/data`; `getent hosts github.com` returned no address. Therefore the archive preflight, staging, guard and original ranker cannot be honestly run together here. Earlier archive checksum matches were reported in iterations 033/035, but bytes are not available in this iteration and must be verified again in the execution environment. No synthetic substitutions, no rerun of old diagnostic replay, no fabricated result.

## Evidence and next action
Target period Aug 1–Dec 31, 2025; independent synthetic initial capital $100,000. No executed baseline or challenger in this iteration, no new net/stress P&L, ending equity, profit factor, drawdown, trade count or benchmark. August and Dec 6–31 remain uncovered by the previously inventoried archive. Existing 2023–25 reports are previously inspected, not fresh holdouts. No challenger registered before original 54-case reproduction. Promotion UNVALIDATED.

Next bounded step: in one disposable environment with pinned source and archive bytes, run iteration 036 archive preflight, iteration 037 staging, iteration 038 guard, then `python -m backtest.target_rank_research` once, retaining output hashes and comparing all 54 cases with the original report. If the environment cannot be assembled, record the precise failing prerequisite rather than claiming a backtest.
