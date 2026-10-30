# OBSIDIAN autonomous engineering checkpoint — October 30, 2026, 15:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only. No trades, credentials, production/main changes, alerts, or unauthorized captures.

## Material P0-2/P0-3 correction — protected preclose cohort can now enter a censored four-session ledger

The existing `obsidian_prospective_maturity_ledger.py` accepted only original MORNING/INTRADAY discovery captures; the protected **14:47 CT IEX prospective preclose capture** has a distinct original manifest and `screen_status` schema. It could not previously enter the same full-denominator non-scoring outcome-coverage audit without mislabeling the frozen cohort.

Added a separate `_audit_preclose` adapter that:
- Replays the original protected `obsidian_iex_prospective.verify` hash, manifest, security identities, classification and clock gates before reading any outcome rows.
- Preserves every original preclose ticker and original watch/exhausted/no-watch/missing classification, with **four 0/+1/+2/+3 actual calendar-session slots** per issuer.
- Rejects duplicate/out-of-cohort outcome rows, preserves missing and conflicting evidence, quarantines structurally inconsistent rows and broken previous-session price chains; all offline vendor claims remain **unauthenticated and censored**.
- Explicitly labels `capture_phase=PRECLOSE` and `preclose_is_separate_unmatched_cohort=true` to prevent treating the preclose capture as an earlier morning/intraday prediction. Existing frozen evaluator, labels, cohort and 136-name roster are unchanged.
- Adds five synthetic regression tests and includes both new code and tests in the existing research CI path filter.

Implementation commits: `10fb0a4d4244dd8a5a1b77f9e54633ab50058c14`, `d645771647b57f2cf856a336651580ac3bf6ed82`, `3ca91a61309431fe918c090473c09e04bc9349c6`.

**Hosted GitHub Actions [run 41125974269](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41125974269): completed SUCCESS** on code head `3ca91a61309431fe918c090473c09e04bc9349c6`. Logs show **530 prospective offline tests passed plus 4 ABC board tests**, including all five new preclose maturity tests. This is a structural regression milestone, **not** evidence of prospective 20%+ collapse accuracy.

## Original evidence and cross-task coordination checked before editing
- Protected Oct30 14:47 preclose original: [run 41118123273](https://github.com/Dirtyhandgernandes/Dudebot/actions/runs/41118123273), original artifact `13006897253`, 8,510 rows, 1,653 **price-only** watches, 21 exhausted, 4,357 stale/future trades; artifact ZIP SHA256 `ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`, metadata matches hosted upload log. This checkpoint **did not download and ingest** that original raw artifact into the ledger; no live performance was computed.
- Distinct Rug Proof delayed SIP original [run 41114832467](https://github.com/Dirtyhandgernandes/Dudebot/actions/runs/41114832467), completed success, artifact `13006191628`; delayed SIP is not an official close or real-time entitlement.
- Existing separate 15:24 CT After-Hours discovery [run 41122875045](https://github.com/Dirtyhandgernandes/Dudebot/actions/runs/41122875045) succeeded, original artifact `13008429628`, 8,510 rows; 12 IEX indicative observations at that phase are **not** fresh trading predictions.
- Existing independent source monitor [run 41122875006](https://github.com/Dirtyhandgernandes/Dudebot/actions/runs/41122875006) succeeded; Nasdaq RSS parsed with as-of limitations, `quotes_connected=false`, `realtime_entitlement_verified=false`, 136 watchlist symbols. Hosted environment exposed an empty `OBSIDIAN_MASSIVE_API_KEY` (no secret value printed). Artifact `13010065001`, ZIP SHA256 `f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`, matches upload log.

No new Rug Proof, Morning Movers, After-Hours, Early Decision Board, IEX intraday, independent monitor, or protected preclose marker was created or retried. The engineering checkpoint was outside the protected capture windows.

## Remaining P0 blockers
The **real** Oct30 8,510-row preclose artifact has not yet been ingested with an independently authenticated four-session exchange calendar and admissible independent official closes. Two genuinely independent source organizations with authenticated exchange-official regular closes, identity/corporate-action provenance and third-source conflict inventory remain unverified. Future sessions +1/+2/+3 have not matured as of this checkpoint. Missing outcomes remain censored; **verified >=20% prospective prediction success, false-positive rate, risk-adjusted returns and SMG execution eligibility are NOT established**.

Next measurable step: load the immutable original artifact into the new adapter with an externally verified session calendar and preserve its full 8,510 x 4 slot inventory; separately authenticate actual independent official closes as they mature. Do not fabricate outcomes or modify original labels.
