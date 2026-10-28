# OBSIDIAN October 27, 2026 — 21:20 CT incremental after-hours audit

**RESEARCH_ONLY_NOT_AN_ORDER.** Additional independent research after the existing 16:23, 17:24, 18:26, 19:26 and 20:18 CT audits. Do not double-count those prior movers or treat price-only signals as executable short orders. No new after-hours IEX observation was triggered, and no protected preclose collection was modified.

## Original preclose denominator and integrity (reverified, not reconstructed)

- Original authenticated research capture [GitHub run 40572768800](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40572768800), artifact **12766795149**, 2026-10-27 19:51:01.669–19:51:04.120 UTC (14:51 CT).
- Independently downloaded original artifact again and checked the raw `universe.jsonl` SHA-256 **10a3d8f30726759105394dac6eeaf6bccc208932d43e1faa51507809aa8c0bb4**, exactly equal to its manifest. All **8,515** original symbols remain in denominator: 433 early weakness watches, 9 exhausted, 3,669 no-watch, 4,252 stale/future prints, 105 missing trade/prior, 44 unverified previous IEX sessions, 3 absent snapshots.
- This original IEX single-venue prior daily bar is **not** the independently verified official previous close. None of the IEX last trades prove current consolidated NBBO, liquidity, SMG eligibility, actual short borrow, fills or P&L.

## New verified after-bell case: OI (screened, no watch)

