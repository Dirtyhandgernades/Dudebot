# OBSIDIAN delayed SIP content verification — 2026-10-26 20:47 America/Chicago

**RESEARCH_ONLY_NOT_AN_ORDER.** This is a read-only SPY endpoint-integrity diagnostic, not an Oct26 prospective capture retry/backfill, a screened ticker board, an official closing-price verification, or evidence of predictive edge. No production, main, orders, live alerts, or credential values touched.

## Verified hosted results

- Research regression suite run https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40434649321 **SUCCESS: 166 offline tests**, zero artifacts. New validator `backtest/obsidian_delayed_sip_integrity.py` and tests `tests/test_obsidian_prospective_delayed_sip_integrity.py` enforce timestamped half-open study intervals, >=15-minute delay, bar shape, finite positive OHLC, OHLC consistency, nonnegative volume, and duplicate/future timestamp rejection. End-boundary minute is explicitly excluded rather than silently counted.
- Read-only diagnostic run https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40434657634 **SUCCESS**, zero artifacts. Paper account/assets HTTP 200; IEX SPY snapshot HTTP 200; real-time SIP SPY snapshot HTTP 403.
- Rolling delayed SIP SPY query 30–45 minutes before diagnostic returned **HTTP 200 but zero bars** during extended hours: `NO_BARS_RETURNED`. HTTP 200 alone is not bar coverage.
- Independently dated **Oct23 SPY regular-session** diagnostic sample, 18:30–18:45 UTC, returned **16 provider bars including the inclusive 18:45 endpoint**. Validated **15 in-window 1-minute bars**, excluded the single 18:45 end-boundary bar. This is a *content-validation* milestone for historical delayed SIP; no Oct26 historical prospective signal or trade record was reconstructed. The fixed sample was selected solely to verify nonempty regular-session data; it was not used for training.
- Intermediate CI https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40434639671 failed because module was updated before matching tests; final updated regression run passed 166 tests. Do not present intermediate failure as unresolved.

## Explicit remaining gaps

- **Real-time SIP remains inaccessible (403)**; IEX is discovery-only and not a substitute for consolidated regular-session closes.
- Historical SPY bar content passing syntactic/as-of checks does **not** establish independent exchange-grade close accuracy, completeness of eligible-universe bars, as-of preclose board availability, SMG borrow, platform short eligibility, or actual fills.
- Prospective Oct26 capture #3 (https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40389830214) remains zero-artifact and must not be retried or backfilled.
- Historical watchlist remains 136 retained symbols (113 master + 23 supplemental), not a confirmed current screen. No change to the frozen baseline, discretionary tiers, or historical winners. True >=20% prospective recall, false positives, lead times, adverse squeezes, matched baseline/challenger after-cost P&L and drawdown remain unmeasurable until independently captured as-of data exists.

**Next research engineering:** build separate, provenance-labelled IEX discovery and delayed-SIP retrospective verification ledgers; never join later data into an earlier decision timestamp, and retain explicit no-bar / source-delay missingness.
