---
title: OBSIDIAN — Trade Discovery and Validation Playbook v2 (proposal)
date: 2026-11-20
tags: [obsidian, SMG, research-workflow, trade-discovery, short, long, candidate-ranking]
status: RESEARCH_ONLY_PROPOSAL_NOT_ACTIVATED
---

# OBSIDIAN: forward-looking trade discovery / capital allocation workflow
Version: proposed v2, **November 20, 2026**. Read together with OBSIDIAN_FULL_MISS_AUDIT_2026_11_20.md and immutable original branch policies. This document updates the RESEARCH PROCESS, not live production logic.

## Mission
Find the highest-quality, **eligible**, **catchable before an end-of-day fill** declines/rallies in the following 1–3 exchange sessions, compared with existing positions, while preserving buying power. The user's $160k/$170k total equity goal is an objective, not evidence that any trade has >=70% chance of a 20% drop or grounds for unbounded sizing. Distinguish direction, magnitude, window, and executable market close.

## Hard rules — fail closed
- NYSE/Nasdaq/NYSE American eligible ordinary common stock as confirmed by actual game's security table and user's platform; avoid SPACs, halted stocks, unsupported stock classes, 5-character nuisance tickers, ETFs/leveraged products in ordinary stock shortlist, ADS with unresolved share ratios.
- Last authentic previous-session regular close >=$3 AND current/execution regular close >=$3; current $3 check is not replaceable by afterhours quote. $25m+ *as-of* market cap with split/ADS/share-class/LLC parity sourced from current issuer/SEC report, not stale vendor counts. At least 10 shares for new orders. Verify game buying power and actual short permission; unknown is NOT_EXECUTABLE.
- The Stock Market Game *EOD* order entered by 16:00 ET settles at that session's official closing price; after 16:00 ET/weekend orders next business session's closing price. A premarket/afterhours event cannot be retroactively bought/sold at pre-news close after it becomes public.
- No assumed halt clearance, quote availability, fill, stop execution, short borrow, exact cap or shares without documented evidence. Historical backtests are not orders.
- Do not alter original write-once signal files, 2023–25 frozen baselines, 136-name retained watchlist, user trades, main branch, deployed config/alerts, credentials, or production workflows. Any experimentation is a separate named research-only challenger.

## Four complementary new-screen lanes
1. **EARNINGS-FRAGILITY / GUIDANCE SHORT**: full eligible U.S. issuer event calendar scheduled next 3 sessions; 21-day price ramp/recent high; business deteriorating KPIs; liquidity/guidance/analyst estimate sensitivity; original dated issuer documents; pre-close bearish price/volume evidence. Record **post-announcement-only** outcomes as after-event, not early capture.
2. **FINANCING / STRUCTURAL SHORT**: actual offering discount relative to live price; offering size vs economic/float shares, saleability and lockups; whether shares registered vs issued vs actually sold; bid/volume/weakness confirmation. AEHL convertible / CD fixed-price placement demonstrate the distinction. Firms are pointers, not proof.
3. **EARNINGS/CLINICAL/IPO PRICE-EXHAUSTION SHORT**: strong prior rise, unusual turnover, failed high, lower highs/lower-low and support break. Catch NEW downside before >25% exhausted; reject unsupported price-only late candidates. Confirm company-specific disclosure and timing. A biotech report described as positive cannot be relabelled failure merely because its stock falls.
4. **POSITIVE CATALYST / MOMENTUM LONG**: scheduled FDA/clinical/contract/earnings positive surprise; primary-filed catalyst, price and liquidity confirmation; no automatic purchase of already +80% to +120% movers. Tag binary positive/negative predecision scenarios and weekend gaps separately. Long lane has its own scoring model and evaluation.

