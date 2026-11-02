# OBSIDIAN Research Engineering — November 2, 2026, 17:49 CST — Unicode EOD source-alias guard

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated P0-1 synthetic source-integrity correction; NOT official exchange-close authentication, verified forward outcomes, trading, or SMG authorization.

## Verified defect and correction

The independent EOD preflight and complete-source conflict inventory previously canonicalized provider organization names and source receipt IDs with case-folding and whitespace normalization only. Canonically equivalent Unicode strings (for example `Café Data` and `Cafe\u0301 Data`) could appear to be different provider organizations on distinct hostnames, incorrectly passing the structural two-provider independence screen. Similarly, Unicode-equivalent source IDs could evade duplicate detection. Invisible Unicode format controls such as U+200B could manufacture apparent distinct names or receipt IDs.

Implementation commit `94c93812fa7f82b3f49d2d7653d1b9a044fef1d9` applies NFKC normalization to comparison keys in both isolated P0-1 modules and censors provider/source labels containing Unicode format controls. The preflight now explicitly rejects an invalid canonical provider or source key, instead of accepting a syntactically nonblank but untrustworthy label. The complete-source ledger retains original spellings, supplied rows and source digests; no original observation is silently discarded. This normalization is a conservative alias screen, **not** a legal provider-ownership certificate; cross-organization evidence remains externally unverified.

Six new synthetic regression tests cover Unicode-equivalent provider names, duplicate receipt IDs, and invisible format controls in both preflight and all-source inventory. Original frozen labels, watchlist and scoring logic were not changed.

## Hosted CI, source artifacts and coordination

- [Prospective research CI #41548369074](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41548369074): completed SUCCESS on implementation commit, **653/653** prospective tests and **4/4** ABC-board tests passed. All six new regressions were explicitly observed passing in the job log.
- [EOD source-contract CI #41548369299](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41548369299): completed SUCCESS on the same commit, **42/42** tests passed.
- Read the October 28 roadmap and original Rug Proof delayed-SIP and postclose reports; verified original November 2 Morning/Intraday/Preclose/After-Hours and separate Rug Proof marker inventory. This 17:49 CST checkpoint is outside the original 12:47 intraday and 14:45–14:58 preclose gates. No capture marker, rerun, backfill, duplicate issuer/day or other task's evidence was created.
- Fresh GitHub artifact metadata verified present, unexpired through January 31, 2027: After-Hours independent monitor **13179429754**, After-Hours IEX **13179494453**, protected preclose **13177274914**, Rug Proof delayed SIP **13176201670**. Contents were not downloaded or independently rehashed in this pass; durable off-platform backup remains **BACKUP_UNVERIFIED**.

## Frozen denominators and blockers

Original frozen **8,510-security** cohort, **34,040** issuer×0/+1/+2/+3 actual trading-session forward slots, historical baseline labels, **136-name** watchlist and JDZG stale/halt failure analysis remain unchanged. No claim of new 20%+ true positives, false-positive rates, costs, squeezes, shares, orders, fills, profitability or SMG shortability. Any missing or immature outcome remains **CENSORED**.

**P0-1 external blocker remains:** zero independently authenticated official regular-session close outcome pairs from two genuinely independent underlying provider organizations with official previous-close, source/third-source conflicts, security identity, corporate actions, exchange calendar and timestamps. Live Massive entitlement remains unverified. The code fix only prevents a new category of source alias false independence; it cannot establish source access or predictive accuracy. No main, production, credentials, account permissions, trading notifications or orders were touched.
