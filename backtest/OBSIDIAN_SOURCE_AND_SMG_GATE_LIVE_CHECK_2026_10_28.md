# OBSIDIAN — official halt + independent quote + SMG gate + task routing verification, 2026-10-28

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only. This checkpoint does **not** certify a future 20%+ collapse prediction, market-wide independent real-time quotes, SMG shortability or a trading order.

## Implemented, verified
- Generic read-only independent-source monitor `backtest/obsidian_independent_quote_halt.py`: at most one official Nasdaq Trader RSS GET and, **only if a separate eligible subscription/key exists**, one Massive snapshot GET per dated research checkpoint; keep every retained original ticker and exact received timestamp, feed SHA, halt/resumption as-of time, and absent/stale quote status. No automatic key enrollment or trading.
- Synthetic CI: first attempt had misdated checkpoint fixture inside original protected preclose window and failed. Corrected under commit `d4913f45452017e65f4c2b43be264bb49f1432d2`. Hosted full offline CI `40803017831` **SUCCESS: 388 tests passed**.
- Single bounded real after-hours research-only monitor run **40803217669**, artifact **12867066489**, **SUCCESS**, original requested **136 retained tickers**. Source as-of `2026-10-29T01:54:43.983822Z` / October 28 20:54:43 Chicago time. Official Nasdaq Trader RSS HTTPS GET returned 200 and XML parsed; no source-fetch error. This validated Nasdaq feed access in the runner, **not** guaranteed continuous/minute-resolution surveillance.
- Original JDZG Oct 28 four trade pauses were reported in the actual RSS downloaded after close. The latest JDZG event was recorded with halt `15:40:32.350 ET` and resumption `16:00 ET`, therefore **already ended at the as-of 20:54 CT observation**; not a newly predicted halt. Historical source: https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts ; guidelines: https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS .
- The **Massive independent price provider was not connected** (`quote_source_connected:false`); `realtime_plan_entitlement_verified:false`. No real-time independent trades or quotes were obtained. The adapter rejects missing, stale/delayed/future-dated prints and does not infer real-time license access. Full-market Stocks Advanced access depends on separately authorized API subscription: https://massive.com/docs/rest/stocks/snapshots/full-market-snapshot .
- SMG public-rule fail-closed `backtest/obsidian_smg_readonly_gate.py` tests $25m cap, $3 on preceding/current session, >=10 share order, exchange, halt, issuer stock class, independently sourced cap/share count, account margin permission, blocked-symbol and security-table presence. This offline module **NEVER authenticates a connected Stock Market Game account** or calls a trade. Public rules: https://views.smgww.org/rotg.html and blocked-symbol UI https://www.stockmarketgame.org/enter-trade_b.html . No SMG tab was available in the connected user's currently open browser tabs at this check; actual platform shortability remains **UNVERIFIED**, and Alpaca `shortable` metadata is not an SMG decision.
- Existing separate Alpaca delayed historical SIP probe **40801276955** returned **5,409 fresh-with-respect-to-17-minute-as-of** / **1,215 stale** / **1,887 unavailable** for original 8,511 capture members; although useful consolidated retrospective evidence, this is **not a real-time independently sourced quote** and not an official closing outcome.

## Automated research tasks (all in current chat ID `6ae01179-4654-83ea-9816-12d5402ebfd1`)
1. Central Engineering `6ae2a70c24388191b83245b1f2673079` hourly :47 CT.
2. Morning Movers `6ae2a72de6b88191a617a8984f825b3a` weekdays 05:12–11:12 CT.
3. After-Hours Audit `6ae2a73004b48191a02458ddcd71fb2e` weekdays 15:22–22:22 CT.
4. Early Decision Board `6ae2a730fb148191aada241cc2158642` weekdays 14:20 CT.
5. Pre-existing Rug Catch Proof `6ae2a48fd098819190694268187d0926` weekdays 09:20,12:20,14:20,18:20 CT.

All five task records were enabled, had current-chat destination ID, and schedule intact at final check. They contain non-duplication rules: Rug Proof alone owns same-day 14:20 delayed SIP marker, Early Board alone owns 14:20 independent vendor/official halt monitor marker, and other authenticated capture dates/clock windows remain separate. **Only the configuration is verified, not future message delivery until a scheduled run completes.**

## Still unproven / blocked
- **Predictive accuracy**: frozen same-day and +1/+2/+3 real-session studies and matched-cohort replays exist; zero independently accepted official close + unchanged-corporate-action source packets for the full captured universe. Do not replace null precision/recall with 0 or fictitious success. True untouched cohort evidence must accumulate over future trading days.
- **Independent real-time market-wide quote access**: eligible separate Massive price subscription/API secret (or an equivalently verified authorized provider) is not connected. Separate public official RSS is functioning for single-time research checkpoints, not real-time streaming. Do not silently add costs or store secret values in commits.
- **Actual SMG platform symbol/account eligibility**: needs read-only authenticated account view of Blocked Symbols, Security Table, game account short/margin/equity and exact decision timestamp; no login, order or borrow proof obtained.
- Automated tasks are configured to post to current conversation, but task executions have not yet proven actual delivery. New future runs verify this.
- No main, production, credentials, live alerts, market trades, orders or frozen evidence labels modified.
