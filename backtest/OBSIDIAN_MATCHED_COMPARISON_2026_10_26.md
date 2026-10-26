# OBSIDIAN matched early-weakness diagnostic — 2026-10-26

**Research branch only:** `research/obsidian-early-rug-20261025`. Validation: [GitHub Actions run 40256403008](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40256403008), success. Reproducible output: artifact `obsidian-matched-comparison-40256403008`. Six unit tests passed.

## Frozen comparison

Paired policy A: previously discovered hybrid signals, restricted to independently recovered timely five-minute windows and a raw prior/current price >$3. Paired policy B: identical gates plus **observed decision-time price <= 98% of prior raw close**. No parameter optimization or re-ranking by future outcomes. Both use the same 3-session modeled exit, 30-bps-per-side/10%-annual-borrow base and 100-bps-per-side/100%-annual-borrow stress, $30,000 nominal position target, $150,000 buying-power assumption and risk controls. Same-day close is a proxy fill, **not an observed executable fill**.

**Crucial:** `net_profit` includes modeled cash interest. The table reports **realized closed-trade P&L**, which excludes that interest. A positive cash-only balance is not trading alpha.

| Year | Existing hybrid base / stress trade P&L | Fixed early weakness base / stress trade P&L | Existing / early closed trades | Early matched signals |
|---|---:|---:|---:|---:|
| 2023 | +$13,596.55 / +$9,494.77 | $0 / $0 | 6 / 0 | 0 of 7 |
| 2024 | -$11,063.22 / -$27,758.99 | -$3,001.32 / -$9,821.97 | 32 / 13 | 15 of 48 |
| 2025 | +$74,987.91 / +$36,293.04 | +$4,576.91 / -$6,178.82 | 56 / 19 | 24 of 90 |

Base-case maximum observed drawdowns (existing vs early): 2023 8.842% vs 0%; 2024 32.694% vs 23.718%; 2025 14.629% vs 9.2%. Stress-case drawdowns: 2023 10.623% vs 0%; 2024 43.672% vs 26.954%; 2025 20.03% vs 12.056%.

## Interpretation and mandatory caveats

The fixed -2% early-weakness challenger **has not demonstrated an edge**. It reduces 2024 modeled losses but removes most 2023 and 2025 simulated winning opportunity. In 2025 its modeled closed-trade P&L becomes negative under stress costs. Do **not** promote it or select a new threshold based on these inspected years.

The original 4,731 candidate windows have all been checked; 2,472 returned timely provider bars, 2,259 were empty or stale, and no original per-ticker gap identity is available. The 145 baseline hybrid signals here are **not** a complete eligible-market denominator. Coverage censoring and selection bias remain, including the possibility that hard-to-borrow, halted, illiquid or volatile stocks are disproportionately absent.

The original 2023–2025 outcomes have been repeatedly inspected, so these are **not untouched chronological out-of-sample years**. Historical SMG market capitalization, security type, borrow/locates, actual closing fills, margin, corporate actions and exact slippage are not independently verified. All dollar figures are hypothetical model outputs, **not actual or reliably executable returns**. There is no defensible basis to assert positive after-cost risk-adjusted performance.

## Next independent research gate

Freeze the baseline and candidate policy before collecting a **genuinely later, independently screened and timestamped** set of prospective sessions. Preserve every screened candidate and unknown eligibility/borrow case, not only triggered signals. Reconcile each missing bar to its exact issuer/day when evidence exists, use explicit no-trade for unknown eligibility, and evaluate signal precision/recall, borrow/SMG executable coverage, cash benchmark, modeled and actual fill slippage, adverse squeezes and drawdowns. Require sufficient independent issuers and sessions before any promotion. No production, live alert, credential, or trading changes.
