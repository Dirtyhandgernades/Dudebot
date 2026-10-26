# OBSIDIAN after-hours follow-up — Monday 2026-10-26, 16:19 America/Chicago (21:19 UTC)

**RESEARCH ONLY, no execution, no frozen-strategy changes.** Observation is a collection of third-party web reads made during this hourly audit. The *individual ticker page* displays its own last-trade time; the *ranked table* has no per-trade timestamp and may be stale or refreshed asynchronously. This is not a synchronized tape or an authenticated Alpaca SIP capture.

## New high-priority data-quality finding: ITGR ranked quote contradicts individual ticker quote

- Ranked after-hours losers page https://stockanalysis.com/markets/afterhours/losers/ displayed **ITGR $95.56, -24.47% from $126.52 close**, with no quote-level timestamp.
- Individual ITGR page https://stockanalysis.com/stocks/itgr/ displayed **$126.00, -0.41% at 4:56 PM EDT**, and **$126.52 regular close at 4:00 PM EDT**. These observations conflict by ~$30.44/share; they are NOT contemporaneous verified independent market prints. The $95.56 figure is NOT a confirmed collapse.
- Context: ITGR has an announced **$127/share all-cash KKR buyout**, August 3 issuer release https://investor.integer.net/news-events/press-releases/news-details/2026/Integer-to-Be-Acquired-by-KKR-in-Transaction-Valued-at-Approximately-5-7-Billion/default.aspx ; Oct21 shareholder approval https://www.stocktitan.net/sec-filings/ITGR/8-k-integer-holdings-corp-reports-material-event-9da195479695.html . This is an important merger-event risk, but no independently confirmed Oct26 merger termination, 8-K or genuine $95.56 executable print was found during this audit. **DATA_CONFLICT, not an actionable short, not proof of bad provider data.**
- Root cause category: **ranked-versus-individual non-synchronous quote disagreement + missing independent timestamp/venue/volume**. ITGR was NOT on the recovered 136 historical ticker list; keep as a data-integrity incident, not a newly confirmed bearish structural watch.

## New timestamped issuer catalyst: CPIX after the decision cutoff

- CPIX individual quote page https://stockanalysis.com/stocks/cpix/ showed **Oct26 regular close $4.35 (-48.76% from $8.49)** and **$4.62 (+6.21%) at 4:50 PM EDT**. This differs from the earlier 4:14 PM EDT after-hours observation of $4.47; the timestamps are different and the later quote is not a synchronized price confirmation.
- The issuer published an ifetroban/DMD NDA plan **at 4:40 PM EDT** on Oct26, source https://www.prnewswire.com/news-releases/cumberland-pharmaceuticals-announces-plans-to-file-new-drug-application-for-ifetroban-dmd-program-302919826.html . The release says FDA raised concerns about efficacy evidence and requested additional analyses, while the company plans a rolling NDA filing. This is a complex, not unambiguously bearish disclosure. The previously announced webcast was scheduled 4:30 PM EDT.
- **Important causality:** the Oct26 regular-session -48.76% closing collapse was already realized BEFORE the 4:40 PM release. Do NOT label the 4:40 disclosure as the known cause of the earlier close or backdate it into a 14:45–14:58 Central entry thesis. No authenticated preclose tape or SMG borrow was captured. Historical watch retained; NOT a verified catchable short.

## Existing research watch APXC and historical firm watch LHSW

- APXC https://stockanalysis.com/stocks/apxc/ showed **$5.25 regular close (-20.45%)** and **$6.67 (+27.05%) at 5:04 PM EDT**, versus the earlier research note's **$9.95 (+89.52%) at 4:24 PM EDT**. The different times illustrate extreme reversal/squeeze risk, not a reliable fill sequence. Oct23 issuer disclosed new Nasdaq ADS offering **400,000 ADS at $4.65, six ordinary shares per ADS**: https://apexcriticalmetals.com/news/ . No current ADS/SMG short availability verified.
- LHSW (present in historical master) https://stockanalysis.com/stocks/lhsw/ showed **$3.87 regular close (-19.37%)**, **$3.91 (+1.03%) at 4:19 PM EDT**, while a dynamic after-hours gainer table at a different observation displayed $4.36 (+12.66%). Issuer announced **1-for-8 share consolidation effective Oct26**, source https://www.globenewswire.com/news-release/2026/10/22/3386359/0/en/lianhe-sowell-international-group-ltd-announces-1-for-8-share-consolidation.html . Indicative vendor market cap ~$5.28M is below SMG $25M gate, and verified split-adjusted shares/cap/borrow/halts are missing. **CORPORATE_ACTION_REVIEW / HARD_BLOCKED**, not a clean intermediate-band short.
- AIOK remains a historical dividend/due-bill review, not a verified preclose setup. CD, XRPN, WFF, AVBP, SDEV, SECZ, AEHL and the other retained structural watches have **no newly recovered authenticated preclose screen/outcome evidence** in this run; do not train on reference winners or invent missing executions.

## Explicit attribution categories and coverage

| Category | As-of result |
|---|---|
| Screened and rejected on authenticated Oct26 preclose board | **None verifiable; original board unavailable** |
| On board, failed confirmation or target | **Unknown, no authenticated preclose board** |
| Not screened | ITGR **not in retained historical manifests**, discovered as after-hours data-quality anomaly; no preclose screen verified |
| Missing/stale bars | Provider auth HTTP 401/403 means **zero Oct26 authenticated prospective capture artifacts**; 98-name/57-gap archive remains unresolved |
| Renamed/split/ADS/corporate action | LHSW 1-for-8, APXC six ordinary shares per ADS, AIOK special dividend due bills; do not assume eligibility |
| Ineligible/borrow unknown | LHSW indicative cap below $25M; **ALL** cases lack verified SMG platform borrow, and other hard gates remain unresolved |
| After-bell disclosure | CPIX 4:40 PM EDT NDA-plan release; **cannot explain prior 4:00 PM regular close by itself** |
| False positives/lead time/after-cost P&L | **NOT MEASURABLE** without authenticated predecision universe and future outcomes; no hypothetical fills or profit |

## Isolated research fix

- New `backtest/obsidian_extended_quote_integrity.py` and `tests/test_obsidian_prospective_extended_quote_integrity.py` enforce fail-closed ranked-versus-individual quote consistency, quote timestamp/freshness, two **independent** sources rather than two pages from one vendor, split/corporate-action clearance, and exact >=20% extreme-move boundaries. No inference of actual SMG execution.
- Updated `backtest/obsidian_afterhours_catchability.py` and regression tests to prioritize post-decision catalyst attribution **even when no preclose signal exists**, and separately reject a catalyst that postdates the observed outcome.
- CI workflow only `.github/workflows/obsidian-prospective-journal-tests.yml` includes new regression paths. **HOSTED VERIFIED:** [GitHub Actions #47](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40403762920), job 121856109699, commit c2aa4c7c54171ab73714b6e81bab741565bb6c31, passed **143 offline tests** at 21:22 UTC. Intermediate #42–46 failed during implementation; fixed exact -20% floating-point boundary and timing tests. No market-data artifact and no demonstrated edge.
- No main/production changes, orders, credentials, live alerts or repeated Oct26 capture.

**Next:** obtain genuinely timestamped preclose board and provider authorization for a future session through the authorized owner; require a second independent extended-hours quote feed and venue/volume to resolve ITGR; continue immutable prospective comparisons, counting all misses and false positives. **Verified executable candidates: zero.**
