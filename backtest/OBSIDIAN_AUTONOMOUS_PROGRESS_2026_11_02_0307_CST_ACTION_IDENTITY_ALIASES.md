# OBSIDIAN Research Engineering — 2026-11-02 overnight P0-1 action/identity alias integrity

**RESEARCH_ONLY_NOT_AN_ORDER.** Authorized research branch only. No main, production, credentials, account access, trades, notifications, or historical scoring changes. Current checkpoint was overnight before the regular U.S. equity session; no 12:47 CT INTRADAY IEX, 14:47 CT protected preclose, morning, after-hours, independent monitor, or Rug Proof marker was created, retried, or backfilled.

## Verified P0-1 software-integrity improvement

The corporate-action/security-identity shadow auditor previously compared raw `source_id` and `provider_organization` strings. In contrast, the existing complete-source conflict, receipt and EOD preflight gates use case-folded, collapsed-whitespace label keys. As a result, two receipts named `a` and `  A  ` could evade duplicate-source screening, while two organizations named `alpha` and `  ALPHA  ` could be counted as different providers. This discrepancy was verified directly in the pre-change source and test contract, not inferred from market data.

Implementation [`5005711c443ba8f9723b2c71608063773d0036b3`](https://github.com/Dirtyhandgernades/Dudebot/commit/5005711c443ba8f9723b2c71608063773d0036b3) reuses the same conservative comparison-key helper in `backtest/obsidian_eod_action_identity_shadow.py`, while preserving every raw source/provider label in the audit rows. Three new synthetic regressions verify case/whitespace duplicate receipts, aliased provider organizations on separate hosts, and collapsed internal whitespace. Invalid/missing labels remain censored. The helper does **not** authenticate actual legal provider ownership or the corporate-action evidence.

Hosted [prospective journal CI #41418259591](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41418259591) completed **SUCCESS** for implementation head `5005711c443ba8f9723b2c71608063773d0036b3`; runner logs show **627/627** prospective offline tests and **4/4** ABC-board tests passed. This is a structural research integrity test, not an authenticated provider run or verified predictive case.

## Coordination and protected evidence

Read the October 28 autonomous validation roadmap, current P0-1 source/action contracts and tests, prior November 2 engineering note, and the October 30 18:20 CT Rug Proof audit before editing. Original October 30 evidence remains separate issuer/day observations, not independent duplicate successes. Rechecked the original seven workflow-run artifact metadata records: `12985950392`, `12995764777`, `13006191628`, `13006897253`, `13008429628`, `13010065001`, `13018333034`; all reported `expired=false`, expected pinned SHA-256 metadata and expiry on January 28, 2027. ZIP contents were not downloaded/rehashed; approved off-platform restoration remains **BACKUP_UNVERIFIED**.

Frozen October 30 8,510-security cohort, 34,040 forward evaluation slots, 1,653 watch/6,857 nonwatch partition, 136-name retained watchlist, JDZG stale/halt/$3-floor failure analysis, original IEX labels, and all historical denominators remain untouched. November 2/3/4 are the actual +1/+2/+3 trading-session dates for the October 30 cohort, not overnight-matured outcomes.

## Remaining blockers

**Zero independently authenticated exchange-official regular-session closes from two genuinely independent underlying provider organizations.** No verified previous close, complete third-source conflicts, corporate-action/issuer identity, live exchange calendar, source receipt ownership or timestamp chain for admissible scoring. All missing outcomes remain **CENSORED**; verified 20%+ prediction accuracy, false-positive rate, cost/squeeze-adjusted profitability and actual SMG shortability remain **UNESTABLISHED**. Optional Massive credentials/real-time entitlement are not verified by this checkpoint. No share count, fill, order or trade authorization was created. Next P0-1 dependency is actual authenticated source evidence, not further inference from offline tests.
