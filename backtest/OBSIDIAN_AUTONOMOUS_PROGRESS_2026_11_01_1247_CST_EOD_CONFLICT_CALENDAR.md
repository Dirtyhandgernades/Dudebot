# OBSIDIAN autonomous engineering — November 1, 2026 12:47 CST calendar guard for all-source EOD conflict ledger

**RESEARCH_ONLY_NOT_AN_ORDER.** Scope: `Dirtyhandgernades/Dudebot`, `research/obsidian-early-rug-20261025` only. Sunday was not an open U.S. cash-equity trading session. No protected 12:47 INTRADAY IEX or 14:47 preclose marker was created; no Morning, After-Hours, Early Decision Board, Rug Proof 09:20/12:20/14:20/18:20 anchor, duplicate issuer/day, retry, backfill, credential, production, main, notification or trade change.

## Verified P0-1 improvement

The all-source EOD conflict inventory could previously return `STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING` for two matching self-attested vendor reports that referred to a skipped real trading day, a scheduled holiday/weekend, or a fabricated normal 16:00 ET session on the NYSE's published 13:00 ET early-close dates. The separate EOD source preflight already rejected these cases, but the complete conflict ledger did not apply the same static published-session screen. That inconsistency risked a misleading source-consistency diagnostic, **not an authenticated official-close outcome**.

Research-only change: reuse the preflight's static published 2026 NYSE cash-equity calendar and previous-session adjacency checks in `backtest/obsidian_eod_conflict_inventory.py`, plus a published early-close/claimed-flag mismatch check. Keep every supplied report indexed, preserve original input packet and calendar hashes, retain all rejected third-source price and identity conflicts, and censor when the claimed calendar conflicts with the published schedule. Static calendar evidence still does **not** prove an actual unscheduled closure, issuer halt, provider entitlement, official exchange closing auction, security identity, corporate action or legal vendor independence.

Implementation commit: [03617e8](https://github.com/Dirtyhandgernades/Dudebot/commit/03617e8ecf744fcfd111009d2a309cc9f55abb78). Six new offline regressions cover skipped trading sessions, holiday/weekend, published early close, previous early close, out-of-scope year, and valid normal/holiday-adjacent sessions. The existing original source-conflict inventory tests remain in the same suite.

**Hosted CI independently checked:** [GitHub Actions run 41338571723](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41338571723), exact implementation head `03617e8ecf744fcfd111009d2a309cc9f55abb78`, completed **SUCCESS**. Runner log: **584 prospective tests and four ABC-board tests passed** (588 offline tests total); no failed tests. No vendor-fetch workflow or authenticated market-data artifact was produced.

## Protected research source and artifact recheck

Read the original October 30 18:20 Rug Proof postclose audit and roadmap before the change. The October 30 8,510-issuer source cohort, 34,040 original 0/+1/+2/+3 trading-session slots, 1,653 price-only watches and 6,857 nonwatches, frozen historical baseline labels, separate 136-name monitor (127 in-cohort and nine off-universe), and JDZG stale-IEX/halt/SMG-shortability investigation are unchanged. No source packet, original decision timestamp, protected marker, historical denominator or trading workflow was altered.

Fresh GitHub run-artifact metadata queries confirmed **all seven protected October 30 artifacts present and unexpired**, with IDs 12985950392, 12995764777, 13006191628, 13006897253, 13008429628, 13010065001 and 13018333034. Each currently reports expiration on **January 28, 2027**. This checkpoint checked metadata only; the preceding checkpoint independently downloaded and SHA-256-verified all seven ZIP contents. A durable off-platform backup and restore remain **BACKUP_UNVERIFIED**.

## Remaining hard gates

**Zero** independently authenticated official regular-session close outcomes from two genuinely independent underlying provider organizations. Still missing: official close and previous-close source-event timestamps, ownership/transport proof, complete actual-session calendar/issuer-halt evidence, security ID and corporate-action continuity, full conflict receipts and verified external source entitlements. No evidence of live Massive realtime entitlement or SMG blocked-security/account approval. Historical labels remain frozen and missing outcomes censored; 20%+ prospective collapse accuracy, false-positive rates, early/exhausted catchability, costs, squeeze-adjusted profitability and executable SMG shortability are **not established**.

Next priority: authentic independent official-close evidence and approved durable off-platform storage/restore. No backfill or performance inference.
