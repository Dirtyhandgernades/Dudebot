# OBSIDIAN P0-1 all-source close as-of claim inventory — November 12, 2026, 04:51 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated offline research on `research/obsidian-early-rug-20261025` only. This does not retrieve or authenticate an official exchange close, provider ownership, corporate action, halt history, SMG approval, or prediction outcome.

## Verified change

- Starting branch head `4a7c4d3ccd15a90d7579aeb3e20e744a62bfc6f1`. Code/test commit [`b5349ab6701514b016a7600665c26c1e7ba77eac`](https://github.com/Dirtyhandgernades/Dudebot/commit/b5349ab6701514b016a7600665c26c1e7ba77eac) was fast-forwarded using an expected-head lease.
- `backtest/obsidian_eod_conflict_inventory.py` already preserved full-source prices, issuer class, security ID and individual per-source timestamps. It did **not** group current-session and previous-session exact close as-of claims across all sources, so two agreeing price receipts could obscure a contradictory timestamp from a rejected third source.
- Added separate current/previous close as-of UTC claim groups, valid-versus-rejected source indices, and unparseable timestamp source indices. An explicit contradictory valid timestamp raises `ALL_SOURCE_REGULAR_CLOSE_ASOF_CLAIM_CONFLICT` or `ALL_SOURCE_PREVIOUS_REGULAR_CLOSE_ASOF_CLAIM_CONFLICT` and censors the packet. Equivalent UTC-offset representations of one instant do not raise a false conflict. Unsupported submicrosecond timestamps remain unparseable/censored, never silently rounded into an exact session close.
- Four new synthetic regression tests cover rejected third-source current/previous timestamp conflicts with matching prices, equivalent offset representations, and unsupported precision.
- [Hosted prospective CI run 43204013135](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43204013135) **completed successfully on the exact code commit**, with **718 offline prospective tests plus 4 board tests passed**, confirmed from the hosted job logs. This verifies code behavior, not market-source authenticity or forecast skill.

## Cross-task source and capture review

- Read the original November 11 [Rug Proof postclose audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md) and existing IEX, SIP, independent-monitor and preclose marker inventory. November 11 protected preclose [43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151), delayed SIP [43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523), and intraday independent monitor [43095840045](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095840045) remained **queued**, unchanged since their original creation, with no verified capture artifacts. Distinct afterhours independent-source run [43102970599](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43102970599) succeeded but did not establish Massive entitlement or two official closing-price sources.
- This checkpoint was outside the original 12:47 CT INTRADAY and 14:45–14:58 CT protected preclose gates. No market capture, marker, retry, backfill, or overlapping Rug Proof / Morning / After-Hours / Early Board action was created.

## Outstanding P0-1 and immutable forward-study blockers

- **P0-1 remains BLOCKED/CENSORED.** No two genuinely independent provider-organization authenticated official current/previous 16:00 ET regular-session closes, independently verified source ownership, complete third-source source-byte/conflict evidence, corporate-action and issuer/security-class reconciliation, full halt history, or actual SMG blocked-security/account borrow permissions. No live hosted proof of a Massive key or real-time entitlement. Alpaca borrowing is not SMG approval.
- Preserve the user's 136-name watchlist, JDZG stale/halt failure analysis, original frozen historical labels/denominators, and 0/+1/+2/+3 **actual exchange trading-session** untouched future-cohort evaluation. Include false positives, late/exhausted cases, squeezes, costs, and missingness. No >=20% success or predictive edge is established. Missing outcomes are censored, not negative outcomes or wins.
- No main/production, secrets, credentials, orders, share sizes, fills, P&L, or trading notifications changed.
