# Dudebot · DECA SMG notifier

A rules-based stock research notifier using GitHub for filing discovery, 15-minute market scans, and event-driven Discord delivery. The live default is the firm-first screen: listed underwriters, auditors and counsel lead the watchlist, including stocks that have not pumped and older IPOs. It uses public SEC filings, free delayed Alpaca data, and Discord source links. It never places orders.

The user's DECA gates apply to both profiles: **Nasdaq or NYSE common equity,
current price strictly above $3, and market cap at least $25 million**. Unknown
market cap suppresses eligibility. Current reported caps come from Nasdaq's free
public stock screener; the report records retrieval time because the source does
not publish a timestamp for each cap value. They are never reused for historical
decisions. Opening buy/short order planning uses a minimum of 10 shares; the bot
does not submit orders, simulate fees, or assert game-security-table availability.

The independently selected source replay is separate from targeted data-gap
diagnostics. `smg.source_replay` selects primary filings from the independent
firm-search corpus, watches discovered issuers daily through the window's end, and
reads the user's reference events only after screening. Checkpoints bound each run;
historical market cap, halt and complete context coverage remain unresolved.

The three hard exclusions remain halts/suspensions, acquisition corporations/SPACs,
and exactly-five-letter tickers. Unknown classification, stale prices or unknown
halt checks suppress alerts. Missing offering terms, low RVOL and an absent pump
are disclosed as preferences/data gaps. `screening_profile: strict` restores the
original transaction screen documented below. Direct offerings keep their own
relationships; an issuer-level historical underwriter is labeled in `FIRM_WATCH`.

Live deployment enables weekday discovery and 15-minute market/evidence scans by
default. Repository variables `SMG_LIVE_ENABLED=false` or `DISCORD_ENABLED=false`
stop the relevant GitHub jobs/uploads. To stop hosted delivery, run the
**Control hosted Dudebot delivery** workflow with `pause`; use `resume` to restart.
The legacy Cloudflare noon clock is paused. A deployment sends one durable,
mention-free activation receipt. Each newly qualified candidate/market phase is
claimed in durable state before one `@everyone` Discord alert. Continuing signals
do not repeat every 15 minutes, and no-match scans remain silent. The full historical replay remains incomplete.

**No Anthropic, OpenAI, Massive, or other paid AI service is required.** Filing extraction runs locally in Python. Alpaca's free historical consolidated SIP feed is used with a deliberate **16-minute delay**; every alert states the feed, timestamp, and delay. See [SETUP.md](SETUP.md) for the exact four secrets and activation steps.

