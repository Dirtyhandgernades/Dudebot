# OBSIDIAN Research Engineering — 2026-10-30 12:47 CT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only; no main, production, credentials, orders, trading notifications, historical baseline, frozen denominator, 136-name watchlist or JDZG stale/halt failure modification.

## Authorized original intraday research source triggers

The existing same-day 12:47 CT IEX INTRADAY discovery and distinct independent halt/optional quote monitor marker files were absent at preflight. NYSE/Nasdaq calendars identify October 30 as a regular session, and the separate authenticated 12:20 Rug Proof anchor (run 41097562159, artifact 12995764777) observed the broker market clock open at 12:17:53 CT. These are **not** evidence of the later engineering source outcome.

Created the original one-time `backtest/OBSIDIAN_IEX_RESEARCH_DISCOVERY_TRIGGER_2026_10_30_INTRADAY.md` and the separate `backtest/OBSIDIAN_INDEPENDENT_MONITOR_TRIGGER_2026_10_30_INTRADAY.md` in commit `07905ee89864b2f9033a7794555d685ea7fc5a79` with expected-head lease `08c37446bcd9e9d5d2bca37d8ad3cd2274d1cc59`. No same-day morning, after-hours, Early Board, protected preclose, Rug Proof anchor or delayed SIP marker was created.

Original hosted workflows were observed **queued**, not successful, at this verification point:
- IEX early discovery: [run 41102112881](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41102112881).
- Independent Nasdaq Trader halt / optional Massive monitor: [run 41102112887](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41102112887).

**Do not retry or backfill** these original captures if runners fail or finish outside the original gate. Later checkpoints may inspect the original run outcomes and immutable artifacts only. The Rug Proof 12:20 intraday anchor and Morning Movers have distinct issuer/session evidence and must not be double counted.

## Outstanding evidence and scoring restrictions

No new independently authenticated official completed regular-session closes, exchange source contracts, corporate-action/security-ID continuity, provider-organization independence, full source/conflict inventory, or Massive realtime entitlement was established in this pass. IEX is a single venue, not consolidated SIP/NBBO. Nasdaq Trader RSS can evidence a reported halt, but absent RSS records do not prove a security is trading or SMG-shortable. Missing and ambiguous outcomes remain censored. No 20%+ prospective prediction success or profitability established.

Forward evaluation remains 0/+1/+2/+3 **actual trading sessions**, matched untouched future cohorts, original frozen labels/denominators, false positives, late/exhausted signals, squeezes, costs and missingness. No platform short approval or orders.

## Subsequent hosted job-log and artifact verification (same original attempts)

The original two hosted **job logs**, retrieved after initial queue-state observation, show the capture/validation steps completed and uploaded artifacts. The GitHub run-summary endpoint still returned a stale `queued` / null-conclusion snapshot at this check, so do **not** substitute this for a verified top-level workflow conclusion.

- **Original IEX discovery** [run 41102112881](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41102112881): 11 offline tests `OK`. Hosted runner reported `VERIFIED_WRITE_ONCE_IEX_RESEARCH_ONLY`, phase `INTRADAY`, **8,510** attempted unique ticker rows and **1,290 indicative early/intermediate** observations (1,252 early 2–15%, 38 intermediate 15–25%), **7 exhausted**, **4,918 stale/future IEX prints**, 8 missing snapshots, 99 missing trade/prior bar, 27 previous IEX days unverified, 361 floor blocked, 1,800 other. The nine mutually exclusive status counts sum to 8,510. Original uploaded artifact **12997544415**, ZIP 1,724,891 bytes, metadata/upload-log SHA-256 `c5279f39dadb7f328178d6ea9b364bb89bcb39a73f62e27185ab586855f1afc1`, expires 2027-01-28. Artifact ZIP bytes were **not** independently downloaded/rehashed in this engineering pass. Indicative labels are **not** 1,290 verified future predictions.
- **Independent Nasdaq Trader halt / optional Massive monitor** [run 41102112887](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41102112887): 21 offline tests `OK`. Hosted runner reported `NASDAQ_RSS_PARSED_WITH_ASOF_LIMITATIONS`, 136 watchlist symbols, `quotes_connected=false`, `realtime_entitlement_verified=false`; the dedicated `OBSIDIAN_MASSIVE_API_KEY` environment variable was empty in the hosted job. Original uploaded artifact **12998407667**, ZIP 2,275 bytes, metadata/upload-log SHA-256 `77036dc55fc7387e5b17da4c384c54675ec713426bcaa6ab8d97acdff9d7ba76`, expires 2027-01-28. Raw ZIP contents were not independently rehashed. This is **not** an independently verified quote, official close, or proof of no halt.

