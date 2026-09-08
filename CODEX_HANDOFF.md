# Dudebot continuation handoff

## Continuation update, September 8, 2026

Development is pushed to `codex/historical-backtest`, draft PR #1. The latest
gap-resolution workflow is https://github.com/Dirtyhandgernades/Dudebot/actions/runs/34191049268.
100 offline tests pass. Initial Alpaca probes found bars for 180 events and empty
five-minute intervals for 50; `reference_gap_audit.json` records wider checks.
An empty five-minute probe is not proof of missing whole-session history.
SEC full-text HTTP 500 errors now split into smaller date ranges and preserve
checkpoints. All 27 SEC index quarters are collected; source review is incomplete.

`backtest/reviewed_firm_findings.json` verifies pre-drop IPO firm relationships for
RAYA and GDHG, covering five reference events. Their $12M and ~$7M base proceeds
fail the original strict IPO floor but are preferences under firm-first. These
source findings are not replay detections. Do not fabricate point-in-time filing
review or historical halt clearance. Actual screening replay remains incomplete.
The firm-first module is research/backtest only; production still uses the strict
entrypoint until explicitly integrated. No changes have been merged to main.

The later user clarification adds a separate firm-first research screen: one
verified listed underwriter/auditor/counsel is central; price, proceeds, geography,
IPO age, RVOL and pump status are preferences. The user explicitly reconfirmed
halts/suspensions, SPAC/acquisition corporations and five-letter tickers as hard
exclusions. Keep the original strict result alongside the firm-first comparison.
Wei, Wei & Co. has SUPER priority. Retain the existing counsel list. The supplied
message.txt exactly matches all 230 committed reference events.

The user clarified the surge threshold: retain 12%–23% gains at low priority.
The implementation now uses a 12% floor and a 23% inclusive low-priority ceiling
over the existing 21 trading sessions. This supersedes the unresolved threshold
statements below. The user also reported adding all repository secrets; provider
access must be checked by the bounded historical workflow, not assumed locally.

`smg.backtest` now collects independent SEC index leads and replays prepared
point-in-time research packets with event comparison. See `backtest/README.md`.
Full historical candidate construction, mapping, filing review and halt coverage
remain incomplete. No real detection rate or miss count is established. The
earlier handoff below remains the requirements record, not a current progress report.

Continue development of **Dirtyhandgernades/Dudebot**, a DECA Stock Market Game research notifier. The user asked to move the ongoing work into Codex after the initial implementation was published. Preserve the existing work and finish the historical backtest next.

## What the user wants next

> Backtest the bot across approximately three years of real, ordinary market history, then determine whether it found the stocks in the uploaded reference list before their listed drops.

The reference list is already committed at **`backtest/reference_events.csv`**: **230 dated events across 137 distinct tickers**, from **2024-01-03 through 2025-07-28**. Repeated symbols on different dates are intentional. The reported declines are user-supplied, unverified labels; the definition of their percentage measurement and intraday drop times was not supplied.

**No real historical replay has been implemented or run yet. No detection rate, hit count, profitability result, or claim that the bot found these events has been established.** At the handoff, `backtest/` contains the reference CSV only. The existing demo is fictional and the 59 tests verify software behavior, not investment performance.

## Published and verified

- Python notifier, free Alpaca market-data adapter, local SEC text parser, current Nasdaq halt checks, deterministic screening and ranking, evidence/rationale reports, and time-gated Discord digest.
- Independent IPO and direct-offering discovery pipelines.
- GitHub Actions for offline tests, setup checks, daily discovery, and noon delivery.
- State persistence on `smg-state`, with SHA-guarded writes and a durable claim before a Discord ping. Repeated or uncertain sends do not blindly retry.
- 59 offline tests passed locally. The published GitHub Actions run also succeeded: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/34186918206
- Verified source-code commit: `e751a4b6bd1277e3a715fed815f2ece442c5bff7` (subsequent commits add this handoff/documentation).
- No user credentials were available during development and no real Discord message was sent. Authenticated Alpaca access and live SEC/Discord integration still need smoke testing.
- The repo is public. Standard hosted GitHub Actions currently have no public-repository runner charge; do not promise all services remain free or available indefinitely.

Read `README.md`, `SETUP.md`, `VALIDATION.md`, `config/strategy.yaml`, and `config/entities.yaml` before changing behavior.

## User constraints to preserve

