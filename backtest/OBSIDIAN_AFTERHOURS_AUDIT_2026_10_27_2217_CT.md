# OBSIDIAN October 27, 2026 — 22:17 CT incremental after-hours audit

**RESEARCH_ONLY_NOT_AN_ORDER.** This audit adds **new** 8:00 PM ET postmarket observations to prior October 27 16:23, 17:24, 18:26, 19:26, 20:18, and 21:20 CT audits. Do not double-count earlier cases, treat after-bell news as available preclose, infer current user holdings, or alter the frozen prospective outcome policy.

## Original preclose capture and independent raw integrity check

- Authenticated preclose IEX-only GitHub run **40572768800**, original artifact **12766795149**, observation 2026-10-27 **19:51:01.669–19:51:04.120 UTC** (14:51 CT).
- Downloaded **original artifact bytes again** for this audit; manifest `universe_count=8515`; recomputed SHA-256 of `universe.jsonl` is **10a3d8f30726759105394dac6eeaf6bccc208932d43e1faa51507809aa8c0bb4**, matching manifest.
- Full original categories: **433** IEX price-only early watches, **9** exhausted, **3,669** no watch, **4,252** stale/future, **105** missing trade/prior, **44** unverified prior IEX sessions, **3** missing snapshots.
- IEX previous daily reference is **not official previous regular close**; original IEX prints are **not** consolidated NBBO, eligibility, platform borrow, actual fills, or after-cost P&L.

## Material new case: UHS — preclose price-only watch, post-bell earnings decline

