# OBSIDIAN P0-1 source-body published-session chain guard — 2026-11-12 02:50 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch `research/obsidian-early-rug-20261025` only. Synthetic offline validation, not a live provider retrieval, actual exchange-calendar authentication, official close, SMG approval, or prediction result.

## Verified change

- Starting branch head `f318aa8ea76cfb09477e2cbe05c27eb6c0a77cd8`; expected-head fast-forward code/test commit [`87ff6a8bde501d3dad4ad1255422dda08c3a001c`](https://github.com/Dirtyhandgernades/Dudebot/commit/87ff6a8bde501d3dad4ad1255422dda08c3a001c).
- `backtest/obsidian_eod_source_body_binding_shadow.py` previously allowed two internally consistent, byte-matching JSON source claims to return `BODY_CONSISTENT_EXTERNAL_AUTH_PENDING` for a published closed session or skipped previous trading day. Its receipt layer validates caller-supplied timestamps and byte digests, not the published session calendar. This could obscure an invalid 0/+1/+2/+3 session chain in manual P0-1 review.
- The body-binding shadow now applies the existing shared `_published_2026_calendar_issues` screen and censors closed/weekend/holiday sessions, skipped previous trading days, published early-close sessions and out-of-scope dates. Explicit 13:00 ET current or previous close claims also require a separate registered session contract even when caller-supplied receipts match. The already-existing early-close fixture was explicitly updated to expect `BLOCKED_CENSORED` rather than a structurally consistent status. This is a stricter research-only source acceptance gate, not a change to frozen baseline labels or scoring.
- Three new synthetic regression tests cover two perfectly matching provider-byte receipts on Thanksgiving, a skipped previous cash-equity trading day, and caller-declared 13:00 ET clocks on ordinary regular sessions. All original row/byte indices remain retained, and even structurally consistent receipts are never authenticated.
- [Hosted prospective CI run 43186485934](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43186485934) completed **successfully on the exact code commit**, with job logs showing **711 prospective tests and 4 board tests passed**. No test workflow artifact was published.

## Coordination and immutable boundaries

- Reviewed [November 11 Rug Proof 18:20 CT audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md), existing 09:20/12:20 anchors, 14:20 board/SIP markers and the latest research branch CI. November 11 protected preclose and delayed SIP had no authenticated artifacts in the original audit; neither was retried or backfilled.
- This checkpoint was outside the authorized 12:47 CT IEX intraday and 14:45–14:58 CT protected preclose windows. No IEX, Morning Movers, After-Hours, Early Decision Board, Rug Proof, or independent-monitor trigger was created. No main, production, credentials, orders, notifications or account access.

## Unresolved external P0-1 and forward evaluation

- The 2026 calendar screen is **static published schedule logic**, not proof of actual exchange operation or issuer-specific halt status. Two genuinely independent organization-level, independently authenticated official regular-session close and previous-close receipts with complete third-source conflict, security-ID/class, corporate-action, timestamps and halt history are **unavailable**. Massive key/real-time entitlement and actual SMG blocked-security/account shortability are unverified. Alpaca borrow is not SMG permission.
- The original **136-name** watchlist, JDZG stale/halt investigation, frozen baseline labels/denominator, and prospective 0/+1/+2/+3 **actual trading-session** matched-cohort requirements remain unchanged. False positives, late/exhausted cases, squeezes, costs and missingness must remain counted. Unauthenticated outcomes are **CENSORED**, not wins, failures, 20% predictions or trading performance.
