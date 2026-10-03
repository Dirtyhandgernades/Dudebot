# Game coverage and risk repair — October 2, 2026

The measured $189,510.63 loss came from a conditional simulation, not a verified loss in the user’s account. The failed firm timing policy remains disabled for qualified live trade alerts. The new experiment has not met the 70% detection or $70k/$89k profit targets.

## What failed and what was repaired

- The prior frozen 248-symbol cohort stopped firm discovery before later-2025 IPOs. Independent name searches now extend through December 5, with each symbol admitted only after dated firm evidence. No friend or reference tickers enter selection.
- Common signed auditor opinions, underwriting tables and issuer-counsel clauses were missed. The parser now recognizes those attached roles, including standard audit opinions saying an internal-control audit was “not required.” Counsel for the underwriter is not automatically issuer counsel.
- An HTTP 500 could pin a query cursor; missing provider symbols could crash the outcome audit. Queries now split/resume and label failures; missing bars stay unavailable rather than becoming zero-price outcomes.
- Cache/checkpoint saves now survive failed jobs. Source review prioritizes one issuer before repeatedly reviewing another. Code pushes validate cached sources; manual runs can gather a bounded new batch.
- Research share orders use prior-close information, falling equity reduces buying power, and intended position sizes are capped at 25% of prior equity. Stop/take-profit requests execute at the next close, not at a guaranteed stop price.
- Comparisons distinguish genuinely absent discoveries from dated hard exclusions and unresolved classification. A later ticker trade is not counted as an entry before the friend’s trade.
- The latest cache optimization stores completed per-symbol, per-period/feed/adjustment data. Expanding a universe fetches new symbols without invalidating old symbols; failed pagination cannot become a complete cache. This changes request reuse, not the price/simulation rules.

## Completed replay and assumptions

[Final hosted validation, run 37081288053](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37081288053) completed successfully. It follows a bounded 1,200-document gather in [run 37081094825](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37081094825). The final run read no new SEC documents and reviewed 1,520 cached filings; the corrected parser changed the symbol set and required 46 market-data requests under the old batch cache. Per-symbol cache reuse is the subsequent tested optimization.

Artifact SHA-256: `ea39144f596b47ffb4193eed235d9186394928793257df067b4e3561d52616f2`.

Each period runs September 8–December 5, starting at $100,000 with assumed total buying power of $150,000. Fixed research policies use a $30,000 intended target, limited by prior equity/capital, minimum ten whole shares, and up to three sessions. Signals use completed prior bars; fills and requested exits use the next close. Base costs are 30bps each way plus $5/order and assumed 10% annual borrow. Historical borrow, market cap, halts, SMG availability, actual game fees and margin liquidation remain unverified. These are conditional price-proxy results, not executable returns.

| Period | Breakdown timing net P&L | Near-peak exhaustion net P&L | Exhaustion trades |
| --- | ---: | ---: | ---: |
| 2023 | $3,458.66 | $31,498.69 | 12 |
| 2024 | $-36,574.18 | $-17,707.11 | 37 |
| 2025 | $-9,337.67 | $49,504.00 | 49 |

The 2025 exhaustion account ends at $149,504.00, with 63.27% winning trades and 12.125% observed drawdown. Its largest winner, MSGY, contributes $21,443.10 (43.3% of net profit). It still loses in 2024, so it is research-only. No tested repaired account became insolvent; that does not establish margin safety.

The exhaustion hypothesis requires a prior 21-session rise of at least 12%, a close within 20% of the recent high, less than a 10% decline that day, at least 1.5× trailing volume, at least 8% daily range and an upper wick at least 35% of the range. These fixed thresholds were declared before this experiment; they are not calibrated probabilities.

Under the fixed stress assumptions of 100bps each way and 100% annual borrow, exhaustion makes $15,718.20 in 2025 and loses $34,597.47 in 2024. Costs materially change the conclusion.

Actual 2025 exhaustion entry notionals range from $3,258.64 to $39,440.52. A share order sized at the prior close can exceed its intended dollar cap after a gap; the simulator does not pretend to know the future closing price when sizing.

## Detection, missed entries and reference checks

| Metric | Breakdown timing | Exhaustion research |
| --- | ---: | ---: |
| Friend tickers watched before an entry | 13/60 | 13/60 |
| Friend tickers with any modeled trade | 6/60 | 3/60 |
| Tickers entered same day or 1–2 sessions before friend | 2/60 | 1/60 |
| Large-drop events with a prior 1–5-session signal | 22/92 | 7/92 |
| Large-drop events with a position open BEFORE the drop day | 5/92 | 3/92 |

