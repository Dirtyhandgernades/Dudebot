# OBSIDIAN P0-1 complete-source issuer-class claim inventory — 2026-11-12 03:45 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only; no market orders, production, secrets, alerts, or scoring changes. This is an offline synthetic test improvement, not an authenticated official-close or forecast result.

## Verified implementation

- Starting head `47b6570c74b300b795ac785e9354d0a38aee0b81`; code/test commit [`5e447f4f57866eed733275ae010d1dadf42a7e8b`](https://github.com/Dirtyhandgernades/Dudebot/commit/5e447f4f57866eed733275ae010d1dadf42a7e8b), fast-forwarded with an expected-head GitHub lease.
- `backtest/obsidian_eod_conflict_inventory.py` previously indexed current and prior security IDs but omitted issuer/share-class claims from its complete-source ledger. A rejected third source claiming ADR versus COMMON (or a previous-session PREFERRED class) could remain visible as a rejected row without a class-specific conflict inventory. This is material to interpreting a 20% close-to-close comparison across the same instrument.
- Added separate **current** and **previous** issuer-class claim groups, original source row indices split by structurally valid/rejected source, explicit missing-claim indices, and class claims in the existing per-source audit record. Explicit disagreement now adds `ALL_SOURCE_ISSUER_CLASS_CLAIM_CONFLICT` or `ALL_SOURCE_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT` and returns `BLOCKED_CENSORED`. No source is promoted to official evidence. Existing missing-class source-contract behavior and frozen policy remain unchanged; separate action/identity authentication is still mandatory.
- Three new regression tests verify a rejected third-source current-class conflict despite matching prices, a previous-class conflict despite matching security ID, and missing-class claim indexing without false authentication.
- [Hosted CI run 43194182675](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43194182675) **completed successfully on the exact code commit**: 714 prospective offline tests and 4 board tests passed. This CI is a code contract check, not a market-data capture or prediction test.

## Cross-task evidence and gates

- Reviewed the original [November 11 Rug Proof postclose audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md) and original IEX, SIP, independent-monitor and preclose markers. At this checkpoint, protected preclose [run 43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151), delayed SIP [run 43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523), and earlier independent monitor [run 43095840045](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095840045) were still **queued**, each with zero artifacts. No retry or backfill. The distinct completed afterhours independent-source [run 43102970599](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43102970599) retained artifact `13893380436`, but did not establish Massive entitlement or independent official closing prices.
- Outside authorized 12:47 CT IEX and 14:45–14:58 CT protected prospective windows; no market trigger or marker was created. Morning, After-Hours, Early Decision Board and Rug Proof ownership preserved.

## Remaining blockers and immutable evaluation

- **P0-1 not complete:** no authenticated official current/previous regular-session closes from two genuinely independent source provider organizations, complete source-conflict ownership proof, actual-session calendar, issuer identity/class and corporate-action reconciliation, full halt history or SMG account shortability. Missing receipts are **CENSORED**, not negative outcomes or wins. Massive key/real-time entitlement remains unverified.
- The 136-name watchlist and JDZG stale/halt failure analysis, frozen historical baseline labels and denominator, and prospective 0/+1/+2/+3 **actual trading-session** paired-cohort evaluation are untouched. Include false positives, late/exhausted cases, squeezes, costs and all missingness before any claim of predictive edge or >=20% success.
