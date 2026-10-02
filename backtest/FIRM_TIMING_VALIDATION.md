# Firm timing validation — October 2, 2026

The revised firm timing policy failed validation. It must remain research-only;
firm association and a breakdown score are not calibrated probabilities of a rug.
The $70k profit / approximately $189k ending-equity targets were not met.

## Results

Source: [completed cached-data replay, run 37054630140](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37054630140).
Artifact: `game-period-outcomes-37054630140.zip`, SHA-256
`a84d1eead532d770d5d17bdf508a7246f51f5c9ef33827a94d4c33b0ef10559e`.
Reproduction inputs: `firm-timing-inputs.json.gz` from that artifact.

Each period runs September 8 through December 5, using market sessions only.
Initial capital is $100,000; initial buying power is modeled as $150,000;
target notional is $30,000 with whole shares and a ten-share minimum.
Buying power decreases with marked equity and unavailable marks block new entries.

| Period | Revised firm policy, 3 sessions | Revised firm policy, 1 session | Older adaptive policy |
| --- | ---: | ---: | ---: |
| 2023 | +$16,777.96 | +$11,218.52 | +$6,995.45 |
| 2024 | -$8,589.59 | -$37,144.37 | -$11,827.25 |
| 2025 | -$189,510.63 | -$21,117.41 | +$10,337.14 |

These are conditional modeled net P&L, not verified executable SMG results.
The 2025 three-session account becomes insolvent. Its theoretical ending
balance of -$89,510.63 describes modeled short liabilities with scheduled
exits, not a certified game balance: actual margin calls/liquidation rules
remain unknown. `financial_status` now labels insolvency explicitly.
The older policy's 2025 ending balance is $110,337.14, with 31 closed trades
and 25.25% maximum observed drawdown; its negative 2024 result prevents a
claim of robust profitability.

The revised 2025 policy closed 85 trades across 47 tickers, won 52.94% of
trades, and had nine gross returns of at least 20%. Those wins did not cover
the losses. SMX alone lost $167,915.33 on a $29,997 modeled entry from
December 2 to December 5. Other large losses were MFI ($24,244.97), ASST
($20,423.32) and SONN ($15,917.88). A structural breakdown signal did not
prevent a subsequent squeeze. Short losses can exceed entry notional.

The three-session 2025 size/cost checks also failed: $15k targets lost
$129,219.30; $50k targets lost $61,924.11; $30k targets with 100bps each-way
costs and 100% assumed annual borrow lost $87,587.06. Outcomes differ because
capital constraints change later entries. They do not justify choosing
larger positions by hindsight.

## Detection and coverage

The frozen 2025 independent filing cohort contains 248 symbols. Reference and
friend tickers never select this cohort or reach the simulation rules.
Comparisons are performed only after all runs complete.

- Four of the friend's 60 distinct short-entry tickers overlap modeled closed
  trades: ASST, MFH, MTEN and NUKK. This is ticker overlap, not replication of
  the friend's entry timing, sizing or profits.
- 52 friend short-entry tickers are outside the frozen cohort. This identifies
  a historical discovery gap; it does not prove that all 52 satisfy the hard
  eligibility rules. The replay source stops before later-2025 IPO discovery.
- DTCK, HUHU, NVFY and QMMM are in the cohort but have no closed trades.
  At the friend's short-entry dates, the revised daily rule produces no
  timing trigger (respectively two, two, one and two entry orders examined).
- Ten traded tickers overlap the user's reference list: HTCO, HTLM, MFH, MFI,
  PC, RAYA, SWIN, TWG, WOK and ZYBT. None of the 230 reference event dates are
  inside this game's period. This is not evidence of detecting those events
  before their drops; the earlier events require their own dated replay.
- The revised 2025 run records 155 symbol-day signals: zero verified
  executable, 155 historical borrow unavailable, zero verified borrow
  rejected. Zero verified executable does not mean all were unshortable.
- 2,136 incomplete-history records are symbol-day checks, not distinct stocks.

## Limits and repairs

Signals use only prior-session information and dated public firm evidence.
Entries occur at the following close; returns use split-adjusted bars while
the >$3 gates use raw prices. Daily 20-session volume ratios proxy the live
same-minute relative-volume calculation; this does not replay every intraday
alert. Positions target dollar notional at fill prices; exact pre-close SMG
share-order sizing has not been reconstructed.

Costs are assumed $5 per order plus 30bps each way and 10% annual borrow,
not verified game costs. Historical borrow, point-in-time capitalization,
halts, SMG security availability and margin liquidation remain unverified.
SWIN's documented October 10, 2025 rename to AXG now connects missing exit
bars, without inventing a delisting price. All positions in the final runs
have exit bars; this does not close the eligibility gaps.

2025 has been inspected repeatedly and is no longer an untouched holdout.
Do not claim training, calibrated confidence, guaranteed daily opportunities
or proven $70k profitability from these results.

## Production disposition and next work

`firm_timing_trade_alerts_enabled: false` keeps verified firm watches visible
in daily research embeds but stops this failed policy from qualifying trade
alerts. Hard exclusions, free delayed Alpaca data and current borrow checks
remain intact. Broad volatility alerts are separate; this report does not
establish that lane as a profitable substitute. Longs remain review-only.

Next work should rebuild independently discovered, date-indexed firm coverage
through the whole game, distinguish lead-time detection from post-drop
breakdowns, and test squeeze-aware exits/exposure under actual end-of-day
game mechanics. Validate any proposed rules on fresh periods with fees and
execution gaps before enabling alerts or increasing allocations. Prospective
miss reviews collect evidence; they do not automatically change trade rules.

Reproduce the nine saved simulations and comparison ledger without network:

```powershell
python -m smg.offline_firm_validation --inputs <artifact-folder>/firm-timing-inputs.json.gz --output <report-folder> --friend-transactions outputs/friend-2025/transactions.csv
```

The output includes per-run JSON, `results-summary.json`,
`list-comparison.json`, and `2025-firm-trades.csv` with entry/exit dates,
shares, sizes, net P&L, and comparison flags. Friend inputs and generated
private/raw outputs are not committed with this report.
