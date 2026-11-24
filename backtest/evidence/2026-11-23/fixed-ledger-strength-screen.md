# Fixed-ledger strength screen H01 — 2026-11-23 CT

Research only. Registered code commit a8ee952c970a9a24b1a6fc353d5fc02f65890bee before first execution. Repaired feature extraction in commit 5b29bfa003b5c627b7f8eb1824aa48289de9f6f4 (blob 2e25ed6ff3dd9dafedbab91188106e21bdb41272); local executed source matched that Git blob exactly. The threshold remains fixed at observed predecision gain >=5%.

## Data-access repair
GitHub artifact connector downloaded original artifact 11378995592 (run 37386241124) and completed hosted replay artifact 14691551088 (run 44864565861), directly into the executing filesystem without GitHub DNS/checkout. ZIP SHA256 values matched server digests: a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e and 95f916cdc1d988f752a49f14c38852c1f9876c5ddfd535bb915c19f840ea1ba1. Existing hosted run had already reproduced original 54 variants and all three published seasons. Future lab should consume this verified checkpoint, not restart archive discovery. Archive ends Dec 5 2025 and is not a fresh holdout.

First diagnostic had 39/55 base trade rows lacking explicit strength feature (78 across base/stress). Derived missing features from archived decision price divided by preceding archived raw close, no current closing price used in feature. Explicit values cross-checked. Second local execution classified all 111 base/stress rows: 78 derived, 33 explicit, zero unknown. Corporate-action/official-close and SMG eligibility verification remain incomplete. Reproduce:
`python -m backtest.obsidian_fixed_ledger_strength_screen --signals original.zip --hosted hosted.zip --out results.json`
Final local results JSON SHA256: 610632993f20789130685d69a329fdd7508fa476dd71ec241c2b3253858734ea.

## Actual rerun results
Fixed original trade ledger, no capital reallocation, no cash interest, no new entries or changed exits. Net trade P&L, not ending equity. Base/stress rows share underlying signals and are not independent.
| Year | Cost case | Baseline trade P&L | Retained P&L | Excluded P&L | Baseline/retained/excluded counts |
|---|---|---:|---:|---:|---|
|2023|base|18475.90|18475.90|0|3/3/0|
|2023|stress|16306.18|16306.18|0|3/3/0|
|2024|base|38922.47|32245.49|6676.98|16/7/9|
|2024|stress|25113.64|27486.45|-2372.81|16/7/9|
|2025|base|103112.45|65339.16|37773.29|36/22/14|
|2025|stress|63903.49|41287.19|22616.30|37/23/14|

Retained P&L per summed entry notional increased from 5.859% to 11.393% in 2024 base and 8.589% to 9.684% in 2025 base, but dollar profits declined and the largest loss was unchanged in both years. 2024 stress improves from 25113.64 to 27486.45; 2025 stress deteriorates from 63903.49 to 41287.19. Reject as universal entry rule; no promotion, no threshold retuning on same sample. Next experiment should isolate adverse exposure/squeeze management with full chronological allocation replay, not repeatedly re-run this diagnostic. Existing frozen source/production/alerts unchanged.
