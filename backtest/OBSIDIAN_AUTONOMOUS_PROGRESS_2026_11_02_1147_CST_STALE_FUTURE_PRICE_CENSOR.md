# OBSIDIAN Research Engineering — November 2, 2026, 11:47 CST

**RESEARCH_ONLY_NOT_AN_ORDER.** Scope: `research/obsidian-early-rug-20261025` only. No protected capture/marker, main or production modification, credentials, account access, orders, alerts, or trade notifications.

## P0-1 independent-quote freshness containment

The optional Massive snapshot parser previously retained a non-null `price` for `DELAYED_OR_STALE_PROVIDER_PRINT` and `FUTURE_DATED_PROVIDER_PRINT`. A downstream reader could use that price without inspecting the status, falsely treating stale or future-dated evidence as a current quote. The research-only parser now censors the usable price for both conditions, while preserving the observed timestamp, age and explicit freshness status. A fresh (at most 60 seconds old, nonfuture) diagnostic trade still exposes its price, but remains explicitly **entitlement unverified, not an official close, and not SMG shortability proof**.

Added regression tests for stale, future-dated and fresh diagnostic prices. This is a defensive source-evidence change, not a new provider entitlement or prediction result.

## Coordination and proof limits

Read the October 28 validation roadmap, November 2 10:53 engineering note and November 2 missed 09:20 Rug Proof record. Verified the November 2 09:12 discovery and independent-monitor workflow artifact metadata (IDs 13153818511, 13154712094; present and unexpired until January 31, 2027) and the October 30 Rug Proof intraday artifact (12995764777; present and unexpired until January 28, 2027). No ZIP content rehash or off-platform durable backup was performed. The missed November 2 morning Rug Proof anchor is not substituted or backfilled. This checkpoint was outside the 12:47 intraday and 14:45–14:58 protected preclose windows.

The frozen 8,510-security cohort, 34,040 0/+1/+2/+3 evaluation slots, 136-name watchlist, JDZG stale/halt analysis, historical baselines and untouched future cohort requirements are unchanged. No issuer/day duplicate is introduced.

## Acceptance remains blocked

No two independently authenticated exchange-official regular-session closes with matching previous close, source ownership, security identity, corporate-action parity, session calendar, timestamps and conflict inventory have been collected. Massive entitlement and SMG account authorization remain unverified. Missing forward outcomes stay censored; 20%+ prediction success, false-positive rates, shortability, fills and profitability are not established. Implementation commit `50a93cb7af65970c4407f2f18a73a3e5ac879109`. Hosted CI independently checked after the implementation:
- [Independent halt/SMG tests — run 41494701562](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41494701562): completed **SUCCESS**, runner logs **53/53 tests passed**, including the three freshness regression assertions.
- [Prospective journal and capture tests — run 41494701560](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41494701560): completed **SUCCESS**, runner logs **638/638 prospective tests passed** and **4/4 ABC-board tests passed**.
These offline tests do not establish live Massive entitlement, authenticated official closes or predictive performance.
