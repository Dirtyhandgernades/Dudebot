# Entry confirmation and forward drop timing

The stricter hybrid research entry reduces losses across the inspected years:
require the decision quote to be at most 2% above the prior raw close. Keep
the existing independently discovered firm cohort, original hybrid setup,
three-session hold limit, dated signals, observed-price share sizing, and
portfolio risk controls. No future outcome chooses an individual entry.

This change was motivated by inspected losses. Every evaluation year has
already been used for research. The results support a new research candidate;
they do not establish reliable future performance or calibrated dump confidence.
The configured firm timing alerts remain disabled pending fresh validation.

| Season | Baseline profit | Confirmed profit | Confirmed stress profit | Confirmed drawdown | Closed trades |
|---|---:|---:|---:|---:|---:|
| 2023 | $13,780.91 | $18,622.15 | $17,313.34 | 0.078% | 2 |
| 2024 | -$10,926.30 | $20,700.90 | $9,298.25 | 18.924% | 17 |
| 2025 | $75,079.35 | $36,482.87 | $14,648.23 | 9.952% | 32 |

2023's two trades are a weak sample. Confirmation rejects some large winners
as well as continuing squeezes. The 2025 ending capital is $136,482.87,
below the user's $189,000 target. Higher profits and better year-to-year
consistency have not both been achieved.

A second fixed experiment retained rising signals at half the normal target
allocation ($15k versus $30k). Three-session profits were $17,039.13 /
$3,132.73 / $48,317.22 in 2023/2024/2025. It lost $12,157.45 in 2024 under
stress, so it failed the cost robustness criterion. Do not promote that sizing
experiment to production on these results.

## Do the trades precede a drop in one to three sessions?

The following counts are for selected simulated entries, not Discord messages.
Benchmarks are split-adjusted entry closes; outcomes are future closes. Trades
without a complete horizon before game end are omitted and reported separately.
A lower close anywhere within the horizon is different from a 20% dump.
These are observed hit rates on reused data, not per-stock probabilities.

| Confirmed policy | Lower close next session | At least 20% lower next session | At least 20% lower within two sessions | At least 20% lower within three sessions |
|---|---:|---:|---:|---:|
| 2023 | 2/2 | 0/2 | 1/2 | 1/2 |
| 2024 | 10/17 | 1/17 | 2/17 | 3/17 |
| 2025 | 18/32 | 1/32 | 1/30 | 3/30 |

In 2025, 23/30 assessable entries had some lower close within three sessions.
Two entries cannot be fully assessed through three sessions before season end.
The unchanged baseline achieved a 20% lower close within three sessions for
2/5 entries in 2023, 5/31 in 2024 and 9/53 in 2025. The stricter entry improved
portfolio consistency while reducing rapid-rug captures in 2025.

Live firm-watch messages recognize a sourced relationship. A watch can precede
a decline without proving its timing. `firm_timing_trade_alerts_enabled: false`
currently prevents promotion of this failed-validation timing policy to a
qualified trade. The separate broad lane has its own checks. No alert promises
a drop tomorrow, and changing an exit limit does not change prediction lead time.

## Reproduction and limits

Run `python -m backtest.confirmation_comparison` at the repo root. It saves
36 separate portfolio runs with trade ledgers and forward timing counts under
`outputs/backtest/confirmation-2026-10-05`, using cached real historical inputs
and zero new provider requests. The hosted pre-close research workflow now
also records a confirmed hybrid comparison beside its original baseline.

All runs start with $100k, assume $150k gross buying power and $30k target
positions, and apply a 25% decision-equity allocation cap. Base costs are $5
per order, 30 bps each side, 10% assumed annual borrow; stress uses 100 bps
and 100% assumed annual borrow. Daily cash interest uses the simplified
collateral ledger. Historical cap/halts/borrow/SMG eligibility/corporate
actions and exact account treatment remain incomplete; these returns are
conditional. Missing minute windows remain visible in the original audits.
Next validation requires new dated inputs outside these reused seasons and
cost tests, with direct 1-3-session dump rates reported separately from profit.
