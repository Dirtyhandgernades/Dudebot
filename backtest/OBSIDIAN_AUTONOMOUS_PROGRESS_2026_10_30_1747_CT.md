# OBSIDIAN autonomous engineering checkpoint — 2026-10-30 17:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated research branch only; no production, main, trading/orders, credential changes, original IEX trigger or rerun, Rug Proof marker, Morning/After-Hours capture, Early Decision Board, or frozen baseline alteration.

## Material P0-2/P0-3 milestone: actual original artifact replayed by the existing hosted maturity adapter

- Original protected October 30 preclose run: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41118123273 ; original Actions artifact **13006897253**, still unexpired.
- Added a separate, read-only, one-off artifact-replay workflow `.github/workflows/obsidian-preclose-maturity-replay.yml` at commit **7d3d8b8bde3a93d89c80cc90de188548ecb17b5b**. The workflow downloads the existing protected artifact via read-only GitHub API; does NOT create, rerun, retry, or backfill any protected source capture.
- **Hosted run 41140665058 completed SUCCESS** (https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41140665058). All job steps succeeded: pinned original ZIP/universe verification, actual `python -m backtest.obsidian_prospective_maturity_ledger` execution, denominator assertions, and evidence upload.
- Original ZIP SHA256 **ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4** matched the independent original upload receipt; original universe SHA256 **169f3c51659cc43ab3385b1b88c6730ee2559eaa6602f7bdf23bde67bc8eaaf3** matched the source manifest.
- Full original preclose denominator: **8,510 unique issuers**; exact original status partition verified: **1,653** IEX_EARLY_WEAKNESS_WATCH_ONLY; **21** IEX_EXHAUSTED_PRICE_ONLY; **2,306** IEX_NO_EARLY_PRICE_ONLY_WATCH; **7** MISSING_SNAPSHOT; **98** MISSING_TRADE_OR_PREVIOUS_BAR; **4,357** STALE_OR_FUTURE_IEX_TRADE; **68** UNVERIFIED_PREVIOUS_IEX_SESSION.
- Existing repository adapter generated a full **34,040-slot** maturity ledger at **2026-10-30T22:49:54.747943+00:00**. The 8,510 session-0 rows (October 30) are **CENSORED_MISSING**; all 8,510 each at +1 November 2, +2 November 3, and +3 November 4 are **NOT_YET_MATURE**. Each horizon preserves the original 1,653-watch / 6,857-nonwatch partition. Zero verified outcomes, hits, false positives, precision/recall or trading returns.
- Replay artifact **13018333034** is unexpired and contains `ledger.json` (14,604,849 bytes) plus `summary.json` (4,510 bytes), from https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41140665058 . Independently downloaded the replay ZIP and recomputed `ledger.json` SHA256 **acae4f164adc9ff35518258b3992bd8bc935dfc8e743846c986762d9f7089925**, matching `summary.json`. Independently verified all 8,510 symbols are unique and every original status/horizon denominator is preserved.
- This is the first **verified hosted execution of the existing maturity adapter against the actual protected preclose source artifact**, not just a separate manual reconstruction. The prior local inventory remains a separate diagnostic; neither is a prediction score.

## Explicit limitations and next gate

**No authenticated official closing-price evidence was supplied.** The replay deliberately used an empty EOD source list. Published NYSE calendar dates and DST-adjusted 16:00 ET close times were checked in prior research, but this offline module does not independently authenticate calendar source receipts. Provider independence, source conflicts, security identity, corporate actions, and real SMG permissions remain unresolved. No 20%+ prediction success, false-positive rate, trading profitability, or executable short is established. Missing outcomes are censored, not favorable.

The replay artifact also expires after the GitHub Actions retention period; **durable off-platform backup remains BACKUP_UNVERIFIED**. Do not treat the small GitHub progress note as an archive of 34,040 ledger rows.

Other owners' evidence was checked before work: Rug Proof delayed SIP run **41114832467**, separate after-hours IEX **41122875045**, independent monitor **41122875006**; all completed successfully. No duplicate issuer/day was counted as a second independent trade.

**Next P0:** obtain and authenticate two genuinely independent organizations' official regular-session closes and corporate-action/security identity equivalence for the untouched October 30 original cohort, with explicit third-source conflict inventory. As November 2/3/4 sessions mature, update only a new versioned shadow ledger with complete original denominator and missingness, not the frozen capture or prior reports. Continue read-only SMG eligibility gates, 136-name roster, and JDZG stale/halt analysis.