These are distinct one-time original 12:47 phase observations, **not** a retry/backfill or a new 20%+ collapse success. The separate Rug Proof 12:20 anchor remains independent research evidence and must not be double-counted. Next checkpoint should inspect the eventual top-level run conclusions and, if authorized and available, independently verify artifact bytes; never re-trigger the original phase.

## Independent downloaded ZIP and source-row verification

Downloaded both **original** GitHub Actions artifacts without re-triggering any workflow, computed local ZIP SHA-256 and compared it to GitHub artifact metadata and runner upload logs. All matched:

- IEX ZIP `c5279f39dadb7f328178d6ea9b364bb89bcb39a73f62e27185ab586855f1afc1`; ZIP entries `manifest.json`, `attention.json`, `universe.jsonl`. Rehashed `universe.jsonl` against manifest SHA-256 `e7cdcabf4ea8b386aec714bd5fe85fb747e0962b87bc9420bff1d50ddbc15285` and `attention.json` against `5cc8a4a4f8780a9e97c02888dc4f3ed5b6a960aa709ec90510b6a3ebfe91b1f4`; both matched. Independently parsed **8,510 JSONL rows / 8,510 unique tickers**; manifest reports 86 batches, observation 2026-10-30T17:52:44.649659Z–17:52:53.547745Z. Its `trading_session_independently_confirmed=false`, so this remains an authenticated one-venue source observation, not verified official exchange session close or full-market universe.
- Independent monitor ZIP `77036dc55fc7387e5b17da4c384c54675ec713426bcaa6ab8d97acdff9d7ba76`; parsed JSON entry SHA-256 `0d81b776987eeba568873e6fbb210802dc1a04b5d978219f11200f6e5ed16127`. Exactly **136** watchlist rows, all **136 independent Massive quotes unavailable**. Official Nasdaq Trader RSS receipt SHA-256 `d8e991c0d9195ca659e7b313970dc0c8206f17cca1ee41694267a1b6a965d6bc`, `NASDAQ_RSS_PARSED_WITH_ASOF_LIMITATIONS` at 2026-10-30T17:52:42.691807Z. Four retained watchlist names had official RSS event records: **TJGC** (T12 halt timestamp 2026-10-14 19:50 ET, no verified resume, `HALT_REPORTED_CHECK_EXCHANGE_BEFORE_TRADING`); **AIOK** (LUDP 2026-10-30 09:45:57 ET, reported resumption 09:50:57 ET); **WFF** and **WHLR** (T3 events 2026-10-29 19:50 ET, reported resumption 2026-10-30 09:00 ET). A past resumption timestamp is **not** current live tradability proof. **JDZG** had no event in this received RSS subset, which is **not** proof that JDZG is unhalted or that its stale/venue coverage issue is resolved.

This verification closes **artifact byte-integrity** for these two new captures, not source completeness, independent quote access, SMG permissions, or prediction accuracy. **TJGC remains a reported halt requiring direct live exchange recheck before any trading consideration**; no order, trading notification, or alert was generated. The original captures remain immutable and distinct from Rug Proof. Do not duplicate them.
