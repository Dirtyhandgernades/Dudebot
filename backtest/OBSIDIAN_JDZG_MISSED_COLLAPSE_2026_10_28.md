# OBSIDIAN JDZG failure audit — October 28, 2026 (retrospective)

**Research only. Not an order, confirmed forecast, executable SMG short, or rewrite of prior capture.**
Primary immutable source: downloaded original GitHub Actions ZIPs from authenticated IEX research runs. All five full `universe.jsonl` SHA256 values matched their original manifests, and original rows, labels, timestamps and shortability metadata are left intact.

## What actually happened

JIADE Limited (Nasdaq JDZG) was **explicitly retained** in master `obsidian_historical_watchlist_manifest_2026_10_26.json` as `USER_EXPLICIT_2026_10_26`. Its status in that October 26 retention manifest was `NOT_SCREENED`, which is a *historical audit status* and does not mean that October 28's later authenticated scans omitted the ticker.

| Original capture | ZIP artifact | Captured Chicago time | IEX last-trade observed (age) | Original status | IEX price vs prior reference |
| --- | ---: | --- | --- | --- | --- |
| Oct 27 preclose | 12766795149 | Oct27 **14:51:03 CT** | $6.10; **18.65m old** | STALE_OR_FUTURE_IEX_TRADE | $6.10 / $6.195 |
| Oct 28 morning | 12822044262 | **09:16:32 CT** | $6.22; **15.14m old** | STALE_OR_FUTURE_IEX_PRINT | $6.22 / $6.10 |
| Oct 28 intraday | 12837584509 | **12:52:34 CT** | $6.20; **151.21m old** | STALE_OR_FUTURE_IEX_PRINT | $6.20 / $6.10 |
| Oct 28 preclose | 12846452112 | **14:48:03 CT** | $1.33; **13.29m old** | IEX_EXHAUSTED_PRICE_ONLY | $1.33 / $6.10 |
| Oct 28 after-hours | 12849591039 | **15:26:05 CT** | $1.90; **16.42m old** | STALE_OR_FUTURE_IEX_PRINT | $1.90 / $6.10 |

IEX source is single venue, not consolidated SIP, NBBO, independently verified official prior/regular close, or price that was executable at receipt. The preclose IEX $1.33 is the last-trade at **14:34:45 CT** and was observed by OBSIDIAN **14:48 CT** (not a 14:48 fill). A market-data page reports prior close **$6.10** and Oct28 final/late printed price about **$1.50** (approximately -75.4%). This is a public-source outcome observation, **not an accepted independent two-provider/unchanged-security official-close packet** under our strict forward study.

Cboe's Nasdaq halt table (https://www.cboe.com/us/equities/market_statistics/halts/) reports **four Oct28 JDZG volatility pauses**, timestamps **Eastern Time**:
1. **14:14:21–15:29:22 ET**, converted to **13:14:21–14:29:22 CT**
2. **15:29:39–15:34:39 ET**, = **14:29:39–14:34:39 CT**
3. **15:35:03–15:40:03 ET**, = **14:35:03–14:40:03 CT**
4. **15:40:32–16:00:00 ET**, = **14:40:32–15:00:00 CT** (reported resume time at closing bell)

This makes the **14:45–14:58 CT execution period overlap an active quoted halt**; the 2:48 CT IEX capture cannot be construed as an executable short. One earlier price site reported approximately **$4.26** during the first LULD, a partial decline already underway. Neither this halted price nor any outside after-the-fact quote is as-of verified in our original morning/intraday snapshots.

The original Alpaca asset metadata in **every** original captured row reads `class=us_equity`, `name=JIADE LIMITED Class A Ordinary Shares`, `shortable=false`, `borrow_status=hard_to_borrow`, `easy_to_borrow=false`. This establishes **Alpaca snapshot's reported shortability**, NOT the separate Stock Market Game platform's borrow/access. Issuer security type, true contemporaneous cap and float, shorts, halts, depth and platform permission remain independently unverified. No actual SMG trade or hypothetical fill is established.

No contemporaneously released **October 28 JDZG-specific negative SEC 6-K/issuer catalyst** was independently located in the searched public SEC/issuer lists; a **June 4–July 31 trading suspension** is a documented prior structural red flag, not proof that an Oct28 -75% breakdown was predictable. Do not assert a fraud cause or false pre-event prediction.

## Failure decomposition (seven-part taxonomy)
- **Historical explicit watchlist:** YES, retained Oct26.
- **Authenticated screened Oct28:** YES, every captured phase includes JDZG. `NOT_SCREENED` in historical manifest is not the current day.
- **Machine valid early price-only watch:** NO. Both morning and intraday print data stale under existing 15m threshold.
- **Prior adverse catalyst or verified support-loss tape:** NOT ESTABLISHED at original decision time.
- **First major volatility halt:** 13:14 CT, after intraday 12:52 capture and before the protected decision window; could only have been escalated by a separate genuine halt/quote feed.
- **Late preclose:** observed $1.33 at 14:48 CT, more than 75% down IEX reference, original class `IEX_EXHAUSTED_PRICE_ONLY`.
- **Executable SMG short:** NOT VERIFIED; source platform reports non-shortable and JDZG was halted across protected decision window.

## Research-only corrective action (prospective independent of winner choice)
New generic, **not JDZG-special-cased**, `obsidian_retained_freshness_shadow.py` examines **ALL** retained watchlist names against original morning and intraday captures. It preserves original statuses, explicitly queues historically important names with stale/missing/no-source records for **independent second-venue fresh-price confirmation**, without claiming a short or bearish prediction. Additional real-time exchange halt source with as-of capture provenance and true SMG-specific borrow would be needed for prospective operational detection, not a retrospective Cboe screenshot.

The original IEX scanner and preclose classifier were **not** changed, and no original prediction labels were upgraded; the Oct28 JDZG diagnosis is a seen outcome development case excluded from future untouched-cohort predictive calibration.

Sources: https://www.cboe.com/us/equities/market_statistics/halts/ ; https://www.marketbeat.com/stocks/NASDAQ/JDZG/chart/ ; https://ir.nasdaq.com/news-releases/news-release-details/nasdaq-resumes-trading-jiade-limited-class-ordinary-shares .
