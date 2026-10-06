# Five-part validation implementation

All five requested work streams now have code, reports and an explicit
validation status. This does not mean the profit and prediction goals are
proven. The new forward window starts October 6, 2026; future outcomes cannot
be reported before they occur.

| Work stream | Implemented | Remaining evidence |
|---|---|---|
| Missed-dump audit | Independent corpus episodes, prior setup/selection dates, position coverage and rejection/gap reasons | Full-market recall and exact old minute-window causes remain unavailable |
| Entry timing | Baseline, 2% confirmation, rank thresholds and three-session outcomes compared; new per-symbol minute provenance | Better fast-dump precision/recall on fresh data |
| Independent data | Bounded gather-only workflow, earlier-year priority, reusable caches, weekly 200-document cap; existing live borrow/feature archive | Unresolved historical tickers, cap, halts, borrow and SMG membership |
| Frozen forward test | Versioned model, thresholds, code/config hashes, first immutable forecast per symbol/day, daily outcome and paper-ledger review | New prospective forecasts and their mature 1–3-session outcomes |
| Confidence and sizing | Nonoverlapping calibration windows, Platt diagnostics, uncertainty bins, prospective readiness gate and separate paper sizing profiles | Enough new evidence for confidence sizing; no automatic live promotion |

## Actual missed-episode audit

An episode crosses 20% below a prior closing price within three actual
exchange sessions. Continuous episodes are deduplicated. After-drop signals
never count as advance detection. These are retrospectively measured events
within the partial independent firm corpus, not an eligible whole-market list.

2025 contains 531 measured episodes: 315 have prices below the $3 gate in
the prior decision window, 39 precede public firm evidence, 157 have no timing
setup or insufficient old minute provenance, nine lack full signal history,
three were rejected by ranking, one was selected without a position at the
drop, and seven had a modeled position open. Position coverage is different
from earning a 20% return from the actual entry price.

Detailed per-event reports for 2023, 2024 and 2025 are saved under
`outputs/backtest/validation-2026-10-05`. New pre-close replay reports include
per-symbol reasons separating missing split/raw windows from absent setups.

## Calibration

The diagnostic fits the rank on 2022–2023 data, calibrates on 172
nonoverlapping 2024 windows, and evaluates on 419 nonoverlapping reused 2025
windows. Brier error falls from 0.2263 for raw balanced scores to 0.0985 for
calibrated estimates. A constant calibration-period base-rate estimate is
about 0.101, so the improvement over that baseline is modest.

Most calibrated estimates fall between 10% and 20%. The 20%–40% bin has
only 14 observations. There is no evidence for a reliable 80%–90% dump
probability. Both `live_trade_enabled` and `confidence_sizing_enabled` are
false in the new forward contract.

## Forward operation

`config/frozen_forward.json` fixes model weights, median training-rank
threshold, target (20% within three sessions), 16-minute data delay and a
pre-close observation window. It also fingerprints the implementation and
strategy settings. A semantic config change or source change blocks the
experiment until a new version is registered; it cannot silently retune a
running test. Line-ending differences do not invalidate the same policy.

Regular-session minute aggregates already downloaded by the live scanner
supply prior features and the current partial candle. This adds no market
request to a scan. Missing features or stale/future data are recorded as gaps.
This feature basis differs from historical provider daily aggregates and must
be assessed in the prospective test; it is not claimed to be identical data.

Forecasts distinguish detection from current game eligibility, halt and borrow
checks. Only selected, currently eligible and borrow-indicated forecasts can
enter the conditional paper portfolios. An Alpaca flag does not reserve a
locate or establish SMG Security Table membership.

The existing nightly review collects completed split-adjusted outcomes and
adds bounded raw daily requests only for forward symbols. Missing raw entries
are not filled from warm-up feature bars. Open paper positions carry across
days instead of being artificially liquidated at every review. Two frozen
portfolios track $30k/25%-equity and $50k/30%-equity sizing separately, each
starting with $100k and assumed $150k gross buying power.

Readiness requires at least 50 mature prospective windows, ten positive
outcomes, five distinct issuers and calibration skill above a constant
base-rate baseline. These are engineering review thresholds, not proof of
future returns. Passing them does not automatically enable live confidence
sizing or trade alerts.

If an eligible forecast is captured on October 6, its first next-session
result can appear October 7 and its full three-session label October 9.
No forecast or future profit has been invented for those dates.

Nightly output: `daily-outcome-review.json` contains `frozen_forward`, paper
balances, prediction counts, calibration and gap status. Scan output:
`frozen-forward-capture.json`. Durable records remain on `smg-state`.
Historical replay and source collection never send Discord messages.

## Reproduction

```powershell
python -m backtest.complete_validation
python -m pytest -q
```

The historical gather workflow can be dispatched with `max_documents=200`,
`source_mode=gather`, `priority_period=earlier_years`. It resumes existing
independent caches and avoids repeating price downloads and profit searches.
It also runs weekly with that cap. Neither the gather nor the daily feedback
silently changes the frozen weights. Fresh data supports a later, separately
versioned model.

Local verification: 241 tests pass, including immutable forecasts, future-data
rejection, nonoverlapping calibration, frozen code changes, borrow/cap gating,
missing raw prices and paper positions retained across reviews.

Hosted tests 37399904375, pre-close replay 37399904292 and source replay
37399904321 passed for commit 17b7af6. The live scan 37399904325 registered
the frozen contract and correctly reported `OUTSIDE_FORWARD_WINDOW` after
hours. The hosted review 37399952559 returned `PENDING_PROSPECTIVE_OUTCOMES`,
zero forecasts and confidence gate `NOT_READY`. No forward market result has
been asserted from the smoke tests.

The first new-document gather 37399950644 waited for an ubuntu-latest runner
without executing steps; it was cancelled before collecting data. The gather
workflow now uses the working ubuntu-22.04 pool, queues multiple pending
requests, and defaults code pushes to cache-only gather instead of repeating
market/profit replay. Workflow-only changes are validated by explicit dispatch.
