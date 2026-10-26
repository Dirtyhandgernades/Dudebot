# OBSIDIAN after-hours missed-move audit — Monday 2026-10-26

**Research-only observation began 15:25 America/Chicago (20:25 UTC), 16:25 Eastern.** This is AFTER the user's 14:45–14:58 Central execution-decision window. Do NOT reconstruct a preclose trade from any price first observed afterward. Quote timestamps below are those displayed by the third-party pages, not authenticated SIP timestamps; snapshots are NOT Alpaca captures.

## Data integrity and board coverage
- Earlier [read-only prospective capture run #3](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40389830214) passed offline tests and its time gate but FAILED HTTP 401/403 provider authorization, with **zero** capture artifacts. Thus no verified 14:47 Central price/volume universe, screening output or preclose execution board exists from that run.
- Historical master manifest [113 retained](obsidian_historical_watchlist_manifest_2026_10_26.json) marks all **NOT_SCREENED** in that specific audit. This does NOT establish that no separate historical board existed.
- During this audit the master manifest was checked: **CPIX, CD, AVBP, SECZ, AEHL present**; **AIOK, XRPN, WFF, SDEV, AVTX, TTMI, AIFA, RZAI, APXC absent**. Added [supplemental retention manifest](obsidian_supplemental_watchlist_2026_10_26.json) with **22 additional historically referenced names** and **APXC as new after-hours discovery**, all without inventing prior screens, holdings, or eligibility. Total 136 distinct retained research tickers across both files, NOT 136 screened.
- No independent current 8-K/6-K universe, confirmed complete after-hours tape, SIP access, platform short-availability or user holdings were available. Names not shown below remain **UNSCREENED/UNKNOWN**, not negative.

## Timestamped observations (all 2026-10-26 Eastern time; third-party indicative)

| Symbol | Historical state | Regular close | After-hours observed | Mechanism and decision-time analysis | SMG action |
|---|---|---|---|---|---|
| **CPIX** | Retained in 113; actual preclose board unavailable | **$4.35, -48.76% vs $8.49 previous close, 4:00 PM EDT** | **$4.47, +2.76% from close, quote displayed 4:14 PM EDT** | Oct19 and Oct23 company announcements had already scheduled **4:30 PM EDT Oct26 ifetroban DMD webcast**; event was knowable BEFORE close, but no preclose breakdown tape/borrow or adverse catalyst is verified. Today's -48.76% move was already realized at close, so NOT a fresh short. The 4:30 event was FUTURE at this audit's start. | BLOCKED: no platform borrow, no preclose entry/tape or independently verified execution. |
| **APXC** | New after-hours discovery, NOT in earlier 113 | **$5.25, -20.45% vs $6.60 previous close, 4:00 PM EDT** | **$9.95, +89.52% from close, quote displayed 4:24 PM EDT** | Extreme postclose rebound/squeeze warning, NOT a proven Category C long because verified support reclaim, higher low and buying-volume structure unavailable. Oct23 issuer press release: new Nasdaq ADS listing and closed **400,000 ADS at $4.65**, each ADS representing **6 underlying common shares**; underwriter option up to 60,000 ADS, NOT evidence of Oct26 selling. Data vendor lists 96.41M shares outstanding, likely underlying common shares: $5.25*96.41M/6 = **$84.36M**, consistent with displayed ~$84.48M cap; unadjusted multiplication would be 6x wrong. ADS security type/SMG short eligibility UNVERIFIED. | BLOCKED: new ADS, after-cutoff discovery, platform eligibility/borrow/halts unknown. |
| **AIOK** | Prior research reference omitted from 113; now retained | **$9.01, -25.04% vs $12.02 previous close, 4:00 PM EDT** | **$9.14, +1.44% from close, quote displayed 4:02 PM EDT** | Oct23 issuer announcement: **$3.50 special dividend**; record Nov2, due-bill period **Nov2–Nov25**, expected ex-dividend **Nov26**. The Oct26 price move is NOT automatically a Nov26 ex-dividend adjustment. News also notes Oct23 halt/resumption and ship sale. Today's >=25% drop is exhausted B absent fresh continuation evidence. No platform short proof. | BLOCKED: corporate-action/due-bill economics, borrow and EOD trigger unverified. |

### Primary dated sources
- CPIX Oct26 quote: https://stockanalysis.com/stocks/cpix/ (page explicitly 4:00 PM close, 4:14 PM after-hours quote).
- CPIX Oct23 announcement (9:05 AM EDT): https://www.stocktitan.net/news/CPIX/cumberland-pharmaceuticals-provides-updated-webcast-registration-smsirzgdl0gv.html ; webcast scheduled Oct26 **4:30 PM EDT**.
- APXC Oct26 quote: https://stockanalysis.com/stocks/apxc/ (page explicitly 4:24 PM EDT after-hours quote).
- APXC issuer Oct23 ADS offering/closing: https://www.accessnewswire.com/newsroom/en/metals-and-mining/apex-closes-offering-and-completes-nasdaq-listing-1240657 .
- AIOK Oct26 quote: https://stockanalysis.com/stocks/aiok/ (page explicitly 4:02 PM EDT after-hours quote).
- AIOK issuer Oct23 due-bill notice: https://www.globenewswire.com/news-release/2026/10/23/3387307/0/en/ai-okto-corp-declares-special-dividend-of-3-50-per-share.html .
- Dynamic ranked after-hours tables https://stockanalysis.com/markets/afterhours/losers/ and https://stockanalysis.com/markets/afterhours/gainers/ showed **inconsistent or changing** prices relative to timestamped individual ticker pages. DO NOT combine ranking snapshot percentages with later per-ticker quotes or call them a synchronized SIP feed.

## Causal missed-move assessment
- **CPIX:** known upcoming event at least three days before close; watchlist retention existed, but no verified preclose signal or screening result. Classification **EVENT_WATCH_NOT_A_PROVEN_CATCHABLE_SHORT**. Today's -48.76% is an *observed collapse*, not a verified missed eligible/executable collapse. No claimed return.
- **APXC:** after-hours surge after regular -20.45% fall illustrates the short-squeeze/reversal hazard. **AFTER_CUTOFF_DISCOVERY**; cannot retrospectively credit an after-hours long or a preclose short. Check six-to-one ADS/share basis before cap or float calculations.
- **AIOK:** structural dividend due-bill and 2026-10-23 news were known in advance, but eligibility/borrow/tape unknown; **EXHAUSTED_B_CORPORATE_ACTION_REVIEW**, not an automatic short.
- **CD, XRPN, WFF, AVBP, SDEV, SECZ, AEHL** and other prior reference names: retained as historical examples; NO new dated preclose price/board evidence from this run, so **OUTCOME_NOT_RECONSTRUCTED**, not 'screened and rejected' or hypothetical winners.
- **Screened/rejected:** none newly verified from a recovered Oct26 preclose board.
- **On-board but failed target:** unknown; no timestamped board.
- **Not screened:** the specific independent Oct26 prospective capture screened zero due provider auth failure; cannot infer status of other scans.
- **Missing/stale bars:** capture unavailable for all names, not a per-symbol negative result.
- **Renamed/corporate actions:** APXC ADS six-share ratio and AIOK due bills require explicit treatment; no unverified ticker aliases invented.
- **Ineligible/borrow unknown:** ALL THREE examples blocked; third-party cap is NOT sufficient proof of SMG eligibility or platform short availability.
- **Unpredictable after-bell news:** no newly confirmed adverse issuer disclosure after 4:00 PM identified for these three in this audit; absence of proof is not proof of absence.

## Isolated research fix and safe follow-through
New pure [after-hours catchability module](obsidian_afterhours_catchability.py) separates a scheduled event known before cutoff from an independently verified tape signal and an actual executable fill; it rejects post-cutoff signals and after-hours outcomes as retroactive trade evidence. It includes an ADS-ratio normalization diagnostic. New offline [regressions](../tests/test_obsidian_prospective_afterhours.py) cover these cases. Research-only CI workflow updated to run them; hosted test outcome must be verified separately, NOT assumed.

For next future session: capture immutable morning, intraday and preclose board with timestamped quotes; separately track after-hours events and pre-decision eligibility; require true platform borrow, split/ADS basis, source timestamps and a pre-specified ≥20% future closing-price outcome horizon. Do not tune on CPIX/APXC/AIOK after observing these outcomes; retain as *reference diagnostic cases*. No trade was placed, and no execution or hypothetical profit is claimed.
