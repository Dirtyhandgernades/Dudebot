# OBSIDIAN P0-1 action/source timestamp claim inventory — November 12, 2026, 07:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research-only, offline synthetic validation on `research/obsidian-early-rug-20261025`. No official closing prices, market-data entitlements, trading instructions, fills, or platform short permissions were acquired.

## Verified engineering change

- Starting branch head: `ceb51fa2c4f64c32eee3ce81c17a6d97e295f32d`, after the Morning Movers OPRX guidance-cut note; original roadmap and the November 11 Rug Proof postclose audit were reviewed before editing.
- [Code/test commit](https://github.com/Dirtyhandgernades/Dudebot/commit/601a32f7d23acc64f3f28454bcc0959097f0143c): `601a32f7d23acc64f3f28454bcc0959097f0143c`, written with expected-head lease.
- The standalone `obsidian_eod_action_identity_shadow.py` audit now inventories **every** supplied provider's action `checked_at` and price-source `observed_at` claims, including rejected third-party reports, grouped by exact canonical UTC instant with valid/rejected source indices. Malformed, absent, and unsupported submicrosecond timestamp claims appear in separate unparseable-source-index lists rather than being silently rounded or promoted.
- Provider observation and corporate-action checking times may legitimately differ. The audit does **not** falsely require equal times across organizations or convert a structurally valid receipt into authenticated evidence.
- Five synthetic regression tests cover equivalent timezone offsets, rejected third-source clocks, valid distinct observations, submicrosecond censorship, and missing/malformed timestamps.
- [Hosted CI run 43230877253](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43230877253) passed on the **exact code commit**, with **733 prospective offline tests and 4 board tests** successful, verified in the hosted job logs. CI emitted no evidence artifact; tests establish software behavior only.

## Cross-task capture ownership

- Original [November 11 Rug Proof postclose audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md) retains the authenticated anchor identifiers and missingness.
- Rechecked November 11 protected preclose [43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151), Rug Proof delayed SIP [43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523), and independent intraday monitor [43095840045](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095840045): all remained **queued**, with zero artifacts at this checkpoint. No late retry, backfill, or duplicate issuer/day capture.
- 07:47 CT is outside the existing authorized 12:47 CT intraday IEX gate and 14:45–14:58 CT protected preclose gate. No Morning Movers, After-Hours, Early Decision Board, or Rug Proof markers were created.

## Remaining P0-1 proof gaps

**BLOCKED/CENSORED.** No two independently authenticated provider-organization official regular-session closes with verified current/previous session prices, complete third-source conflict provenance, external security identity/corporate-action reconciliation, and actual exchange calendar/halts were established. Nasdaq Trader RSS is finite halt attention only; optional Massive quote key and real-time entitlement remain unproven. Actual SMG blocked-symbol/security-table/account permissions and shortability are unverified; Alpaca borrow is not SMG approval.

Preserve the original 136-name watchlist, JDZG stale/halt failure analysis, frozen raw baseline/denominator, and 0/+1/+2/+3 **actual trading-session** matched untouched future cohorts. Count false positives, exhausted/late signals, squeezes, costs, and missingness. No >=20% predictive-success claim or trade/P&L claim. No main, production, credentials, notifications, or order changes.
