---
title: OBSIDIAN — CAPR FDA long recommendation failure, Nov 20 2026
created: 2026-11-20
status: POST_EVENT_INCIDENT_RESEARCH_ONLY_NOT_A_TRADE
tags: [obsidian, risk-failure, capr, fda, event-gap, lookahead-discipline]
---

# CAPR — November 20 2026 failure review

## The user's event and what was recommended
On Friday November 20, the assistant shortlisted CAPR as a speculative positive-FDA-outcome LONG before its Sunday Nov22 PDUFA target, despite its July29 FDA advisory vote of 9–3 against efficacy evidence and existing documented data-integrity disagreements. The final 3-trade research sheet proposed **BUY 500 CAPR near $7.99**, approximate $3,995 notional, alongside BGIN short and ADUR short addition. The user then said "I did those three." This is a self-report of order submission, NOT confirmation of fill, share quantity, or the game's actual position.

The assistant also explicitly favored a positive outcome despite the company’s previous complete response letter and the documented adverse FDA record. This was a **bad decision-construction/risk screening error**, regardless of whether the loss ultimately equals the indicative market mark. CAPR was not supported by calibrated probability; social sentiment was overwhelmingly bullish but irrelevant to FDA scientific evaluation.

## What actually happened as of November 20 evening
- FDA **declined to approve** Capricor's deramiocel for DMD on Friday November 20, ahead of its previously published November22 target.
- Reuters Nov20 23:42 UTC reports data integrity violations including unauthorized post-start analysis-plan changes, blinding protocol violations and unreliable results, plus failure to establish study endpoints; noted shares down ~77% in extended-hours trading (at Reuters's observation time).
- Connected Stocktwits quote queried near 19:26 ET Nov20 returned **$1.475 afterhours**, quote recorded 2026-11-20T19:26:33-05:00, down ~80.4% *versus its quote provider's reference* (may not match official Nov20 close). Afterhours liquidity and last trade are not guaranteed executable.
- Separate indicative Friday close source reported ~$7.95 at 16:00 ET (Equibles; official exchange-closing-price proof NOT independently authenticated). Hypothetical mark-to-market on 500 shares: 500*(7.95-1.475) ≈ **-$3,237.50**, excluding fees and Monday movement. This is not accepted SMG P&L; user has not furnished actual fill/remaining shares.
- Source: https://www.reuters.com/legal/litigation/us-fda-declines-approve-capricors-cell-therapy-duchenne-muscular-dystrophy-2026-11-20/
- FDA evidence known in advance: https://www.fda.gov/media/193912/download and https://www.sec.gov/Archives/edgar/data/1133869/000110465926125355/capr-20260930x10q.htm

## Why it was avoidable
1. The model gave the appearance of diversification (two shorts + one FDA long) while allocating capital to an unhedged binary approval outcome where negative primary FDA evidence was public before Friday cutoff.
2. It conflated upside magnitude (possibly 50–100%+ if FDA accepted) with expected return/probability, over-weighted Stocktwits 91/100 bullish sentiment and underweighted known adverse primary regulatory documents.
3. A risk label and smaller 500-share size are not substitutes for **hard event exclusion** with nonzero chance of catastrophic overnight loss.
4. Portfolio was targeting approximately $160–170k by Dec4; $3–4k in a binary FDA bet was not consistent with a strategy that needs repeatable evidence-backed close-to-close edge.
5. The key event was **Nov20 after close**, two calendar days before the November22 target; the published target date NEVER guarantees information won't emerge Friday after hours.
6. EOD SMG account cannot close or stop afterhours; stop at $6.50 presented in earlier plan was NOT an executable gap-loss cap.

## Required corrective gates — proposal for future research
- **NO UNSUPPORTED PREDECISION BINARY LONG** when a major FDA advisory efficacy vote is negative, agency inspection/data-integrity findings remain open, and approval probability has no independently tested calibration.
- For any binary catalyst (FDA/clinical readout, litigation ruling, takeover ruling, earnings when full overnight repricing possible) require a *symmetric adverse scenario* showing complete possible capital loss and EOD inability to stop between sessions. Predefine maximum loss-budget at Friday close BEFORE ranking optimism.
- Social sentiment and analyst targets NEVER override primary regulator documents. In conflict: regulator/SEC primary records are higher priority.
- Separate events trading **after confirmed announcement** and price-based continuation from **pre-announcement binary exposure**. Explicitly classify latter as event gamble unless independent historical risk-adjusted payoff validation exists.
- Require source time checks. Scheduled date not a safety boundary; decisions can be disclosed early. Existing afterhours workflows must highlight published Friday events, not pretend executable exits.
- Prioritize **measured prospective trading edge**, not 10-15k/d hypothetical returns or 80-100% upside best case.
- Red-team each candidate: "Why would this position fall 70–80% overnight? What previously published evidence would support that?" Stop if answer is convincing and unmitigated.
- Limit concentration in ambiguous/uncalibrated weekend/overnight binary biotech events. This file DOES NOT authorize changing active alerts, software risk configuration or SMG orders.

## Immediate operational checklist
- Confirm actual SMG filled CAPR share quantity and Friday entry, not just submitted status.
- If the order is *still unfilled/pending*, check platform cancellation rules immediately; if filled, market already closed and Friday afterhours cannot be transacted through EOD game. Exit evaluation should consider Monday's earliest available EOD settlement (not pretend Monday open or stop fill).
- Do not average down to rescue a regulatory thesis rejected on evidence-integrity grounds. No revenge-sized shorts/longs to "win it back".
- Track Friday regular official close vs Monday game EOD price, actual commission and realised loss when independently observed.
- Record this loss in performance ledger **even if it invalidates model promotion and confidence**. Do not delete the recommendation or retrospectively replace it with a short.

## State
This is a user-initiated retrospective failure investigation. Neither actual account position nor game P&L was accessible here. No trade/cancellation submitted. Frozen baseline, main production, alert policies and original capture files untouched.


## November 20 user-provided SMG screenshot — crucial position-size correction
User uploaded a screenshot of the SMG Equity Positions table after the adverse CAPR news. **This supersedes the previous assumption of a 500-share CAPR long in the hypothetical performance illustration, NOT the original fact that 500 shares were recommended.**
- Screenshot: CAPR | dated **2026-11-20** | **Long 1,000 shares** | **cost basis ---** | **previous close $7.53** | **displayed current price $1.48** | **price change -80.345%** | **market value $1,480** | **gain/loss ---**. The row is yellow, which the screenshot legend labels **Intraday transactions**; do NOT infer final order fill, confirmed settlement price, or realized loss from this alone.
- Conditional *mark-to-market only* using screenshot previous close as a HYPOTHETICAL entry: 1,000 x ($1.48 - $7.53) = **-$6,050**; if hypothetical purchase $7.95, 1,000 x ($1.48 - $7.95) = **-$6,470**. Neither is confirmed final game P&L. Recorded cost basis is BLANK.
- Additional yellow intraday screenshot rows: ADUR short -3,500, BGIN short -4,000, CDNL short -3,500, CD short -3,000, AIIO short -750, FTH short -1,500. The screenshot separately shows a dated Nov18 ADUR old -2,000 short with $1,058 gain. **These values represent visual snapshot positions, not independently confirmed settled orders**. Do not invent price of fills from prior-close column.
- The earlier assumption of only **500 CAPR shares** understated potential loss by about half. Confirmed in screenshot: **1,000 share displayed long**; remaining account cash, NAV, buying power and EOD execution report not shown. User is distressed about serious portfolio damage. Prioritize clear ownership of recommendation error and account loss clarity; refrain from revenge trading or promising quick recovery.
- Proper next step: verify CAPR actual game execution/settlement and pending orders from SMG transaction history; Friday market is closed; for a filled long, consider a valid sell for the next available EOD settlement without suggesting intraday afterhours fill or certain recoveries.

This entry is an append-only correction drawn from the user's own screenshot. No account orders or production model changes.
