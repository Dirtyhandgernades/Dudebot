# Firm coverage and entry-quality results

October11 deployment correction: the October7ranked-v8/entry-v2 definitions
described at the end were local drafts and were never deployed. Actual older
deployed versions were ranked-v7/original-v8/entry-v1. Current prospective
versions are ranked-firm-2026-10-12-v3, firm-shadow-2026-10-12-v3 and research-only
entry-quality-2026-10-12-v3. Default live weights, timing and exposure limits
are unchanged. Historical tables below remain diagnostic results.

All four requested work streams now have implementations and measured status: source-gap review, premature-entry diagnostics, net-return learning, and prospective validation. None of the new entry policies passed the complete historical gate. The current base selection weights and exposure limits remain in place. The $70,000 seasonal target is not established.

## Independent discovery and benchmark audit

[Source/replay run 37569717822](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37569717822) succeeded with 400 new SEC documents, 80 per year from 2021 through 2025. Relative to the original packet, the merged corpus has 226 added records and 545 independent symbols; this is five more symbols than the preceding rebuild. The source backlog and identity gaps remain explicit. Reference/friend labels never nominate candidates, prices, features or training examples.

The [cached entry study 37570684442](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37570684442) reconstructed observed partial candles from the existing minute cache and gathered 24 bounded news pages across the three game seasons. It retained actual partial close location, prior-support breaks and candle direction before each decision, rather than treating a later closing candle as an earlier signal. Headlines are unavailable for many earlier decisions; absence of archived headlines is not evidence that no news existed. News stays timestamped audit context rather than a learned negative feature.

A separate [labelled audit 37573536673](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37573536673) completed the previously budget-limited lookup. Its cache and outputs cannot be merged into independent backtest selection. Of the friend's 60 short-entry tickers: 18 already have accepted independent evidence; three additional source-dated relationships were found by the targeted audit; 38 have no listed-party match in the sampled filings; and one automated identity lookup remained unresolved. Sampling two filings does not prove that a company never used a listed firm.

The three targeted findings are ATMV/UHY, HWH/D. Boral Capital as placement agent, and WLDS/Aegis. ATMV is explicitly an acquisition corporation and remains excluded. HWH's issuer classification is unresolved and remains review-only. WLDS has a dated IPO relationship; this still does not certify historical cap, halt, borrow or game eligibility. These are audit findings, **not three new independent detections or eligible trades**.

