# OBSIDIAN — Oct 28, 2026 authorized 15:22 CT after-hours IEX checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER**. This report uses the original authenticated provider artifacts, not reconstructed hypothetical executions. All times America/Chicago unless marked UTC or ET. Never treat single-venue IEX reference prices as official regular-session closes.

## Authorized checkpoint and run
- Scheduled After-Hours Audit checkpoint: Wed Oct 28 **15:22 CT**; actual audit began **15:25 CT**, within the independently authorized 15:00–15:45 CT window. No prior marker or after-hours trigger existed for the date. The official [Nasdaq 2026 schedule](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule) and [NYSE 2026 calendar](https://www.nyse.com/trade/hours-calendars) establish a normal trading session.
- Verified the branch-only workflow `.github/workflows/obsidian-iex-research-discovery.yml` and prior passing standalone discovery run [40739809362](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40739809362), as well as research offline CI run [40748516089](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40748516089).
- Created **exactly one** marker `backtest/OBSIDIAN_IEX_RESEARCH_DISCOVERY_TRIGGER_2026_10_28_AFTERHOURS.md` on `research/obsidian-early-rug-20261025`, commit `c2afb57fa8e5f4bd2f3262405689415e3dbbf0bf`.
- New branch-only authenticated after-hours [GitHub Actions run 40763211800](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40763211800): **completed SUCCESS**. 11 dedicated offline tests passed; collection, independent hash replay and artifact upload all succeeded.
- Original raw artifact **12849591039**, `obsidian-iex-research-discovery-40763211800`, downloaded and independently inspected; **8,511 requested/retained symbol rows**; source 14,403 active paper Alpaca assets, NYSE/Nasdaq subset 8,511; 86 GET batches. Source capture 2026-10-28 **20:26:00.937387–20:26:09.213297 UTC**.
- Cryptographic integrity: `universe.jsonl` SHA256 `9d469faf2b6e43c8a8c5edec0eb65a4ea562261174faca8aaf0f0e6728802ebb`; `attention.json` SHA256 `bf99236f511916f63c9fe24123a7060f96fa970adcaba0fbd932e3d0d72e2e5a`; `manifest.json` SHA256 `b092c47fae52363c22fba586a7d0ac6d2c8095f261222591c928c5879f896a91`. The first two agree with manifest digest declarations. `previous_reference_is_official_close=false`, `trading_session_independently_confirmed=false` in provider artifact, `future_regular_close_outcomes=null`, `smg_eligibility_confirmed=false`. Exchange calendar independently checked in this audit, not misattributed to the raw artifact.

## Critical after-hours data quality
- **8,375/8,511 (98.40%) stale/future IEX last prints** under the frozen 15-minute freshness gate. This is expected to be a severe source-limited after-hours coverage blocker; do not call these live movers or treat their unchanged last prices as postclose performance.
- **102** missing trade/prior pairs; **2** missing snapshots; **1** sub-$3 indicative price-floor block; **25** other usable IEX price observations; **5** early indicative IEX-reference watches; **1** intermediate indicative IEX-reference watch. Only **32/8,511** have non-stale, non-missing IEX status (one is price-floor blocked). No full-market after-hours coverage, no official prior close, no SMG borrow, no order authorization.
- This is a successful authenticated raw capture, **not** a verified forward-collapse success.

## Reconciliation with immutable preclose board (Oct 28)
Original preclose source: [GitHub Actions run 40757495722](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40757495722), artifact **12846452112**, original **8,511** rows, capture 2026-10-28 **19:47:59–19:48:06 UTC** (14:47 CT). All figures below compare independent single-venue IEX *last trades* in the original two captured files; percentages are **not** verified official close-to-afterhours returns. No fills or trading permission is inferred.

| Ticker | 14:47 CT preclose IEX last | 15:26 CT IEX last | Last-to-last change | Original preclose class | Afterhours interpretation |
| --- | ---: | ---: | ---: | --- | --- |
| NOW | $149.105 | $130.00 (20:14:24 UTC) | **-12.81%** | `IEX_EARLY_WEAKNESS_WATCH_ONLY` | Price-only preclose recognition; *not* advance earnings knowledge or 20% regular-close proof. |
| GOOG | $322.24 | $295.46 (20:23:26 UTC) | **-8.31%** | `IEX_NO_EARLY_PRICE_ONLY_WATCH` | Screened/no-watch; Alphabet earnings were scheduled for after close, so do not retroactively assert preclose catalyst knowledge. |
| CHKP | $154.97 | $146.23 (20:12:28 UTC) | **-5.64%** | `IEX_EARLY_WEAKNESS_WATCH_ONLY` | Price-only preclose recognition; catalyst publication timing not independently verified in this pass. |
| CRWD | $265.51 | $254.16 (20:25:59 UTC) | -4.27% | `IEX_NO_EARLY_PRICE_ONLY_WATCH` | Screened/no-watch; do not invent adverse news or executability. |
| CBRS | $111.77 | $111.09 (20:25:27 UTC) | -0.61% | `IEX_EARLY_WEAKNESS_WATCH_ONLY` | Candidate watch without material new verified after-hours continuation. |

ServiceNow announced on Oct 7 that its Q3 results would publish **after the Oct 28 close** ([official issuer announcement](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-to-Announce-Third-Quarter-2026-Financial-Results-on-October-28/default.aspx)). Alphabet announced an Oct 28 **16:30 ET** earnings call and a release ahead of it ([Oct 6 issuer announcement](https://www.publicnow.com/view/44136C85C4D5D099F2F1F5740EF199299B51D499)). These are dated *event schedules*, not proof of exact new result-publication timestamps or the causal explanation for a quote move.

## Same-day already-exhausted decline audit
- **BCAX:** original intraday 12:52 CT IEX print $9.87 vs IEX previous bar $17.50 (about -43.60%), already **EXHAUSTED**; original preclose 14:47 CT $9.88 still **EXHAUSTED**. The afterhours IEX trade was stale, so it is **not** a valid afterhours continuation. No early-catch credit.
- **INBX:** original intraday 12:52 CT $71.00 vs previous IEX $95.83 (about -25.91%), already **EXHAUSTED**; original preclose $71.02 still exhausted. Afterhours trade stale; no early-catch credit.
- **MTLS** and **FFIV:** intraday price-reference declines about -22.54% and -20.36% were recognized as intermediate, not proven pre-collapse. At preclose both were no early-price-only watch; no verified advance mechanism, borrow or later official close. No manufactured wins.
- Reference-watch reconciliation: CD preclose early IEX weakness $9.42; WFF preclose weakness $0.0528 but far below $3 and not eligible; XRPN preclose stale; AVBP/SECZ no watch; AEHL very thin single-venue tape; SDEV not in the 8,511 original symbol universe. None is assumed a current holding or actionable short.

## Frozen forward-rug outcome gate
The frozen `backtest/OBSIDIAN_IEX_FORWARD_STUDY_FROZEN_2026_10_27.md` and `backtest/obsidian_forward_collapse_study.py` remain **unchanged**. At this 15:26 CT pass there is no full 8,511-symbol JSONL of two independently timestamped, agreeing **official prior/current 16:00 ET regular-session closes**, with independently reviewed corporate-action and security identity comparability. Therefore **verified early hits, misses, recall, precision, adverse squeezes, and after-cost P&L are all UNKNOWN**, not zero. Postclose 15:26 CT prices cannot be used to score Oct28 regular-session predictions. Missing and corporate-action-conflicted rows remain censored.

No main, production, frozen scoring policy, credentials, live alerts, orders, trade authorizations or holdings were changed. No repeat trigger is authorized for this date/phase.
