# OBSIDIAN — October 26 missed-move coverage and early discovery implementation
**Research branch:** `research/obsidian-early-rug-20261025`  
**Mode:** RESEARCH_ONLY_NOT_AN_ORDER  
**Compiled:** October 27, 2026 — from existing immutable reports, chat-context references and inspected Actions artifacts.

## Observed coverage vs manifests
- Recovered master: **113** retained names. Supplemental: **23**. Combined **136** distinct retained. NOT screened universe.
- Date-only provenance records: **38** describing **36** distinct tickers. **14** previously retained and **22** absent recovered manifests, but previously mentioned in the documented audits.
- **Absent recovered manifests but observed elsewhere:** XP, AGBK, PICS, INTR, AFYA, STNE, BRAI, EIKN, ITGR, DVLT, SPRC, ONCO, SNTI, ARTV, HQY, ZSQR, RFAI, ELWT, INOD, MFIC, CLRO, ACRS.
- **Already retained and mentioned in this evidence set:** CPIX, AIOK, APXC, AEHL, SECZ, AVBP, WFF, GCTK, GCDT, MKDW, NAUT, IPDN, MRNA, XLAB.
- **Authenticated Oct26 preclose scanner rows recovered:** **none**. This means **UNKNOWN** screening coverage, NOT zero actual screening and NOT 22 proven missed executable trades.
- No original 98-symbol/57-missing-price per-ticker archived screen ledger was recovered by this audit. Do not assign those historic gaps to the symbols above.

## Timing and evidence
- CPIX Oct23 post-cutoff issuer release existed ahead of Monday; no authenticated Monday preclose tape/SMG borrowing. Monday collapse is retrospective. A Oct26 afterbell FDA/NDA release cannot explain prior regular close.
- XP and other Brazil-related names: election shock publicly reported prior to Monday U.S. session, but XP was vendor-observed already ~49% down **before** the 14:45 CT execution window. These are late-discovery cases, not pre-event predictions.
- AIOK: special dividend/due-bill and shelf registration warrant corporate-action and issuance-vs-saleability checks; neither registration nor warrants establish actual sales.
- APXC: U.S.-listed ADS (six underlying common shares per ADS) excluded by common-stock gate; intraday/afterhours rebounds are squeeze risks.
- EIKN: conflicting vendor regular-close records are **outcome-censored**, not accepted as independently verified >=20% close.
- ITGR: asynchronous leaderboard vs ticker-detail quote conflict; no synchronized 20% drop established.
- ARTV: Oct27 negative issuer press release was **not public** at the Oct26 EOD decision despite an earlier private board decision. Morning discovery already followed a ~30% premarket repricing; cannot be scored as early catch.

## Material implementation
1. `obsidian_early_discovery.py.reconcile_coverage` creates per-symbol provenance and distinguishes retained, mentioned, authentically scanned before cutoff, authentically scanned only after cutoff, and unknown. A chat or report note is **not** a scanner receipt.
2. `audit_archive_health` refuses to accept a green/ARCHIVED workflow status as evidence of a complete usable scan.
3. `prioritize_early_discovery` scores only **ordinal research attention**, prioritizing a dated adverse mechanism + independently timestamped fresh tape while the move is still early. A price-only -2% setup is only a watch; -15% to -25% is intermediate; >=25% pre-existing declines are exhausted. Morning/afterhours discoveries never inherit the EOD execution clock.
4. Quote and prior regular-session close must have independent as-of proof, values matching the row, completed prior session and freshness. Unverified or conflicting bars are censored. Filing registration alone is not actual issuance, saleability, or observed selling.
5. Frozen OBSIDIAN policy and journal remain unchanged. This is an **offline research diagnostic**, not a connected scanner or verified SMG trade.

## Workflow/artifact reconciliation
- Latest pre-change research CI [40511693710](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40511693710) successful (218 offline tests). New early discovery CI [40512919272](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40512919272) passed 234 offline tests; additional strict-close evidence checks need their own hosted CI.
- [Main archive 40510465196](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40510465196) failed. Downloaded `evidence-archive-40510465196` reports **166** symbols, `market_rows=0`, `asset_available_rows=0`, `asset_unavailable_rows=166`, despite `status=ARCHIVED`; not a successful screened market board.
- [Matched comparison 40260569154](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40260569154) artifact shows no established edge from the fixed -2% filter; tested 2023–2025 are contaminated development years.
- Prospective Oct26 capture #3 [40389830214](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40389830214) has **no capture artifact**. Do not retry/backfill.
- Later verified independent closing outcomes, full eligible-universe denominator, lead times, misses, squeezes, after-cost returns, and a matched untouched forward comparison remain **unmeasurable** until complete write-once captures exist.

## Next verification gate
Acquire fresh, independent authenticated scanner candidate+coverage inventory in a **future** session; preserve all screened/rejected/unknown rows with observed/published timestamps. Run new research triage against it, then in the authorized 14:45–14:58 CT session only run the existing one-attempt future-date IEX capture as separately instructed. Label IEX single venue, not SIP or official fill. After future regular-session close, separately verify outcomes and compare incumbent/challenger on identical eligible denominators. **No winner-selected universe, retroactive prediction, rank-as-probability, or $160K sizing exception.**
