# OBSIDIAN — October 28, 2026, 18:25 CT after-hours missed-move and source-integrity audit

**RESEARCH_ONLY_NOT_AN_ORDER.** Branch `research/obsidian-early-rug-20261025` only. This audit is a new source-limited postclose observation, **not** a new authenticated IEX capture, an SMG order, an official-close score, or a trade recommendation.

## Original authenticated cohort replay

Re-downloaded and rehashed October 28 original GitHub morning (run 40704289113, artifact 12822044262), intraday (40739809362, 12837584509), preclose (40757495722, 12846452112) and afterhours (40763211800, 12849591039) ZIPs. Each original raw universe has **8,511** lines; each SHA-256 matches its original manifest, and each ZIP SHA-256 matches the GitHub artifact API digest. The preclose original `universe.jsonl` SHA is `c3c61d3621bf50442acc319cd8f7081914f80393ef485f3b6a8aa65e645ba116`; the afterhours original SHA is `9d469faf2b6e43c8a8c5edec0eb65a4ea562261174faca8aaf0f0e6728802ebb`. The 15:26 CT IEX afterhours artifact is real, but **8,375/8,511 (98.40%)** of its trades are stale/future-dated under the frozen 15-minute rule. `previous_reference_is_official_close` remains false in substance: IEX previous daily bars are not independently verified official previous closes.

## NEW material missed-move diagnostic: GBFH

