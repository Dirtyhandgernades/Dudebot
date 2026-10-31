# OBSIDIAN Research Engineering — October 31, 2026, 12:44 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday, no U.S. regular equity trading session. No original IEX intraday, preclose, morning, afterhours, independent-monitor, delayed-SIP, or Rug Proof anchor/marker created. Refreshed the authorized research branch, October 28 validation roadmap, prior 11:43 engineering note, October 30 18:20 Rug Proof audit, recent CI, and the protected artifact metadata before work. No duplicate issuer/day evidence.

## P0-1: preserve authoritative access/quota cause in censored vendor observations

In `backtest/obsidian_two_provider_close_reconciliation.py`, the previous checkpoint correctly stopped further paid requests on HTTP 401/403/429 even with malformed or oversized bodies, but `category()` still prioritized `RESPONSE_BODY_TOO_LARGE` or other body errors over the authoritative HTTP status. The resulting per-provider observation could misleadingly report only a response-size problem, obscuring the **actual authentication, entitlement, or rate-limit blocker**.

Implemented research-only correction in [commit 8ae1f8936e8f0de66bb75797f9729307a8da54fa](https://github.com/Dirtyhandgernades/Dudebot/commit/8ae1f8936e8f0de66bb75797f9729307a8da54fa): HTTP 401 is `AUTHENTICATION`, 403 is `ENTITLEMENT_OR_ACCESS`, and 429 is `RATE_LIMIT` even when the body is oversized/malformed. `response_body_truncated` remains independently recorded, incomplete bodies still have no SHA-256, no price is accepted, and the existing one-request quota stop remains in force. Added one table-driven regression test covering all three denial statuses and both body failure forms, including normalized censorship and stopped request budget.

**Hosted CI verified:** [GitHub Actions run 41225916403](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41225916403) on the exact implementation SHA completed SUCCESS. Job `124609908645` logs report **32 offline tests passed** (the two-provider reconciliation and ABC board suites). The vendor-fetch step was SKIPPED, and artifact upload reported **no file found**, so no provider entitlement, live independent close, or market outcome was established. The broader prospective CI suite was not run against this exact SHA and is not claimed.

## Preserved original evidence and unresolved blockers

Rechecked protected Oct 30 GitHub artifact metadata: preclose run `41118123273` / artifact `13006897253` (expires 2027-01-28T19:47:32Z); maturity replay run `41140665058` / artifact `13018333034` (expires 2027-01-28T22:49:48Z); independent monitor run `41122875006` / artifact `13010065001` (expires 2027-01-28T20:24:01Z). All report `expired=false`. ZIP bytes were not downloaded or rehashed here; off-platform durable backup remains **BACKUP_UNVERIFIED**.

The frozen 8,510-issuer denominator, 34,040 issuer×horizon 0/+1/+2/+3 trading-session slots, 136-name watchlist, JDZG stale/halt analysis, historical labels, source timestamps, original future cohorts, and other task boundaries are unchanged. Oct 30 h0 official outcomes remain censored; Nov 2/3/4 are future actual trading sessions. No future evidence was promoted to historical knowledge.

**P0-1 external blocker unchanged:** no independently authenticated official completed regular-session closes and previous closes from two genuinely independent provider organizations with validated provider ownership, security identity, corporate actions, exact session calendar, chronology and full third-source conflict inventory. Massive live entitlement, actual SMG blocked-symbol/account permission and real-time independent halt clearance remain unverified. No 20%+ collapse prediction success, false-positive rate, SMG executable short, fill, shares, or after-cost profitability is established.

No main/production changes, secrets, paid live requests, market orders, notifications, policy changes, retry/backfill, or duplicate capture. Next priority remains genuine independent official-close provenance and a durable verified backup destination, not another synthetic claim of model accuracy.
