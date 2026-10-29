# OBSIDIAN — actual October 28 rug-catch and data-rescue experiment

**RESEARCH_ONLY_NOT_AN_ORDER.** Published after the October 28 outcomes; not an untouched forecast, official price proof, or SMG trading signal.

## A. Actual original frozen prediction-label replay vs dated October 28 losers

Independently re-read the October 28 **MORNING run 40704289113 / artifact 12822044262, INTRADAY run 40739809362 / artifact 12837584509, and PRECLOSE run 40757495722 / artifact 12846452112**. Each contains **8,511** requested original source tickers; SHA256 for raw `universe.jsonl` was checked against its own manifest.

As an external **provisional vendor outcome reference only**, the Oct28 postclose <https://stockanalysis.com/markets/losers/> page listed these 20 names at 20%+ declines: JDZG, PLCE, BCAX, HUHU, MWYN, MEGL, SCKT, MKDW, MF, SVRE, NXXT, OTLY, RUBI, HTCO, FSP, INBX, PARA, AIAI, MTLS, CENN. This is **outcome-selected after the fact**, *not* an unbiased sample of all 8,511 names; no sample precision/recall or future edge can be claimed from it. Other same-session vendors, including <https://stocksetups.com/movers/today>, disagree on some closing prints (JDZG $1.43 versus $1.50; BCAX $9.73 versus $9.76); none of these vendor closes is independently verified as an official regular 16:00 ET exchange closing print with unchanged shareholder entitlements. Do NOT ingest this vendor list as a validated frozen forward outcome.

- **19/20** externally listed losers were in the immutable 8,511 symbol morning source universe; **FSP** was absent, so its absence must not become a false model rejection.
- **4/20** showed an original **MORNING IEX price-only watch**: BCAX, INBX, OTLY, MTLS. No first intraday price-only watch was found among the 20; **CENN** was labeled preclose price-only watch *after* falling below $3 and so was **not executable**.
- Comparing the original morning trade to ONE vendor's reported finish, using *the IEX prior daily reference rather than an authenticated official previous close*: **BCAX $13.73 to $9.76: approx 51.29% of the proxy total decline still remained**; **INBX $88.00 to $73.29: approx 65.26%**. Two **potentially early observational watches**, NOT two validated predictive wins, actual fills or SMG-eligible shorts.
- **OTLY $8.745 to $8.56: approx 5.98% of proxy decline remained**, already late; OTLY is an ADS. **MTLS $6.77 to $6.78**: proxy remaining fraction negative, already late; MTLS is also an ADS and SMG-eligible instrument class unverified. Original < $3 cases remain hard-blocked.
- **JDZG** was present at every Oct28 selected source phase but morning and intraday IEX last trades were stale, and at preclose the observed $1.33 was already exhausted. First major external-recorded halt began 13:14:21 CT and repeated pauses extended through the protected 14:45–14:58 CT execution window. Source Alpaca asset metadata `shortable=false`, but actual **SMG** platform borrow not independently verified. JDZG has **no credited early prediction**.
- This retrospective outcome-conditioned set cannot measure false positives among the other ~8,491 scanned names. No verified real-prediction accuracy / market recall / after-cost P&L from these observations.

## B. Actual authenticated historical consolidated SIP data-rescue run

[GitHub Actions **40801276955**](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40801276955) SUCCESS. Artifact **12866685199**, `obsidian-delayed-sip-oct28-historical-40801276955`. Locked ORIGINAL Oct28 **12:52 CT intraday** IEX run 40739809362, source raw SHA **`1ca1cf79c79c8a18a7913b088dbefba655e9226b3d07f7582e48eb0fee90db9b`**. GET-only historical consolidated Alpaca SIP **1Min** bars up to the original observation minus **17 minutes**; observed during later research replay at approx Oct28 **20:35 CT**, *not* at the historical decision time. **All 86/86 historical SIP request batches completed**, original 8,511 symbols retained.

