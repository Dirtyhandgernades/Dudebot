# OBSIDIAN Research Engineering — 2026-10-30 11:50 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Branch `research/obsidian-early-rug-20261025` only. No production/main, account access, trading, credentials, original prospective captures, policy changes, 136-name watchlist, JDZG failure analysis, frozen baseline labels, cohort denominators, or Rug Proof/Morning/After-Hours/Early Decision Board task ownership changed.

## P0-1: diagnostic vendor receipt status integrity

Implementation commit `f56b6d13bc74704a6a7608e486cb3151e8ccc2c5` corrects two fail-open cases in `backtest/obsidian_two_provider_close_reconciliation.py`:

1. A malformed or non-integer HTTP status in a legacy/injected vendor receipt could raise an exception in `category()`, interrupting the complete missingness inventory. Now only integer 100–599 statuses are accepted; other shapes become `MALFORMED_HTTP_STATUS` and are censored.
2. A vendor JSON payload with missing, unexpected, or partial status could previously enter the diagnostic `VALID_VENDOR_BAR` count if it echoed a matching symbol/date and numeric close. The observation now requires provider-specific successful status (`MASSIVE: OK`, `TWELVE_DATA: ok`) before admitting even a diagnostic vendor bar. All other statuses are `UNEXPECTED_PROVIDER_STATUS`, censored.

Two new regression tests cover malformed HTTP status shapes and vendor-status mismatches. Hosted `OBSIDIAN two-provider close reconciliation (research only)` run **41093462962** on the exact implementation commit completed **successfully**: **28 offline tests passed** (24 vendor-reconciliation tests + 4 ABC-board tests). The live vendor-fetch step was **skipped** on push; no vendor API requests, new raw close receipts, or reconciliation artifact were produced. Evidence: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41093462962 .

## Coordination and original evidence

At 11:49–11:50 CT the original 12:47 CT INTRADAY and protected 14:45–14:58 CT preclose capture gates were **not open**. The branch contained the October 30 Morning Movers and Rug Proof morning markers, but no October 30 engineering INTRADAY or preclose marker at this time. No new market capture, retry, backfill, duplicate marker, or speculative official halt/quote claim was made. Original October 30 Rug Proof morning run **41071432540** artifact **12985950392** and Morning Movers run **41069835420** artifact **12985125331** remained present and unexpired (both January 28, 2027 expiration); raw ZIP contents were not rehashed in this pass.

## Unresolved P0-1 acceptance gate

This software correction **does not** prove Massive real-time entitlement, exchange-authenticated official auction closes, independent underlying market-data source organizations, issuer/security-ID continuity, split/dividend/corporate-action basis, session calendar or source publication timestamps. No live vendor fetch was attempted. Independent source/conflict inventory and durable authenticated original receipts remain incomplete; all unverified forward outcomes remain **censored**.

Prospective 20%+ collapse prediction accuracy and profitability remain **unestablished**. Preserve forward 0/+1/+2/+3 actual trading sessions, all original frozen historical labels and denominators, and compare only untouched matched future cohorts including false positives, late/exhausted signals, squeezes, costs, and missingness. Alpaca borrowing does not establish SMG permissions; no SMG order or execution is authorized.