- **O-I Glass (NYSE: OI)** was in the original preclose universe with `IEX_NO_EARLY_PRICE_ONLY_WATCH`, fresh IEX last trade **$6.475 at 2026-10-27 19:51:02.577 UTC (15:51:02 ET)** against previous IEX daily reference **$6.445**. This is only an indicative **+0.47% IEX reference change**, not a certified official close or executable ask/bid.
- The issuer's **October 5** [earnings-date announcement](https://www.o-i.com/news/o-i-glass-announces-third-quarter-2026-earnings-conference-call-and-webcast/) explicitly said Q3 results would be issued **after the October 27 market close**. The date was foreseeable, but the contents were **not known by the 15:58 ET execution cutoff**.
- A contemporaneously timestamped [October 27 16:38 ET market recap](https://www.investing.com/news/stock-market-news/afterhours-movers-stx-enph-hood-v-csgp-boom-cake-ppg-oi-ter-432SI-4976906) reported **OI approximately -11% after hours** following the release. This is a media-reported indicative reaction, **not** a separately timestamped executable print or verified 20:00 ET extended-hours closing price.
- [October 27 16:46 ET 8-K](https://www.streetinsider.com/SEC+Filings/Form+8-K+O-I+Glass%2C+Inc.+DE+For%3A+Oct+27/27242098.html) and [SEC-exhibit coverage](https://www.stocktitan.net/sec-filings/OI/8-k-o-i-glass-inc-de-reports-material-event-d80c521209fa.html) document a **$13M net loss, $234M adjusted EBITDA vs $329M prior-year, 2026 adjusted EBITDA guidance cut to $925M–$950M, and free cash flow use revised to approximately $300M** (prior negative $50M–$150M).
- **Classification:** `SCREENED_NO_WATCH / POST_BELL_RESULTS_UNAVAILABLE_AT_CUTOFF / AFTERHOURS_INDICATIVE_DECLINE / SMG_BORROW_UNKNOWN`. This is a new sharp **after-bell** decline, not a missed demonstrated preclose short. July 2026 weakness was public but does not establish knowledge of Q3 results or a verified early timing edge. No simulated fills, after-cost profit or EOD -20% regular-close hit claimed.
- **Source integrity:** a generic dynamic [stockmarketwatch OI page](https://stockmarketwatch.com/stock/OI/afterhours) currently displays **Monday** as-of 20:15 ET and $6.45, despite the current study day being Tuesday. This is **stale session evidence** and is excluded rather than averaged against the Tuesday market recap.

## New daytime comparison, not a fresh post-bell rug: BA

- **Boeing (NYSE: BA)** was already **`IEX_EARLY_WEAKNESS_WATCH_ONLY`** in the immutable 14:51 CT capture. Original fresh IEX last trade **$168.025 at 15:51:00.901 ET** against IEX prior daily reference **$188.14**, an indicative **-10.69%**; by the scanner checkpoint the large selloff had already occurred.
- [Issuer earnings schedule](https://investors.boeing.com/investors/news/press-release-details/2026/Boeing-to-Release-Third-Quarter-Results-on-October-27/default.aspx) was public September 30, with October 27 10:30 ET earnings call. [Reuters October 27](https://www.reuters.com/business/aerospace-defense/boeing-jetliner-production-challenges-weigh-third-quarter-results-2026-10-27/) reports delayed 737 ramp and weaker-than-expected free cash flow outlook, and [dated market recap](https://www.investing.com/news/stock-market-news/afterhours-movers-stx-enph-hood-v-csgp-boom-cake-ppg-oi-ter-432SI-4976906) records BA approximately -10.69% in regular session.
- **Classification:** `SCREENED_ON_PRICE_ONLY_BOARD / PUBLIC_EARNINGS_BEFORE_PRECLOSE / ALREADY_DOWN_APPROX_10PCT / NO_VERIFIED_PRE_COLLAPSE_EDGE`. This is evidence of late-session recognition of a publicly disclosed move, **not** a verified advance prediction of a 20% closing rug. No actual borrow, trade or holdings inferred.

## Coverage categories and no retrospective promotions

- Screened/no-watch: OI, previously audited RAPP, STX, NXPI, BBNX, HOOD, TER, PPG, etc. Post-bell earnings, offerings and mergers do not become preclose-known signals.
- Screened/on-board but full eligibility/target unverified: BA and previously audited INTA, ENPH, CSGP, CLW, XYL. Do not claim mechanism confirmation, >=20% official closing outcome, or executable borrow.
- Missing/stale: 4,252 original stale/future IEX prints; DRIO was `STALE_OR_FUTURE_IEX_TRADE` at $3.36 (last trade 15:07 ET), so its later indicative upside is not a preclose actionable reversal.
- Never screened vs absent: SDEV is absent from **this** immutable 8,515-symbol capture only, not proof of never being considered by other OBSIDIAN workflows.
- Corporate action: NUWE, ENLV, SCAG, PARA previously identified same-day split/ADS comparability blockers; do not treat raw cross-session IEX ratios as returns.
- Eligibility/borrow: CD, XRPN, WFF, AVBP, SDEV, SECZ, AEHL and all other retained structural watches remain research references, not confirmed current user positions or valid shorts. Covered trades are not silently reopened.
- Adverse squeeze: ULBI, BRAI, BOOM, UCTT, MANH and other upside cases are already documented; no repeat counting or inferred costless exit.

## Frozen forward-study and CI verification

- The current research-branch hosted [offline CI run 40617114820](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40617114820) completed **success**, **303 tests passed**. The separate [source-contract shadow audit](OBSIDIAN_FORWARD_EOD_SOURCE_CONTRACT_AUDIT_2026_10_27.md) identified a stricter EOD preflight that is **not automatically enforced by the frozen scorer**; keep this as an unresolved integrity gate, not a post-hoc frozen-policy change.
- No independently complete, provider-distinct, 16:00 ET price-as-of corroborated October 27 EOD outcome JSONL and corporate-action identity reviews are available for the original 8,515-symbol denominator. Thus early vs late verified >=20% regular-session closes, recall, precision, squeeze P&L, costs and false-positive rates are **unknown**, not 0%.
- The single October 27 15:22 CT authenticated **after-hours** IEX trigger was missed. Current 21:20 CT is outside the authorized 15:00–15:45 CT trigger window and is not the scheduled-for-15:22 checkpoint. **No trigger, retry, backfill or replacement raw capture** created.
- This document is isolated research evidence only. No main, frozen scorer/policy, production, credentials, alerts, orders, watchlist reclassification or automation schedule changed.

**Material increment:** newly verified OI after-bell earnings-driven indicative ~11% decline with original **no-watch** preclose row; Boeing late-recognition negative control. Neither is a demonstrated early or eligible preclose short. Source-contract and official-close blockers remain unresolved.
