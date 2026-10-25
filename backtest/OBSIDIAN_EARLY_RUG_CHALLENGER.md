# OBSIDIAN 2.1 — Early-rug challenger (research only)
Created 2026-10-25. Branch: research/obsidian-early-rug-20261025.

## Objective
Improve **prospective recall** of eligible stocks that fall >=20% from an executable closing short entry within the next 1, 2, or 3 NYSE sessions, while keeping positive after-cost, executable portfolio returns. Do not maximize recall at the expense of large short squeezes.

## Data and leakage contract
1. Use only issuer, SEC, daily bar, intraday, catalyst and borrow data whose observation/publication timestamp precedes the decision timestamp. Delayed SIP bars must be available with the existing 16-minute lag. Freeze features and model version at decision time.
2. Build the candidate universe from independently discovered securities, **not** from future biggest losers, the user reference-event CSV, or friend tickers. Those are audit labels only.
3. Exclude unsupported security types, five-letter tickers, SPACs, halts, unknown current cap/borrow/price, price <= $3, cap < $25M, and any game-ineligible symbols. Historical missing eligibility remains UNKNOWN, not eligible.
4. Preserve duplicate issuer/ticker/corporate-action boundaries and separate discovery from qualification. No use of later revised SEC facts as if previously published.
5. Run identical data availability and EOD execution assumptions for incumbent Dudebot, frozen Obsidian baseline, and challenger. If no frozen Obsidian baseline exists, label it a qualitative comparator, not a quantified one.

## Candidate lanes (predefined)
- EARLY: 2%–15% session decline; failed intraday reclaim / declining late-session VWAP; unusually high dollar turnover; independent fresh catalyst or filing. A firm relationship alone never qualifies.
- STRUCTURAL: documented offering, resale registration, financing, lockup, redemption or other supply overhang, plus bearish price confirmation.
- BROAD: liquid high-volume failed rally or bearish breakdown with no firm link, with stronger price confirmation.
- EXHAUSTED: >=25% already down; research only unless a separately timestamped new catalyst exists.
- REVERSAL: reclaim after failed breakdown; flag for short avoidance/cover, not automatic long promotion.

## Outcome definitions
- Decision: eligible pre-close observation, then next available executable EOD entry.
- Primary outcome: entry close to minimum **future closing** price in 1/2/3 sessions >=20% lower. No intraday low credit.
- Secondary: >=30%, >=40%, >=50% decline; any lower close; after-cost exit P&L; maximum adverse closing excursion; max portfolio drawdown; false positive rate; alert delivery status.
- Exit: existing fixed previous-close stop/target executed at following close, max 3 sessions, and game-end forced close. Never select exit based on best future low.
- Maintain separate counters for candidate watches, qualified alerts, Discord delivery receipts, executed SMG positions and paper simulations.

## Validation
- First reproduce existing 2023–2025 baselines from cached bundles and compare their published hashes/ledgers. These years are contaminated by repeated inspection: use for development only.
- Freeze candidate definitions, rank weights and thresholds BEFORE untouched forward dates. Report chronological, issuer-nonoverlapping prospective decisions with timestamped predictions and missing data.
- Evaluate recall denominator using independently screened *eligible universe* and count undetected dumps; report unknown eligibility separately. Precision denominator is every qualified short signal, not just winners.
- Compare incumbent vs challenger on matched candidate opportunities, same capital/risk/cost assumptions, both base and high-cost scenarios. Show uncertainty, per-year results and worst squeezes.
- Do not promote unless prospectively better on risk-adjusted profit and rug recall without unacceptable drawdown, across >=20 sessions and >=10 independent issuers; retain existing repository stricter promotion gates for any production change.
- Never auto-raise size, relax hard eligibility checks or turn on live alerts as part of this experiment.

## Required output
Produce dated CSV/JSON of each candidate with decision timestamp, source evidence timestamp, classification, frozen score, qualified/rejected reason, entry and exit closes, 1/2/3-session outcome, modeled P&L, and data gaps. Summary must show confusion counts, recall, precision, missed 20%+ eligible moves, after-cost equity curve and drawdown, compared to Dudebot incumbent.

## Execution status
Research specification only. No model retraining, replay, production promotion, live alert change, or verified Discord performance is implied by this file.
