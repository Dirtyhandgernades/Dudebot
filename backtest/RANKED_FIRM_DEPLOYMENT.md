# Ranked firm strategy deployment — October 6, 2026

The earlier broad daily-return candidates did not fix the weak year. They were rejected. I selected the ranked **pre-close firm exhaustion** policy because it was profitable in all three tested seasons in normal costs, a full higher-cost portfolio replay, and higher costs on identical base trades. Its worst observed stressed drawdown was below 25%. This is approval for gated advisory alerts, not automatic orders or calibrated percentage confidence.

## Final replay

The corrected four-checkpoint study is [run 37516775704](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37516775704). Earlier and pre-close decisions use the same independently discovered firm universe and preceding daily ranking features. Inputs and actual five-minute bars are cut off 16 minutes before each decision. No reference/friend ticker or future decline selects a signal. All tested checkpoint policies remain in the artifact, including the ones that failed.

| Season | Selected pre-close profit | Ending balance | Full cost stress profit | Trades | Base / stress drawdown |
|---|---:|---:|---:|---:|---:|
| 2023 | $3,373.47 | $103,373.47 | $2,179.15 | 2 | 0.17% / 0.43% |
| 2024 | $40,180.81 | $140,180.81 | $27,004.55 | 18 | 17.20% / 20.60% |
| 2025 | $75,549.15 | $175,549.15 | $35,622.07 | 44 | 17.42% / 22.92% |

Identical-base-trade cost-only stress: $2,013.13 / $26,287.92 / $46,192.38. That diagnostic excludes different stressed cash-interest and buying-power paths. Fees are $5 each order plus modeled 30 bps each side and 10% annual borrow in the base; full stress uses 100 bps each side and 100% annual borrow. These borrow/slippage rates are sensitivity assumptions, not certified SMG costs. The supplied rules summary confirms $5 each trade, 0.75% positive-cash interest and 7% negative-cash interest. SEC's Section 31 fee was zero during the 2025 game period. [SEC advisory](https://www.sec.gov/rules-regulations/fee-rate-advisories/2025-2).

Historical cap, halt, actual borrow and complete SMG membership are not verified throughout the corpus; these profits remain conditional. 2023's two trades are a small sample. All years have been inspected repeatedly, so this is not an untouched holdout or a promise of consistent $90k profits.

## What runs on the bot

`config/ranked_firm_alerts.json` enables the independent ranked layer from **October 7, 2026**. It learns the seven daily price/volume ranking features on 4,013 earlier observations, including 457 target declines; the latest matured training label is December 5, 2025. The frozen training-median rank threshold is 0.43827250876096624. That number is a rank, not a 43.8% probability.

`smg.ranked_firm --prepare` downloads preceding complete provider daily bars in batches, stores one rolling cache and prioritizes the existing bounded firm shortlist. This matches the historical ranking input basis and avoids making every firm download 150 days of minute data merely to rank it.

`smg.ranked_firm --send` evaluates actual delayed five-minute candles for the independent firm candidates. Current or prior-day exhaustion can form a watch. Source-dated historical auditor/underwriter/counsel associations remain eligible watch evidence; they are not misrepresented as proven current engagement or fraud. Existing source freshness, security classification, exchange, acquisition and five-letter exclusions remain enforced. The supplied SMG excluded symbols remain hard.

Forming watches can be sent during the session, once per ticker/day, without mentions. They explicitly say they are research watches and not qualified short entries. Qualified short-entry alerts require the tested pre-close timing window plus price >$3, current sourced cap >=$25M, a fresh clear halt check, current executable Alpaca borrow indication, valid common equity and fresh deliberately delayed SIP data. A continuing unqualified setup cannot be promoted merely to create a daily trade.

Qualified messages share the existing durable ticker/side/phase claims with other lanes. Claims are committed before Discord; ambiguous sends are not retried. The layer does not place orders. It preserves the original failed daily-breakdown proxy's disabled setting; it does not reactivate that different strategy by flipping its flag.

Sizing remains a research reference: $50k target bounded by 30% observed decision equity, with a 20% pre-order price reserve. No confidence-driven leverage is enabled. The game backtest enters at the day's close from a genuinely earlier timestamped signal, holds at most three sessions, and acts on a previous close's stop/target at the following close. A fill that exceeds a target is reported rather than retrospectively cancelled.

## Corrections and learning

The first entry of each day was tested at 11 a.m., 1 p.m., 3 p.m. and twenty minutes before close Eastern, adjusting for half days. Earlier entry and deferred-entry variants failed the 2024 cost check; the $96,848.19 best 2025 early variant was **not** chosen because its 2024 stressed result lost money. Watches remain available early; qualified entry timing follows the strategy that passed the multi-year cost check.

Additional corrections: aligned split-adjusted share volume and VWAP as well as prices across ticker renames; share volume is rescaled inversely to price so dollar turnover remains comparable. Borrow and halt archive observations are timestamped when received, not optimistically at request start. No old missing inventory has been invented. [Alpaca split adjustment definition](https://docs.alpaca.markets/us/reference/stockbars).

`smg.action_learning` is installed in the nightly review workflow. It labels the actual delayed stop/target policy return, profitability and large losses, rather than rewarding every eventual 20% dump as a successful trade. The historical diagnostic found 34 dump hits that the delayed exit policy would lose. Proposed return and risk models remain research-only; they are not automatically swapped into the running alert model.

The two observation bases are kept separate: original regular-session minute forecasts and the ranked layer's completed-provider-daily inputs. Watch and qualified observations are immutable; no future label changes their earlier features or action. Unknown outcome prices stay unknown. The learner performs no new provider requests and cannot send messages or orders.

The original frozen experiment is now `firm-shadow-2026-10-07-v4`, preserving its weights and archived v1–v3 definitions. The new ranked alert policy is a separate contract and does not silently change those forecast weights. Both receive future outcome review. Source fingerprints prevent unnoticed implementation/config changes after publication.

Reproduction artifacts: `outputs/intraday-checkpoints-37516775704` and `outputs/action-policy-37502827341`. Rejected return/core models are also retained in `outputs/backtest/action-policy-2026-10-06` and `outputs/backtest/firm-core-2026-10-06`. No tested losing policy is hidden or relabeled as profitable.
