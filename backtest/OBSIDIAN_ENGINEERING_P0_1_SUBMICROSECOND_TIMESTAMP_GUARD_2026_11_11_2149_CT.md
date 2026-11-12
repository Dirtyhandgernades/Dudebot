# OBSIDIAN P0-1 source-time precision checkpoint — 2026-11-11 21:49 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch `research/obsidian-early-rug-20261025` only. Frozen baseline labels and original denominators, 136 retained names, JDZG stale/halt failure analysis, and 0/+1/+2/+3 actual trading-session matched future cohorts remain untouched.

## Verified, isolated software fix

- Starting branch head: `621c67aa3585bb2779a96dcea787da884d2c917b`.
- Code and four synthetic regression tests committed with an expected-head GitHub lease as [`6fd2d76f987915cd3b02cd277cfc8565f171641b`](https://github.com/Dirtyhandgernades/Dudebot/commit/6fd2d76f987915cd3b02cd277cfc8565f171641b).
- Python `datetime.fromisoformat` silently truncates a 7+ digit fractional second, so `2026-10-28T20:00:00.0000001Z` can compare equal to an exact 20:00:00Z (16:00 ET) close. The offline EOD source-body parser now requires a strict aware ISO second-resolution timestamp with at most six fractional digits and explicit UTC offset/Z. Unsupported precision remains rejected and censored; no rounding to an exact official close.
- Tests cover submicrosecond **current close as-of**, **previous close as-of**, and **publication time** rejection, plus acceptance of a genuinely exact six-digit fractional UTC-offset close. Rejected as-of claims remain visible in the untrusted all-source conflict inventory, not promoted to authenticated outcomes.
- Hosted [prospective CI run 43150811285](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43150811285) completed **successfully** on the exact code/test commit. Its job logs show **685 prospective tests and 4 additional board tests passed**, including all four new regressions. Offline tests are not market evidence.

## Source/ownership and capture reconciliation

- Reviewed original [November 11 Rug Proof 18:20 CT postclose audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md), distinct 09:20/12:20/14:20/18:20 marker ownership, and branch markers. No anchor/SIP/early-board/morning/afterhours trigger was created or duplicated.
- [Protected November 11 preclose run 43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151) and [Rug Proof delayed SIP run 43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523) remain **queued, no artifacts**, as verified in this checkpoint. No retry, retroactive capture, or backfill.
- Nasdaq RSS remains source-limited; optional Massive quotes and real-time entitlement unverified. Neither IEX single-venue observations nor a finite halt RSS establishes two independent official regular-session closes or current SMG shortability.

## Unresolved P0-1 and evaluation gate

**BLOCKED/CENSORED:** independently authenticated official 16:00 ET regular-session closes from two genuinely independent provider organizations; complete source ownership/transport and conflicting-third-source inventory; issuer/class/security-ID continuity; actual exchange-session and corporate-action verification; SMG platform blocked-security/account permissions and shortability; forward 0/+1/+2/+3 actual-session outcomes. Preserve all false positives, late/exhausted cases, squeezes, costs, missingness, and untouched future cohorts. No 20% collapse prediction success, execution eligibility, fills, profit, or trading edge is established.

No main/production changes, credentials, orders, trading notifications, unauthorized access, or policy changes.
