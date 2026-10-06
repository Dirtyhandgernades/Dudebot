# Daily automatic improvement

The hosted daily workflow runs at 23:55 UTC each weekday. It refreshes completed live outcome prices, trains candidates, replays the 2023–2025 game seasons from cached historical data, and decides whether to stage, promote, retain or roll back a model. It requires no running Windows PC and no daily user approval. Existing source discovery and bounded news/fundamental enrichment continue during the day.

Research is automatic, but a new fit does not become a live policy merely because it is new. The frozen challenger records its decisions before the next three sessions finish. It must pass the multi-year cost tests and the fresh prospective tests before automatic promotion. Missing prices and historical borrow/cap/halt/security membership remain explicit gaps. These are paper signals and conditional simulations, not brokerage orders or certified profit.

The only permitted automatic strategy change is an additional rank filter on the original qualified firm signals. It cannot raise capital allocation, disable exclusions, relax borrow gates, turn on longs, change the entry window or rewrite code. The original rank/setup method remains the fallback. This scope matches the historical timestamped corpus, which was selected by the incumbent model and cannot fairly validate a replacement universe.

## Daily cycle

1. Keep source-dated firm associations, current rules and current delayed market/borrow checks from the existing live system.
2. Label prior base-qualified decisions using the actual following-close stop/target policy and three-session maximum hold. Save completed labels so they survive the rolling price cache; retain unavailable outcomes as unknown.
3. Fit three fixed profitable-policy logistic recipes with L2 0.02, 0.1 and 0.5. Each year's model sees only earlier matured labels; its threshold is the training median. Keep every result, including rejected recipes.
4. Replay all three seasons under ordinary costs, a higher-cost portfolio path and higher costs on identical base trades. Require positive results throughout, drawdown at most 25%, no individual profit regression over 10%, at least two trades per year, and at least $500 aggregate stressed improvement.
5. Freeze a challenger with its exact weights, threshold, input/source hashes and creation time. Record keep/reject decisions on every base-qualified firm entry before later prices exist.
6. Promote automatically only after at least 50 issuer-nonoverlapping matured decisions from at least 10 issuers and 20 sessions, with at least 20 kept and 10 rejected. Require positive kept returns and positive paired improvement under base and stressed costs, including both chronological halves. Those return sums are fixed-$25k paper diagnostics, not an account balance.
7. Continue daily training. After 25 additional training outcomes, test a new frozen challenger against the current active model on aligned, independently recorded decisions. A new challenger must improve the current model, not simply the original strategy.
8. Roll back an active filter if at least ten subsequent matured comparisons show a paired return regression worse than 0.10, or if its model/context integrity fails. Retain the lifecycle audit trail and avoid restaging the identical failed model.

## First cached comparison

| Recipe L2 | 2023 profit | 2024 profit | 2025 profit | Historical gate |
|---|---:|---:|---:|---|
| 0.02 | $3,373.47 | $35,078.30 | $77,500.52 | Rejected: 2024 regression |
| 0.10 | $3,373.47 | $35,078.30 | $65,647.76 | Rejected: regressions and stress improvement |
| 0.50 | $3,373.47 | $41,569.54 | $74,537.40 | Passed; prospective gate still required |

The selected recipe's aggregate full-stress improvement is $2,313.71. The live incumbent remains unchanged while fresh evidence is collected. These repeatedly inspected seasons are comparative diagnostics, and 2023 remains a sparse two-trade sample. No untouched test or guaranteed improvement is claimed.

The replay makes zero market-data requests and took about three seconds locally. GitHub stores the historical bundle in one cache rather than creating duplicate data caches every day. Source input hashes prevent an artifact or dataset change from silently changing the experiment.

GitHub artifacts named `daily-adaptive-<run>` contain the complete daily summary, selected candidate weights, all recipe results and trade ledgers. Durable state holds the staged/active model, base decisions, prospective scores, completed labels and promotion/rollback records. The research workflow sends no Discord messages and places no orders; validated changes affect the existing ranked alert lane on subsequent scans.

The extension is explicit contract `ranked-firm-2026-10-07-v2`. It preserves the original base weights, hard gates and disabled confidence sizing; v1 is archived. The separate original `firm-shadow-2026-10-07-v4` experiment remains unchanged.
