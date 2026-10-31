# OBSIDIAN Research Engineering — October 31, 2026, 05:47 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday non-trading day; engineering-only checkpoint. No new IEX, SIP, protected preclose, independent-monitor, Morning Movers, After-Hours, Early Decision Board, or Rug Proof marker/capture. No trade, credentials, production/main edits, policy changes, baseline relabeling, or watchlist changes.

## P0-1: Preserve contradictory session and corporate-action window claims

Reviewed the [October 28 validation roadmap](OBSIDIAN_AUTONOMOUS_VALIDATION_ROADMAP_2026_10_28.md), the previous [04:47 Engineering report](OBSIDIAN_AUTONOMOUS_PROGRESS_2026_10_31_0447_CT.md), and the original [October 30 Rug Proof postclose audit](OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_10_30_1820_CT.md) before editing. The source-byte binding shadow already rejected bodies with incorrect current/previous session dates or action coverage windows, but its **cross-source conflict inventory** did not explicitly preserve those disagreements. A rejected third provider's contradictory calendar or action-coverage claim could thus be absent from the consolidated conflict list even though its row was censored.

Research-only implementation [`27db0bd1ed21e4f433f496505a6b0c0e1093aab0`](https://github.com/Dirtyhandgernades/Dudebot/commit/27db0bd1ed21e4f433f496505a6b0c0e1093aab0) adds four parsed original-body claims to the complete cross-source inventory: `session_date`, `previous_session_date`, `corporate_action.coverage_start`, and `corporate_action.coverage_end`. Disagreements produce separate `PARSED_BODY_*_CLAIM_CONFLICT` issues, including for rejected third-party bodies. This is a complete **claim disagreement inventory**, not authenticated exchange-calendar or corporate-action evidence. The existing row-level rejection remains in force and the aggregate status is `BLOCKED_CENSORED` whenever conflicting claims exist.

Five synthetic regression tests cover current/previous session disagreement, rejected third-source action-window start disagreement, action-window end disagreement, and an agreeing-source control. Hosted [GitHub Actions run 41194505188](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41194505188) completed **SUCCESS** on the exact implementation SHA: job `124517841040` confirms **563 prospective tests plus four ABC decision-board tests passed**; all five new cases passed. The implementation used an expected-head GitHub lease from `29a7bb04cf3952f8e96f67e09239de497dee454f`. No changes to frozen capture/forward-study source code or historical rows.

## Original prospective evidence, deduplication, and retention

Rechecked GitHub artifact metadata, **not underlying ZIP payload bytes**:

- October 30 protected 14:47 CT preclose: run `41118123273`, artifact `13006897253`, metadata SHA256 `ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`, unexpired until `2027-01-28T19:47:32Z`.
- October 30 maturity replay: run `41140665058`, artifact `13018333034`, metadata SHA256 `956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc`, unexpired until `2027-01-28T22:49:48Z`.
- October 30 independent source monitor: run `41122875006`, artifact `13010065001`, metadata SHA256 `f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`, unexpired until `2027-01-28T20:24:01Z`.

Original October 30 prospective cohort remains **8,510 securities**, **1,653 preliminary IEX price-only weakness observations**, and **34,040 original issuer × 0/+1/+2/+3 actual trading-session slots**. October 30 h0 remains `CENSORED_MISSING`; November 2, 3 and 4 (+1/+2/+3) were not yet mature on Saturday October 31. Frozen original baseline labels, cohort denominator, 136-name retained watchlist, and JDZG stale/halt failure analysis remain unchanged. The Rug Proof task owns its original 09:20/12:20/14:20/18:20 CT anchors; no issuer/day or capture was duplicated.

## Unresolved acceptance gate

**Independently authenticated official regular-session closes: zero.** Neither a pair of genuinely independent provider organizations' official current/prior closes nor matching security identity, corporate-action adjustment basis, authoritative session calendar, verified transport/ownership, complete third-source conflicts and publication/retrieval timestamps has been established. Massive credentials or real-time entitlement are not proven; SMG platform borrow/blocked-table/account permissions are not proven. The offline shadow **always** returns `official_close_verified=False`, `eligible_for_frozen_scoring=False`, and censored outcome. No 20%+ prospective success, false-positive rate, prediction edge, trade size/fill, or profitability is established. Missingness stays censored, not a loss or a win. ZIP payloads were not downloaded/rehashed and durable off-platform archive remains `BACKUP_UNVERIFIED`.

**Next:** obtain verifiable independent official close/current-prior security-level provenance without changing frozen labels or post-hoc tuning; then mature matched untouched cohorts on actual sessions only. Maintain research-only boundaries and distinct scheduled-task ownership.
