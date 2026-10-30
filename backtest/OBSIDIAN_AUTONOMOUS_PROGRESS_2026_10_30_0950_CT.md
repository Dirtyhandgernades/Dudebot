# OBSIDIAN Research Engineering — October 30, 2026, 09:50 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only. No main, production, credentials, account permissions, trading orders, alerts, frozen baseline/labels, or original market captures modified.

## P0-1 vendor-source collection correction (diagnostic only)

The existing two-provider Massive/Twelve Data daily-bar reconciliation used Twelve Data `outputsize=10` without an exact date range. Its returned history could silently drift away from the requested October 27–28 dates as subsequent sessions accumulate. Official Twelve Data support documentation confirms that `start_date` plus `end_date` defines a bounded interval and that supplying `outputsize` alongside the date range can truncate it: https://support.twelvedata.com/en/articles/5656039-how-to-get-historical-prices .

Commit `322fa6d4f64b92abdd66f54a37036f35336ed2a8` changed only the research-only `backtest/obsidian_two_provider_close_reconciliation.py` and its tests: use a single bounded `start_date`/`end_date` Twelve Data request per ticker, omit `outputsize`, retain only exact requested ticker/date rows, and reject duplicate, unordered, malformed, over-wide or over-budget requests *before* making any vendor API calls. The existing four Massive requests/two Twelve Data requests, no-retry rate-limit policy, and complete four-row missingness denominator remain intact. Additional regression tests cover date-filtered extra rows, the request contract and pre-network fail-closed behavior.

The first hosted offline run `41075090548` failed due to an accidentally double-escaped raw date-regex literal in the new guard. Corrected **only** that regex in commit `1947b0ca34a6f832c0dc6debda724752b72e2949`. Final hosted GitHub Actions run **41075140174** completed **successfully**, with **24 offline tests passed** (20 reconciliation tests plus 4 ABC-board tests). The live vendor-fetch step was **skipped** because this was a push-triggered test, not a separately authorized workflow_dispatch. This is software-contract validation only, not a live credential/entitlement check or official-price verification. Run: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41075140174 .

## Coordination and original evidence

Before the change, read the October 28 roadmap and October 30 08:50 Engineering note, refreshed the branch ref and recent Actions, and read the separate Rug Proof October 30 morning source verification. The distinct Rug Proof 09:20 morning run **41071432540**, original artifact **12985950392**, and Morning Movers 09:12 discovery/independent-monitor runs **41069835420**/**41069835376** all completed successfully; GitHub artifact metadata shows each unexpired, with January 28, 2027 expiration. No ZIP was newly downloaded/rehashed by this Engineering checkpoint. Rug Proof's original 8,510-security denominator and 136-name historical watchlist (127 represented, 9 absent from that morning IEX universe) are preserved; those 9 were not retroactively treated as captured.

At 09:48–09:50 CT neither the original 12:47 INTRADAY IEX gate nor protected 14:45–14:58 CT preclose gate was open. No original or independent-monitor capture marker was created; no Morning Movers, After-Hours, Early Decision Board or Rug Proof checkpoint was duplicated.

## Remaining external blockers

The two vendor daily OHLC endpoints do **not** establish two independently authenticated official exchange regular-session closes or independent underlying market-data feeds. No live hosted run in this checkpoint proves Massive/Twelve Data keys, data entitlements, source ownership, security identity, corporate-action continuity, official exchange-calendar source or complete conflict provenance. The separate independent halt/optional Massive quote monitor remains source-limited; SMG blocked-symbol/security table and account-specific permissions remain unverified. Missing outcomes stay **censored**. The frozen original 0/+1/+2/+3 trading-session labels/denominators, JDZG stale/halt analysis, false positives, late/exhausted cases, squeezes, costs and untouched future-cohort comparisons remain unchanged. **No prospective 20%+ collapse prediction success, precision/recall or profitability has been established.** Durable raw-source backup remains unverified.

Next P0 gate: authenticate two genuinely independent source organizations' exact previous/current regular-session closes and independently verify action/identity/calendar receipts; keep the vendor-bar diagnostic isolated from frozen scoring.
