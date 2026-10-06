# October 6 repairs and timing comparison

The verified engineering faults are repaired and tested. The new models are **not** consistently profitable across years, and historical execution evidence remains incomplete. No research model has been activated as a live trade or confidence-sizing policy.

## Repairs verified

- Firm-role features now exclude disclosures published after the decision close, including publications later on the same calendar day.
- Cached news pagination advances to older pages on subsequent runs. Earlier archived articles survive changes to ticker batch boundaries. Failed requests count against the budget; creation and revision cutoffs remain enforced.
- Missing future bars retain the observable earlier candidate with an unavailable outcome. They no longer silently remove that candidate from the decision population.
- Daily-bar features enter at the **next** exchange-session close; the intervening gap cannot be claimed as short profit. Training labels must mature before the chronological fold cutoff. CIKs, where resolved, keep renamed issuers on the same held-out side and prevent overlapping calibration windows under different tickers.
- BREA became SLMT on October 3, 2025. Dated continuity now values outstanding BREA positions using the same security's subsequent prices, retains history for new SLMT decisions, and stops screening the expired BREA identity. SWIN/AXG is handled too. Separate provider split units are aligned without smoothing the actual return. No IPO-age reset or retrospective new-ticker selection is allowed. [Issuer announcement, October 2 at 9 a.m. EDT](https://www.nasdaq.com/press-release/brera-holdings-plc-nasdaq-brea-announces-new-ticker-symbol-slmt-reflecting-its).
- Current borrow gates require actual boolean `true` values and reject known inactive, non-equity or unapproved-exchange assets. Unknown historical borrow is not inferred from current flags. Alpaca's new `borrow_status` remains the supported field. [Alpaca schema change](https://docs.alpaca.markets/us/changelog/2026-06-05-borrow-status-6b96a5a).
- Shares are sized before the fill with a fixed 20% price reserve in the new study and forward paper profiles. A closing-price overshoot is reported, **not** retrospectively cancelled by a strategy target. Actual modeled buying-power rejection remains separate. End-of-day stop signals cannot guarantee a 12% maximum loss.
- Two earlier live jobs failed with GitHub HTTP 403. The 16 MB state database now uses one raw-file restore rather than metadata plus Base64 blob retrieval; later commands in the serialized same workflow reuse only an identical, successfully checkpointed local file. Every write retains its remote SHA guard. Unchanged files skip redundant writes. Short provider-signaled rate delays can retry GETs; permission errors, long limits and mutations are not blindly retried. The earlier 403 subcause was not captured, so this is not a guarantee against every future GitHub outage. [GitHub raw-content support](https://docs.github.com/en/rest/repos/contents), [rate-limit behavior](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

All **265 tests passed**. CI [37496712776](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37496712776) and repaired live scan/archive [37496712779](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37496712779) succeeded. The latter archived 134 available asset indications and one unavailable indication, with no reported archive failures. These are current broker indications, not historical locates or certified SMG membership.

Discord practice [37497135644](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37497135644) succeeded: receipt `SENT`, `embed-v1`, message `1557069379341123708`, no mentions and explicitly no trade recommendation.

## Wider independent data

Hosted data run [37495259370](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37495259370) succeeded: 623 audit symbols, 515 independent firm identities, 6,728 measured closing-collapse episodes, 5,740 stock-linked news records and 57 symbols without provider histories. Those are not fraud findings, unique news articles or a complete exchange universe. Four price requests and the capped 40 news requests were made in that resumed run.

The final local timing replay uses that run's `mechanism-audit/audit-inputs.json.gz` and the repaired code at `800b4ab`, plus the fixed-trade cost diagnostic. It contains 14,016 candidate observations across 317 symbols. Twenty-seven labels have unavailable entry/outcome data and remain visible; raw missing price windows and issuer-history gaps are counted separately. Reference and friend tickers never select these candidates.

Per-decision CSVs explain rank rejection, timing rejection, selection, unavailable outcomes and execution gaps. Per-portfolio JSONs include exact ticker, signal, entry and exit dates, shares, notional, fees, returns and losses. Local final directory: `outputs/backtest/repair-final-37495259370`.

## Actual conditional comparison

Each game uses September 8–December 5, $100,000 initial capital, assumed $150,000 gross buying power, a $50,000 position target bounded by 30% of observed decision equity, a 20% pre-order price reserve and a three-session maximum planned holding period. A 12% loss or 20% profit observed at the previous close requests an exit at the next close. Base costs are $5 each order, 30 basis points each side and assumed 10% annual borrow. Fees, margin and borrow are research assumptions, not certified game execution.

| Model | 2023 net profit | 2024 net profit | 2025 net profit |
|---|---:|---:|---:|
| Core price rank | $34,527.74 | −$16,238.78 | $134,327.78 |
| Structure plus dated context | $37,305.62 | −$4,187.39 | $78,189.90 |
| Same context rank with cooling guard | −$2,612.00 | $12,687.91 | $15,062.31 |

All three predefined comparisons are disclosed. No policy was selected for deployment by its best year. Core price uses seven features; the context model adds wick, close location, peak age, volume trend, realized volatility, longer ramp and dated role/news indicators. The cooling guard additionally requires a prior-session return between −12% and +10% and a close in the lower 65% of its range. Ranks use unweighted regularized logistic fitting, past-only calibration and a fixed prior-training 90th-percentile threshold.

For the expanded context model, **higher costs applied to exactly the same base trades** produce $20,144.20 / −$41,702.65 / $31,426.23. This diagnostic assumes 100 basis points each side and 100% annual borrow; it is not a stressed buying-power replay. Separate full higher-cost portfolio replays change subsequent allocation and trades and can be nonmonotonic: their results are $20,503.45 / −$31,806.76 / $96,887.81. The last number is not evidence that expensive borrowing improves a strategy.

The expanded context model's selected nonoverlapping entry-window 20% hit rates are 29.41% / 16.67% / 30.16%. The target is measured after the next-close entry, so these percentages cannot be compared directly with the previous same-close watch-recall table. Held-issuer samples remain small. In particular, 2023 has only two held-issuer positive outcomes; the calibration/diversity gate fails. All dates have been inspected before and are retrospective diagnostics.

The 2025 expanded model took 79 conditional trades across 48 tickers. Seven traded tickers appear in the 137-ticker reference inventory: CLIK, ELWS, MFH, PMAX, QMMM, WETH, WOK. Eight appear in the 60-symbol friend short inventory: CCHH, DTCK, MAGH, MFH, NVFY, PHOE, QMMM, RYOJ. These are symbol overlaps, not matched-event recall or proof of the friend's entries being reproduced. DTCK's November 5 signal / November 6 entry contributed $30,381.18 net in this model. Largest 2024 losses include QUBT, TWG, ELWS and ATGL; the latter year's expanded-model drawdown reached 46.97%.

The strict historical-evidence ledgers take **zero trades**, finish at $100,000, and do not validate profit. Historical cap, security/SMG membership, halt and borrow evidence is missing. The new resolver accepts only dated, sourced facts known before the decision; a later failure cannot resurrect an earlier passing fact. The daily borrow archive keeps building actual observations going forward. Missing old inventory and borrow fees cannot be repaired by substituting today's availability.

## Live and remaining validation

Forward contract `firm-shadow-2026-10-07-v3` starts October 7. Original v1 and v2 files are preserved in `config/experiments`; the downloaded live state contained **zero forecasts** before this migration. Empty superseded contracts are reported explicitly. Populated changed contracts still fail verification rather than being silently rescored.

Forecast weights and threshold are unchanged. v3 fingerprints the execution/state repairs and freezes the paper sizing reserve. `live_trade_enabled` and `confidence_sizing_enabled` remain false; the candidate models above have separate blocking gates for cross-year losses, cost stress, missing execution evidence and fresh prospective validation. The first full three-session outcome for an October 7 forecast is October 12; it is not available today.

The remaining issues are **evidence and strategy validity**, not claimed resolved bugs: complete dated current/former firm engagements, historical float/cap/security/halts/borrow, missing price identities, full pre-event news, and reliable entry timing across regimes. There is no demonstrated 70% profitable-event capture or consistent $90k per-game return. The existing scheduled archive and outcome review continue collecting future evidence; they do not retune the live weights after every winner or loser.

Reproduce without provider calls:

```powershell
python -m backtest.repair_study --packet outputs/mechanism-audit-37495259370/mechanism-audit/audit-inputs.json.gz --out outputs/backtest/repair-final-37495259370
python -m pytest -q
```
