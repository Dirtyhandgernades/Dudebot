# OBSIDIAN Research Engineering — October 31, 2026, 16:47 CDT

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday closed market: no original IEX intraday/preclose, Morning Movers, After-Hours, independent intraday monitor, or Rug Proof capture. No retries, backfills, duplicate issuer/day markers, orders, notifications, secrets, main or production changes.

## P0-1 provider-specific success envelope / quota protection

The generic HTTP-200 JSON classifier recognizes both `OK` and `ok`, but the Massive and Twelve Data provider contracts require distinct exact statuses. Previously a wrong-case response was rejected only downstream, allowing additional paid calls. The bounded budget now receives each provider's exact success status and stops immediately after the first mismatch, retaining censored fixed-denominator rows. Two new regression tests cover both directions and a full four-row fixed diagnostic cohort. No vendor call was made during this engineering change.

**Scope:** This is a vendor-diagnostic contract improvement only. Passing tests does not prove independent underlying exchange feeds, official completed regular-session or previous-session closes, legal security identity, corporate-action continuity, real-time entitlement, or model performance. Source authentication and full conflict inventory remain P0 blockers.

Original 8,510-issuer / 34,040 0/+1/+2/+3 actual-session slots, frozen denominator/baselines, 136-name watchlist and JDZG stale/halt investigation unchanged. October 30 h0 remains censored; November 2/3/4 are untouched future sessions. No forward verified cases, 20%+ success, SMG shortability, shares, fills or profits. Eventual comparisons must include false positives, squeezes, costs, late/exhausted signals and missingness.

Three protected October 30 artifact records were reviewed in the prior checkpoint; ZIP bytes and off-platform restore remain **BACKUP_UNVERIFIED**. Hosted CI must be independently checked after this commit; this note does not claim a pass.
