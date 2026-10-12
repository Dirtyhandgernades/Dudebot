# Daily automatic improvement

## October 11 daily-learning repair

The current prospective contract is `ranked-firm-2026-10-12-v4`, with the matching
original and entry-quality v4 contracts. Exact v3 definitions are archived. The
actual October 7 observations remain under ranked v7, original v8 and entry v1;
none are relabelled. Base ranking weights, eligibility, current exposure limits,
preclose timing and maximum three-session horizon are unchanged. This repair
changes validation and learning bookkeeping, not a live model promotion.

Two promotion defects were corrected. Historical challenger replays previously
used larger research sizing instead of the current bounded exposure envelope.
They now use the same bounds as the incumbent, and cash interest cannot pass a
trading-profit check. Fresh paired tests previously checked chronological halves
only at base costs. Both kept returns and paired improvement must now be positive
in both halves under base and higher costs. Unknown/nonfinite outcomes cannot pass.
Active filters can also roll back after a verified higher-cost paired regression.
Known, normalized SEC issuer identities are required for independent prospective
counts; ticker aliases and unknown CIKs cannot manufacture ten different issuers.

The bounded original three-season diagnostic retains all recipes. L2 0.02 and
0.10 fail; L2 0.50 passes the historical gate with $560.83 aggregate higher-cost
improvement. Its base profits are $432.27/$6,020.65/$7,039.98 for 2023–2025,
compared with the incumbent's $432.27/$5,601.23/$7,328.97. This is a small,
reused-data comparison, not the $70k seasonal goal or fresh validation.
The earlier large-sizing table below is archived research, superseded for
automatic promotion by these bounded results.

Each hosted daily review now records its Chicago date, completed independent
outcome count, newly matured count, fit status, staged/active IDs, historical and
prospective gates, and any rollback. State keys `adaptive_daily_report` and the
`adaptive_daily_learning` audit trail persist these records. Repeated runs with
unchanged ready labels reuse a valid frozen fit; new ready labels trigger a fit.
Unavailable labels remain unknown and never count as learning or wins. Same-day
labels still wait for the existing conservative training-date maturity rule.

The nightly job learns from qualified live decisions and evaluates an additional
rank filter. The separate daily eight-season research collects bounded source
and spring checkpoint data, tests timing/hold alternatives and retains every
failure. It cannot automatically increase allocation, enable longs, change entry
timing or rewrite code. Research and daily evaluation are automatic; better
returns are not guaranteed, and the incumbent stays in place when gates fail.

Hosted verification on `8fa3dd5`: [daily learning 38198293821](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38198293821),
[evidence scan 38198293454](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38198293454),
[closed-market preflight 38198295311](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38198295311)
and [CI 38198293446](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38198293446)
all succeeded. CI passed 372 Python and 25 Cloudflare checks. The nightly result
is `FROZEN_CHALLENGER_STAGED`, ID `adaptive-52216c0a89d0d3641584`, with active model
null, zero newly matured live outcomes, zero historical provider requests and
zero orders. A first ready historical fit was made under the repaired context;
this is not new live learning or a promotion. The preflight correctly reported
the market closed; it did not perform a new live quote probe or send a trade.
Detailed verification is `DAILY_LEARNING_VERIFICATION_2026_10_11.json`.

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
