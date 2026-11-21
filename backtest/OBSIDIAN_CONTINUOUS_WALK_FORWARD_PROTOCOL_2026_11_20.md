# OBSIDIAN continuous walk-forward protocol — registered November 20, 2026

**RESEARCH ONLY.** Separate from the live portfolio desk. No actual SMG orders or credentials, deployment, alerts or protected baseline edits.

## Starting evidence
- FAST_DUMP_RANK_RESULTS.md: 2023/24/25 normal modeled profits $18,658.11/$39,124.52/$103,258.54; stress $16,487.95/$25,305.11/$64,020.56; observed drawdowns 3.059%/25.691%/19.966%; 2025 target hits 6/35. Two names supply ~56% of 2025 net profit.
- FIRM_TIMING_VALIDATION.md: alternate 2025 policy loses $189,510.63 in conditional simulation, including $167,915.33 SMX loss. All evaluation years already inspected. Neither report proves executable SMG returns.
- Artifact inventory: workflow run 37054630140 lists unexpired artifact 11248765264, game-period-outcomes-37054630140, 8,923,491 bytes; original report publishes SHA256 a84d1eead532d770d5d17bdf508a7246f51f5c9ef33827a94d4c33b0ef10559e. Listing is not download, checksum verification or rerun. Obtain actual data and verify expected dataset coverage before computing any results. Existing report covers Sep 8–Dec 5, not all Aug–Dec.

## Target experiment
Replay Aug 1–Dec 31, 2025 through each exchange session, synthetic starting equity $100,000. Use the actual archived strategy/version and information available before decision time, not later announcements or closing price. Freeze baseline, candidate universe, input hashes, cutoff and rules; simulate whole-share orders at permitted EOD closes using decision-time share sizing, fees, buying power, margin and exit rules. Record missing or unverified eligibility/halts/short availability as conditional or censored, never confirmed execution. Apply raw prices to eligibility and corporate-action-consistent valuations. Check >$3 threshold against actual game rule (at least $3), $25m as-of cap, minimum ten shares for opens, and actual EOD/early-close calendar. Retain all eligible, blocked and unseen issuers; preserve no-trades. If August data is missing do not fabricate it or imply full-period coverage.

## Repeated loop
1. Recover point-in-time data and archive seeds; log missing dates, provenance and exact inputs.
2. Reproduce original result on identical inputs before claiming baseline matched. Versioned orders and daily ledger must determine net equity, not target-selected winners.
3. Audit all decisions, misses, false positives, wrong direction, late signals, missing prices, squeezes, losses, concentration, sizing and failed exits.
4. Register exactly one challenger hypothesis and threshold change before outcomes; retain original results and every failed variant.
5. Train on earlier periods only; purge overlapping labels. Evaluate on next nonoverlapping time fold; previously inspected 2023–25 data is retrospective, not fresh holdout. Use genuinely fresh windows and paired prospective evidence for promotion.
6. Compare baseline and challenger on identical cohorts/costs with realized/modelled gains distinguished. Record start/end equity, net/stress P&L, closed trades, win rate, profit factor, expectancy, drawdown, turnover, largest loss, issuer concentration, precision/recall and coverage; benchmark cash and index. Confidence ranks are not calibrated probabilities.
7. Repeat on next hour's bounded research iteration, preserving manifest, immutable decisions, code/input hashes, full denominators and reproducible run IDs. No invented results if compute/data not available. If blocked, take one concrete remediation step.

## Proposed validation criteria (preregistered, not optimized)
Positive net and stressed returns across at least three genuinely fresh nonoverlapping windows; target at least 100 independent closed trades across test windows with dependence and uncertainty reported, after-cost profit factor >=1.3, observed maximum drawdown <=20%, no insolvency, no issuer >25% net profit. Benchmark appropriately and respect stricter existing forward proof gate. No gate weakening to meet target. A pass is evidence for review, not guarantee; freeze challenger if passed. No automatic promotion to actual trading. If insufficient data, report unproven. 

## Current status
Baseline reports reviewed, archive inventory located. New Aug–Dec replay **not yet executed**. Next task: verify raw input coverage, reproducibility and compute access; create isolated baseline ledger and log real data gaps before revising the strategy.
