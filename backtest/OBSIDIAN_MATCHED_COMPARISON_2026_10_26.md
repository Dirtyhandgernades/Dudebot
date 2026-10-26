# OBSIDIAN matched early-weakness diagnostic — 2026-10-26

> **Revalidated corrected diagnostic:** [GitHub Actions run #28 (40260569154)](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40260569154) completed successfully at 2026-10-26 02:45 UTC on commit `ed73111e8e0eade2bdc6901a0e4957023814f926`; all six matched-comparison unit tests passed and the paired-diagnostic artifact was uploaded. Commit `462d5fd66b9a24fe23c6fb5fbbcf6e772bd07b65` removed the future full-session-close >$3 pre-close selection gate; the regression test now crosses the final close below $3. **The corrected run produced exactly the same reported historical signal counts, realized trade P&L and drawdowns as run #26**, so the table below remains numerically unchanged. This does NOT demonstrate executable performance, genuine OOS edge, or absence of other selection biases.

**Research branch only:** `research/obsidian-early-rug-20261025`. Corrected validation: [GitHub Actions run #28](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40260569154), success; artifact `obsidian-matched-comparison-40260569154` (artifact ID `12623914069`). Six unit tests passed. Earlier [run #26](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40256403008) used the flawed future-close gate; its figures happen to agree with the corrected run but should not be the canonical evidence.

## Frozen comparison

Paired policy A: previously discovered hybrid signals, restricted to independently recovered timely five-minute windows, with **decision-time price >$3 and previous-session raw close >$3**. The same-day raw/split daily bars remain required to compute modeled outcomes, creating coverage-conditional selection; they are **not** permitted to gate on their future closing price. Paired policy B: identical gates plus **observed decision-time price <= 98% of prior raw close**. No parameter optimization or re-ranking by future outcomes. Both use the same 3-session modeled exit, 30-bps-per-side/10%-annual-borrow base and 100-bps-per-side/100%-annual-borrow stress, $30,000 nominal position target, $150,000 buying-power assumption and risk controls. Same-day close is a proxy fill, **not an observed executable fill**.

**Crucial:** `net_profit` includes modeled cash interest. The table reports **realized closed-trade P&L**, which excludes that interest. A positive cash-only balance is not trading alpha.

| Year | Existing hybrid base / stress trade P&L | Fixed early weakness base / stress trade P&L | Existing / early closed trades | Early matched signals |
|---|---:|---:|---:|---:|
| 2023 | +$13,596.55 / +$9,494.77 | $0 / $0 | 6 / 0 | 0 of 7 |
| 2024 | -$11,063.22 / -$27,758.99 | -$3,001.32 / -$9,821.97 | 32 / 13 | 15 of 48 |
| 2025 | +$74,987.91 / +$36,293.04 | +$4,576.91 / -$6,178.82 | 56 / 19 | 24 of 90 |

Base-case maximum observed drawdowns (existing vs early): 2023 8.842% vs 0%; 2024 32.694% vs 23.718%; 2025 14.629% vs 9.2%. Stress-case drawdowns: 2023 10.623% vs 0%; 2024 43.672% vs 26.954%; 2025 20.03% vs 12.056%.

## Interpretation and mandatory caveats

The corrected run leaves all 145 matched baseline signals and 39 early-weakness signals unchanged (7/48/90 baseline and 0/15/24 early by year). The fixed -2% early-weakness challenger **has not demonstrated an edge**. It reduces 2024 modeled losses but removes most 2023 and 2025 simulated winning opportunity. In 2025 its modeled closed-trade P&L becomes negative under stress costs. Do **not** promote it or select a new threshold based on these inspected years.

The original 4,731 candidate windows have all been checked; 2,472 returned timely provider bars, 2,259 were empty or stale, and no original per-ticker gap identity is available. The 145 baseline hybrid signals here are **not** a complete eligible-market denominator. Coverage censoring and selection bias remain, including the possibility that hard-to-borrow, halted, illiquid or volatile stocks are disproportionately absent.

The original 2023–2025 outcomes have been repeatedly inspected, so these are **not untouched chronological out-of-sample years**. Historical SMG market capitalization, security type, borrow/locates, actual closing fills, margin, corporate actions and exact slippage are not independently verified. All dollar figures are hypothetical model outputs, **not actual or reliably executable returns**. There is no defensible basis to assert positive after-cost risk-adjusted performance.

## Next independent research gate

Freeze the baseline and candidate policy before collecting a **genuinely later, independently screened and timestamped** set of prospective sessions. Preserve every screened candidate and unknown eligibility/borrow case, not only triggered signals. Reconcile each missing bar to its exact issuer/day when evidence exists, use explicit no-trade for unknown eligibility, and evaluate signal precision/recall, borrow/SMG executable coverage, cash benchmark, modeled and actual fill slippage, adverse squeezes and drawdowns. Require sufficient independent issuers and sessions before any promotion. No production, live alert, credential, or trading changes.