| Exact original-denominator outcome | Count |
| --- | ---: |
| Original IEX source-unusable (stale, missing, unverified previous day) | **5,064** |
| Original IEX with some usable source classification (not necessarily eligible) | **3,447** |
| Fallback SIP recent relative to delayed as-of | **5,409** |
| Fallback SIP stale relative to delayed as-of | **1,215** |
| Fallback SIP no 1Min bar within requested window | **1,887** |
| Previously IEX-unusable now **historically reconstructable** with lagged SIP bar | **2,012** |
| IEX-unusable STILL lacking a recent SIP bar | **3,052** |
| Combined source classifications with recent IEX OR historically reconstructable SIP data | **5,459** |

The combined 5,459 are *not* all live, actionable, price above $3, common stock, liquid, unhalted, nor a source of 5,459 bearish predictions. IEX source prints and 17-minute-lag historical SIP bars have different as-of timing and cannot be treated as simultaneous real-time quotes.

- **JDZG** at original 12:52 CT intraday: its reconstructed eligible SIP 12:34–12:35 CT bar closed **$6.205**, approximately +1.72% relative to the IEX previous daily reference $6.10. This **did not reveal the impending afternoon crash**; stale-source repair alone cannot predict sudden, new halt/crash catalysts. True historic SIP GET was performed **after** JDZG's collapse.
- **MF**: original IEX stale; SIP eligible bar at delayed source as-of ~$6.01 versus IEX reference $10.165, already approximately **-40.9%**, late/exhausted.
- **PARA**: original IEX stale; delayed SIP ~$3.51 versus IEX reference $4.54, already approximately **-22.7%**, intermediate observed price weakness, but original paper metadata `shortable=false` and genuine SMG short availability unknown.
- Among the original IEX-unusable symbols with a recent SIP bar and both IEX reference/SIP price at least $3, **139** had reconstructed -2% to -15% IEX-relative weakness, **8** had -15% to -25%, and **5** had already lost at least 25%. These include possible preferreds, funds, ADS and restricted securities, and are NOT 147 new verified executable shorts or historical machine predictions.

## C. Changes implemented and verified
- Branch-only `backtest/obsidian_sip_fallback.py`: GET historical SIP with explicit 17min embargo, 1Min bar-end timestamp handling, pagination completeness, symbol-set inventory, no silent provider request errors, lookback freshness, full original source denominator, pinned hashes/write-once artifact, and no retroactive original predictions.
- Research regression CI [run **40801156580**](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40801156580) passed **366 tests**.
- New preregistered *genuinely future* **14:15–14:30 CT** prospective research mode uses a **new real observation clock** and new policy variant. Hosted CI [run **40801694325**](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40801694325) passed **369 tests**. It has NOT yet produced a prospective market capture.
- Research-only GitHub workflows `.github/workflows/obsidian-rug-proof-anchor.yml` and `.github/workflows/obsidian-rug-proof-delayed-sip.yml` established, but their first future runs are **unverified**. They do not modify old original EOD capture windows.
- One ChatGPT weekday automation **OBSIDIAN Rug Catch Proof** created and enabled for **09:20, 12:20, 14:20 and 18:20 CT**, starting Oct29, to create checked markers, inspect real jobs, and later audit independently verified EOD. It has its own platform-assigned task conversation; do not claim delivery in the user's current chat. Old tasks remain paused.

## D. Still not solved or proven
- A source data feed cannot be forced to print a recent trade for a halted/illiquid symbol; **3,052** original IEX-unusable names still had no sufficiently recent lagged SIP bar. Price-source coverage and live quote availability must be separately measured; all remaining gaps retained as explicit UNKNOWN/research.
- SIP historical 17-minute lag is **not** real-time SIP and could miss a sudden 15-minute collapse; separate properly authorized real-time consolidation or independently verified halt feed is required for stronger immediate situational awareness.
- Original selected scope lacks some NYSE American and other venue securities (e.g. TP; FSP absent), and may include ineligible ordinary/ADS/ETF/preferred types. Future separate full-asset universe expansion and platform borrow evidence needed.
- Need actual **untouched** subsequent-session write-once signals; October 28 after-outcome audit can only diagnose. Need independent 16:00 ET prior/current official closes, 2 different provider organizations, verified market session calendar and corporate-action/security IDs. No validated conditional precision/recall or after-cost P&L exists yet.
- Do not train on these October 28 known winners or add manual exceptions to their codes.
- No production, main, frozen original prediction files, credentials, live alerts, actual trades or orders changed.
