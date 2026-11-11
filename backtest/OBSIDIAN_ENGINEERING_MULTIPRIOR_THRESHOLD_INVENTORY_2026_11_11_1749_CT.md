# OBSIDIAN P0-1 multi-prior threshold inventory — 2026-11-11 17:49 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only; no market capture, orders, production, main, account permissions, credentials, or changes to frozen labels or denominators.

## Problem and isolated change

The existing all-source EOD preflight retained contradictory previous-close claims but its 20% event-boundary inventory only tested a threshold straddle when there was exactly one previous-close claim. Multiple distinct previous-close claims could move the threshold across a single current-close claim without the explicit threshold-ambiguity issue appearing. Other blocking issues still censored the record, but this obscured the complete source/conflict diagnosis.

The shadow preflight now tests the exact Decimal range of every parseable claimed current close against every parseable claimed previous-close 80% threshold, including rejected third-source claims. It adds `ALL_SUPPLIED_CLAIMS_STRADDLE_20PCT_THRESHOLD` only when both hit and non-hit classifications are possible. Claims remain explicitly untrusted; no provider is promoted to official evidence. Three new synthetic tests cover differing prior claims with identical closes, a wrong-security third source, and a non-straddling control.

## External evidence and limitations

The 2026-11-11 14:47 CT protected IEX workflow 43098152151 and separate 14:20 delayed SIP workflow 43095851523 were still **queued** in the latest read; neither was retried. The 15:22 CT after-hours independent source workflow 43102970599 completed successfully, but a successful collection job is not proof of two independently authenticated official regular-session closes. November 11 Rug Proof anchor 43077205260 is a distinct capture, not a second issuer/day outcome.

P0-1 remains **BLOCKED**: independent official regular-session close receipts from two genuinely independent provider organizations, complete legal source ownership, actual exchange session, security identity, corporate actions, and SMG short permissions are not established. Massive real-time entitlement is not verified. All 0/+1/+2/+3 actual-session forward outcomes remain censored until independently verified. Preserve 136-name watchlist, JDZG stale/halt analysis, false positives, late/exhausted cases, squeezes, costs, missingness, original baseline and matched untouched future cohorts. No 20% success or profitable trade claim.

This note documents a proposed source-integrity regression change; hosted CI must be checked on the exact resulting commit before calling the software fix verified.
