# Exposure limits — October 6, 2026

The change limits advisory size and overlapping recommendations. It does not promise a loss-free short or establish the $70k season target. The base firm ranking, current eligibility/borrow/halt gates, preclose entry policy and three-session horizon are unchanged. Timing changes that fail validation remain research-only.

## Changes running on the bot

All newly qualified short cards use a shared exposure envelope. For the explicit $100,000 paper account, the quoted order budget cannot exceed $10,000 per position, $60,000 across active recommendations, or a modeled $2,000 adverse-move budget. The adverse-move stress is the larger of 25% and twice the largest range/close in the preceding five completed sessions. Missing range history uses a 100% adverse-move stress. The stress is a sizing assumption, not a maximum possible price move.

Exact shares include the $5 entry fee, modeled entry friction and a 20% price reserve. Strength scores or a favorable historical probability cannot override these limits. The shared ledger spans firm and volatility discovery lanes, reserves capacity before Discord delivery, retains it after ambiguous delivery, and blocks another recommendation for the same ticker through the following three actual exchange sessions. It does not assume a weekend is a trading session or resurrect expired entries when the rolling calendar advances.

Reservations represent proposed paper exposure, **not connected SMG holdings or brokerage orders**. Release after the planned three-session horizon is an advisory planning convention; it does not verify that a human closed a position. Closing fills and subsequent squeezes can exceed the quoted exposure envelope. Actual holdings and account equity remain unknown. Discord cards say this explicitly.

The simulator has an optional versioned exposure policy. It sizes from prior data, limits aggregate decision-time exposure without spending anticipated exit proceeds, charges entry costs inside the budget, and imposes three sessions of cooldown after a stop signal. It preserves actual closing-price losses and reports fill overshoot. This cooldown is a historical paper simulation feature; no claim is made that the bot monitors or closes the user's actual game positions.

## Controlled tests

The offline study made zero provider requests. Original and expanded independently discovered corpora, all three seasons and both cost regimes are retained. No known loser or winner ticker is filtered. The first broader 22-session volatility envelope and the final five-session envelope are both saved; the five-session window reflects the current 1–3-session holding horizon and is not calibrated as a tail-loss bound. All tested timing variants, including failed ones, remain available.

| Expanded season | Unprotected net | Bounded net | Bounded higher-cost net | Base drawdown before / after |
|---|---:|---:|---:|---:|
| 2023 | $4,991.13 | $2,730.58 | $2,345.57 | 9.10% / 1.43% |
| 2024 | $42,099.89 | $4,706.87 | $3,296.15 | 18.76% / 2.07% |
| 2025 | $29,040.32 | $3,408.07 | $12.58 | 36.19% / 5.68% |

Original-corpus bounded profits are $432.27 / $5,601.23 / $7,328.97; higher-cost profits $331.94 / $4,257.14 / $3,837.14. Sparse 2023 and the nearly flat expanded 2025 stress case do not establish a strong edge. This is a risk reduction, not a claim of improved profit.

The expanded 2025 modeled PLRZ loss falls from $35,582.01 to $2,312.22; CCHH falls from $24,413.50 to $3,364.04. These changes come from smaller pre-entry quantities. No future closing price changes those quantities, and the resulting loss is never clipped to the $2,000 stress budget.

Requiring nonpositive current price change for prior-day patterns improves the bounded expanded 2025 result to $5,266.25 ($2,673.72 under higher costs), but produces **zero trades** in original 2023. It is not promoted. Reduced allocation also reduces wins; increasing leverage to recover the old advertised profit would undo the protection.

Historical borrow, caps, halts and complete SMG eligibility remain unknown. All results are conditional paper simulations. The code cannot invent unavailable historical inventory or guarantee a closing-price exit.

## Versioning and verification

Explicit contracts are `ranked-firm-2026-10-07-v6` and `firm-shadow-2026-10-07-v7`; the preceding contracts are archived. Their base model weights and first-session dates are preserved. Source hashes include `smg/exposure.py`. A staged adaptive model from an older source context cannot silently become active under this version.

310 offline tests pass, including unchanged hard gates, fees/capacity limits, cross-version reservations, weekends, ambiguous Discord sends, quote-based share sizing and uncapped closing losses. Reports and ledgers are in `outputs/backtest/exposure-2026-10-06-final`. This historical protection test uses fixed research targets; the Discord guide can allocate less for lower evidence strength and unknown account/range inputs. The two are not mislabeled as an exact executed-account replay.

Hosted verification on commit `61dff3e`: [CI 37567145742](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37567145742), [Cloudflare deployment 37567145739](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37567145739), [full evidence workflow 37567145796](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37567145796), and [existing swing regression 37567145875](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37567145875) all succeeded. [Practice 37567145829](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37567145829) succeeded with an actual `SENT` receipt: message `1557234726354423830`, channel `1546733107846324254`, at October 6, 2026, 10:34 p.m. America/Chicago. The two mention-free practice embeds show a watch and explicit sizing illustration, not a qualified live stock recommendation or an order. Archived local receipt: `outputs/exposure-verification-37567145829`.
