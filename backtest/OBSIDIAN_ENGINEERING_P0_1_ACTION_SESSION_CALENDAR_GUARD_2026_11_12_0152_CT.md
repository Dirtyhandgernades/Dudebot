# OBSIDIAN P0-1 action/identity published-session chain guard — 2026-11-12 01:52 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Branch `research/obsidian-early-rug-20261025` only. Offline validation, not a provider fetch, official close, trading approval, or model-performance result.

## Verified software milestone

- Starting branch head `c989b8f45c90dc9eee259336d308df92935f0e60`. Expected-head fast-forward code/test commit [`b62fccb5458e949cc5af74345bc3209eecec7af4`](https://github.com/Dirtyhandgernades/Dudebot/commit/b62fccb5458e949cc5af74345bc3209eecec7af4).
- `backtest/obsidian_eod_action_identity_shadow.py` previously checked caller-supplied corporate-action receipt timestamps against a synthetic 16:00 ET session end, but did **not** apply the published 2026 cash-equity session calendar and adjacent-previous-session screen already used by the independent price preflight. Consequently, mutually consistent fabricated action receipts for a closed exchange day or a skipped prior trading day could return `STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING` in this standalone auditor. That status is not an official-close verdict, but it could obscure an invalid session chain in downstream manual review.
- The standalone action/identity auditor now includes the shared `_published_2026_calendar_issues(session, previous)` screen. Invalid published holidays/weekends, out-of-scope years, skipped prior sessions, and published 13:00 ET early-close sessions remain `BLOCKED_CENSORED`. Every supplied source row and original action/identity claim remains indexed; no frozen label, score or denominator changes.
- Five synthetic regression tests cover holiday/weekend cases, skipped prior trading day, current/previous early-close, out-of-scope year, and a legitimate holiday-gap adjacent trading-session pair. These do not assert independent calendar authentication.
- [Hosted GitHub Actions run 43178588924](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43178588924) completed **successfully on the exact code commit**. Its job logs show **708 prospective tests and 4 board tests passed**, including the five new tests. No artifact was published by this test workflow.

## Coordination and immutable boundaries

- Read the [November 11 18:20 CT Rug Proof postclose audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md) and existing 09:20/12:20 anchors, 14:20 board/SIP markers. No duplicate issuer/day anchors, board, morning, after-hours, or protected IEX markers were created.
- Independently rechecked November 11 delayed SIP [43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523), protected preclose [43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151), and independent monitor [43095840045](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095840045): each remains **queued with zero jobs and zero artifacts**. Their genuine capture windows expired; no retry, backfill, or substitution.
- This run is outside the authorized 12:47 CT intraday and 14:45–14:58 CT preclose windows. No new live source retrieval, account access, production/main changes, secrets, market orders, or trading notifications.

## Unresolved external evidence / evaluation gates

- The static 2026 calendar screen is not exchange-authenticated session evidence. P0-1 still lacks two independently authenticated provider-organization **official regular-session** closing-price and previous-close receipts with complete source/conflict inventory, corporate-action and security-class continuity, actual exchange calendar, session timestamps and halt reconciliation. Optional Massive live key/entitlement and actual SMG account-level blocked-symbol/security/shortability permissions are **unverified**; Alpaca borrowing is not SMG approval.
- The original **136-name** watchlist, JDZG stale/halt failure analysis, frozen baseline labels and denominator remain untouched. Future evaluation is only 0/+1/+2/+3 **actual trading sessions** on matched untouched cohorts, accounting for false positives, late/exhausted cases, squeezes, costs and missingness. Without independently authenticated outcomes, all such cases remain **CENSORED**, neither successes nor failures. No 20%+ predictive success or trading-performance claim.