- **Original 09:16 CT MORNING:** `GBFH` present, **STALE_OR_FUTURE_IEX_PRINT**, last IEX trade from **October 27 19:59:21 UTC**; previous IEX reference $17.71, last stale $17.535.
- **Original 12:52 CT INTRADAY:** `GBFH` present, **STALE_OR_FUTURE_IEX_PRINT**, last IEX trade **17:34:57 UTC** (12:34:57 CT), $17.535 versus IEX previous $17.535.
- **Original 14:48 CT PRECLOSE:** `GBFH` present, **STALE_OR_FUTURE_IEX_TRADE**, last IEX trade **19:33:00 UTC (14:33 CT)**, $17.31 versus previous IEX $17.535 (**-1.28% raw IEX-reference**, not official close). Received at 19:48:02 UTC, just beyond the 15-minute freshness gate. **Not an original early weakness watch**, and the stale print cannot be retroactively promoted.
- **Original 15:26 CT AFTERHOURS:** `GBFH` present, **STALE_OR_FUTURE_IEX_PRINT**, last IEX trade **19:59:25 UTC (15:59:25 ET)**, $17.07 versus previous IEX $17.535. This is a pre-16:00 ET regular-session print, not an authenticated after-hours observation.
- **Independent later external observation:** [StockAnalysis GBFH](https://stockanalysis.com/stocks/gbfh/) showed regular-session close **$17.06** at **16:00 ET** and **$12.00 at 18:44 ET**, **-29.66% after hours**. This is a timestamped **single external market-page observation**, not two-provider official-close evidence, verified volume, short borrow, or a hypothetical fill. It is not a same-session regular-close collapse.
- **Post-bell catalyst:** [GBFH Q3 2026 results](https://www.nasdaq.com/press-release/gbank-financial-holdings-inc-announces-third-quarter-2026-financial-results-2026-10) published **16:16 ET**, reporting net income **$3.9m**, down from **$5.5m** sequentially, and net revenue **$20.3m**, down 7.3% sequentially; gaming credit-card interchange volume/income weakened. [October 19 issuer filing/news](https://www.stocktitan.net/sec-filings/GBFH/8-k.html) had announced the results date and planned release around **16:05 ET**, but **not their contents**. October 22 CEO transition was publicly known; it is a structural historical risk, not an as-of signal that specifically predicted this drop.
- **Classification:** screened but **missing/stale IEX provider bar** at all original checkpoints, **not an original watch**; specific earnings surprise was **unpredictable after-bell news**. Regular price around $17 was above the $3 floor, but **actual SMG short availability, liquidity/depth, spread, and corporate-action entitlement comparability are unverified**. Not a missed *executable* short, not an early forward-collapse success. Do not assign hypothetical P&L.

## Additional independent current-session cases (not retroactive catches)

| Ticker | Original preclose price / IEX previous reference and original status | Later external AH observation | Catalyst / classification |
| --- | --- | --- | --- |
| **FORM** | $109.80 / $106.97 (**+2.65%**), **NO WATCH** | [StockAnalysis](https://stockanalysis.com/stocks/form/) **$103.40 at 19:00 ET**, -6.26% vs $110.31 regular close | [Issuer results](https://investors.formfactor.com/news-releases/news-release-details/formfactor-inc-reports-2026-third-quarter-results) **16:01 ET**. Screened/no watch; post-bell earnings, no predicted drop. |
| **MDXG** | $3.955 / $3.90 (**+1.41%**), **NO WATCH** | [StockAnalysis](https://stockanalysis.com/stocks/mdxg/) **$3.56 at 18:47 ET**, -9.87% vs $3.95 regular close | [Issuer results](https://www.globenewswire.com/news-release/2026/10/28/3390724/0/en/mimedx-announces-third-quarter-2026-operating-financial-results.html) **16:03 ET**, 2026 revenue guidance reduced to $250m–$260m. Screened/no watch, after-bell information. |
| **BRAI** | $3.52 / $3.28 (**+7.32%**), **NO WATCH** | [External after-hours losers board](https://stockanalysis.com/markets/afterhours/losers/) displayed -13.89% at observation, without individual quote time | Screened/no watch; no specific newly released catalyst independently established; no post-hoc signal. |
| **FFTT** | $3.74 last IEX at 14:10 UTC, missing prior IEX daily bar, **MISSING_TRADE_OR_PREVIOUS_BAR** | Same dynamic board displayed -12.41%, without individual quote time | Missing provider bar; original tape is not a validated decision-time signal; borrow/liquidity unknown. |

Previously reconciled FTNT/SFM/NOW/QUAD declines and PRCH/MAX/GKOS reversals are **not new independent hits**. Do not double-count leveraged NOWL or issuer-share-class duplicates.

## Miss taxonomy, outcomes and source gate

1. **Screened/rejected:** FORM, MDXG, BRAI had original fresh no-watch classifications; GBFH was in the universe but rejected as stale.
2. **On board but confirmation/target unmet:** FTNT, SFM, NOW, QUAD were original preclose price-only watches before later after-hours declines; PRCH was a watched adverse upside reversal. **No same-day regular-close forward hit** follows from these post-bell moves.
3. **Never screened:** SDEV absent from original Oct28 8,511 rows; absence is a coverage limitation, not a model rejection.
4. **Missing/stale bars:** GBFH at every original observation; FFTT missing prior IEX bar; afterhours source 98.40% stale/future.
5. **Rename/corporate action:** prior reverse-split/ADS-ratio examples remain separately censored; no new GBFH unchanged-shareholder-entitlement proof established here.
6. **Ineligible/borrow unknown:** WFF below $3; no verified SMG borrow for any examined name. GBFH's price floor alone does not establish executable eligibility.
7. **Unpredictable after-bell:** GBFH 16:16 ET, FORM 16:01 ET, MDXG 16:03 ET, after the permitted 14:45–14:58 CT decision window.

**P0-1/P0-3 source check:** [Nasdaq Closing Cross](https://www.nasdaq.com/products/north-american-markets/nasdaq-stock-market/closing-cross) establishes Nasdaq-listed official closing price; [Nasdaq historical-data API](https://www.nasdaq.com/products/data/data-link/api) offers consolidated historical data via provider access. [NYSE TAQ closing prices](https://www.nyse.com/data-products/catalog/taq-nyse-closing-prices) is a separate exchange data product, with its [client specification](https://www.nyse.com/publicdocs/nyse/data/TAQ_Closing_Prices_Client_Spec_v2.0.pdf) indicating typical NYSE file availability ~22:00 ET, later than this checkpoint. These are **candidate provider contracts, not acquired source records**. StockAnalysis market-page data alone lacks complete original-universe prior/current **two-distinct-provider** exact 16:00 ET source records, full third-source conflict inventory, independent security-identifier and corporate-action proof. No self-attested source flags were used. **Zero accepted EOD input packets available** does **NOT** mean zero collapses or 0% performance. Frozen scorer was not invoked.

**P1-5 milestone:** All eight Oct27–28 GitHub artifact ZIPs independently downloaded, original universe hashes and ZIP digest verified; see `backtest/OBSIDIAN_ARTIFACT_RETENTION_LEDGER_2026_10_28.md`. No durable storage authorization exists; every artifact remains `BACKUP_UNVERIFIED`.

No new 15:22 marker (the authorized Oct28 marker already exists); no capture retry, no frozen code changes, no main, production, credentials, live alerts, orders, or trade actions.