1. **Notification only.** No trading, order submission, account mutation, or automatic entry/exit logic.
2. **No paid AI or credit-based extraction.** No Anthropic/OpenAI/model API key and no hosted model calls in the running bot. The user chose free Alpaca after asking about Massive. Local Python rules and text parsing are the intended implementation.
3. **Separate IPO and direct-offering pipelines.** Find the qualifying transaction/issuer facts first, then apply market confirmation. Direct offerings must use their own transaction terms.
4. **Exclude halted/suspended stocks, acquisition corporations/SPACs, and every exactly-five-letter ticker independently.** A shorter ticker does not prove an issuer is not a SPAC. Do not weaken exclusions just to match reference examples.
5. **Recent IPOs:** maximum three calendar years old. Prioritize 30–100 days, then other IPOs within the past year. Original listing age must not reset with a ticker change.
6. **Any one** verified listed underwriter/placement agent, auditor, or counsel is sufficient. Categories in `entities.yaml` set priority. Historical IPO underwriter membership alone does not qualify a later direct offering.
7. **Offering price $4–$10 and base gross proceeds $15M–$30M, inclusive.** Original IPO terms for IPOs, separate transaction terms for direct offerings. Current share price is not the offering price. Share/ADS units and bundled warrants need correct treatment.
8. **RVOL at least 1.0.** Compare volume with recent months on a consistent basis. Stronger recent volume can affect context/ranking; no invented fixed 3× threshold. Current engineering implementation uses same-session-minute cumulative volume, up to 60 prior sessions, at least 20 usable sessions, and a 20-session comparison for context.
9. **Big monthly price surge for IPOs**, but the user has not supplied a numeric minimum. `surge_return_min_pct` remains null. `SURGE_RETURN_MIN_PCT` can override it. Do not silently use the demo's 100% threshold. Ask for the real number when required, or clearly label a separate sensitivity analysis without changing the production rule.
10. Reversal/exit decisions remain case by case. No requirement to wait for a reversal before recognizing a qualifying surge.
11. Discord integration requests `@everyone`, with rationale, metrics, timestamps, firm/category matches, and source links. Only send at the configured noon time, never from tests or historical replays.
12. The firm list is a research screen, not proof of wrongdoing or a guaranteed stock outcome. State matched facts directly without inventing future certainty.

## Working interpretations already visible to the user

These are the current code defaults, not grounds for silently adding new requirements:

- Nasdaq listing scope.
- China principal operations for the IPO pipeline. Direct offerings prefer operations outside the U.S./Canada but do not exclude U.S./Canadian operations.
- No three-year IPO-age restriction or mandatory monthly surge for the separate direct-offering pipeline.
- Trailing 21 trading sessions defines the monthly price-return window. Direct-offering backfill is 30 calendar days.
- Literal **12:00 PST, fixed UTC−08:00 year-round** (20:00 UTC), rather than a daylight-saving-adjusted Pacific clock. This is **1 p.m. PDT during summer**. The user said “12pm PST” but has not explicitly resolved the daylight-saving ambiguity. README explains switching to `America/Los_Angeles` and changing both cron entries.
- Free consolidated Alpaca SIP data is deliberately **16 minutes delayed**, stated in every alert. Free live IEX is single-exchange coverage and is not the default. Historical backtests should reproduce this configured delay and clock, rather than evaluate market-close data that would not yet have been available.
- GitHub schedules can be delayed or dropped. Sending is suppressed outside the configured noon minute; exact network delivery time is not guaranteed.

## Credentials and activation

The user said they would add secrets after publication. Check current setup rather than assuming they are still absent. Never ask them to paste secret values into the conversation.

| GitHub Actions secret | Value |
|---|---|
| `ALPACA_API_KEY` | Alpaca API key ID |
| `ALPACA_SECRET_KEY` | Matching Alpaca secret key |
| `SEC_USER_AGENT` | Team label plus real contact email; not an SEC-issued API key |
| `DISCORD_WEBHOOK_URL` | Incoming webhook URL for the chosen Discord channel |

