# OBSIDIAN Research Engineering — 2026-11-02 03:48 CST, Nasdaq RSS resumption alias integrity

**RESEARCH_ONLY_NOT_AN_ORDER.** Authorized `research/obsidian-early-rug-20261025` branch only. This overnight checkpoint is outside the authorized 12:47 CT intraday and 14:45–14:58 CT protected preclose windows. No IEX, Morning, After-Hours, Rug Proof, independent monitor, or preclose trigger/marker was created or backfilled; no source-network market requests, trading accounts, orders, credentials, main, production or notifications were changed.

## P0-1 defect and tested correction

The Nasdaq Trader RSS parser already rejected exact duplicate XML fields but treated `ResumptionDate` versus `ResumeDate`, and `TradeResumptionTime` versus `ResumptionTradeTime` or `ResumeTradeTime`, as different keys. Those names represent the same source claim. If two aliases appeared in one RSS item, the prior `or` selection could silently ignore contradictory resumption timestamps. That is not reliable halt-clearance evidence.

Research-only implementation commit [`d79ee035e2207809347ac5d4e7ee702541c7442b`](https://github.com/Dirtyhandgernades/Dudebot/commit/d79ee035e2207809347ac5d4e7ee702541c7442b) canonicalizes only these explicitly supported semantic aliases before duplicate-field detection. Coexisting aliases fail closed as `HALT_RSS_DUPLICATE_FIELD`; a single alternate alias remains parseable. Original source feed bytes remain fingerprinted by the collector when present, and a rejected feed cannot establish live trading clearance or SMG eligibility.

Three new offline regression tests cover conflicting resumption-date aliases, conflicting trade-resumption-time aliases with whole-source censoring, and correctly parsed single alternate field names. Hosted [independent halt/SMG CI #41423806392](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41423806392) completed **SUCCESS**, **49/49 tests passed**. Hosted [prospective journal CI #41423806398](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41423806398) completed **SUCCESS**, **630/630 prospective tests and 4/4 ABC-board tests passed**. Runner logs and job steps were inspected. Offline tests prove parser behavior, not a live Nasdaq session or independent market-data entitlement.

## Coordination and protected evidence

Re-read the October 28 validation roadmap, October 30 Rug Proof postclose audit, original intraday verification, and previous engineering report. Requeried the seven original October 30 workflow-run artifact lists. IDs `12985950392`, `12995764777`, `13006191628`, `13006897253`, `13008429628`, `13010065001`, and `13018333034` each reported `expired=false`, the previously pinned SHA-256 metadata digest and January 28, 2027 expiration. This pass did not download or rehash ZIP bytes or restore a durable off-platform copy: **BACKUP_UNVERIFIED**.

Original 8,510-security October 30 cohort, 34,040 issuer×0/+1/+2/+3 actual trading-session slots, 1,653 watch/6,857 nonwatch split, 136-name retained watchlist, JDZG stale/halt/$3 floor investigation, original labels, baseline denominator and evidence anchors remain untouched. November 2, 3, and 4 are the October 30 +1/+2/+3 session dates; no prospective outcome has been promoted into an authenticated close.

## Remaining external evidence gap

**Zero independently authenticated exchange-official regular-session closing-price outcomes from two genuinely independent underlying provider organizations.** Previous-session close proof, issuer/security identity, corporate actions, complete source/conflict ledger, timestamp provenance, and verified live session calendar are still missing. Optional Massive API key/real-time entitlement is not established by these offline runs. All missing outcomes remain **CENSORED**, not false negatives or hits. Verified 20%+ collapse accuracy, precision/recall, false-positive rates, costs/squeezes, SMG shortability, fills and profits remain **UNESTABLISHED**. The next material dependency is real independent official-close evidence and an approved durable artifact backup/restore.
