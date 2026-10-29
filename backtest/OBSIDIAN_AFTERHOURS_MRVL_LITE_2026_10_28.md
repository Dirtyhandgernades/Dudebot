# OBSIDIAN — October 28, 2026 evening after-hours audit: MRVL/LITE takeover-report divergence

**RESEARCH_ONLY_NOT_AN_ORDER.** Repository `Dirtyhandgernades/Dudebot`, branch `research/obsidian-early-rug-20261025` only. Incremental evidence after the 18:25 CT audit; not a new authenticated capture, official-close evaluation, actual SMG trade, or verified prediction.

## Original source-integrity replay

Independently re-downloaded and inspected the **original October 28 14:48 CT prospective preclose ZIP** (run 40757495722, artifact 12846452112) and **15:26 CT after-hours IEX ZIP** (run 40763211800, artifact 12849591039). Both original universes have **8,511 records**, and the raw `universe.jsonl` SHA-256 values match the original manifest:
- PRECLOSE ZIP `a4ea5404f4855431b1a3b7348d55627d21079f8ff8b41ab86a1a341edd6525d7`; raw `c3c61d3621bf50442acc319cd8f7081914f80393ef485f3b6a8aa65e645ba116`.
- AFTERHOURS ZIP `9d416ea494693baf91c5a766049c9d43621fd9ec8b99e707a29b836660833da2`; raw `9d469faf2b6e43c8a8c5edec0eb65a4ea562261174faca8aaf0f0e6728802ebb`.

Original preclose statuses: 488 IEX early price-only watches, 10 exhausted, 3,537 no-watch, 4,326 stale/future trades, 101 missing trade/prior, 46 unverified previous IEX session, 3 missing snapshots. Original afterhours: **8,375/8,511 (98.40%) stale/future**, 6 early/intermediate indicative watches. These are **single-venue IEX**, not official prior/regular closes or SMG borrow/fills.

The research engineering matched-cohort hosted replay run [40790013742](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40790013742) independently succeeded on Oct 28, with derived artifact 12861206900, 347 offline tests, 8,511 unique captured morning/intraday tickers, **438 unique first-observed raw IEX price-only watches** and 1,329 changed/missing IEX previous-reference cases quarantined. These are **not** 438 forward-collapse successes. No duplicate morning/intraday issuer/day scoring.

## Material new late-session catalyst: reported MRVL/LITE deal discussions