This repository is public. GitHub currently includes standard hosted Actions runners for public repositories at no charge. This is a scheduled program with no credit balance to refill; continued operation depends on GitHub, Alpaca, SEC, and Discord availability and policies. It cannot promise indefinite service or exact wall-clock delivery. [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

For the pending three-year historical replay and the user's reference-event comparison, see [backtest/README.md](backtest/README.md) and [CODEX_HANDOFF.md](CODEX_HANDOFF.md). The full real backtest remains incomplete.

## Original strict screen (available as a separate profile)

The bot checks the filing criteria first, then obtains market confirmation. Missing or ambiguous required facts remain review records, rather than becoming qualified alerts.

| Rule | Implementation |
|---|---|
| IPO age | At most three calendar years; prioritize 30–100 days, then other IPOs within one year |
| IPO geography | China principal operations, supported by filing text |
| Direct-offering geography | Prefer operations outside the U.S./Canada; U.S./Canada remain eligible |
| Firm relationship | Any one listed underwriter/placement agent, auditor, or counsel; list categories determine priority |
| Offering size | $15M–$30M inclusive, base gross proceeds |
| Offering price | $4–$10 inclusive per traded share/ADS, not the current stock price |
| Exclusions | Current halts/suspensions; acquisition corporations/SPACs; every exactly-five-letter ticker independently |
| RVOL | At least 1.0 against comparable same-time historical volume |
| IPO surge | At least 12% over 21 trading sessions; 12%–23% inclusive is low priority, above 23% normal priority |
| Direct offerings | Separate research pipeline; no mandatory monthly surge by default |
| Notification | One durable alert when a candidate first enters a new qualified market phase; scans run every 15 minutes |

The source firm's category names are the user's screening labels. A list match does not establish fraud, manipulation, or a future price decline. Trading and reversal decisions remain the team's case-by-case decisions.

`config/entities.yaml` contains the supplied firm list. `config/strategy.yaml` holds the rules and explicit engineering defaults. The user clarified a 12% monthly floor with 12%–23% inclusive retained at low priority. Repository variable `SURGE_RETURN_MIN_PCT` can override the floor. A deliberately null threshold still produces `CONFIG_REQUIRED`; direct-offering review remains separate.

## Try it without credentials

From the repository root, using Python 3.11 or later:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]' -c requirements-tested.txt
python -m pytest -q
python -m smg.cli demo
python -m smg.cli doctor
```

Windows activation: `.venv\Scripts\activate`.

The demo uses fictional securities and an explicit demonstration-only 100% threshold. It writes the report and Discord preview under `reports/`, never sends a message, and does not change the real strategy. A sample is in [examples/synthetic-discord-preview.txt](examples/synthetic-discord-preview.txt).

## Free data and discovery

**Recent IPOs:** SEC quarterly indexes supply three years of `424B4` prospectus leads for current Nasdaq/NYSE issuers. SEC ticker/CIK mappings identify the issuer. Listing dates must be supported by explicit trading-date language in filings; filing date is never substituted for IPO date. A changed ticker does not reset the IPO clock. Ambiguous multiple-share-class mappings require review.

**Direct offerings:** A separate scan checks the past 30 days of prospectuses and `8-K`/`6-K` filings. A bounded current-filings Atom feed adds same-day leads; the nightly-updated index fills gaps from the bounded feed. Registered direct offerings must have their own offering terms. A shelf registration, ATM program, or direct exchange listing alone does not qualify. A historical IPO underwriter alone cannot qualify a later direct offering.

**Local extraction:** Python patterns look for an identified transaction, share/ADS price, gross proceeds, operating geography, trading date, security type, and listed-firm role. The parser saves exact source passages, filing dates, and document fingerprints. Where it computes gross proceeds as shares × price, it records the calculation. Bundled warrants, conflicting proceeds, missing fields, or unrecognized wording remain review items. Recent annual and event filings supply context. This avoids model costs, but it is not an exhaustive understanding of every filing format: omissions and complicated transactions can produce missed matches. Reports expose the evidence for team review.

Discovery is incremental, with per-run filing, parsing, and time budgets. Initial three-year backfill can take multiple runs. Pending jobs persist. This version is daily research, not continuous event monitoring.

**Alpaca:** Requests go only to its Market Data API, with `feed=sip`, `adjustment=split`, and an explicit end timestamp at least 16 minutes before the check. No account, trading, or order endpoints are called. Free SIP historical data must be at least 15 minutes old; the extra minute provides margin. Price freshness is evaluated relative to the declared delay. Halt checks use current time. [Alpaca data access](https://docs.alpaca.markets/us/docs/market-data-faq), [historical bars](https://docs.alpaca.markets/us/reference/stockbars)

An optional `iex` feed with zero delay can be configured in the strategy file. It covers IEX only, so its volumes are not consolidated full-market volumes. The default remains delayed SIP for consistent broader volume comparisons. No paid-plan fallback is attempted.

## Volume and price confirmation

- Monthly gain uses the current observed price versus the close 21 trading sessions earlier. Insufficient history cannot pass an invented monthly gain.
- RVOL compares regular-session cumulative volume with average volume through the same session minute over up to 60 prior sessions, with at least 20 usable sessions required.
- Historical short sessions that do not reach that minute are omitted. Entirely missing expected sessions are flagged. Partial minutes, future bars, duplicate bars, and premarket/after-hours bars are excluded.
- The 20-session RVOL is also shown for context. No additional unapproved 3× multiple is imposed.
- Alpaca split adjustment applies to price and volume. ADS-ratio or unresolved unit changes require review. Corporate-action changes not identified by available filings can still require human investigation.
- Nasdaq's current-day halt RSS is checked before confirmation. A quote-resumption time alone does not establish trading resumption. Unknown status, feed failure, or stale prices suppress qualification. Older suspensions absent from the current-day feed ordinarily fail the price-freshness gate; this public feed is not an exchange status guarantee.

## Event-driven delivery

The evidence workflow runs every 15 minutes across U.S. market hours in both daylight and standard time. It archives point-in-time market and borrow evidence, scans the stored SEC candidate pool, and sends immediately when a candidate enters a newly qualified phase. Holidays and closed sessions cannot qualify because the delayed market snapshot must be inside a valid exchange session.

Alerts use Discord embeds: one card per stock, matched firms, market context, timestamps and filing links. The first message requests `@everyone`; later cards do not repeat the mention. Practice checks have no mentions and are explicitly labeled as research checks.

The legacy [Cloudflare dispatcher](cloudflare/README.md) remains deployed for validation but its noon alarm is paused. GitHub owns event-driven scans and persists each signal claim on the `smg-state` branch before contacting Discord. GitHub schedules can start late, so “immediate” means the first successful scheduled scan after qualification rather than guaranteed wall-clock delivery.

The old noon workflow is manual-only. GitHub can delay or drop scheduled jobs, and public repository schedules may be disabled after 60 days without activity. [Schedule behavior](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule), [enabling workflows](https://docs.github.com/actions/managing-workflow-runs/disabling-and-enabling-a-workflow)

## Sending, reports, and state

Scheduled live jobs require `SMG_LIVE_ENABLED` not to be `false`. Discord additionally requires `DISCORD_ENABLED=true`. Without Discord enabled, scans generate reports only. No-match runs stay silent.

`reports/latest.json` contains evaluation results, reasons, and source evidence. `reports/discord-preview.txt` shows eligible alert text. Data access failures are recorded separately from market criteria that did not pass.

The `smg-state` branch stores a SQLite record through GitHub's Contents API with SHA-guarded writes. Workflows serialize state updates. The daily digest is durably claimed before its first Discord request. Uncertain or failed sends do not blindly retry the ping; delivery can be missed after an ambiguous failure. Source text cannot inject extra mentions. The first chunk explicitly allows `@everyone`, while later chunks do not. Discord permissions and recipient settings still govern notifications.

Continuing candidates can appear again on the next eligible day. Direct-offering agreement dates help group related filings; unresolved amendments may remain separate review records. Pending discovery work and normalized facts persist, while full downloaded filings are cached only within a run. A very large history may eventually need a different storage backend; that migration is not included.

## Commands

```bash
python -m smg.cli doctor       # Offline configuration presence check; never prints values.
python -m smg.cli demo         # Offline fictional examples; cannot send.
python -m smg.cli discover     # SEC discovery and local extraction; no Discord messages.
python -m smg.cli scan         # Market confirmation and report; no Discord messages.
python -m smg.cli alert --send # Send only newly qualified phases; durable duplicate suppression.
python -m smg.cli archive      # Append point-in-time price, borrow, halt and research evidence.
```

`.env` files are not automatically loaded. Use shell environment variables locally or the provided Actions workflows. Keep actual credentials out of the repository.

See [SETUP.md](SETUP.md) for activation and [VALIDATION.md](VALIDATION.md) for what has been tested. Authenticated Alpaca access, the user's SEC contact identity, and actual Discord delivery require the user's secrets for live verification.

Additional references: [SEC access and indexes](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data), [Nasdaq halt RSS](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS), [Discord webhooks](https://docs.discord.com/developers/resources/webhook).
