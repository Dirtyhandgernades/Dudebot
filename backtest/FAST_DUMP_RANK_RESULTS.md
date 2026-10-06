# Twenty-percent dump target: chronological rank experiment

Target: a split-adjusted closing-price decline of at least 20% within the
three trading sessions after entry. One aggressive research variant exceeds
$90,000 profit in the previously inspected 2025 season, but not the other
seasons or the 2025 stress case. Rapid-dump accuracy is still low.

Two labeling defects were corrected. Risk-model samples must contain every
actual exchange session across their 22-session features and forward label;
a December-to-June cache jump cannot represent consecutive sessions. Outcomes
must have matured before the training cutoff, including signals near year end.
The live daily review now checks the next three actual exchange sessions,
exposes missing bars, leaves an unfinished negative pending, and applies the
20% threshold before rounding. It ignores an incomplete current-day daily bar.
Daily scans also retain one timestamped feature snapshot per symbol/lane/day,
including price, volume ratios and returns. A later scan without a quote
preserves that snapshot with its original timestamp. This gathers new forward
evidence without an extra data request or storing every quarter-hour scan.

The ranking experiment uses the expanded independent firm-date map in the
cached research packet rather than the older, narrower discovery file. It
fits the existing deterministic seven-feature logistic ranker using earlier
years only. Each September–December test uses frozen training-score 50th, 75th and
90th percentile thresholds from before that year. Ranks are not calibrated
probabilities. No friend or reference list selects trades.

## Results

The top-half rank policy with a $50k target and 30% decision-equity cap retains
the three-session hold limit and the same $150k gross buying-power assumption.
The allocation fraction is an explicit research parameter; default behavior
remains capped at 25%. It is not calibrated confidence sizing.

| Year | Aggressive candidate profit | Ending capital | Stress profit | Drawdown | Closed trades | 20% lower close within three sessions |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | $18,658.11 | $118,658.11 | $16,487.95 | 3.059% | 3 | 1/2 |
| 2024 | $39,124.52 | $139,124.52 | $25,305.11 | 25.691% | 16 | 5/16 |
| 2025 | $103,258.54 | $203,258.54 | $64,020.56 | 19.966% | 36 | 6/35 |

The three-session denominators censor entries without a full horizon before
game end (one in 2023, one in 2025). 2023 training has only four positive
labels. In 2025 DTCK contributes $33,966.51 and MSGY $24,176.51, together
about 56% of net profit. This dependence and the 2024 drawdown prevent
claiming stable $90k seasons or reliably forecasting massive dumps.

For comparison, the broader top-half rank with the default 25% cap and $30k
target earns $15,587.70 / $37,403.93 / $73,815.54 in 2023/2024/2025, with
stress profits $13,809.62 / $26,795.01 / $48,528.08. It has lower 2024
drawdown (17.465%) than the aggressive candidate. The risk/return tradeoff
is visible rather than presented as a single absolute optimum.

Top-quartile comparison: three-session hold, $100,000 initial balance, $150,000 gross buying-power
assumption, $30,000 position target, 25% decision-equity cap:

| Year | Top-quartile rank profit | Stress profit | Closed trades | Observed drawdown | 20% drop within three sessions |
|---|---:|---:|---:|---:|---:|
| 2023 | $2,859.18 | $2,211.40 | 1 | 0.077% | 0/1 |
| 2024 | $35,277.28 | $26,233.91 | 14 | 16.372% | 5/14 |
| 2025 | $67,549.55 | $49,488.44 | 26 | 11.798% | 5/26 |

Training samples / positive labels: 2023 98/4, 2024 284/38, 2025 666/82.
The four positive training examples for 2023 and one realized trade cannot
establish robustness. Labels and signals overlap and are correlated.

Increasing the position target to $50,000 retains the 25% decision-equity cap.
It raises 2025 profit to $76,849.99 (stress $51,023.58) but reduces 2024
profit to $31,077.96 (stress $21,649.28) and increases 2024 drawdown from
16.372% to 20.429%. The $30k target performs better on the earlier validation
year. The $50k case does not establish the $90k target or justify larger
live recommendations based on an uncalibrated score.

The top-decile score gate and combining the rank with the strict 2% observed
gain gate both reduce 2025 profit and trade coverage. All variants are saved;
none is presented as a globally optimal setting. This experiment improves
2024/2025 profit relative to the confirmation-only policy while preserving a
three-session maximum planned hold, but capture of fast dumps is still low.

## Validation status

All evaluation years were previously inspected. Model fitting is chronological,
but this is retrospective research, not an untouched holdout or proof of
future consistency. Historical cap, halts, borrow, SMG eligibility, corporate
actions, and exact margin/cash treatment remain incomplete. The conditional
P&L includes $5 per order, 30 bps each side, 10% annual borrow assumption and
cash-interest assumptions. Stress uses 100 bps and 100% annual borrow.

Reproduce with `python -m backtest.target_rank_research`. Models, training
cutoffs, ledgers and all 54 portfolio runs are saved at
`outputs/backtest/target-rank-2026-10-05`. Original minute and filing gaps remain.
No new provider requests or paid model calls are used. Live firm timing alerts
remain disabled; this model needs new dated data and calibration before it can
support trade confidence or sizing.

Local verification: 230 tests passed, including exchange-session continuity,
label maturation, exact 20% thresholds, partial horizons, feature retention
and allocation caps computed from decision-time equity.
