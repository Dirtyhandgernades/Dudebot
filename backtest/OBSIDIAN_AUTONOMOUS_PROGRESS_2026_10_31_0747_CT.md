# OBSIDIAN Research Engineering — October 31, 2026, 07:47 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday non-trading day. Read the Oct 28 validation roadmap, previous 06:47 engineering note, and Oct 30 Rug Proof 18:20 postclose audit before changing research code. Refreshed the research branch head and GitHub CI, confirmed existing Oct 30 capture/Rug Proof ownership, and created **no** original IEX/SIP, preclose, independent-monitor, Morning Movers, After-Hours, Early Decision Board or Rug Proof marker. No trades, main/production changes, credentials, trading alerts, frozen baselines, 136-name watchlist, JDZG analysis, or original cohort denominators changed.

## P0-1 material source chronology fix

Found a concrete fail-open timestamp ordering issue in `backtest/obsidian_eod_source_body_binding_shadow.py`: the supplied raw JSON body could claim an embedded corporate-action `checked_at` *later* than that same body's `observed_at` (its source publication claim), while both were before receipt retrieval. The old gate accepted this anachronistic embedded evidence as structurally consistent. A later independent action check cannot be backdated into an earlier-published source body; it needs its own authenticated receipt.

Research-only commit [`1b7855c1a48ebfc74d2e3a22ddfce18116c131fc`](https://github.com/Dirtyhandgernades/Dudebot/commit/1b7855c1a48ebfc74d2e3a22ddfce18116c131fc) adds `EMBEDDED_ACTION_CHECK_POSTDATES_SOURCE_PUBLICATION`, censors the offending source row, and retains the original receipt/claim indices. It does not authenticate a source or change scoring. Two synthetic regression tests cover the post-publication-but-pre-retrieval invalid case and the pre-publication control.

Initial hosted [run 41202488473](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41202488473) **FAILED one synthetic early-close fixture**: its previously accepted action check also postdated its source publication claim. The failure was not suppressed. Follow-up commit [`bd97401f8b270f25d1a94eb855ddabc7e7a27562`](https://github.com/Dirtyhandgernades/Dudebot/commit/bd97401f8b270f25d1a94eb855ddabc7e7a27562) corrects only that synthetic fixture's action-check chronology. Hosted [run 41202560391](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41202560391) on the exact repair SHA completed **SUCCESS**; decoded job `124541082365` logs confirm **568 prospective tests and four decision-board tests passed**, including both new tests. All branch changes used expected-head GitHub leases and did not touch frozen capture code.

## Original evidence and unresolved gate

Rechecked metadata only, **not ZIP payload bytes**:
- Oct 30 protected preclose: run `41118123273`, artifact `13006897253`, SHA256 `ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`, expires `2027-01-28T19:47:32Z`.
- Oct 30 maturity replay: run `41140665058`, artifact `13018333034`, SHA256 `956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc`, expires `2027-01-28T22:49:48Z`.
- Oct 30 independent monitor: run `41122875006`, artifact `13010065001`, SHA256 `f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`, expires `2027-01-28T20:24:01Z`.

Preserved Oct 30 **8,510 original securities**, **1,653 preliminary IEX price-only watches**, and **34,040 issuer×0/+1/+2/+3 actual-session slots**. Oct 30 h0 remains `CENSORED_MISSING`; Nov 2/3/4 forward sessions are not yet mature on Saturday Oct 31. No same-issuer/day duplicate, false-positive, late/exhausted, squeeze, cost, or profitability outcome is inferred from missing evidence.

**Independently authenticated two-organization official regular-session closes: 0.** Source ownership/transport, current and previous official closes, issuer/class and corporate-action parity, calendar and publication/receipt chronology, and complete independently authenticated third-source conflicts remain unproven. Massive live entitlement, actual SMG platform blocked-security/account short permission, and durable off-platform ZIP backup remain unverified. Synthetic passing tests are **not** 20%+ prediction successes, SMG approval, fills, shares, or profits.

**Next acceptance gate:** obtain two genuinely independent source-owned official closing-price receipts with full provenance, keep missing/conflicting cases censored, and evaluate only matched untouched future cohorts after real trading sessions mature.
