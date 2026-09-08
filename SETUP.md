# Dudebot setup: exact secret names

Add these **four repository secrets** at [Settings → Secrets and variables → Actions → Secrets](https://github.com/Dirtyhandgernades/Dudebot/settings/secrets/actions), using **New repository secret** for each one.

| Exact secret name | Value to paste | Where to get it |
|---|---|---|
| `ALPACA_API_KEY` | Your Alpaca API key ID | [Alpaca dashboard](https://app.alpaca.markets/): generate API keys; a paper-account key pair can be used for market data |
| `ALPACA_SECRET_KEY` | The matching Alpaca secret key | Same generated key pair; copy the secret when it is shown |
| `SEC_USER_AGENT` | Your team label and real contact email, such as `DECA SMG Team your-real-email@example.com` | You write this value. Replace the example email with a real contact email. SEC does not issue an API key for these public endpoints. |
| `DISCORD_WEBHOOK_URL` | The complete incoming webhook URL for the desired Discord channel | Discord server → Server Settings → Integrations → Webhooks → New Webhook → choose channel → Copy Webhook URL |

**No `MASSIVE_API_KEY`, `ANTHROPIC_API_KEY`, or other AI key is needed.** You do not need to buy a market-data plan for the default delayed mode. Use both keys from the same Alpaca account/key pair. The program only requests market data and contains no order execution path.

The Discord account creating the webhook needs permission to manage webhooks. `@everyone` is requested once per digest; actual notifications depend on Discord server permissions and recipient settings. Do not paste real keys or webhook URLs into chat, code, issues, or screenshots.

## Repository variables

Open the separate [Variables tab](https://github.com/Dirtyhandgernades/Dudebot/settings/variables/actions) and choose **New repository variable**.

| Exact variable name | Value |
|---|---|
| `SMG_LIVE_ENABLED` | Lowercase `true` to enable scheduled discovery and market research. Leave unset or `false` until the secrets are added. |
| `DISCORD_ENABLED` | Lowercase `true` when ready to allow noon notifications. Leave `false` for report-only runs. |
| `SURGE_RETURN_MIN_PCT` | Optional positive numeric override of the configured 12% minimum for the trailing 21-session price gain, without a `%` sign. Leave unset to use 12%. |

The user clarified that gains from 12% through 23% inclusive remain eligible at low priority, with gains above 23% at normal priority. The existing window is 21 trading sessions. Do not set an old demonstration threshold such as 100 unless intentionally overriding this rule. Direct offerings retain their separate criteria.

GitHub supplies `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, and `GITHUB_ACTIONS` automatically. Do **not** create them manually. The workflows request `contents: write` for the separate `smg-state` branch. Repository or organization policies must allow that permission; check Settings → Actions → General → Workflow permissions when a state-write permission error occurs.

## Activate

1. Add the four secrets.
2. Run **Check setup (offline, no messages)** in [Actions](https://github.com/Dirtyhandgernades/Dudebot/actions). It reports which settings are present, without revealing values. This does not validate the keys against live providers.
3. Add the variables. Set `SMG_LIVE_ENABLED=true`; choose the surge threshold when ready. Keep `DISCORD_ENABLED=false` while checking research.
4. Run **Discover IPOs and direct offerings** manually. It reads public SEC filings and saves candidates without sending messages. Inspect its logs for source errors or a remaining backfill budget. Initial three-year discovery can require multiple runs.
5. Set `DISCORD_ENABLED=true` when ready for the daily digest. The noon workflow refuses out-of-window sends even when manually started. Leave the Discord variable false to inspect reports first.

The default target is **12:00 PST, fixed UTC−08:00 year-round (20:00 UTC)**. During daylight saving time this is **1 p.m. PDT**. To use noon local Pacific time instead, follow the two configuration changes in the README. Every alert clearly labels the **16-minute market-data delay**.

## Cost and operating limits

Filing parsing runs entirely in Python. Alpaca's free consolidated historical data is available once it is at least 15 minutes old; this bot requests a 16-minute delay. SEC and Nasdaq public feeds need no paid key. [Alpaca's access rules](https://docs.alpaca.markets/us/docs/market-data-faq)

Dudebot is currently public, so standard GitHub-hosted Actions runners are free under GitHub's current public-repository terms. Private repositories have included quotas and possible overages; changing visibility changes this cost assumption. No service can be promised free and available forever. GitHub schedules can be delayed or disabled, and third-party APIs can change. [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

With the supplied strict gate, late runs skip the ping. Data-source failures and unrecognized filing text produce review records or logged errors. They do not become fabricated qualifying matches.

References: [GitHub secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets), [Discord webhook setup](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks), [SEC contact header](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).
