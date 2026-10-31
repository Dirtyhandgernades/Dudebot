# OBSIDIAN Research Engineering — October 31, 2026, 02:47 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday non-trading-day engineering only. No new IEX, SIP, halt-monitor, protected preclose, Morning Movers, After-Hours, Early Decision Board, or Rug Proof capture/marker. No trading, orders, credentials, main/production changes, policy relabeling, or watchlist changes.

## P0-1 — retain contradictory previous-session class and action-record identity claims

Research-only implementation commit `392f149a5557a2011f4195812d38d4b5d92eee66`, advanced with exact expected-head GitHub lease from `610fb655cb88a4a3ee6048249869572f8d4e8052`.

The separate corporate-action/issuer-identity shadow gate already censored any report whose previous issuer class differed from its current class, or whose action-record previous security ID differed from the source report. But when a rejected third source contradicted two agreeing reports, the complete conflict inventory did not explicitly identify the **previous-session issuer-class conflict** or **action-record previous-security-ID conflict**. Those matter because a 20% decline's reference close must correspond to the same underlying security and class.

In `backtest/obsidian_eod_action_identity_shadow.py`, each supplied report now retains these two scalar claims (including rejected rows), with grouped valid/rejected source indices and separate indices for missing or unparseable claims. New conflict flags are `CROSS_SOURCE_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT` and `CROSS_SOURCE_ACTION_PREVIOUS_SECURITY_ID_CLAIM_CONFLICT`. No rejected row is authenticated, promoted into scoring, or used to revise any historical label.

Three synthetic regressions cover rejected-third prior issuer-class contradiction, rejected-third action-record previous-ID contradiction, and missing prior claims that remain censored. GitHub Actions [run 41181713432](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41181713432) ran on the **exact implementation commit** and completed **SUCCESS**. Job `124480295182` shows all steps successful; downloaded hosted log reports **551 prospective tests and four ABC board tests passed**, including the new regressions. These are software-contract tests, **not** independent provider ownership, authentic official closes, or evidence of predictive performance.

## Cross-task and evidence status

Re-read the October 30 Rug Proof original intraday anchor and its 18:20 postclose audit, as well as the original protected October 30 preclose trigger; no overlapping or duplicate captures. Original 136-name watchlist, JDZG stale/halt analysis, frozen baseline labels and cohort denominators remain unchanged.

Read-only GitHub Actions artifact metadata rechecked:
- Protected Oct30 preclose run `41118123273`, artifact `13006897253`, SHA256 metadata `ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`, unexpired, Jan 28 2027 expiry.
- Maturity replay run `41140665058`, artifact `13018333034`, SHA256 metadata `956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc`, unexpired, Jan 28 2027 expiry.
- Independent monitor run `41122875006`, artifact `13010065001`, SHA256 metadata `f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`, unexpired, Jan 28 2027 expiry.

These are **metadata** checks; underlying ZIP bytes were not downloaded and rehashed in this checkpoint. Durable off-platform storage remains `BACKUP_UNVERIFIED`.

Original October 30 preclose cohort remains **8,510 securities**, **1,653 preliminary price-only weakness observations**, and **34,040 0/+1/+2/+3 issuer-session slots**. October 30 h0 is censored; November 2, 3 and 4 future trading-session horizons are not yet mature. **Zero authenticated official-close outcomes** from two genuinely independent provider organizations. The Massive key/realtime entitlement remains unproven. No verified 20%+ prediction success, false-positive rate, precision/recall, after-cost edge, SMG platform shortability, shares, fills, or profits.

**Next acceptance gate:** authenticated organization-level official regular-session closes and prior closes, with externally verified ownership/identity/corporate actions, timestamps, complete source-conflict inventory and calendar provenance. Missing outcomes remain censored. Do not tune on later-known cases or count duplicate issuer-days.
