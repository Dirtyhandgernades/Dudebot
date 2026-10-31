# OBSIDIAN Research Engineering — October 31, 2026, 09:47 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday non-trading day. Read the October 28 validation roadmap, October 31 08:47 engineering progress, and October 30 18:20 Rug Proof postclose audit. Verified the original protected preclose, maturity replay and independent monitor artifact metadata; all remain present and unexpired. No Saturday original IEX/SIP, preclose, Morning Movers, After-Hours, Early Decision Board, independent-monitor or Rug Proof capture marker was created. No main, production, credentials, notifications, frozen historical labels, 136-name watchlist, JDZG investigation, orders, shares or fills changed.

## P0-2 historical as-of source-evidence leakage — fixed and hosted-tested

The research-only preclose maturity ledger's `_audit_preclose` audits all caller-supplied future outcome rows. Before this correction, the public per-horizon `source_evidence` field exposed that internal structural verdict even when the horizon's close had not occurred, or when a supplied source receipt was later than the report's historical as-of. The outcome category already remained `NOT_YET_MATURE` or `CENSORED_BLOCKED`, but the accompanying evidence field could leak future information into a retrospective inventory.

Implementation commit [`228ea2624cf00f98ba3f196a9863afc166d1ee65`](https://github.com/Dirtyhandgernades/Dudebot/commit/228ea2624cf00f98ba3f196a9863afc166d1ee65) now publishes `NOT_YET_OBSERVABLE` before the actual exchange close and `SOURCE_NOT_OBSERVABLE_AT_REPORT_AS_OF` for a postclose horizon whose receipt was obtained later than the report as-of. Structurally rejected sources actually observable by the report as-of retain their original censor reason. This changes only the derived research-only maturity ledger, not original captures, original statuses, frozen denominator or authenticated outcome logic.

Added three synthetic regressions: future session evidence is masked, later-retrieved same-day evidence is masked, and observable structurally rejected evidence remains available for auditing. Hosted [GitHub Actions run 41211679761](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41211679761) on the exact implementation SHA completed **SUCCESS**; decoded job `124567811583` logs show **573 prospective tests** and **four decision-board tests** passing. The implementation used an expected-head ref lease. Passing tests prove only this offline as-of contract; no provider data or official close was authenticated.

## Protected evidence recheck (GitHub artifact metadata only)

- October 30 protected preclose run `41118123273`, artifact `13006897253`, SHA256 `ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`, `expired=false`, expiry `2027-01-28T19:47:32Z`.
- October 30 maturity replay run `41140665058`, artifact `13018333034`, SHA256 `956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc`, `expired=false`, expiry `2027-01-28T22:49:48Z`.
- October 30 independent monitor run `41122875006`, artifact `13010065001`, SHA256 `f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`, `expired=false`, expiry `2027-01-28T20:24:01Z`.

Underlying ZIP bytes were **not** downloaded or independently rehashed, and off-platform durable backup remains **BACKUP_UNVERIFIED**. These artifact digests are GitHub-reported metadata, not independent source authentication.

## Frozen denominator and unresolved gates

Original October 30 protected cohort remains **8,510 securities**, **1,653 preliminary price-only watches**, **34,040** original issuer×horizon slots. October 30 h0 is `CENSORED_MISSING`; November 2/3/4 +1/+2/+3 sessions have not yet occurred. Original 136-name watchlist and JDZG stale/halt failure analysis remain preserved. No confirmed 20% collapse, false positive, late/exhausted outcome, squeeze, costs, SMG platform shortability, execution or profitability is inferred.

**Primary P0-1 external blocker remains:** zero independently authenticated exchange-official regular-session closing-price outcomes from two genuinely independent provider organizations, including previous-session closes, source ownership/transport, security/class/corporate-action equivalence, publication chronology and complete third-source conflict coverage. Massive real-time entitlement and actual SMG blocked-security/account permissions remain unverified. All missing/conflicting outcomes remain censored. Next gate is live provider-owned official-close receipts and later mature untouched cohorts; never declare prediction accuracy from synthetic tests.
