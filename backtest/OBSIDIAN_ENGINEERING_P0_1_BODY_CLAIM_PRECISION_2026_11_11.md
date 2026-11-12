# OBSIDIAN P0-1 source-body precision and partial-claim audit — 2026-11-11

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated research branch only. This note does not amend original captures, frozen baseline labels, decision timestamps, denominators, retained 136-name watchlist, JDZG stale/halt diagnostics, SMG rules, or the 0/+1/+2/+3 **actual trading-session** evaluation contract.

## Verified software milestone

- [Commit a2a1988b5eae75e35fcf3c587846cbae06f94e52](https://github.com/Dirtyhandgernades/Dudebot/commit/a2a1988b5eae75e35fcf3c587846cbae06f94e52) updates only `backtest/obsidian_eod_source_body_binding_shadow.py` and its synthetic regression tests.
- The source-body claim ledger now compares a 20% decline with a 512-digit Decimal context rather than silently rounding the prior close under the default 28-digit context. Bounded prices with more than 100 significant decimal digits are rejected and censored, not scored.
- Conflicting *independently parseable* current/previous close claims are inventoried across rejected partial-source bodies, even if no complete same-row pair exists. New issue `PARSED_BODY_ALL_CLAIMS_STRADDLE_20PCT_THRESHOLD` means **untrusted threshold ambiguity**, not verified market movement.
- [Hosted prospective CI run 43129728236](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43129728236) completed **successfully** on the exact code commit. Original job logs show **674 offline tests passed plus 4 additional tests passed**, including all three new precision/partial-source regression cases. This proves synthetic code behavior only.

## External evidence and capture separation

- November 11 protected preclose [run 43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151) and delayed SIP [run 43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523) were **queued without jobs or artifacts** at this checkpoint. Neither was retried or backfilled. The separate Rug Proof [18:20 CT postclose audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md) owns its evidence, including distinct Morning/Intraday/SIP markers.
- The independent afterhours Nasdaq RSS parser and single-venue IEX captures are **not** two independently authenticated organization-level official regular-session closes. Massive independent quote entitlement remains unverified/disconnected for the retained 136-name roster.
- P0-1 official close verification remains **BLOCKED/CENSORED** pending real independently authenticated source bodies/receipts, full third-source conflict review, exact security and corporate-action continuity, actual exchange calendar and completed-session proof, and two distinct provider organizations. Actual SMG blocked-security/account permissions and shortability remain unknown.
- No 20%+ prediction-success, precision, recall, trade eligibility, shares, fills, P&L, or edge is established. Future outcomes must preserve false positives, late/exhausted/squeeze/cost/missingness cases and the frozen denominator; no retroactive winner promotion.

No production/main changes, orders, alerts, new capture triggers, duplicate markers, or unauthorized account access.
