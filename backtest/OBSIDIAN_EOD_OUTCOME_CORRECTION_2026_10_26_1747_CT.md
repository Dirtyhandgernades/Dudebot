# OBSIDIAN EOD outcome integrity correction — 2026-10-26 17:47 America/Chicago

**RESEARCH ONLY. Material correction to 17:24 CT EIKN audit; earlier note retained unchanged as an immutable audit trail.**

## EIKN is NOT yet a verified >=20% regular-session close collapse

The earlier note described EIKN as a newly discovered >=20% Oct26 closing collapse, based on two pages from **one** vendor (StockAnalysis). That outcome claim must be **downgraded to UNVERIFIED** until independently timestamped, completed-session closes agree. Do not count this as a true positive, missed eligible >=20% case, or backtest winner.

Sources observed in this after-hours audit:
- StockAnalysis history/overview, Oct26 **$5.54, -23.69%**, 965,641 volume, claims **4:00 PM EDT** regular close; historical view previously showed **$5.48, -24.52%**. Both are the SAME vendor and do not independently corroborate the threshold: https://stockanalysis.com/stocks/eikn/history/
- ChartExchange history displayed **$6.06, -16.529%** from Oct23 $7.26, 965,180 shares, but its overview identifies **2:28:47 PM EDT** for the "At Close" quote, **before** the actual 4:00 PM EDT close. This is not verified complete-session evidence and cannot refute a later true close without provenance: https://chartexchange.com/symbol/nasdaq-eikn/historical/
- Investing.com historical display listed **$6.59, -9.23%**, 250,480 volume, inconsistent with completed-session volume; likely a partial-session/stale observation, **not** verified final close: https://ph.investing.com/equities/eikon-therapeutics-inc-historical-data
- QuiverQuant's historical page had not yet added Oct26 and still ended Oct23 at **$7.26**; it supplies no Oct26 corroboration: https://www.quiverquant.com/stock/EIKN/historical-prices/
- Prior-session **Oct23 $7.26, -11.89%** is consistent across the consulted historical feeds. Oct23 SEC 8-K at 09:15 ET and Oct26 issuer 06:00 ET releases remain dated predecision evidence, but no verified preclose screen exists. https://www.sec.gov/Archives/edgar/data/1861123/000119312526429549/0001193125-26-429549-index.htm

**Classification:** `OUTCOME_UNVERIFIED_CROSS_VENDOR_EOD_CONFLICT` and `NEVER_SCREENED_IN_RECOVERED_MANIFEST`. No authenticated Oct26 preclose Alpaca artifact; cannot measure catchability, lead time, eligible-universe denominator, false positives, squeezes, or after-cost P&L. EIKN remains an **unvalidated retrospective research candidate**, not a confirmed >=20% miss. No tuning on it.

## Other after-hours reconnaissance

- Oct26 after-hours ranked table showed SPRC -30.62% near $0.90 and market cap ~$0.75M; **hard-blocked** by both $3 and $25M SMG gates, not an eligible catch. https://stockanalysis.com/markets/afterhours/
- Retained historical **WFF** appeared on a high-volume board (108M shares as of 5:06 PM ET), but independently reported price near $0.08 and Oct23 cap ~$5.03M, **hard-blocked**. Oct15 registered-direct offering and Oct21 termination of additional purchase right are dated capital-structure research, **not** proof of actual new selling at any specific time. https://www.stocktitan.net/rankings/stock-movers-today/after-hours https://www.bamsec.com/companies/1980210/wf-holding-limited/chronological
- APXC remains an ADS/squeeze review, ITGR ranked-versus-individual quote conflict unresolved, CPIX postbell disclosure remains not preclose attribution. CD/XRPN/AVBP/SDEV/SECZ/AEHL retained as structural watches, no new as-of preclose evidence. Do not infer current positions from historical advisories.

## Isolated research engineering

New `backtest/obsidian_regular_close_integrity.py` and `tests/test_obsidian_prospective_regular_close_integrity.py` fail closed on independent provider disagreement, duplicated vendor pages, incomplete or future-dated records, and sources straddling the >=20% threshold. This is **outcome-label quality control only**; it cannot certify an exchange close, prove preclose detectability, or authorize a trade. New files are included in the research-only offline CI path filter. No frozen journal, baseline, production, credentials, orders, or live alerts changed.

**Provider blocker:** read-only Alpaca connection diagnostic #1 (run 40406257264) returned HTTP 401 on paper assets, live assets, and SIP snapshot. No Oct26 retry/backfill; future capture requires owner-authorized authentication repair. **No verified executable candidates.**
