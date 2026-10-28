# OBSIDIAN — October 28 18:50 CT immutable matched-cohort replay verification

**RESEARCH_ONLY_NOT_AN_ORDER.** The highest-priority safe P0-3 subtask (actual raw-artifact replay without outcomes) is now independently executed on hosted GitHub Actions. This is NOT a successful forecast or independently authenticated official-close outcome.

## Hosted verification

- Research implementation commit: `8be0e1a4d0072c6e2b1efe68adbfdc325dba3678` (isolated research workflow + protocol).
- Hosted replay: [GitHub Actions run 40790013742](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40790013742), job `123172617302`, **SUCCESS**, all steps successful.
- Offline tests: **347 passed**.
- Original morning run `40704289113`, artifact `12822044262`, ZIP SHA256 `581de21834482d82a2ee8e91f8077c7497141e94e5b9deec16f7d8727cde6110`: downloaded, archive hash checked OK, raw capture verified by existing replay.
- Original intraday run `40739809362`, artifact `12837584509`, ZIP SHA256 `07e6d370e0a52b2c887c21f46d41273f0ea50fefbefd47dce53abf5571085801`: downloaded, archive hash checked OK, raw capture verified by existing replay.
- Derived write-once matched-cohort artifact `12861206900` (GitHub SHA256 `2f750c2842e3e179fd41675439904e1e5d4ab740dd00168c74bf2f0cf663b8a2`). It contains full 8,511-row matched ledger and source evidence summary; **not** a replacement for the original raw ZIPs.

## Observed original-denominator findings

| Replayed field | Verified count |
| --- | ---: |
| Original morning symbols | 8,511 |
| Original intraday symbols | 8,511 |
| Union (unique ticker) | **8,511** |
| Original morning IEX price-only watches | 264 |
| Original intraday IEX price-only watches | 342 |
| Unique first-ever morning or intraday price-only watches | **438** |
| First observed morning watches | 264 |
| First observed intraday watches | 174 |
| Comparable same IEX asset/reference | 7,182 |
| Quarantined changed/missing IEX previous reference | **1,329** |

These 438 are unique raw price-only watches, NOT verified early >=20% regular-session collapses, genuine eligible SMG shorts, or independent trading opportunities. Intraday first-observed status is NOT proof that the deterioration began at that time; prior stale observations remain flagged. 1,329 changed/missing IEX references prohibit comparable-onset claims and require careful separate investigation. Morning and intraday scans are correlated, not independent predictions.

**Outcome evidence:** zero independently corroborated official regular-session closes/corporate-action-comparable JSONL; conditional precision/recall, after-cost P&L and actual SMG eligibility remain unestablished. Raw artifact retention expires Jan 26 2027; durable backup **BACKUP_UNVERIFIED**.

**Next highest-priority dependency:** independent exact-session EOD source provenance, calendar and security identity validation, followed by frozen matched 0/+1/+2/+3 session scoring on the same eligible universe. Do not retrofit known outcomes, modify frozen policies, create captures outside gates, or touch main, production, credentials, alerts or orders.
