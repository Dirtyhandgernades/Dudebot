# OBSIDIAN IEX forward-collapse evaluation — frozen policy v1 (2026-10-27)

> **RESEARCH_ONLY_NOT_AN_ORDER**. This is a pre-outcome policy specification and *not* a claimed predictive edge or SMG recommendation.

## Primary question
For each authentic, write-once morning or intraday IEX research capture, did OBSIDIAN mark an issuer **before most of a future >=20% decline at the completed 16:00 Eastern regular-session close**, relative to the independently verified previous regular-session close? An IEX single-venue bar is NEVER treated as the official previous or final close.

## Fixed, not outcome-tuned rules
- **Frozen time:** original raw quote time / capture timestamp from an immutable IEX research artifact; do not infer a date from an audit written later.
- **Frozen watch rule:** `IEX_INDICATIVE_EARLY_2_TO_15` or `IEX_INDICATIVE_INTERMEDIATE_15_TO_25` as classified at collection using only IEX last trade / IEX previous bar. These are price-only exploration watches, not the full speculative mechanism classifier and not validated short recommendations.
- **Target:** same-session independent, unadjusted regular close divided by independently verified previous regular close minus one <= -20%, **only when independently verified that comparable shareholder entitlements/security identity were unchanged**. Known/unclear splits, distributions, spin-offs, rights, ADS changes or mergers are censored; do not silently adjust an issuer case to create a win.
- **True early credit:** target occurs, frozen IEX watch exists, fresh timestamped last IEX trade exists *before* close and at least **50% of that day's complete prior-to-final close absolute price decline remained** at the IEX last print. Formula `remaining = (IEX_at_signal - official_final_close) / (official_previous_close - official_final_close)`, evaluated only for verified collapses.
- **Late watch:** outcome crosses -20%, but less than half the eventual decline remained at signal. Not credited as a prospective early hit. A stock already down >=25% at observed IEX prior reference is also never promoted into early-watch status.
- **Unwatched, even if outcome >=20%:** count in missed conditional events, not a magically screened eligible trade. Missing stale tape is separately reported.
- **After-hours cohort:** NEVER score Oct27 after-hours snapshots as predictions of Oct27 regular close. They may form a separately defined *future-session* study after another advance-frozen horizon protocol.
- **Outcomes:** require 2 independently timestamped distinct-host external EOD sources agreeing within half a cent on prior/current regular-session prices, 16:00 ET session close, explicit date, original source URL, independently reviewed corporate actions/identical security identifier, report collection AFTER close, and unchanged write-once raw capture.
- **Missing outcomes and incomplete prior sessions:** censor, never treat as no collapse. 16:00 ET rule excludes early-close sessions until separately defined policy.
- **Metrics:** preserve all captured securities and raw reference watches; report verified/censored subset, early hits, late watches, unwatched collapses, valid quote denominator, provisional conditional recall and precision. Because missingness is nonrandom, conditional metrics are NOT market-wide recall.
- **Matched future sessions:** Research morning and intraday same issuer/day are **correlated** and must not be counted as independent opportunities. If combining, count once at earliest verified real signal. A future validated mechanism-and-tape challenger requires contemporaneous signed-off evidence; absent evidence is UNKNOWN, not baseline loss.
- **Eligibility/P&L:** unknown common-stock class, capital structure, price floors, exchange, real-time halt, liquidity, actual SMG platform borrow/short, buying power, fees/fills remain **hard blocked** and cannot be upgraded from Alpaca asset metadata. No edge/probability/P&L claims.
- **No training on known winners:** 2023–2025 historical movers, Oct26 collapse cases, AIOK/AEHL examples, or the first inspected pilot run must not be used to tune the 20% endpoint, frozen watch bands, or half-remaining rule. First truly untouched cohort begins AFTER this policy is committed and verified.

### Practical protocol
1. Preserve the SHA-256, run ID and complete immutable `manifest.json`, `universe.jsonl`, `attention.json` for each eligible future session. Keep stale, unknown, failed and unrelated rows.
2. After the *completed* regular session, independently collect and review outcome JSONL only for original captured symbols; include source timestamps and corporate-action proof. Missing closes remain censored.
3. Run `python -m backtest.obsidian_forward_collapse_study --capture <raw-capture-folder> --outcomes <independent-EOD.jsonl> --output <new-write-once-report.json>`. Omitting `--outcomes` verifies readiness and records 0 confirmed outcomes, NEVER fabricated performance.
4. Across multiple unique future sessions compare frozen all-factor baseline and mechanism/tape challenger on same genuinely verified eligible universe, with separate interval lead times, squeeze and after-cost economic assessment. No automatic live orders.

### Provider limitations
Alpaca authenticated paper/IEX only; SIP real-time 403. Older main archive's separate ALPACA secret family 401 does not resolve simply because research IEX works. All changes isolated to research branch, without touching main, frozen baseline, credentials, alerts or actual orders.
