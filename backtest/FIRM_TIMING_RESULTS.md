# Firm timing comparison

Four fixed rules were tested on the same cached, independently discovered timestamped firm signals. The original rank, preclose quote, pricing, capital cap, three-session exits and transaction/borrow-cost assumptions remain identical. Confirmation reads only the observed quote versus the prior close, never the later closing fill or subsequent decline. No provider requests were made.

| Timing rule | 2023 net | 2024 net | 2025 net | 2025 stress net | 2025 base drawdown |
|---|---:|---:|---:|---:|---:|
| Existing mixed setup | $3,373 | $40,181 | $75,549 | $35,622 | 17.42% |
| Current-session exhaustion only | $181* | $36,683 | $38,142 | $18,439 | 18.72% |
| Keep current setups; prior-close setups only if quote is flat/down | $181* | $41,212 | $91,047 | $55,152 | 14.94% |
| Keep current setups; prior-close quote gain at most2% | $2,859 | $41,212 | $95,491 | $60,770 | 14.63% |

*The $181 cases had zero trades; the reported increase is modeled cash interest, not trading profit.*

The2%confirmation rule keeps the same seven2025filled-trade20%drop outcomes using38trades rather than44. Its2025same-base-trade cost stress is$68,292.65, with19.66%drawdown in the full stressed portfolio path. Those findings support testing confirmation instead of discarding every prior-close setup.

It is not approved for live promotion. The2023sample falls from two trades to one and its profit regresses15.25%, exceeding the existing10%regression limit. The original policy remains active; all variants, including inferior current-only results, are retained. All periods are reused research and historical eligibility/borrow facts remain unavailable, so these are conditional paper profits.

The new timing sidecar records all four prospective keep/reject decisions during the preclose window. Its contract is registered before each decision, its source files are fingerprinted, and known outcomes are saved immutably. Nightly research compares issuer-nonoverlapping paired returns and repeats the historical replay. Missing future prices remain unknown. The sidecar cannot promote a policy, change alerts, allocate capital or send orders.

Results and trade ledgers are saved under outputs/backtest/firm-timing-2026-10-06. Future reports appear as timing-shadow.json and timing-history under the daily-adaptive GitHub artifact.
