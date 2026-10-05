# Fixed hybrid strategy across SMG seasons

The five-session hybrid policy is profitable in the inspected 2023 and 2025
seasons but loses in 2024. It has not established a repeatable $189,000 ending
balance. This comparison changes no live policy.

Every season starts with $100,000 and assumes $150,000 gross buying power,
$30,000 target positions, a 25% decision-equity allocation cap, and the same
prior-close stop/profit signals filled at the next close. Orders use observed
pre-close prices to determine share quantities. Each year covers September 8
through December 5 on trading sessions. Independent dated firm evidence selects
the universe; friend/reference lists do not select trades.

| Year | Hold limit | Profit | Ending capital | Closed trades | Maximum observed drawdown |
|---|---:|---:|---:|---:|---:|
| 2023 | 3 sessions | $13,780.91 | $113,780.91 | 6 | 8.842% |
| 2024 | 3 sessions | -$10,926.30 | $89,073.70 | 32 | 32.694% |
| 2025 | 3 sessions | $75,079.35 | $175,079.35 | 56 | 14.629% |
| 2023 | 5 sessions | $14,753.85 | $114,753.85 | 6 | 8.918% |
| 2024 | 5 sessions | -$10,052.33 | $89,947.67 | 30 | 34.073% |
| 2025 | 5 sessions | $90,525.87 | $190,525.87 | 49 | 14.171% |

Base costs: $5 each order, 30 basis points each side, assumed 10% annual
borrow. Cash interest uses 0.75% positive / 7% negative annual rates in the
simulator collateral ledger. Stress uses 100 basis points each side and 100%
annual borrow. Five-session stress profits: 2023 $10,274.64; 2024 -$29,215.85;
2025 $57,684.65.

The 2024 five-session win rate is 43.3%. Its three largest realized losses
were ELWS (-$17,810.54), YRD (-$13,163.63), and FTEL (-$12,778.95). All
three exited through a prior-close stop signal; a closing-price execution model
does not guarantee the stop threshold's price. These outcomes show continued
upward moves after short entry, rather than a notification failure.

The 2023 sample contains only six trades. The 2025 five-session profit is
concentrated: DTCK contributed $23,491.02 and MSGY $22,561.32, together about
51% of net profit. 2025 had already been inspected before hold lengths were
compared; the earlier claim that it was untouched was incorrect.

Source coverage contains 379/569/1,311 missing or stale candidate-session minute
windows for 2023/2024/2025. Every scheduled scan session has an input record;
that does not imply complete candidate data. Historical borrow evidence is
unavailable for all 7/48/90 signal events. Historical cap, halt status, SMG
eligibility, SEC fees and exact margin accounting remain unverified. These are
conditional returns, not certified executable SMG profits. 2022 and earlier
have no completed independent intraday input packet and remain untested.

Reproduce without new provider requests:

```powershell
python -m backtest.compare_cached_years
```

The script saves every portfolio, equity curve, trade ledger and a SHA-256
input identifier under `outputs/backtest/other-years-2026-10-05`.
