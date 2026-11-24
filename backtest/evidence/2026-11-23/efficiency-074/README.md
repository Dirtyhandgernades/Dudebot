# Capital efficiency attribution

Computed from SQUEEZE-073 saved results. No new simulations, data downloads, threshold changes or strategy promotion.

| Season | Normal efficiency change | Stressed efficiency change | Stressed notional retained | Stressed trade profit retained |
|---|---:|---:|---:|---:|
| 2023 | +11.039 pp | +11.017 pp | 15.5% | 26.1% |
| 2024 | +3.688 pp | +3.409 pp | 10.0% | 18.6% |
| 2025 | −2.520 pp | −1.927 pp | 12.5% | 8.3% |

Efficiency is realized net trade profit divided by summed closed entry notionals. Capital is reused across trades, so this is not a portfolio equity return. Entry notional is recovered algebraically from the saved ratio and trade profit, with floating-point precision limits. Cash interest is excluded. Trade profit plus interest reconciled to net profit within two cents for all six rows. All saved marked-exposure series have zero missing sessions, which establishes internal completeness only.

The policy reduced allocated notional sharply. In 2023 and 2024 profits fell less than notional, improving this efficiency measure. In 2025 profits fell more than notional, worsening it under both costs. This does not support a universal capital-efficiency improvement. Composite exposure, cooldown and allocation changes remain inseparable here. Risk reduction remains supported on inspected development data; promotion criteria remain failed.

Reproduce from repository root with `python -m backtest.obsidian_capital_efficiency backtest/evidence/2026-11-23/squeeze-073/results.json NEW_OUTPUT.json`.

Next task is a cached trade-level attribution of the 2025 policy package: save original and bounded closed-trade ledgers from the existing batch runner only if absent, then reconcile matched, omitted and changed-size trades. Register the attribution before collecting these additional outputs. Do not retune parameters or repeat the rejected strength filter.
