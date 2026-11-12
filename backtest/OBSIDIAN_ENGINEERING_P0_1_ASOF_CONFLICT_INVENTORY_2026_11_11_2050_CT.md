# OBSIDIAN P0-1 research checkpoint — November 11, 2026, 20:50 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only: `research/obsidian-early-rug-20261025`. Original frozen baseline, 136-name retained watchlist, JDZG stale/halt diagnostic, and 0/+1/+2/+3 actual-session matched-cohort rules unchanged.

## Independently checked code and hosted test milestone

- Starting research head `c83acc3dba8c8bbec65598bdf159963109fe2b0a`. Code/test commit [`00feb0c995e6cd591064076b694977887f1e354d`](https://github.com/Dirtyhandgernades/Dudebot/commit/00feb0c995e6cd591064076b694977887f1e354d) was applied with expected-head GitHub lease.
- The offline P0-1 source-body conflict inventory now retains contradictory **current and previous regular-close as-of timestamp claims** from rejected source bodies, even when two other source bodies agree. The original indexed source rows remain censored; the new flags are `PARSED_BODY_REGULAR_CLOSE_ASOF_CLAIM_CONFLICT` and `PARSED_BODY_PREVIOUS_CLOSE_ASOF_CLAIM_CONFLICT`.
- Compare timestamp claims as canonical aware UTC instants, not differing textual offsets, to avoid false conflict for 16:00 ET = 20:00 UTC. Invalid nonempty timestamp claims remain conflicting and rejected, not silently dropped or treated as a completed session.
- Four new synthetic regression cases verify rejected current-as-of, rejected previous-as-of, equivalent UTC-offset, and malformed-as-of behavior.
- Hosted [prospective journal workflow 43144099482](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43144099482) completed **successfully** at 2026-11-12 02:50 UTC on the exact code/test commit. Its job logs confirm **681 prospective tests + 4 separate board tests passed**, including all four new tests. No artifact is produced by this offline regression workflow.

## Verified capture ownership and remaining P0-1 blocker

- Separate Rug Proof [18:20 CT November 11 original postclose audit](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_POSTCLOSE_AUDIT_2026_11_11_1820_CT.md) was reviewed; its 09:20/12:20/14:20/18:20 original markers and delayed-SIP ownership were not touched. No morning, afterhours, early-board, or SIP markers were created here.
- Protected preclose [run 43098152151](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43098152151) and 14:20 delayed SIP [run 43095851523](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43095851523) were still **queued** with no verified artifacts on this check. No retry or backfill was attempted outside the original gates.
- Afterhours IEX and independent-source monitor runs from November 11 succeeded but their single-venue observations and Nasdaq RSS/optional disconnected Massive data do not establish independently authenticated **official regular-session closing prices from two genuinely independent provider organizations**, corporate-action/security-ID continuity, full session calendar evidence, source-owned publication/transport proof, actual SMG account permission/shortability, or complete forward outcomes.
- This is an **offline source-conflict accounting improvement only**, not an official-close proof, new provider entitlement, verified >=20% forecast, win/loss, borrow confirmation, fill, or P&L. Missing 0/+1/+2/+3 actual-session outcomes remain **CENSORED**; preserve all false positives, late/exhausted cases, squeezes, costs, missingness, and third-source conflicts.

No main/production/credential edits, market orders, notifications, duplicated captures, frozen-label changes, or unauthorized account access.
