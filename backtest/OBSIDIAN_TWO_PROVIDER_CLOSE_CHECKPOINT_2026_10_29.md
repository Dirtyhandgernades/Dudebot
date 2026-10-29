# OBSIDIAN vendor close reconciliation checkpoint — 2026-10-29 11:52 CT

RESEARCH_ONLY_NOT_AN_ORDER. This note does not change the frozen baseline, 136-name watchlist, JDZG stale/halt failure, cohort denominators, 0/+1/+2/+3-session horizons, or original Rug Catch Proof anchors.

## Verified hosted evidence
- Run 40915118143: original per-date request design, completed but **0/10** paired vendor bars; many 400/429 responses. Do not infer mismatches from missing data.
- Commit 48e00a0e79db6c210d47136069079f62be3164cb: new bounded pilot **AAPL/MSFT × 2026-10-27/28**; one latest-10-daily-bars Twelve Data request per ticker, four single-date Massive requests, exact session matching; missing values censored. This 2-symbol connectivity pilot is **not** a replacement for the 136-name watchlist or a forecast evaluation.
- Run 40915627437: **4/4 paired vendor bars matched within $0.005**, original artifact 12915408510. AAPL 10/27 347.10 vs 347.10001; 10/28 343.83 vs 343.82999; MSFT 10/27 531.33 vs 531.33002; 10/28 531.01 vs 531.01001. This establishes vendor numerical agreement on four historical daily bars **only**.
- Commit 6e95ce762a32f22d74499afb5c2439cea2d5e9f1 adds offline missingness/request-budget tests; hosted run 40915668951 completed successfully, **2 offline tests passed**, artifact 12915582889. Its repeated live fetch yielded **1/4** paired bars, other three Massive requests HTTP 429; Twelve Data returned all four. No retry/backfill or fabricated values.
- The subsequent live run illustrates rate-limit sensitivity; preserve both immutable artifacts, do not select only the favorable run.

## Strict P0-1 blockers
No exchange-authenticated official regular-session close, no proven distinct underlying exchange-feed provenance, no complete source/conflict inventory, no security-ID/issuer mapping, no corporate-action adjustment equivalence, and no independently verified exchange session/close timestamp. Therefore **official_exchange_close_verified=false**, **outcome_scoring_eligible=false**, and **20%+ collapse prediction accuracy unestablished**. Vendor daily bars are diagnostic and cannot fill missing frozen prospective outcomes. Provider response-body SHA256 and retrieval time are recorded; original vendor receipt body and cryptographic exchange attestations are not preserved. Next engineering pass should avoid burning rate-limited requests on repeated identical historical checks and design a non-retroactive source-contract gate with immutable raw receipt archiving, independent venue provenance and strict censoring. Any historical pair is not a forward prediction.

No production/main, credentials, orders, SMG execution, original IEX captures or independent proof anchors were changed.
