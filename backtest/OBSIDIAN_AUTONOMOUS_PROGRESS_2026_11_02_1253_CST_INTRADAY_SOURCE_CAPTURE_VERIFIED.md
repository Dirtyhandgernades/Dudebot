# OBSIDIAN Research Engineering — 2026-11-02 12:53 CST authenticated INTRADAY source checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Named branch `research/obsidian-early-rug-20261025` only. This note is a read-only engineering/source-integrity milestone, **not** a prediction, an order, an execution approval, a verified regular-session close, or a retrospective replacement for an absent capture.

## Original gate, deduplication and branch lease

- Independent clock observed `2026-11-02T12:52:42-06:00` within the original **12:40–13:15 CST** engineering INTRADAY window (nominal 12:47). November 2 is a scheduled regular NYSE/Nasdaq session (published 2026 calendars: https://www.nyse.com/trade/hours-calendars and https://www.nasdaq.com/market-activity/stock-market-holiday-schedule). This static calendar is not a fresh live-open attestation.
- Refreshed roadmap, source workflows, marker inventory, branch commits, recent Actions runs and the separate Rug Proof 12:20 original source verification. Rug Proof authenticated market open at `2026-11-02T12:17:12.740820-06:00` in independent run **41499091360**, artifact **13166549888**. That earlier source event remains separate and is **not** counted as a second future issuer/day outcome.
- Both original engineering November 2 INTRADAY marker paths returned GitHub **404** before creation. At expected research head `4ac103576af6fc30976d9ebd28bcc991dad28b22`, created exactly one each: `OBSIDIAN_IEX_RESEARCH_DISCOVERY_TRIGGER_2026_11_02_INTRADAY.md` and `OBSIDIAN_INDEPENDENT_MONITOR_TRIGGER_2026_11_02_INTRADAY.md`. Committed with a Git tree and **expected-head ref lease** to `bb034757f078fcf81b908be9748986b8974852d0`. Both new file blob hashes were independently read back.
- No MORNING, AFTERHOURS, 14:20 SIP, 14:45–14:58 protected preclose, or Early Decision Board marker was created. No rerun/backfill. No main, production, credentials, alerts, orders, or account-permission changes.

## Independently checked hosted results and bytes

**IEX single-venue discovery:** [GitHub Actions run 41504808713](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41504808713) completed **success** at the exact marker commit, with **11/11 offline discovery tests passed**, provider collection, local manifest verification and artifact upload successful. Artifact **13170527051**, `obsidian-iex-research-discovery-41504808713`, present/unexpired, expires **2027-01-31**, ZIP SHA-256 **5ecff9ce6a79c0ab76342d2f8feeb88277232a67fd1ae50b7f99787e5a91ac20**. Independently downloaded the ZIP; SHA-256 matched GitHub artifact metadata. Inner `universe.jsonl` and `attention.json` SHA-256 both matched `manifest.json`. The original provider-selected **8,501/8,501 distinct ticker** denominator was verified, with status counts summing exactly to 8,501:

| Source-limited indicative category | Count |
| --- | ---: |
| Early 2–15% IEX reference move | 661 |
| Intermediate 15–25% | 9 |
| Exhausted | 5 |
| Other | 2,423 |
| Indicative $3 price-floor block | 384 |
| Stale/future IEX print | 4,884 |
| Missing IEX snapshot | 3 |
| Missing trade/previous bar | 95 |
| Unverified previous IEX day | 37 |
| **Total** | **8,501** |

The **670** early+intermediate records are *indicative IEX price-reference attention only*, not verified pre-collapse catches, actual >=20% regular-session outcomes, shortable symbols or executable shares. JDZG remains in the source records, **price-floor blocked**, with stale/halt failure analysis preserved; no retrospective JDZG success is asserted. New provider scope 8,501 is not the frozen 8,510 baseline or a revised denominator.

**Independent Nasdaq halt / optional quote monitor:** [GitHub Actions run 41504808627](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41504808627) completed **success**, **53/53 independent-source/SMG offline tests passed**, and bounded source collection/artifact upload succeeded. Artifact **13169773242**, `obsidian-independent-sources-41504808627`, present/unexpired, expires **2027-01-31**, ZIP SHA-256 **3cd4802e01dfa4926a5be1d8140ecdeff37752724545701d86a827a2c2ce4b6d**. Independently downloaded ZIP and matched SHA-256 to GitHub metadata. JSON contains **136/136 distinct retained watchlist names**, Nasdaq Trader official RSS status `NASDAQ_RSS_PARSED_WITH_ASOF_LIMITATIONS`, receipt SHA-256 `122a1a9db7678241ecb6b06f5d40744d9d13da7c3a9844c213bffc109ae92766`, and exactly four source-limited halt rows: GCDT/TJGC reported halt; RBNE/RETO elapsed resumption **without live clearance verification**. Missing RSS rows never establish a security is unhalted. **All 136 optional Massive quotes were `INDEPENDENT_QUOTE_PROVIDER_NOT_CONNECTED`**, with no live entitlement or real-time claim. Official halt events are not official closing-price evidence.

## Frozen proof and unresolved P0-1 dependency

- Preserve frozen 8,510-security cohort, **34,040** issuer×0/+1/+2/+3 actual-trading-session slots, 136-name retained watchlist, nine separate provider-universe gaps, JDZG stale/halt/price-floor investigation, and all baseline historical labels. Preserve matched untouched future cohorts, false positives, late/exhausted cases, squeezes, costs and missingness; no duplicate same-issuer/day future outcome.
- The IEX provider remains single-venue and non-SIP. The independent halt feed is a finite as-of RSS, not exchange-authoritative full-market clearance. No verified Massive key/plan/quote data and no two independently authenticated exchange-official regular-session closes with identity, previous-session, corporate-action, source ownership, timestamp and conflict inventory. **Zero new admissible official-close outcome pairs.** Missing outcomes are censored. Verified >=20% prediction accuracy, precision/recall, false-positive rate, SMG blocked-symbol/account permission, borrow, shares, fills, costs and profitability remain **unestablished**.
- This checkpoint's highest-value safe advancement was original in-window source collection and byte-level validation, not an unproven vendor entitlement or an additional synthetic code-only fix. Durable off-platform archive remains **BACKUP_UNVERIFIED**; GitHub artifacts expire after 90 days. The protected 14:45–14:58 CST capture remains owned by its original later gate and is not preauthorized by this report.
