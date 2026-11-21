# OBSIDIAN research and engineering operating guide

Research branch: `research/obsidian-early-rug-20261025`. Source of truth: this repository and linked Actions evidence. No main/production changes, orders, credentials, live alerts or new scheduled owners. This workflow is not proven profitable or end-to-end complete.

## Start and resume the bounded research lab

Use existing checkout, existing repository dependencies and the pinned original hybrid ZIP (run 37386241124, artifact 11378995592, ZIP SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e). The new `obsidian-strategy-lab.yml` workflow authenticates those bytes, runs the full test suite, reproduces `target_rank_research.py` unchanged, then runs `obsidian_research_runner`.

The runner verifies data/code/registration hashes, reproduces all 54 historical portfolio variants, audits every closed trade from those variants and executes E01/E02 risk diagnostics, E03 unranked control and a cash control. It records conditional results, not executable SMG gains. All 2023–2025 seasons were inspected before this work. Do not optimize on them and call them an unseen holdout.

```sh
python -m backtest.obsidian_research_runner --out outputs/backtest/obsidian-lab-UNIQUE_VERSION
```

Repeat the same command to resume. A completed stage is reused only when all recorded input/code and output hashes match. Missing/corrupt output or changed code fails closed; preserve the old checkpoint and create a new version. To restore an Actions checkpoint, restore the artifact's `backtest/` contents under `outputs/backtest/` and use its original lab directory name, after obtaining the original input ZIP and checking source/code hashes. No task is claimed to run continuously after a chat turn; this is a resumable bounded engine, not a new schedule.

Full raw ZIPs, trade/decision ledgers, daily equity and source bodies belong in Actions artifacts. Commit compact registrations, summaries, hashes, gaps and provenance. Artifact retention is finite; expiration is not proof of a durable backup.

## Keep three evidence layers separate

1. Frozen baseline and predictions: historical source files and prospective records remain unchanged.
2. Derived diagnostics: all new findings, losing variants, source repairs and late reviews have separate versions. `continuity-repair-registration.json` permits a valuation-only VERB→TONX / BREA→SLMT bridge after exact raw-overlap and primary-document checks. It does not authorize new entry signals, historical holdings, a full corporate-action clearance or official-close scoring.
3. Promotion: require authentic source/identity/execution coverage and genuinely untouched independent periods, plus the preregistered count, concentration, profit factor, drawdown and insolvency gates. A positive inspected-data simulation never promotes itself. No current candidate meets those requirements.

The Nov20 daily-heuristic diagnostic cycles in their existing note use a DIFFERENT archive, population, dates and strategy from the original seven-feature intraday ranker. Their losses are real conditional computations but not a failed reproduction of the profitable rank baseline. Keep both records and do not replace the original model with that simpler screen.

## Current source-to-board path

The existing manual `obsidian-free-quant-feed.yml` now collects a complete 139-name watchlist packet (retained 136 plus explicit scope overlay), preserves every missing/stale result, rotates bounded SEC enrichment, and calls `obsidian_candidate_pipeline`. It uses the shared V2 row assessor from commit 5515938 without weakening its weak-tape/counterevidence gates. Caller-supplied reviews must bind to original source receipts and clocks; such human assertions are not automatic source authentication. Keyword passages, proposed issuance, registration and actual sale remain distinct.

The collector uses IEX trade/quote clocks separately; delayed SIP minute bars are clipped to the actual regular-session close and never called live. Redacted response bodies, safe request parameters, original/archived hashes and receipt times are archived; redaction may change bytes, which is explicitly recorded. Empty Nasdaq halt rows never clear a security.

A fixed copy of the reproduced 2025 seven-feature model can receive 22 prior completed exchange-session raw/split bars. Its model card records the exact source and hash. The generic free watchlist is not the historical hybrid-trigger population: without that match the score is diagnostic and excluded from candidate ordering. Resulting scores are CONDITIONAL ORDINAL SHADOW RANKS, never calibrated confidence, approved signals or a qualified replacement. Missing/duplicate/future/invalid daily inputs have no score. The live baseline is not retrained or replaced. Classifier thesis, completeness, supply review, counterevidence, liquidity and model rank remain separate. The board gives all rejection rows and no forced recommendation slots. After-hours or off-checkpoint boards are labeled late/research, never retroactive 14:20 predictions.

The actual 14:20 owner/destination must still be verified through its scheduling system; no tool for those task records is available here. Existing schedules were not duplicated. Artifact creation, actual message delivery and completed market outcomes are distinct facts.

## Portfolio and execution boundary

`obsidian_portfolio_guard` reuses the conservative exposure helper, preserves research theses when account evidence is absent, and blocks sizes on stale/missing account data, permissions, account exposure, unknown borrow, deadline or duplicate/ambiguous intent. It is a paper preview and reconciliation state machine. There is no order-submission method; browser success is not an execution receipt. No account private values or credentials are persisted by this work. The prior TinyFish/TinyVault read-only account setup is documented, but its scoped runtime tool/session is not available in this execution environment.

Do not activate a strategy before the research gates pass. Do not use an Alpaca shortable flag as SMG permission. Reconcile ambiguous confirmations before proposing another intent; do not bypass the user's confirmation requirement.

## Work queue

Read `backtest/evidence/2026-11-20/strategy-overhaul/gap-ledger.json` and the latest hosted-verification report. Resume source continuity and coverage gaps first, then genuinely untouched long/short and catalyst studies. Portfolio allocation and execution previews may consume only qualified components. No current script certifies consistent profitability, source-independent official closes, full-market recall or real SMG execution.
