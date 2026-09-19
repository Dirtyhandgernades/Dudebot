# Three-period price-outcome validation

Evidence: GitHub run 35453983958, commit 0a7e0b1, artifact 10586939866.
Artifact SHA-256: 5dfdc25a17db751b7a98bea89660d306276449370895739ed7483e61beb9539f.

Each fall period starts with $100,000. Cohorts are independently discovered and frozen before the period. Reference-event labels are never loaded. Results include $5 per order, 30 basis points of assumed slippage on entry and exit, and 10% annualized short borrow. These are price-outcome simulations, not verified executable returns.

## Pump-failure short ending balances

| Hold | Fall 2023 | Fall 2024 | Fall 2025 |
|---:|---:|---:|---:|
| 1 session | $103,540.80 | $94,493.37 | $98,088.26 |
| 3 sessions | $105,384.09 | $96,309.89 | $107,629.45 |
| 4 sessions | $105,213.21 | $101,257.99 | $107,829.72 |
| 5 sessions | $106,877.62 | $109,130.93 | $112,174.97 |
| 7 sessions | $109,868.16 | $111,389.68 | $124,096.71 |

The 4-, 5-, and 7-session variants were positive in every tested period. The 7-session variant had 5, 20, and 26 closed trades with win rates of 100%, 65%, and 80.8%. Sequential compounding of the three independently restarted 7-session returns is approximately $151,900 from $100,000. It does not reach the $160,000–$170,000 objective.

For fall 2025, the severe cost test used 100 basis points each way and 100% annualized borrow. The 7-session variant ended at $114,581.92; 5 sessions ended at $103,676.85; 4 sessions ended at $100,311.13; 3 sessions ended at $100,495.37; and 1 session ended at $92,381.94.

## Breakout-long result

The breakout rule is unstable. Most period/hold combinations lost money. Examples include $74,491.62 for the 2023 four-session test and $69,194.28 for the 2024 seven-session test. Positive isolated combinations had very large observed drawdowns, including $128,818.41 with a 55.4% drawdown for the 2025 four-session test. The long strategy remains review-only.

## Limits

- Historical market capitalization, halts, borrow availability, dividends, and SMG security availability remain unverified.
- Signals use daily bars and next-session closing fills; this does not certify actual fills or short availability.
- Cohorts come from the independent firm-source corpus, not the full Nasdaq/NYSE universe.
- Results are fixed-hypothesis research with no reference-label selection, but three periods are still a small sample.
- No result is represented as guaranteed, executable, or sufficient to reach a target balance.