- **UHS / Universal Health Services (NYSE):** original immutable row `IEX_EARLY_WEAKNESS_WATCH_ONLY`, IEX last trade **$177.33 at 2026-10-27 19:50:23.732589 UTC (15:50:23 ET)**, versus **$185.95 prior IEX daily reference**. Indicative prior-IEX-reference weakness was **-4.636%** before the earnings release. This is a genuine as-of price-only observation, **not** independently corroborated previous official close, SEC catalyst recognition, or a verified SMG short.
- The issuer's **October 9, 2026** public [schedule change](https://ir.uhs.com/node/20886/pdf) specifically set Q3 results for **after the October 27 market close** and the investor call for October 28 at 08:00 ET. Earnings-date awareness was public, but earnings contents were not available at the 15:58 ET permitted execution cutoff.
- The [issuer's October 27 results](https://ir.uhs.com/node/20916) were published after the close; [independently timestamped press-release distribution](https://www.stocktitan.net/news/UHS/universal-health-services-inc-announces-financial-results-for-the-g3w67mayxlyr.html) shows **16:16 ET** (18 minutes after the permitted cutoff). Reported Q3 net income **$308.7M / $5.22 per diluted share**, down from **$373.0M / $5.86** a year earlier, while revenue increased **5.3% to $4.733B**. A $26M pretax insurance reserve adjustment related to a tentative legal settlement was disclosed; do not assert any single detail caused the market reaction.
- The [TipRanks Oct27 after-hours losers snapshot](https://www.tipranks.com/markets/after-hours/losers), retrieved for this audit after the completed extended session, lists **UHS $166.10, -6.33% versus the October 27 regular-session close**, with **246.36K** displayed volume. This is a **vendor's end-of-after-hours board**, not a timestamped individual 20:00 ET fill or official next-session close. Relative to the original $177.33 IEX last trade, $166.10 is **-6.33%**; relative to $185.95 prior IEX reference, **-10.67%**, a mixed-venue, different-time comparison NOT a verified official daily return.
- **Classification:** `ORIGINAL_PRE_CLOSE_IEX_PRICE_ONLY_WATCH / KNOWN_FUTURE_EARNINGS_DATE / POST_BELL_RESULTS_NOT_YET_PUBLIC / ADDITIONAL_INDICATIVE_AFTERHOURS_WEAKNESS / NO_VERIFIED_20PCT_REGULAR_CLOSE / BORROW_UNKNOWN`.
- **Strict conclusion:** Preclose recognition of **some weakness** before an after-hours extension, but **no** proof of pre-announcement catalyst foresight, a full -20% future *regular-session* collapse, sufficient lead time for executable setup, or a successful SMG trade.

## Other previously unreported end-of-after-hours losers (do not promote)

The same [TipRanks Oct27 snapshot](https://www.tipranks.com/markets/after-hours/losers) gives:
- **LOGI $105.50, -5.65% AH**: original fresh IEX $111.95 vs prior IEX $109.945 (**+1.82%**), `IEX_NO_EARLY_PRICE_ONLY_WATCH`. [Reuters earnings report 16:08 ET](https://www.marketscreener.com/news/logitech-beats-profit-forecast-as-sales-gaming-conferencing-products-rise-ce785cddde80f021) documents post-bell results. A profit beat does not establish a shortable preclose mechanism. `SCREENED_NO_WATCH / POST_BELL_NEWS`.
- **LPLA $301.68, -5.00% AH**: original fresh IEX $318.86 vs prior $317.12 (**+0.55%**), `IEX_NO_EARLY_PRICE_ONLY_WATCH`. [Issuer Q3 results](https://www.lpl.com/news-media/press-releases/lpl-financial-announces-third-quarter-2026-results.html) published Oct27 and [issuer's 17:00 ET earnings call](https://investor.lpl.com/events/event-details/lpl-financial-holdings-third-quarter-2026-earnings-call). No independent proof release was pre-cutoff; do not backdate it. `SCREENED_NO_WATCH / POST_BELL_EARNINGS`.
- **MIR $14.70, -4.61% AH**: original fresh IEX $15.42 vs prior $14.915 (**+3.39%**), `IEX_NO_EARLY_PRICE_ONLY_WATCH`. [Issuer Q3 release](https://ir.mirion.com/news-events/press-releases/detail/186/mirion-announces-third-quarter-2026-financial-results) and independently timestamped [SEC summary 16:18 ET](https://www.rapidtradeview.trade/earnings/reports/mir-2026-q3) document after-bell disclosure. `SCREENED_NO_WATCH / POST_BELL_RESULTS`.
- **AAP $44.04, -3.91% AH**: original fresh IEX $45.76 vs prior $46.595 (**-1.79%**, below frozen -2% early-watch band), `IEX_NO_EARLY_PRICE_ONLY_WATCH`. No independently dated October 27 after-bell issuer-specific catalyst was established; `SCREENED_NO_WATCH / CATALYST_UNATTRIBUTED`. A negative -1.79% must not be reclassified using a post-outcome threshold.

## Capped small-cap after-hours board: eligibility/missingness audit

[StockTitan October 27 20:00 ET board](https://www.stocktitan.net/rankings/stock-movers-today/after-hours) (signed-out delayed, whole percentages, **no trade prices**; change relative to **same-day 16:00 ET close**) additionally shows **NWGL -19%, MEGL -15%, SHFS -12%, MKDW -9%, CLRO -9%, IPW -8%, PFAI +9%** and other small names. It is a capped alert leaderboard, **not** a complete market denominator or a quote at 22:17 CT.

Matched to original immutable preclose:
- **NWGL:** `IEX_NO_EARLY_PRICE_ONLY_WATCH`, fresh **$0.0992**, +15.08% vs prior IEX reference; **below $3**. A subsequent -19% AH reversal is not a missed eligible short.
- **MEGL:** `UNVERIFIED_PREVIOUS_IEX_SESSION`, fresh last **$0.2911**, prior IEX reference from a nonmatching session; **below $3**. No valid prior-close comparison.
- **SHFS:** `IEX_NO_EARLY_PRICE_ONLY_WATCH`, fresh **$0.1175**, +25.13% vs prior IEX reference; **below $3**.
- **MKDW:** `IEX_EXHAUSTED_PRICE_ONLY`, fresh **$0.263**, already **-34.02%** vs prior IEX reference and below $3; not an early eligible short.
- **CLRO:** `IEX_NO_EARLY_PRICE_ONLY_WATCH`, fresh **$5.385**, +8.13% vs prior IEX reference. AH -9% is an observed reversal, but no verified contemporaneous adverse mechanism, consolidated tape or SMG short borrow.
- **IPW:** `IEX_EARLY_WEAKNESS_WATCH_ONLY`, original last **$2.68** vs prior IEX $2.99 (**-10.37%**), but **below $3** and no verified platform borrow. AH -8% is a price-only watch followed by additional AH weakness, **not** an eligible missed trade.
- **PFAI:** `STALE_OR_FUTURE_IEX_TRADE`, original last **$3.57** stamped **2026-10-27 15:36 UTC** (10:36 CT), about 4h15m before capture. AH +9% is a stale-quote/possible adverse reversal case, not a validated signal.
- Other large AH events **ULBI, BRAI, DAVI, SCKT, RAPP, INTA, ENPH, CSGP, BOOM** were already documented in earlier Oct27 audit files and are **not** counted again here.

## Seven-category reconciliation, no fabricated performance

1. **Screened and rejected/no-watch:** LOGI, LPLA, MIR, AAP, NWGL, SHFS, CLRO (and previously audited names); no-watch means only **no price-only signal**, not proof of a complete mechanism-based rejection.
2. **On price-only board but full confirmation/target absent:** **UHS**, and **IPW** below floor; previous ENPH, INTA, CSGP and others are already recorded. None proves SMG borrow or 20% official future close.
3. **Never screened:** not established from one captured universe. SDEV was absent original 8,515 only; no claim of absence from other scans or user watchlists.
4. **Missing/stale provider bars:** 4,252 original stale/future, 105 missing trade/prior, 44 unverified prior IEX sessions, 3 missing snapshots; MEGL invalid prior and PFAI stale.
5. **Rename/corporate action:** previous NUWE/ENLV/SCAG/PARA adjustments remain quarantined; no new unverified split inference.
6. **Ineligible/borrow unknown:** NWGL, MEGL, SHFS, MKDW, IPW below $3; all other actual SMG platform short availability, shares-cap, halts and consolidated liquidity remain UNKNOWN.
7. **After-bell unpredictable disclosures:** UHS official results 16:16 ET, LOGI earnings 16:08 ET, MIR 16:16–16:18 ET; LPLA postclose release and call, not verified pre-cutoff. Earnings **dates** were not the **results**.

Retained structural references CD, XRPN, WFF, AVBP, SDEV, SECZ, AEHL remain research references; covered positions are not assumed open. No new actual holdings evidence, advisory reservations are not executions.

## Forward-proof and research CI checkpoint

- [Latest research CI run 40622858493](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40622858493) completed successfully with **309 offline tests**. Passing tests do not prove a live market edge.
- [Frozen forward EOD source-contract shadow](OBSIDIAN_FORWARD_EOD_SOURCE_CONTRACT_AUDIT_2026_10_27.md) still warns that the frozen scorer does not automatically enforce the stricter per-source provenance preflight. [Calendar shadow](OBSIDIAN_FORWARD_CALENDAR_ASSUMPTION_AUDIT_2026_10_27.md) flags holiday-adjacent session assumptions, though Oct27 is a normal session.
- No complete **independent two-source exact-16:00 ET** completed-session official closing outcome and reviewed security/corporate-action JSONL exists for the original **8,515** symbols. Thus true early-vs-late verified -20% regular close, conditional precision/recall, adverse squeezes, cost-adjusted hypothetical P&L and false-positive rate remain **UNDEFINED**. No outcome invented.
- The authorized **15:22 CT** afterhours authenticated IEX observation was **missed** on Oct27. At 22:17 CT, the 15:00–15:45 CT checkpoint is over. **No marker, retry, backfill, or protected preclose trigger** created.
- This file adds only independent afterhours research evidence. **No** change to main, production, credentials, live alerts, orders, frozen forward scorer, frozen policy, historical baselines, or automation schedules.

**Material new incremental finding:** UHS was genuinely on the original price-only weakness board **before** its 16:16 ET postclose earnings release and subsequent -6.33% afterhours vendor move. This is useful *timing evidence*, **not** a verified rug prediction or executable short. Additional LOGI/LPLA/MIR afterhours declines were **screened/no-watch** and occurred in the post-bell earnings context.