## Data capture checkpoints (America/Chicago / exchange calendar)
- 09:20 CT morning discovery: all eligible security/issuer listing universe, scheduled upcoming events, prior official closes, dated filing/news and source timestamps.
- 12:20 CT intraday: verified regular-trade/VWAP, high-low, volume, gap, price floor and first observed sign.
- 14:20 CT triage: 10–25 ranked candidates, existing positions and all documented exclusions, updated SEC/issuer catalyst, independent source freshness.
- 14:45–14:58 CT protected EOD decision: only if actual open market and authenticated as-of quotes, independent official prior close, actual game platform eligibility, buying power and known cutoff. Record before outcome. If data unavailable: NO QUALIFIED ORDER; retain research watch.
- After 15:00 CT / weekend: label AFTER_CUTOFF; monitor postclose headlines and halt/filing announcements to prepare next eligible decision; never backfill Friday entry from Sunday event.
- Monday 09:20 / next session: refresh afterhours weekend ledger, but do not assume a next-day opening fill for EOD account.

## Short and long hypothesis card fields
- ticker, stable issuer/security ID, share class/ADS ratio/NYSE venue, dated share count+float, as-of cap; previous official close (two independent sources) vs observed price, source exchange and latency; 21/5/1 session returns, opening gap, day range, VWAP, relative volume, spreads/liquidity and halt records.
- exact SEC EDGAR accession/issuer page, source publication timestamp and observation timestamp, catalyst class, adverse-vs-positive counterevidence, next catalyst calendar, how much of the initial decline is already realized.
- separate **directional hypothesis** (down or up), **magnitude** (e.g. further 10% vs 20%), **horizon** (+1/+2/+3 sessions), and **execution scenario** (close-to-close) — never replace with one fictitious confidence percentage.
- exact SMG eligibility and current available buying power/borrow flag; entry price is EOD closing fill unknown at 14:20; minimum 10 shares; proposed notional, shares, concentration, opposing-catalyst scenario, review/invalidation, maximum 3-session horizon or explicit exception.
- user portfolio positions and unrealized P&L should only be treated as current after verified account snapshot; "submitted" vs pending vs executed vs settled distinct states.
- original decision timestamp, author/source ID, category A early / B already exhausted / C reversal / D blocked, reason, research shortlist rank. Append-only after close outcome.

## Ranking rather than invented probability
- Gate 0: identity / eligible / reliable as-of price / borrow / upcoming scheduled disclosures. If missing, research candidate, not executable.
- Signal factors 1–5: (1) verified dated catalyst; (2) price weakening/strengthening actually supports direction; (3) turnover/liquidity supports an EOD position; (4) material remaining move versus relevant support and $3 rules; (5) no strong contrary immediate event or active squeeze.
- Score is an **ordinal rank only**, not P(20% fall). Keep two columns: evidence completeness and speculative potential. Large speculative upside should not displace better-supported entry.
- Compare existing shorts and longs vs any new candidate on **remaining** downside/upside from next EOD fill, rather than historic full fall.
- Do not promote 70–80% probability of success until forward actual independent outcomes justify calibrated bin-level frequency with uncertainty, across misses and false positives, with minimum cohorts as specified in existing frozen proof gates.

## Capital allocation and candidate action
- First reconcile account's **current buying power after pending orders** and holdings. SMG opening buying power is derived from available equity and is recalculated; short covers do not free the same amount dollar-for-dollar. Ref: https://www.stockmarketgame.org/acctsum_b.html
- Proposed exposure policy for research: preliminary $5k–10k; confirmed $10k–20k; unusually well-supported liquid $20k–30k; >$30k exceptional and separately reviewed. Existing active positions count toward same-issuer/sector/financing exposure. Use the tighter of any prior repository risk caps and the newer research suggestions.
- Rank high expected remaining net P&L vs downside/squeeze cost *if* measured forward; otherwise output optimistic/base/adverse price scenarios clearly labeled, not false probabilities. Stops in EOD account are review/next-close intents, not guaranteed prices. Short losses can exceed initial notional.
- If buying power is unknown or all three previously entered trades are pending, provide conditional share counts and wait for current snapshot before claiming executable quantities. No automatic GitHub-to-SMG execution.
- Preserve no-trade and missed records even when aggressive $160k/$170k equity target motivates searching.

