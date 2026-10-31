# OBSIDIAN Research Engineering — October 31, 2026, 06:47 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday, no authorized market-session capture window. No IEX/SIP, protected preclose, independent-monitor, Morning Movers, After-Hours, Early Decision Board, or Rug Proof marker created. No orders, trading notifications, credentials, main/production changes, baseline edits, watchlist changes, or historical relabeling.

## P0-1 material correction: prior-session issuer class must agree with corporate-action evidence

Read the October 28 [validation roadmap](OBSIDIAN_AUTONOMOUS_VALIDATION_ROADMAP_2026_10_28.md), prior [05:47 Engineering checkpoint](OBSIDIAN_AUTONOMOUS_PROGRESS_2026_10_31_0547_CT.md), and original [October 30 Rug Proof postclose audit](OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_10_30_1820_CT.md) before writing. Refreshed branch head `71920f2b28ce02f74a158684a47eff6d80a77b2a` and latest hosted research CI. Existing task markers are separately owned and were not duplicated.

Found a concrete fail-open **structural** identity gap in `backtest/obsidian_eod_action_identity_shadow.py`: a provider's corporate-action evidence could omit `previous_issuer_class` or claim a different prior-session class while the top-level report claimed a stable class, yet the action record could still be structurally accepted. This could hide a previous-session common-share/ADR mismatch relevant to the prior-close denominator.

Research-only implementation [`dfa34a8000c839fc97983ea5571ffdb1f181073e`](https://github.com/Dirtyhandgernades/Dudebot/commit/dfa34a8000c839fc97983ea5571ffdb1f181073e) now requires the action record's explicit previous-session issuer class to match the report's previous class. It separately indexes **all** supplied action previous-class claims (including rejected third-party rows), reports `CROSS_SOURCE_ACTION_PREVIOUS_ISSUER_CLASS_CLAIM_CONFLICT`, and tracks missing/unparseable action prior-class claims by original source index. No evidence is promoted to independently authenticated official-close status.

Three new synthetic regression tests cover absent prior action class, a contradictory rejected third-party action class with agreeing top-level identity, and an agreeing-source control. Hosted [GitHub Actions run 41198867410](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41198867410) completed **SUCCESS** on exact implementation SHA, job `124530491494`; decoded runner logs confirm **566 prospective tests plus four decision-board tests passed**. Commit touched only the action identity shadow and its regression tests. It was applied using an expected-head GitHub ref lease, not a force push.

## Immutable evidence and outcome limitations

Rechecked **metadata only**, not underlying ZIP bytes:
- Oct 30 protected preclose: run `41118123273`, artifact `13006897253`, SHA256 `ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`, expires `2027-01-28T19:47:32Z`.
- Oct 30 maturity replay: run `41140665058`, artifact `13018333034`, SHA256 `956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc`, expires `2027-01-28T22:49:48Z`.
- Oct 30 independent monitor: run `41122875006`, artifact `13010065001`, SHA256 `f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`, expires `2027-01-28T20:24:01Z`.

Original October 30 **8,510-security** cohort, **1,653 preliminary price-only watch labels**, **34,040 original issuer×horizon 0/+1/+2/+3 actual-session slots**, **136-name retained watchlist**, and **JDZG stale/halt failure analysis** remain untouched. October 30 h0 remains censored for absent official closes; November 2/3/4 forward horizons have not matured on Saturday October 31. Same issuer/day is not double counted. Frozen baseline labels and denominators were not modified.

**Official close outcomes independently verified by two genuinely independent provider organizations: 0.** Provider ownership/transport, exact current and previous official closes, issuer/class identity, corporate-action basis, exchange session calendar, source publication/retrieval chronology and complete third-source conflicts are not externally authenticated. Massive key/real-time entitlement, actual SMG blocked-table/account borrow permissions, and durable off-platform ZIP backup remain unverified. This synthetic structural fix is **not** a 20%+ predictive success, precision/recall estimate, SMG approval, fill, or profit.

**Next gate:** obtain independently retrievable source-owned official closing evidence from two independent provider organizations without changing frozen policies, and evaluate only matched untouched future cohorts after actual trading-session maturity. Until then all missing/conflicting outcomes remain censored.
