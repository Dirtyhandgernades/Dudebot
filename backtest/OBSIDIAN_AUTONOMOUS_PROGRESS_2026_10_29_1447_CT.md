# OBSIDIAN Research Engineering — October 29, 2026, protected 14:47 CT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch `research/obsidian-early-rug-20261025` only. No main/production, secrets, orders, live alerts, historical frozen labels, or external SMG account actions.

## Authorized single attempt and independently verified source receipt

- Preflight: `backtest/OBSIDIAN_IEX_PROSPECTIVE_TRIGGER_2026_10_29.md` absent; separate Oct29 Rug Proof morning/intraday anchors, 14:20 delayed-SIP marker, Morning Movers, Early Decision Board, and engineering 12:47 intraday discovery marker already present. No duplicate markers or captures created for those owners.
- Calendar: official NYSE/Nasdaq 2026 holiday schedules show Thursday October 29 as a normal open session, not a holiday/early close; 09:30–16:00 ET. https://www.nyse.com/trade/hours-calendars ; https://www.nasdaq.com/market-activity/stock-market-holiday-schedule .
- Original one-time preclose marker created with expected-head GitHub lease from `9181a20494c64b0e4e4cb1c0fc2769c0e86a8225` to `98d332f53b76f154a0548d606782a7b7db8a87c9`, at the authorized 14:47 CT checkpoint. No retry/backfill.
- Hosted workflow [40943205148](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40943205148), on commit `98d332f53b76f154a0548d606782a7b7db8a87c9`, completed **success**. Hosted gate explicitly printed `IEX prospective gate: OPEN`.
- Original immutable GitHub Actions artifact ID **12928470853**, name `obsidian-iex-prospective-40943205148`, 90-day retention. Downloaded and independently inspected the actual ZIP containing `manifest.json` and `universe.jsonl`; computed SHA256 of original `universe.jsonl` matches manifest `72b22c4c7e846045ab80c29c382a965a46cf484bb2f7a2dc01dff2bc1f351556`. Exactly **8,502 JSONL rows, 8,502 unique tickers**, and status counts sum to 8,502.
- Manifest recorded 2026-10-29 19:47:25.236380+00:00 start, 19:47:32.788313+00:00 finish; feed `iex`, Alpaca single venue, **not** SIP, NBBO, or official closing auction.

| Original immutable status | Count |
| --- | ---: |
| IEX_EARLY_WEAKNESS_WATCH_ONLY | 689 |
| IEX_EXHAUSTED_PRICE_ONLY | 14 |
| IEX_NO_EARLY_PRICE_ONLY_WATCH | 3,246 |
| MISSING_SNAPSHOT | 5 |
| MISSING_TRADE_OR_PREVIOUS_BAR | 100 |
| STALE_OR_FUTURE_IEX_TRADE | 4,396 |
| UNVERIFIED_PREVIOUS_IEX_SESSION | 52 |
| **Total** | **8,502** |

## Strict outcome limitations

- 689 is **price-only watch count**, not independently catalyst-verified A predictions, executable SMG short opportunities, or realized outcomes. 14 exhausted are not early catches.
- 4,396 stale/future IEX prints, 52 unverified previous-session bars, and 105 missing snapshot/bar cases are preserved as separate missingness/quality classes, not silently filled.
- The separate 14:20 Rug Proof delayed SIP run [40939489402](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40939489402) had its own original 8,502-symbol denominator and 5,665 historical SIP bars fresh at delayed as-of, 975 stale, 1,862 missing; it is a different time/source checkpoint and **not another independent issuer/day prediction**. No double counting.
- Independent monitor run [40939694009](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40939694009) parsed Nasdaq halt RSS with as-of limitations, `quotes_connected=false`, `realtime_entitlement_verified=false`; not an independent official closing-price source.
- Still **zero independently authenticated 20%+ forward prediction successes**. Exact official regular-session close receipts from two genuinely independent source organizations, security ID, adjustment parity, exchange calendar, complete source/conflict inventory, and +0/+1/+2/+3 actual-session outcomes remain unavailable/censored. No success-rate inference from vendor daily OHLC or IEX reference.
- Durable backup beyond 90-day GitHub Actions retention remains **BACKUP_UNVERIFIED**; artifact hash/ID and original denominator preserved here but this note is not raw evidence archival.
- Original frozen 136-name baseline, JDZG stale/halt case, same-cohort comparison, false positives, squeezes, and costs remain unchanged.

Next highest-value research gate remains P0-1 independent authenticated official-close provenance. Do not promote any current capture to verified official outcome.