## Forward evidence / model evaluation
- Freeze signals BEFORE subsequent official closes with both independent providers and matched issuer identity and split/ADS adjustments, source hashes and alert timestamp. Track 0,+1,+2,+3 sessions (holiday/early-close aware).
- Outcomes: >=10/20/30/40% favorable EOD closing moves; adverse +20/+50% squeezes; biggest later low and rebound; fees, slippage, EOD quote drift, pending order rejection; true executable return vs predictive trend.
- Full denominators: whole market screened, genuine eligible names, no-source, missingness, A/B/C/D, early vs exhausted, found vs never discovered, false alarms, rejected eligibility, shortable vs no evidence, baseline vs challenger.
- Keep original frozen v1 and new v2 shadow side-by-side, no manual winner promotion. The prior prospective gate requires >=20 fresh sessions and >=10 independent issuers at minimum, and stricter applicable earlier proof requirements must prevail; do not turn on alerts or increase allocation until validated.

## Daily publishables
1. Full-universe **coverage ledger** with timestamp and source-count exceptions.
2. EOD preclose top 2–3 short / top 2–3 long cards with exact rejected alternatives, not 136 stale tickers.
3. Current holdings reconciliation (submitted/pending/executed separated); 0 / +1 / +2 / +3 follow-through.
4. "Missed trades" audit: first observable forecast timestamp vs actual news/price/halts vs cutoff; classify never-found, discovered-too-late, data-gap, ineligible, premature cover, or real forecast miss.
5. Weekly capital efficiency: winning vs losing cohorts and opportunity cost with same capital and after-cost assumptions, avoid selecting best exit retrospectively.

## Source reference anchors
- https://www.stockmarketgame.org/tsc-rotg.html
- https://www.stockmarketgame.org/acctsum_b.html
- backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md
- backtest/OBSIDIAN_OCT28_REAL_RUG_CATCH_PILOT_2026_10_28.md
- backtest/OBSIDIAN_PROSPECTIVE_ABC_BOARD_2026_11_12_1420_CT.md
- backtest/MECHANISM_FINDINGS.md
- backtest/FAST_DUMP_RANK_RESULTS.md

**Implementation status: DOCUMENTATION ONLY.** No live scanner, automated orders, new alert schedule or modified model trained/deployed by this file.


## Critical Nov 20 2026 incident update — CAPR FDA long FAILURE
See backtest/OBSIDIAN_CAPR_FDA_LONG_FAILURE_2026_11_20.md. **Assistant proposed a 500-share long before the Nov22 PDUFA target despite a negative 9–3 advisory vote and outstanding data-integrity concerns.** FDA rejected the therapy Nov20 afterhours; Reuters observed ~77% afterhours fall and a later indicative Stocktwits print ~$1.475, not an EOD game exit. Estimated adverse change for 500 at ~$7.95 versus $1.475 is -$3,237.50, **not confirmed actual SMG loss**.

**Rule correction for v2 research-only playbook:** A binary predecision FDA **long** with unresolved negative agency evidence must be classified HIGH GAP-RISK / NOT AN EVIDENCE-BACKED LONG, no matter how bullish social sentiment or attractive the best-case gain. Reject it from the standard 2–3 concentrated trade shortlist unless a separate independently validated binary-event strategy and explicit, sustainable loss budget are established. A weekend "event optionality" label never converts an unsupported gamble into a quantified edge. Run worst-case *alongside* best-case scenarios even when the user requests best-case only. The delayed EOD game cannot use an intraday stop to limit an afterhours 80% drop. Maintain a complete and immutable record of CAPR as a failure, not a favorable hypothetical after-the-fact short. Documentation-only; no production/alert/trade changes.