[Reuters, October 28, 2026, published 23:10 UTC](https://www.reuters.com/business/marvell-advanced-talks-buy-lumentum-bloomberg-news-reports-2026-10-28/) reports Bloomberg's earlier story that **Marvell Technology (MRVL) is in advanced discussions to acquire Lumentum (LITE)**. It is **unconfirmed talks**, not an announced binding agreement; Reuters said the companies had not commented. An earlier Reuters syndicated bulletin was timestamped approximately 22:21 UTC. Both are well **after the 14:45–14:58 CT execution window**.

**Actual immutable preclose snapshot (19:48 UTC / 14:48 CT):**
- **MRVL**: `IEX_NO_EARLY_PRICE_ONLY_WATCH`, fresh last IEX **$250.26** (19:48:00.361 UTC), previous IEX daily reference **$243.61**, raw indicative **+2.73%**.
- **LITE**: `IEX_NO_EARLY_PRICE_ONLY_WATCH`, fresh last IEX **$914.45** (19:47:59.173 UTC), previous IEX daily reference **$866.06**, raw indicative **+5.59%**.
- **AFTERHOURS 15:26 CT original capture**: both **STALE_OR_FUTURE_IEX_PRINT**, with their latest IEX trades at approximately 15:59:59 ET **before** the 16:00 ET regular-session close. These are **not** fresh post-bell price observations.

**Independent later after-hours board:** [StockSetups after-hours leaderboard](https://stocksetups.com/movers/after-hours), explicitly **as of Oct 28 19:43 ET, 15-minute delayed**, reported **LITE $998.00 (+9.19% after hours)** and **MRVL $234.00 (-7.01% after hours)**. Reuters' earlier article reported approximately LITE +11%, MRVL -8%, which is a **different observation time**, not corroborated 16:00 ET official close. No fill/borrow/cost assumption.

**Classification:** both **screened, no original preclose weakness watch**; reported merger discussions **became public after the allowed cutoff**. MRVL is an after-bell loser, not an OBSIDIAN early-rug miss. LITE is an adverse upside/squeeze diagnostic for indiscriminate shorting, but no actual position is presumed. The event's future outcome is unknown; do not call the takeover completed.

**Derivative non-independence:** the same 19:43 ET leaderboard showed **LITZ -23.80%** and **LITG +26.93%**, but both are Cboe leveraged LITE ETFs, **not two additional operating-company collapses**. Issuer information: [Tradr LITZ](https://www.tradretfs.com/litz) seeks -2x daily LITE; [StockAnalysis LITG](https://stockanalysis.com/etf/litg/) is 2x long LITE. Neither appears in the original 8,511-ticker preclose universe. Likewise, NOWX (Cboe 2x NOW) is not an additional NOW issuer outcome; [Cboe issuer listing](https://www.cboe.com/us/equities/listings/listed_products/symbols/NOWX/).

## Additional new after-bell source and provider-bar diagnostics

- **FINW:** original preclose `STALE_OR_FUTURE_IEX_TRADE`, last **$10.39 at 16:26:08 UTC (11:26 CT)**, prior IEX $10.33. [FinWise issuer release](https://www.globenewswire.com/news-release/2026/10/28/3390768/0/en/finwise-bancorp-reports-third-quarter-2026-results.html) was published **16:15 ET**, after the cutoff. [StockAnalysis afterhours leaderboard](https://stockanalysis.com/markets/afterhours/) displayed **+24.03%**, but this is a dynamic quote with no independent exact trade time in the leaderboard; it does not establish a preclose signal or official close. **Screened/stale**, after-bell earnings, adverse upside only.
- **NEXR:** original preclose `STALE_OR_FUTURE_IEX_TRADE`, **$0.4701**, last trade 19:26:41 UTC, prior IEX $0.5675. External dynamic board displayed **-27.87% after hours**. **Below $3 floor**, stale, borrow unknown; no eligible missed short.
- **NCPL:** original preclose `STALE_OR_FUTURE_IEX_TRADE`, **$1.09** last 19:16:05 UTC, prior IEX $1.30; later dynamic board **+40.46%**. **Below $3 floor**, stale, market cap reported <$25m by StockAnalysis; adverse reversal risk only.
- **GOOG / GOOGL:** both original preclose `IEX_NO_EARLY_PRICE_ONLY_WATCH` (+1.71%/+1.52% versus IEX prior); later 19:43 ET board GOOG **-9.64%** and GOOGL **-9.95%** after earnings. **Screened/no watch, after-bell earnings**, not a retrospectively predicted collapse.

The external mover lists differ by venue, ETF inclusion, timing and display scope. Their snapshots are **not** a complete original-universe outcome input or a complete third-source conflict inventory.

## P0-1/P0-3 source and corporate-action gate; P1-5 retention

- **No accepted independent official 16:00 ET regular-session prior/current EOD packets for the original 8,511-member full universe**. Neither the IEX prior bar, a single dynamic external quote board, nor two webpages republishing the same data provider establish independent organization-level EOD corroboration, exact close-as-of, full third-source conflict inventory or security-identifier/corporate-action comparability. **Do not run frozen scorer or report a false zero hit rate.**
- Frozen `backtest/OBSIDIAN_IEX_FORWARD_STUDY_FROZEN_2026_10_27.md` and `backtest/obsidian_forward_collapse_study.py` remain unchanged; the stricter separate source preflight is not retroactively part of the frozen scorer. Research-only preflight is not itself accepted EOD evidence.
- The existing [artifact retention ledger](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_ARTIFACT_RETENTION_LEDGER_2026_10_28.md) records original ZIP digests, run IDs and expiry; earliest currently recorded expiry **2027-01-25 13:53:33 UTC**. Long-term storage approval/restore test absent: **BACKUP_UNVERIFIED**. No off-platform archive was made.

**No capture trigger or retry** outside the single authorized 15:22 CT checkpoint; no new raw datasets, frozen policy edits, main, production, secrets, live alerts, orders, trades or P&L assumptions. This note is isolated source-limited evidence only.
