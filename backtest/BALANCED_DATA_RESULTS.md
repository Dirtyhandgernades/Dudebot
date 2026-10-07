# Balanced data collection and season replay

The confirmed target is at least $70,000 net paper profit per SMG season, with each position held at most three trading sessions. The new data audit does **not** establish that target. The collection correction and hosted replay succeeded in [run 37565427552](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37565427552); 304 tests passed. The expanded corpus remains research-only.

## What changed

The previous collector searched new 2025 filings while relying on old cached evidence for earlier years. It now searches 2021–2025 with separate resumable cursors and equal new-document quotas. This run downloaded 40 documents per year, added 141 firm records, improved 74 independent first-source dates, expanded the discovered corpus from 515 to 540 symbols, and added 21,818 raw daily observations. No conflicting CIK identities or price-alignment gaps were reported. That does not certify every ticker mapping.

Existing minute queries were reused. The replay required 16 daily-price requests and 32 additional minute requests. The first attempt failed on a calendar bound; the corrected workflow covers the late-2020 warmup and preserves partial caches. No paid data or additional live strategy was enabled.

The search remains incomplete: 3,412 source documents were skipped for the download budget, 965 reviewed sources had unresolved symbol/exchange identity, and the 2021 search recorded a provider HTTP 500. There were 36/73/129 known-firm symbols without season prices in 2023/2024/2025; some were not yet listed or had renamed/delisted. Missing bars do not prove a data-download bug.

## Same two-year prior training window

Each model sees only labels matured before January 1 of its test year. Decisions use delayed prices available before the modeled closing entry; later prices evaluate outcomes only. The calendar window is September 8 through December 5 in each year, using actual trading sessions. References and the friend's transactions do not select candidates.

| Season | Preclose net profit | Ending balance | Closed paper trades | Higher-cost net | Base drawdown | Filled trades falling 20% within three sessions |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | $4,991.13 | $104,991.13 | 4 | $2,529.15 | 9.10% | 1 / 4 known outcomes |
| 2024 | $42,099.89 | $142,099.89 | 20 | $27,567.41 | 18.76% | 6 / 20 known outcomes |
| 2025 | $29,040.32 | $129,040.32 | 46 | $396.75 | 36.19% | 7 / 45 known outcomes |

One 2025 three-session price outcome was unavailable. Historical borrow availability was unknown for all 4/33/63 modeled detected entry attempts; zero were certified executable. These are conditional simulations, not brokerage/game orders. Historical cap, halt and complete game-security eligibility also remain unverified.

The account starts at $100,000 with modeled $150,000 buying power. Target size is $50,000, constrained by 30% of decision equity and a 20% decision-price reserve; exact integer shares are computed before the closing fill. Actual fill notional can exceed a decision target. Base costs are $5 per order, 30 bps each side and assumed 10% annual borrow; stress uses 100 bps each side and assumed 100% annual borrow. Those borrow costs are sensitivity assumptions. Paper results include cash interest.

## Timing and losses

Earlier signals are not consistently better. First-signal profits were $48,070.23 / -$9,970.65 / $12,814.05 across the three years, with higher-cost 2024 and 2025 losses. The preclose two-percent prior-gain filter produced $4,991.13 / $34,369.45 / $39,934.05. The nonpositive prior-gain filter produced $1,981.90 / $34,369.45 / $53,011.39. None reaches $70,000 in every year; neither can be selected from a favorable single season.

The expanded 2025 replay added a December 3 PLRZ short losing $35,582.01, and changed LAES to an October 6 entry losing $6,940.68. PLRZ's modeled stop used a prior close and filled at the following close, after an adverse price move. The simulator must retain that loss: a closing-price game cannot assume a continuously executable stop.

## Coverage versus lookback controls

[Run 37565738245](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37565738245) succeeded with all 304 tests and zero new market-data requests. It reproduced the original benchmark exactly, then changed the corpus and training lookback separately. Every policy/result is retained; these controls are not additional recipes selected for profit.

| Preclose corpus / lookback | 2023 net | 2024 net | 2025 net |
|---|---:|---:|---:|
| Original / expanding | $3,373.47 | $40,180.81 | $75,549.15 |
| Original / trailing two years | $3,373.47 | $40,180.81 | $72,151.15 |
| Expanded / expanding | $4,991.13 | $42,099.89 | $31,865.35 |
| Expanded / trailing two years | $4,991.13 | $42,099.89 | $29,040.32 |

The coverage/evidence change has the larger effect in 2025: at a fixed two-year lookback, profit decreases $43,110.83. Shortening the original lookback decreases it $3,398.00. The corpus change includes earlier dated firm evidence, added price history and its resulting training changes, so it does not isolate any single new record. The expanded result remains weak with either lookback. The old $75.5k result is reproducible, but it is fragile to a broader independently collected corpus and cannot establish consistent performance.

## Comparison with supplied stocks

The 2025 preclose ledger traded six of the friend's 60 distinct short-entry tickers: CCHH, DTCK, MAGH, NUTR, NVFY and PHOE. This is ticker overlap, not proof of matching his entry timing or profitability. Of the remaining symbols, 42 lack independently discovered firm evidence in this packet, 11 have no qualifying preclose signal, and one signaled without a paper fill. The categories do not imply all 60 belong to the user's firm strategy.

All 230 events in `reference_events.csv` fall outside this September–December 2025 season. They cannot be counted as seasonal misses or advance detections. Three tickers overlap earlier reference events, but later-season trades are not advance detection of those earlier events.

## Decision

Do not replace the pinned live training corpus, raise position sizes or advertise a reliable $70,000 outcome from these results. The user was partly right about inconsistent collection; the revised test also exposes adverse entries and sensitivity to training data. More complete discovery, independently recorded timing evidence, and loss-aware sizing need validation before promotion. The expanded candidate fails the existing 25% drawdown criterion in 2025.

Artifacts are under `outputs/balanced-research-37565427552`: source and coverage summaries, all tested policies, timestamped signals, full paper ledgers, and `balanced/trades.csv`, `balanced/friend-audit.json` and `balanced/reference-comparison.json` from the offline comparison. `outputs/balanced-research-37565738245/balanced/controls` contains the four controlled replays. All losing variants are retained.
