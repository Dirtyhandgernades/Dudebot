# Why earlier paper profits were higher

The earlier $75,549.15 2025 result was reproduced exactly with current simulator
code, its archived dated signal set and original price packet. It was not the
same experiment as the recent bounded eight-year or matched-candle tests.
Forty-eight controlled portfolios were rerun without provider requests. They
use the same twenty-minute preclose checkpoint, three-session maximum, closing
fills, stop/target execution, $100k start, $150k buying power and costs.

| 2025 input / training | Larger research sizing | Current bounded sizing | Bounded stress |
|---|---:|---:|---:|
| Original / expanding | $75,549.15 | $7,328.97 | $3,837.14 |
| Original / trailing two years | $72,151.15 | $6,062.44 | $2,762.08 |
| First balanced expansion / trailing two years | $29,040.32 | $3,408.07 | $12.58 |
| Eight-year expansion / trailing two years | $19,976.41 | $3,494.65 | -$730.72 |

These are conditional seasonal paper profits, including cash interest, not live
account returns. Unprotected sizing remains research-only. It targets $50k,
bounded by 30% decision equity and a quote-price reserve. The current shared
exposure envelope caps proposed positions at 10% equity and a modeled 2%
adverse-move budget, with a five-session range estimate and gross-exposure cap.
It can allocate substantially less to extreme-range stocks. Closing fills and
squeezes can exceed the modeled loss budget; no loss is clipped.

Changing only sizing on the original expanding data reduces 2025 profit by
$68,220.18. Changing only the original training lookback reduces unprotected
profit by $3,398.00. Broadening the first data set at the same two-year lookback
reduces unprotected profit by $43,110.83. These are separate controlled paths,
not additive independent causes; corpus changes alter sources, price history,
prior training and selected entry dates together. The full JSON preserves every
year, cost case and cell, along with input and signal hashes.

The larger original result also drops to $35,622.07 under higher assumed costs.
Original 2023 had only two trades and $3,373.47 base profit. The original study
therefore never established a consistent $70k seasonal outcome across years.
Restoring its larger quantities would increase both profits and squeeze losses;
it would not repair the entry signal.

The recent matched-candle study uses fifteen-minute and five-minute checkpoints
and a different training basis. Its $4,389 one-session 2025 result must not be
presented as an apples-to-apples replacement of the $75,549 archived result.
Current research has not silently replaced the running incumbent model.

## Improvement now being collected

The matched-candle learner previously had only 35/36 independent prior examples
for its 2025 models; earlier years could not meet its training minimum. A bounded
collector now gathers April–June delayed checkpoints from 2018–2024 using the
same source-dated firm discovery, prior-year rank and deliberately delayed
five-minute candles. No friend/reference ticker or later dump selects a stock.

Daily collection has a twenty-new-page total budget and a small equal per-year
quota. It caches complete individual raw/split symbol pairs, reads completed
pairs without further requests, and preserves partial pages for later runs.
Uncompleted pairs are unavailable, never an invented empty price series or a
successful zero-trade period. The manual audit can opt into the same bounded
collection; its default remains fully cached and requires no provider calls.

Spring samples are training-only. They must mature before the test year's
January 1 cutoff, use the same earlier two-year window, preserve held-issuer
exclusion and nonoverlapping outcomes, and never appear in the fall trade
ledger. Same-year spring samples cannot train that year's fall model. Both the
season-only and spring-expanded learners are retained for comparison; the fixed
thresholds, sizing and 1–3-session hold choices are unchanged.

The hosted daily workflow saves the added observations and reruns the unchanged
fall game tests. This addresses a measured training-coverage gap. It does not
establish that additional observations will improve returns, or authorize an
automatic allocation increase or model promotion. Live October 12 v3 contracts,
hard exclusions, current borrow/halt/cap gates and free Alpaca delay are preserved.
Historical borrow/cap/halts/game membership remain unknown. Longs remain
review-only, and all inspected-year results require fresh validation.
