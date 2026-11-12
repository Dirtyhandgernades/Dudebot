# OBSIDIAN P0-1 preflight timestamp precision — 2026-11-11 22:48 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Only `research/obsidian-early-rug-20261025`. This is a software-validation milestone, not verified market data or a trading signal.

## Verified change
- Starting head: `3f11434f5c574ea9688928107a37e94485129c62`. Code/test commit: [`d986981c3e473796789831b5e73cbbb11c00552b`](https://github.com/Dirtyhandgernades/Dudebot/commit/d986981c3e473796789831b5e73cbbb11c00552b), advanced with expected-head GitHub lease.
- The independent, caller-supplied `obsidian_eod_source_preflight.py` previously used `datetime.fromisoformat` directly. Python silently truncates seventh-plus fractional digits, so a purported `16:00:00.0000001` as-of could compare equal to an exact 16:00 ET regular close.
- The preflight now requires an explicit aware ISO-8601 timestamp with seconds and at most six fractional digits (Z or ±HH:MM). It rejects unsupported precision in current/previous close as-of, publication and collection times, matching the separate byte-binding shadow's existing policy.
- Five new synthetic tests cover each invalid timestamp path plus legitimate six-digit offset-equivalent closes. No historical observations, original watchlist, frozen labels or scoring rules were modified.
- [Hosted prospective CI 43157224610](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43157224610) succeeded on the exact code/test commit: **690 prospective tests plus 4 board tests passed**. [Hosted EOD source-contract CI 43157224583](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43157224583) also succeeded: **54 tests passed**. Verified from GitHub job logs, not merely inferred from workflow status.

## Coordination and evidence limits
- Read the [original 18:20 Rug Proof audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md) and the branch's distinct anchor/trigger markers. This run was outside authorized 12:47/14:47 market-capture windows. No new IEX, SIP, independent-source or protected preclose marker was created.
- [Nov 11 protected preclose 43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151), [Rug Proof delayed SIP 43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523), and [independent monitor 43095840045](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095840045) remain queued, with **zero artifacts** as checked in this run. No retry or backfill.
- No authenticated two-organization official regular-session closes, independent ownership/transport proof, full third-source reconciliation, actual session/halt calendar, corporate-action/security-identity continuity or Massive entitlement were established. SMG public and account-level shortability remain unverified; Alpaca borrow is not SMG approval. Keep outcomes **CENSORED**, not failures or successes.
- Preserve the 136-name watchlist and JDZG stale/halt failure analysis, frozen historical denominators and 0/+1/+2/+3 **actual trading-session** future-cohort evaluation, including false positives, late/exhausted observations, squeezes, costs and missingness. No 20%+ prediction success, fills, profits, executable shorts, or predictive edge are claimed.

No main/production changes, credentials, unauthorized account access, orders, notifications, or silent policy changes.
