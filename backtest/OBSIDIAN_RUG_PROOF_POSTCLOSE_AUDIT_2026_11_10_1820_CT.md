# OBSIDIAN rug-proof postclose source audit — 2026-11-10 18:20 CT

RESEARCH_ONLY_NOT_AN_ORDER. New research-only audit; no alteration of frozen prospective boards or historical baselines. Repository branch research/obsidian-early-rug-20261025. Source branch head inspected: eb178051be98ea4540a8bbb61eb998b9dbde19ee. October 28 future-checkpoint protocol and both anchor/SIP workflow definitions reviewed. Official NYSE 2026 calendar confirms November 10 regular trading session, completed at 16:00 ET / 15:00 CT; 18:20 CT is post-close, not a new capture window.

## Authenticated original evidence
- Morning IEX workflow 42842720370 succeeded; artifact 13775948302, recorded artifact SHA256 f0d274e75877461b29fe4837703863a0c09cf4b6a8701a586e35dd77a8699be2.
- Intraday IEX workflow 42875025667 succeeded; artifact 13791701457, recorded artifact SHA256 69c19d31adcddd0d58c928220581ed406ca2781d4f1764026c90a6514ae20b4d. Original full IEX universe 8,496; runner verified source integrity. Artifact ZIP bytes not independently rehashed in this audit.
- Original 14:20 decision board: backtest/OBSIDIAN_PROSPECTIVE_ABC_BOARD_2026_11_10_1420_CT.md. It explicitly labels itself INCOMPLETE: 136 retained symbols, 8,496 IEX universe, 828 indicative early (2–15%), 14 indicative intermediate (15–25%), 4 exhausted, 338 floor blocked, 5,117 stale/future, 90 missing trade/prior bar, 11 missing snapshot, 19 unverified previous IEX day, 2,075 other. Mechanical buckets are not complete issuer-level predictions. CBRS price-only conditional, RAPP unresolved, SPTX stale, JDZG below-$3 floor-blocked; no verified executable signal.

## Delayed consolidated source
- 14:20 SIP workflow 42894089239 completed SUCCESS on first attempt, original intraday anchor 42875025667, source receipt at 14:19 CT, artifact 13798399857, recorded artifact SHA256 feeeee435d679b6f3e1222a53b126ab2e832ca52272c0bd57e9fbfebb83bf51f. ZIP-byte independent rehash not performed.
- Runner source verifier: 8,496 attempted = 8,496 rows; historical delayed SIP fresh-at-asof 5,576; stale-at-asof 1,068; no consolidated bar 1,852. Stale+missing 2,920/8,496 = 34.37%. Runner did not report a separately quantified 401/403 denominator in the reviewed summary; do not infer zero HTTP failures. At least 17-minute historical lag, not a current quote, not original IEX timestamp, not official 16:00 ET close.

## Independent source blockers
- Original 14:20 independent monitor run 42894591595: Nasdaq halt feed not retrieved / malformed or unverifiable; Massive disconnected; 136 requested, zero independently verified quotes; no current official halt clearance.
- Afterhours independent monitor run 42904525935 completed SUCCESS but source summary remains NASDAQ_HALT_FEED_NOT_RETRIEVED, quotes_connected=false, realtime_entitlement_verified=false, 136 retained, trade_authorized=false. Successful workflow does not mean successful independent data coverage.
- No two independent organization-level completed 16:00 ET regular close receipts, conflicting-third reconciliation, security identity/corporate-action proof, and issuer-specific timestamped catalysts were authenticated in this audit. Thus zero officially verified outcomes, NOT zero collapses. Preserve 0/+1/+2/+3 actual trading-session matched denominator as unscored/censored; do not infer performance or edge, and do not retrospectively select winners.

No unscheduled capture, retry, backfill, order, alert, main/frozen evidence modification, or borrow/fill/holdings claim. Research-only evidence note.
