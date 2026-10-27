# OBSIDIAN Alpaca read-only feed diagnostic — 2026-10-26 19:44 America/Chicago

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated engineering evidence; not a preclose trading screen, market-data capture, proof of consolidated SIP entitlement, or modification to frozen strategy parameters. No credentials or secret values are recorded here.

## Verified hosted diagnostic

GitHub Actions run: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40428320069
Job: 121939554547; workflow commit: f333180152035283b23fd40b0ffa711bfdd0b7da.
The job completed **failure** at 2026-10-27 00:44 UTC (2026-10-26 19:44 America/Chicago). Logs emitted:

| Read-only endpoint check | Result | Interpretation |
| --- | --- | --- |
| PAPER_ACCOUNT | AUTHORIZED_HTTP_200 | Dedicated research secret references authenticate with Alpaca paper account. |
| PAPER_ASSETS | AUTHORIZED_HTTP_200 | Paper asset listing accessible. |
| LIVE_ASSETS | UNAUTHORIZED_HTTP_401 | Paper credentials do not authorize live assets; not required for paper-account authentication. |
| SIP_SPY_SNAPSHOT | FORBIDDEN_HTTP_403 | Consolidated SIP snapshot access denied to this credential/account path. |
| IEX_SPY_SNAPSHOT | AUTHORIZED_HTTP_200 | IEX feed snapshot endpoint accessible. |
| MARKET_DATA_RESULT | IEX_ONLY_SIP_BLOCKED | Provider access is partial; the strict SIP diagnostic intentionally fails. |

Artifacts for this run: **zero**. A successful GET is not proof that timestamps, depth, full eligible-universe coverage, consolidated close, borrow availability, or SMG eligibility are adequate.

## Data integrity / next steps

- **Authentication issue resolved:** earlier hosted HTTP 401 for paper account/assets is no longer reproduced after dedicated research-only references were populated. Do not change keys or access credential values.
- **Market-data blocker remains:** IEX-only observations are **not** consolidated SIP prices or independent official regular-session closes. Never silently substitute IEX for SIP in the frozen baseline or speculative challenger, and never count a market-wide >=20% closing-price collapse from an IEX-only print.
- **No Oct26 backfill:** prospective capture #3 (https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40389830214) failed with zero artifacts. This historical absence cannot be repaired by querying data after the fact and calling it prospective.
- **No confirmed eligible lead times, fills, borrow, preclose candidate decisions, false-positive denominator, after-cost P&L, or drawdown** follow from this diagnostic.
- For future research, maintain feed provenance and explicit **SIP_UNAVAILABLE / IEX_AVAILABLE** missingness; independently verify official EOD close and as-of eligibility from approved sources before scoring. Do not relax hard gates or initiate live alerts/trades/orders.
- Existing retained watchlist totals remain 113 master + 23 supplemental = 136 distinct historical symbols, not 136 current screened candidates. No confirmed new eligible preclose setup follows from this access test.

Research CI run https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40422433434 remains successful with 153 offline tests; this diagnostic has no test artifacts and did not change research code. No main, production, frozen baseline/journal, credentials, orders, or live alerts changed.