Repository variables: `SMG_LIVE_ENABLED=true` enables scheduled live research; `DISCORD_ENABLED=true` enables noon pings; `SURGE_RETURN_MIN_PCT` supplies the still-unresolved monthly threshold. The two enable flags are initially unset/false. GitHub supplies `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, and `GITHUB_ACTIONS` automatically.

GitHub Actions secrets are consumed by workflows. Do not assume a separate Codex execution environment has their values. A dedicated backtest workflow can use the Alpaca/SEC secrets without exposing them. Backtesting must never require a Discord webhook or send notifications.

## Backtest work to implement

Build a reproducible historical replay, not a claim based solely on the supplied winners/losers or on synthetic tests.

1. Select and record an approximately three-year real-data window that includes every reference event. A reasonable proposed default is **2022-07-29 through 2025-07-28**, ending on the latest supplied event. This window has not yet been user-approved or executed. Include sufficient pre-window history for RVOL, monthly returns, and then-eligible older IPO prospectuses.
2. Construct a historical candidate universe independently of the supplied drop list. The current `Discovery` uses today's Nasdaq universe and latest filings; it cannot be reused unchanged as a point-in-time historical universe. Account for delisted/renamed issuers and historical exchange/CIK/share-class mappings. Report uncovered issuers and survivorship limitations explicitly.
3. Use only filing facts that were public by each simulated decision time. Prefer SEC acceptance timestamps; when only a filing date is available, a documented conservative next-day availability rule avoids same-day look-ahead. Never backfill a newly learned fact into earlier dates. Keep original IPO dates and offering terms distinct from later offerings.
4. Reuse the production rule engine and market calculations where appropriate. Replay only the permitted noon decisions and the declared 16-minute SIP delay. Handle holidays, early closes, splits, ADS ratios, missing bars, and ambiguous ticker histories.
5. Preserve the halt exclusion. **A current-day halt feed cannot verify historical status.** Nasdaq's public halt search exposes only the past year, which is insufficient for the whole requested period. Unknown historical status must remain unknown, never be fabricated as clear. Distinguish fully verified matches from matches that pass the other criteria but lack historical halt verification. Supporting historical halt records can be added with documented source/coverage.
6. Produce an event-by-event comparison with ticker/date, first prior alert date, lead time, pipeline, qualification evidence, rejection reason or missing-data reason. Do not count after-the-drop signals as advance detection. The reference has dates but no drop times, so same-day alerts cannot be assumed to precede the drop. A proposed analysis window is the preceding 20 trading sessions; label it as an evaluation parameter, not a new production rule.
7. Report event-level and distinct-symbol coverage separately, repeated alerts, unmatched reference events, extra alerts, and incomplete coverage. The list is not an exhaustive set of all market declines, so an extra alert is not automatically a false positive. Do not infer trading profit without defined entry/exit rules and costs.
8. Keep user-supplied drop percentages out of screening features and thresholds. Do not optimize the strategy to this labeled list and then present the fit as out-of-sample validation. A sensitivity table for unresolved thresholds must be clearly separate from the fixed-rule result.
9. Add meaningful tests for look-ahead prevention, timestamp/lag parity, reference matching, splits, delisted/renamed coverage, unknown halts, and missing-data reporting. Offline test success must remain separate from real replay results.
10. Add a bounded, resumable GitHub Actions backtest workflow with progress and downloadable reports. Large SEC/minute-data backfills need pagination, rate limits, caching, and persistent checkpoints. Use separate historical state so live notification/dedup state cannot be changed by the replay. Do not start an unbounded paid compute job or add a model dependency.
11. Run the real replay once the necessary provider access and numeric threshold are available, inspect failures, and deliver the actual comparison. Until then report **not run/incomplete**, not zero hits or a success percentage.

## Implementation review priorities

The initial implementation has passing tests but has not had authenticated integration validation. Review these concrete risks while adding history:

- Local extraction intentionally recognizes a limited set of filing phrases. Exact quote provenance is not proof of semantic correctness. Original-transaction scope, current versus historical roles, currency/ADS units, subsequent cancellations, and multiple offerings need stronger fixtures drawn from real public filings.
- Some historical IPO covers will not establish an actual first-trading date until a later filing. Do not substitute the prospectus date or treat a future announcement as already public.
- Current discovery can be incomplete while capped backfill is pending. Preserve backlog and expose coverage; do not label every unprocessed symbol a strategy rejection.
- Three-year full-market history is substantially larger than a targeted test on 137 symbols. Avoid claiming full-market coverage from a present-day universe or from only the reference set.
- The SQLite/GitHub Contents backend has finite file-size limits. Large bar histories should not be committed wholesale; choose bounded cached/derived records and a reproducible data manifest.
- Alpaca pagination is implemented. Historical `asof` symbol mapping and streaming/aggregation may be needed to avoid repeatedly downloading entire minute histories for each day.

## Local verification commands

```bash
python -m pip install -e '.[test]' -c requirements-tested.txt
python -m pytest -q
python -m smg.cli demo
python -m smg.cli doctor
```

`demo` and `doctor` require no credentials and do not send messages. Live discovery and scanning require the applicable secrets. Run from the repository root. `.env` is not automatically loaded.

## Technical sources already checked

- Alpaca historical data, free SIP lag, authentication, and symbol mapping: https://docs.alpaca.markets/us/docs/market-data-faq
- Alpaca bar parameters and split-adjusted price/volume: https://docs.alpaca.markets/us/reference/stockbars
- SEC public indexes and access: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- SEC APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Nasdaq halt search (past year): https://nasdaqtrader.com/Trader.aspx?id=TradingHaltSearch
- Nasdaq halt RSS: https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS
- GitHub Actions schedules: https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule

The original strategy PDF and a prior Word specification were supplied in the earlier chat, but are not required to locate the code or comparison list. The current repository configuration and this handoff preserve the implemented rules, remaining ambiguities, and next work. The earlier Word document described a superseded paid-extraction approach; do not reintroduce it.
