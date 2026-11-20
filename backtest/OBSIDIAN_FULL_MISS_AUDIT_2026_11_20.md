---
title: OBSIDIAN — Full Historical Miss Audit (Oct–Nov 2026)
date: 2026-11-20
tags: [obsidian, SMG, historical-misses, research-only, forward-validation]
status: RESEARCH_ONLY_NOT_AN_ORDER
sources: [GitHub research artifacts, StockTitan monthly event leaderboards, SEC/issuer disclosures, Nov 20 user decisions]
---

# OBSIDIAN — Historical missed-drop audit and mechanism findings
As-of: **November 20, 2026**. **Research-only evidence and retrospective audit.** No order, automated alert activation, model promotion, or validated forecast is implied.

## Coverage, provenance, and limits
- Existing research branch: Dirtyhandgernades/Dudebot, research/obsidian-early-rug-20261025. Preserve immutable original watchlist, snapshots, prediction labels, and GitHub Actions artifacts.
- User's SMG: End-of-Day execution; entered before market close settles at that session's close, after close at next session's close. At least $3 previous and current regular stock price, at least $25m market cap, minimum 10 shares, supported ordinary stock/security and actual platform eligibility; see https://www.stockmarketgame.org/tsc-rotg.html .
- Historical sample reviewed in conversation: StockTitan 2026-10 and 2026-11 top 100 news-linked losers, plus existing GitHub audits. November 99/100 entries parsed successfully, October 100/100. These are OUTCOME-SELECTED, NOT an all-stock random population and not a validated missed-trade list.
- Preliminary screen (pre-event price >=$3 and vendor-reported market cap >=$25m): October 53/100, November 47/99, combined 100 candidate events. Current/later vendor cap can differ from point-in-time cap; shortability, corporate actions, halts and actual SMG eligibility were NOT universally verified. Do NOT call these 100 executable shorts.
- Of those 100 selected events, 57 had earnings-related catalysts (26 October, 31 November). November 24/47 preliminary eligible cases gapped down at least 20% by the opening print: critical to distinguish realized headline move from catchable EOD decline. This is NOT a 57% probability that an earnings stock will drop or a 24/47 forecast hit rate.
- Primary event list provenance: https://www.stocktitan.net/rankings/top-news/losers/2026-10?micro=1 and https://www.stocktitan.net/rankings/top-news/losers/2026-11?micro=1 (as-of snapshots, not official exchange data).
- Historical algorithm diagnostics in backtest/MECHANISM_FINDINGS.md: advance watches for 559/873 selected collapse episodes; only 360/3861 warning windows followed by >=20% lower close in three trading sessions (9.32%). Different cohort and denomination from StockTitan.
- Backtest/GAME_COVERAGE_REPAIR.md: among 92 large-drop selected events, 5 with simulated position open BEFORE drop for one rule. Backtest/FIRM_TIMING_VALIDATION.md documents the unacceptable extreme squeeze loss of a policy; backtest/ENTRY_FAILURE_RESULTS_2026_10_11.md reiterates no robust historically consistent strategy. These are conditional research simulations, not actual SMG trade returns.
- No calibrated >=70% or >=80% drop probabilities or verified, consistent executable portfolio edge established. Do not transform 0–100 raw social/algorithm score into a forecast probability.

## Chronological missed/diagnostic event cases
| Ticker | Date 2026 | Historical observation | Classification / catchability |
|---|---|---|---|
| WFF | Oct 14 | -91.75% offering case, pre ~$53 | Vendor cap ~$9.9m, exclude under >=$25m; audit only. |
| AVBP | Oct 06 | -46.98% clinical update, pre ~$28.46 | Existing historical watch; catalyst discovered late relative to outcome. Earlier dated eligibility/entry unverified. |
| CPIX | Oct 26 | -48.76%, ~$8.49 to ~$4.35 | Retained; webcast known ahead, but no verified preclose signal/catchable entry; no retroactive short. |
| APXC | Oct 26 | -20.45% regular close and ~+89.5% indicated afterhours rebound | After-cutoff discovery; ADS representing six common shares; market-cap parity/squeeze hazard. |
| AIOK | Oct 26 | -25.04% amid special $3.50 dividend/record/due-bill arrangements | Corporate-action-adjusted economics; not an ordinary short trigger. |
| JDZG | Oct 28 | roughly -75% one-day collapse with repeated LULD halts | Morning/intraday IEX stale; preclose observed at ~$1.33 while halted and <$3. Not verified executable. See backtest/OBSIDIAN_JDZG_MISSED_COLLAPSE_2026_10_28.md. |
| BCAX / INBX | Oct 28 | Morning IEX early price watches with apparent remaining selling later | Potential advance observations only; official source/SMG fill unverified. |
| ATEC | Oct 30 | -38.08% earnings-related | Post-event diagnosis; earnings calendar gap. |
| DRUG | Nov 02 | -52.35% clinical-development announcement, pre ~$54.98 | Opening gap ~-46.9%; end-of-day strategy cannot capture pre-news price post-publication. |
| MNTN / VCYT | Nov 05 | -54.68% / -54.30% earnings | Both afterhours announcements the evening before; opening gaps already near -51% / -44%. |
| BDSX | Nov 06 | -57.01% earnings | Afterhours announcement on Nov 05; next-day opening gap ~-37%. |
| STLN | Nov 06 | -45.97% earnings, pre ~$6.70 | Afterhours earnings; following session previously watched as a continuation candidate, subsequently <$3. |
| ZURA | Nov 09 | -69.68% clinical, pre ~$4.09 | Pre-market shock, opening gap ~-69%; difficult/blocked after price falls below $3. |
| FTH | Nov 09 | -42.49% following company-described positive Phase 2 results, pre ~$22.05 | Repricing not necessarily trial failure; later continuation to ~$8.11 Nov 20. |
| CDNL | Nov 12 | -62.37% on negative margins/withdrawn guidance | Morning publication, opening gap ~-49%; observed already exhausted in Nov12 A/B/C board. Strong revenue growth and $50m buyback are counterevidence. |
| ADIG | Nov 12 | -49.85% earnings/impairment | Already largely moved before verified 14:20 board; corporate action and official close unresolved. |
| PSFE | Nov 12 | -43.26% earnings, pre ~$6.82 | Later fell below $3 current price; new shorts fail game floor. |
| KPLT | Nov 12 | -27.01% earnings then further declines Nov 20 | Later price around $7.99 in intraday research; not proof of new 20% forward edge. |
| CUE | Nov 17 | -79.93%, pre ~$14.10, post ~$2.83 | Later bounced to ~$4.31 Nov 20; extreme rebound/squeeze and sentiment risk. |
| HY | Nov 18 | -41.07% convertible notes announcement | Deal-time and opening-gap timing important. |
| JMIA | Nov 18 | -40.82% earnings, pre ~$4.63, post ~$2.74 | End-day collapsed below $3 so late fresh short blocked. |
| PRE | Nov 18 | -36.62% M&A/narrative event | Observed after deterioration; verify catalyst and timing, not automatic short. |
| BGIN | Nov 18–20 | User previously shorted then earlier assistant advised full cover; stock down ~12–14% Nov 20 | In hindsight covering all prematurely missed follow-through; avoid outcome-driven blanket 'always hold' rule. |
| NUAI | Nov 18–20 | Earlier assistant advised cover after rising; down ~10–11% Nov 20 | Reversal/exit-timing diagnostic; don't assign retroactive prediction win. |
| CD | Nov 19–20 | 6.5m-share $1.70 fixed-price placement vs ~$3.8–3.9 stock | Model overweighted discounts relative to issuance size and improved cash/operating counterevidence; position-sizing error. |

