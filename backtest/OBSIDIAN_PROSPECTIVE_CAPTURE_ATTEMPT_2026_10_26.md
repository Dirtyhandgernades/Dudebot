# OBSIDIAN first prospective SIP attempt — 2026-10-26 14:47 America/Chicago

**Immutable research evidence, not a price snapshot. Do not backfill or re-trigger this session.**

- One-time research-branch-only workflow comment trigger commit: `5f899d38531ce0073207fecb4d476461f47c34f6`.
- Hosted [prospective capture workflow #3](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40389830214), job `121807596582`, started 2026-10-26 19:47 UTC, **FAILED**.
- All **76 offline tests PASSED** before provider access. Weekday 14:45–14:58 CT gate was **OPEN**.
- Read-only `GET` provider acquisition was attempted; collector raised `ProviderAuthError: ALPACA_READ_ONLY_AUTH_REJECTED` after attempting the primary and alternate asset endpoints. The exception corresponds to HTTP **401 or 403**, which does not distinguish invalid credentials, authorization/scope, or account permission. **Do not assume the cause.**
- The artifact uploader reported **no files** at the expected capture path; artifacts API returned **zero artifacts**. Therefore **zero market bars, zero candidates, zero verified coverage, and no executable trade** resulted from this attempt.
- Do not retry the Oct26 session or reconstruct an as-of 14:47 snapshot using later prices. Investigate authorization outside production, without reading, modifying or disclosing secrets, before a *new future session* attempt.
- Separately [prospective journal CI #35](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40389411315), job `121806170177`, passed **76 offline tests** on research commit `65dcec7d8083d2eca05e86add08dd54b956e82b5`, including isolated mechanism and watchlist reconciliation regressions. CI success is **not** a market edge.
- No changes to `main`, production/live trading/alerts, credentials or orders. All unknown SMG shortability, eligibility, float, current price, halts, and financing saleability remain BLOCKED.

## Next safe research steps

1. Diagnose whether the GitHub Actions provider credentials have the required account/market-data permission through authorized owner review; no secrets need to be revealed in the research report. Do not infer entitlement from a 401/403.
2. Continue independent archival watchlist and 98-name missing-data reconciliation; preserve not-screened versus missing-data and no original-gap repairs inferred.
3. Implement timestamped morning/intraday/after-hours research-only discovery and capital-structure provenance with point-in-time tests.
4. Accumulate genuinely later prospective observations only after a working read-only provider source is verified. Keep the frozen 2023–25 comparison untouched; do not recommend trades.