The final automated lookup, OCTO, was resolved manually to Eightco Holdings, CIK 1892492, using its pre-game [2025 10-K](https://www.sec.gov/Archives/edgar/data/1892492/000164117225004802/form10-k.htm) and [April 15 filing receipt](https://www.sec.gov/Archives/edgar/data/1892492/0001641172-25-004802-index.htm). The registration table identifies Nasdaq common stock OCTO; the financial statements name Stephano Slack and former auditor Morison Cogen, neither in the supplied auditor list. This resolves the identity, not every historical party relationship. It remains a labelled manual audit and is excluded from selection.

Seasonal ticker overlap is still six of the friend's 60 shorts: CCHH, DTCK, MAGH, NUTR, NVFY and PHOE. It is not matching his entry timing or verified advance-event recall. All 230 original reference events lie outside the September–December 2025 game period and cannot be scored as seasonal misses or detections.

## Premature-entry evidence

PLRZ's independent evidence was an Aegis relationship in the other-notable tier. CCHH had a focus-tier Cathay relationship. Both produced large adverse paper moves; a primary firm association alone is not a timing clock or a fraud finding.

PLRZ issued [positive preclinical news at 9:28 a.m. Eastern on December 3](https://www.globenewswire.com/news-release/2025/12/03/3199003/0/en/Polyrizon-Reports-Positive-Mucoadhesion-Results-for-Intranasal-Naloxone-Hydrogel-Compared-to-Marketed-Intranasal-Naloxone-product.html), before the 3:40 p.m. research signal. That item was absent from the earlier archived news. This is a verified retrospective coverage finding, not a manually injected model feature. The publisher's original revision history is not archived. The free live collector now retains up to five headline/source rows with publication and actual capture timestamps, so future reviews can establish what was observed at the decision.

## Actual tested net outcomes

Every strategy uses the current exposure envelope, whole shares, a three-session maximum, genuine earlier delayed observations, actual closing-price fills and delayed closing stop/target execution. Base costs are $5 each order, 30 bps each way and assumed 10% annual borrow; stress uses 100 bps and assumed 100% annual borrow. Historical borrow/cap/halts/full game membership remain unknown. These are conditional paper simulations, not executed profits.

| Expanded corpus policy | 2023 net | 2024 net | 2025 net | 2025 higher-cost net |
|---|---:|---:|---:|---:|
| Existing selection, bounded exposure | $2,764.57 | $3,219.45 | $2,751.65 | -$759.90 |
| Current price confirmation | $4,251.93 | $5,077.85 | $491.36 | -$625.86 |
| Focus-tier firm context | $4,514.22 | $621.75 | $3,820.86 | $1,087.75 |
| Learned return/profit/tail filter | $4,063.94 | -$772.49 | -$385.60 | -$973.65 |

Original-corpus base outcomes for the same four policies are $432.27/$5,601.23/$7,328.97; $180.98/$5,077.85/$621.11; $432.27/$2,949.13/$6,081.92; and $432.27/$1,469.88/-$25.42, respectively. The $180.98 chart-confirmation result is cash interest with **zero trades**, not a trading success. Expanded 2023 confirmation has only one trade. All variants and failures are retained.

The return model trains on earlier matured net-policy outcomes, including unbounded squeeze losses, using nonoverlapping issuer windows and a stable issuer holdout. Each year uses the same trailing two-year training window. Thresholds come from prior training, not the test year's winners. Price and source-dated firm features are used; sparse/mixed-provider news is audit-only. Returns, profitability and severe-loss scores remain uncalibrated research ranks. The stock can eventually fall 20% and still lose money under the actual entry/exit policy.

An arithmetic boundary bug was repaired in the simulator and return labels: exactly 20% can evaluate as 19.999999999999996% in floating point. Thresholds now use a tiny numerical tolerance consistently. A test verifies that the exit still occurs at the following close, including a loss if the stock rebounds. The actual study values above were rerun after the repair and did not change; no improvement is manufactured.

## Comparison with the friend's execution

All 80 reported short entries have archived raw daily closes; 79 match within 1% and none differ by more than 5%. This supports the closing-price convention, although vendor/account conventions can explain small differences. None of his short entries was priced at or below $3 or ordered fewer than ten shares.

Of his 77 matched closed short lots, 38 were held at most three actual trading sessions. Those lots have reported net allocated-fee P&L of $89,941.23; the 39 longer-held lots contribute $11,918.33. These are components of his supplied transaction ledger, not a new Dudebot backtest or an independently reconciled account return. They establish a useful example for the seasonal objective; they do not establish this model's predictive edge. The audit is `outputs/backtest/friend-execution-audit.json` and is never a selection input.

## Hosted forward checks and deployment

`entry-quality-2026-10-07-v2` is a frozen research trial. It records base, current-chart, firm-tier and return/tail decisions before subsequent closing prices. The first ticker/day record is immutable. Repeated or renamed issuers cannot supply overlapping independent windows. Nightly review waits for actual completed prices plus the 16-minute data delay; missing labels stay unknown. It evaluates base and higher-cost paired returns and both chronological halves. Fresh evidence requires at least 50 nonoverlapping outcomes, ten issuers, 20 sessions, 20 kept and ten rejected. The module cannot send alerts, place orders, increase allocation or automatically promote a candidate; historical failures remain failures.

The new review shares the existing timing worker's loaded state and checkpoint, adds no market requests, and runs in the hosted evidence and daily-adaptive workflows. [Evidence 37571860307](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37571860307), [daily-adaptive 37571862400](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37571862400) and [CI 37571860278](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37571860278) succeeded on the research implementation. The entry trial has zero matured live outcomes; the separate automatic rank-filter challenger is staged, with active model null. These are not promotions. First October 7 closing entries cannot have full three-session outcomes until October 12.

A delivery bug was also corrected: free delayed bars can remain fresh after the actual exchange close, and checkpointing can cross that close. Every new trade now requires an actually open exchange and rechecks freshness/deadline after checkpoint immediately before posting. Definitely unposted expirations release advisory capacity and can retry after a fresh valid scan; ambiguous sends still cannot retry. This reduces late-alert errors without claiming zero network delay. Existing watch/status messages remain separate from actionable entries.

Final contracts are ranked-firm-2026-10-07-v8, original firm-shadow-2026-10-07-v8, and entry-quality trial v2. Earlier versions are archived. Base weights, gates, exposure limits and first-session dates remain unchanged. 319 offline tests pass. The current base strategy stays active; none of the failed entry filters is promoted. Free Alpaca delay and all hard exclusions are preserved. Reports are in `outputs/balanced-research-37570684442/balanced/entry-quality`, `outputs/backtest/entry-quality-final` and `outputs/entry-verification-37573536673`.
