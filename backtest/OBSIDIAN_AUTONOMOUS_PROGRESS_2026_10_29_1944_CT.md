# OBSIDIAN — 2026-10-29 19:44 CT source-conflict inventory arithmetic hardening

**RESEARCH_ONLY_NOT_AN_ORDER.** Engineering-only postclose code/test checkpoint; NOT a market capture, prospective prediction, official-close certificate, or order. Repository `Dirtyhandgernades/Dudebot`, research branch `research/obsidian-early-rug-20261025` only.

## Verified change and CI

- Initial inspected branch head `6f904c70bf9c8257d76ac18f39db3af05484ad8f` already contained the separate 19:17 CT After-Hours source audit. Rug Proof 18:20 CT original anchors and after-hours markers were read before any work; no new IEX or official halt marker was created outside the protected windows.
- The **all-source EOD conflict inventory** (`backtest/obsidian_eod_conflict_inventory.py`) previously accepted positive, finite but extreme untrusted decimal exponents. Computing `prior * Decimal("0.8")` could raise `decimal.Overflow` and terminate the complete source inventory rather than preserving missingness and all third-source rows.
- Added an arithmetic-context guard for untrusted finite decimal prices (generous adjusted exponent range -100 through +100, **not** an SMG eligibility threshold). Such records remain indexed, with their original claim and digest, but are rejected/censored as invalid prices before threshold multiplication. Also catches invalid numeric conversion without losing other source rows.
- Added two synthetic regression tests covering an extreme regular close, an extreme previous-close reference and an extremely tiny positive close; all verify complete three-source indexing, unparseable-claim indices, rejected third-source classification and no success/official-close claim.
- Code-and-test commit `afbba1161e86ce82f999bca6d70735c49beea074` was published using a non-forced expected-head GitHub lease. **Hosted GitHub Actions run [40981543644](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40981543644) completed SUCCESS** on exactly that commit, with **486 prospective offline tests + 4 ABC-board tests passing**. No hosted external market-data retrieval was performed for this change.

## Unchanged evidence gates and future work

This is a software safety regression fix, **not** independent authentication of two official 16:00 ET regular-session closes. Provider ownership, raw source receipts, full conflict inventory, exchange calendar, issuer/security identity, corporate actions and future 0/+1/+2/+3 trading-session outcomes still require external evidence. **All unmatched or missing outcomes remain CENSORED; no prospective 20%+ prediction success or precision is established.** Original 136-name watchlist, JDZG stale/halt failure analysis, all frozen baseline labels/denominators and separate Rug Proof/Morning/After-Hours/Early Decision Board evidence remain unchanged. No main/production, credentials, market orders, notifications, captures or frozen scorer modified.

P0-1 next gate: collect independently authenticated organization-level official close receipts for the original prospective cohort, with previous-session and corporate-action/identity parity, full third-source conflict handling and source as-of timestamps. Do not promote self-attested vendor daily bars into official outcomes. Durable original ZIP backup remains BACKUP_UNVERIFIED.