Event prices and moves are selected-vendor snapshots; they are NOT independently certified exchange official closes. See original immutable backtest notes before scoring any one case.

## Exact failure taxonomy
1. **Never discovered issuer or mechanism**: earnings surprise and biotech/regulatory shocks outside narrow watched intermediary associations.
2. **Discovered but too late**: already opening-gapped/exhausted, first bearish signal after EOD cutoff, active halt, or price already <$3.
3. **Data failures**: stale IEX-only prints; missing independent prior close, corporate-action-adjusted shares, current cap; 9 retained of 136 absent from Nov12 source. Original Nov12 delayed SIP audit: 2,834/8,492 (~33.37%) stale or missing; afterhours IEX 8,359/8,492 (~98.43%) stale/future. 8,492-source scan does NOT imply complete independent issuer-level mechanism review.
4. **Bad initial allocation**: sizing speculative CD near financing by discount alone versus stronger active weakness and genuine convertible pressure at AEHL/USDE; hindsight returns are not evidence this could have been known beforehand without recorded features.
5. **Premature cover vs unmanaged squeeze**: BGIN/NUAI losses at original review led to full exit; later decline shows a potential missed second leg. But keeping full size under all conditions exposes severe squeeze risk—log exposure and reason at each decision, not only final outcome.
6. **Instrument/eligibility mismatch**: ADR/ADS ratios, special dividend due bills, post-split stale vendor market caps, halted stocks, non-ordinary-share issues.
7. **No calibrated odds**: raw 0–100 confidence score, social sentiment and historical firm association do not equal a 70–80% probability of further fall.

## Mechanism taxonomy to preserve
- Earnings/guidance deterioration: margin down, backlog and liquidity, debt covenant, weak outlook; capture announced earnings times before decision.
- Clinical/FDA/adverse disclosures: scheduled data readout, target population, endpoint, response statistics, interpretation and competing positive evidence; true binary event risk.
- Actual vs potential share supply: identify approved/finalized/registered/issued/exercisable/unrestricted/actually sold, exact timestamps and shares outstanding before/after each action.
- Speculative rally exhaustion: top-side wick, failed high, lower high, support breakdown, real sell-side volume, gap and remaining room >$3.
- M&A: financing, close conditions, lockups, issued deal consideration, stock exchange ratio, announcement times, reciprocal positive asset value.
- Long momentum: genuinely positive FDA/data, earnings beat/guidance rise, authentic contract/deal, volume-backed persistence; distinguish pre-news opportunity from unrepeatable post-news gap.
- Issuer/network connections: preserve historical underwriter/placement agent/auditor dates as discovery leads, NOT evidence of misconduct, not a collapse clock.

## Research-source links
- https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_OCT28_REAL_RUG_CATCH_PILOT_2026_10_28.md
- https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_AFTERHOURS_MISSED_MOVES_2026_10_26_1525_CT.md
- https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_PROSPECTIVE_ABC_BOARD_2026_11_12_1420_CT.md
- https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_12_1820_CT.md
- https://www.stocktitan.net/rankings/top-news/losers/2026-10?micro=1
- https://www.stocktitan.net/rankings/top-news/losers/2026-11?micro=1

## Important nonconclusion
This file is a retrospective diagnosis of selected cases and earlier models, **not** a validated forecast and **not** permission to turn on live trading, change risk limits, edit frozen strategies or rewrite historical labels. An independent future full eligible market denominator must include non-falling stocks, excluded instruments, missed eligible falls and false alarms.
