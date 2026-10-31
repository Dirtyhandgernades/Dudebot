# OBSIDIAN Research Engineering — October 31, 2026, 10:47 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday, no exchange session or authorized IEX/SIP capture. Read the October 28 roadmap, October 31 09:47 checkpoint, October 30 18:20 Rug Proof audit, and protected artifact metadata. This is a research-only prospective maturity-ledger correction, not new market evidence.

## P0-2 historical as-of inventory leak — candidate correction

The earlier 09:47 fix masked the displayed source-evidence verdict of future receipts, but future outcome rows still altered the published `provided_source_rows` count and changed a postclose slot from `CENSORED_MISSING` to `CENSORED_BLOCKED`. This disclosed whether a source packet would arrive after the report's historical as-of. Future receipts also participated in the internal prefix chain.

This patch excludes future-received rows from the historical source inventory and prefix chain, so a report at a fixed as-of is identical whether a future receipt is supplied or absent. Unstamped rows remain blocked, not authenticated. All original supplied rows, including future rows, are still checked for duplicates, malformed rows and out-of-cohort securities; the frozen 8,510-symbol original capture and 34,040 issuer×horizon slots are untouched. Added regression coverage for full-report as-of equivalence and fail-closed future duplicates/outside symbols.

**Validation:** pending hosted CI verification of this commit. Passing synthetic tests cannot authenticate any provider's exchange-official close. The original protected preclose, maturity replay and independent-monitor artifacts were metadata-checked and remain unexpired; ZIP bytes were not independently rehashed, and durable off-platform backup remains unverified. No two genuinely independent official completed regular-session closes, legal security identity/corporate-action proof, Massive entitlement or actual SMG blocked-symbol/account permission has been established. All such outcomes remain censored. No trading, production, main, secret, notification, frozen baseline or JDZG/watchlist changes.