The 70% target requires 42 of 60 friend tickers. Independent qualified firm-watch coverage is 13/60 (21.7%), not 70%. Of the remainder, 42 have no dated matched-source record in this reviewed corpus, three have earlier evidence but unresolved issuer classification, and two have dated hard exclusions. A match or friend entry does not establish fraud, a future drop, or eligibility.

Breakdown trade overlaps: ANPA, ASST, HUHU, MFH, MTEN and NUKK; entries align with the friend on ASST and MFH. Exhaustion overlaps: ANPA, MAGH and NVFY; only MAGH has an aligned entry. “Aligned” means the same date or one/two sessions earlier, not proof of the same fill or profit.

The 92 large-drop events are independently measured at least 20% one-session close declines in the discovered firm corpus with a prior raw close above $3. Consecutive drops are deduplicated. This is not whole-market recall. The 5,833 missing symbol-day outcomes include unlisted/pre-IPO/inactive periods and unknown missing data; they are not all provider failures or all misses.

The supplied reference CSV has 230 events across 137 tickers, with zero event dates inside this game. Post-selection ticker overlaps are saved separately; this replay cannot claim pre-drop detection of those earlier events.

### The user’s named examples

- XHLD and WCT have independent dated firm evidence (February 18 and January 17, 2025 respectively), but all 64 game closes are below $3. Their 2026 examples need their own dated replay; the 2025 game cannot establish those detections.
- DTCK generated an exhaustion signal November 6, 2025. The planned November 7 close was $1.41; it was rejected by the price rule. A completed daily-bar signal can arrive too late for the end-of-day game order. Testing a pre-close intraday decision is necessary to establish an earlier feasible entry.
- MCTR is independently discovered but below $3 throughout this game. MCTA and TJGC have no eligible dated symbol record in this reviewed corpus; their identity/date gaps remain unresolved. No guessed MCTA-to-MCTR mapping is made.

## Confidence and remaining work

The separate class-balanced ranking model’s validation threshold is 0.847; its 2024 target precision is 18.5% and repeatedly inspected 2025 precision is 30.5%. Its scores are ranks, not confidence percentages. Overlapping samples are correlated; 2025 is no longer a fresh holdout.

1. Resolve historical issuer symbol/exchange and dated operating-versus-acquisition classification from filing evidence. There are 882 unresolved identity documents and 3,759 unread selected documents. The search index being complete for configured names does not make the market universe complete.
2. Add verified, dated corporate-name mappings. For example, [D. Boral’s announcement](https://dboralcapital.com/news/ef-hutton-llc-announce-rebranding-to-d-boral-capital-llc/) documents EF Hutton LLC’s November 8, 2024 rebranding. This mapping is not yet implemented; similarly named firms must not be merged blindly.
3. Test pre-close decisions using only bars available under the 16-minute delay, with point-in-time firm evidence and both winners and non-dumps. Compare true order timing, false positives, squeeze losses, recall and costs on new periods, not only the inspected 2025 winners.
4. Keep saving daily borrow observations prospectively. No historical borrow observation exists for the 248 breakdown or 73 exhaustion signal events in this test; executable counts are zero and unavailable counts are 248/73. Current borrow cannot be substituted for 2025 borrow or SMG permission.
5. Calibrate any percentage on later validation data before using it for sizing. None of the current experiments justifies a high-confidence rug label, guaranteed daily trades or promotion of the failed policy.

[Alpaca’s aggregation rules](https://docs.alpaca.markets/us/docs/market-data-faq) say extended-hours T/U trades do not update daily open/close prices, though they may update volume. Daily close remains a price proxy rather than verification of the exact SMG pricing feed; daily RVOL can include volume that minute-price rules treat differently.

## Validation and reproducibility

- Final independent hosted replay succeeded; local Python suite: 206 passed. The added tests cover dated exclusion reporting, universe-growth cache reuse, separate query contracts and failure during pagination.
- Source/reference/friend selection remains separate. Full ledgers, source audit, friend comparison, ranking diagnostics and cost stress are under `outputs/backtest/game-firm-37081288053`.
- Offline comparison: `python -m smg.game_comparison --report-folder outputs/backtest/game-firm-37081288053 --friend-transactions outputs/friend-2025/transactions.csv --baseline-decisions outputs/backtest/source-replay-35415517622/decisions.json`.
- This report does not certify production delivery, executable historical profit, all bugs fixed, or the 70%/$189k targets achieved. Firm watches continue as research; the failed firm trading qualification remains disabled.
