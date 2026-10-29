# Broader free-feed scope and verified SEC rotation — Oct29 2026

RESEARCH_ONLY_NOT_AN_ORDER. Current source-feed coverage overlay adds CBRS/RAPP/SPTX to retained 136; all 139 preserved. No frozen historical cohort, prior prediction, threshold or outcome modified.

Existing first packet 40929567179 seeded eight actual successful SEC checks. New run 40932613239 selected CBRS,RAPP,SPTX,AMTD,APUS,APXC,ARTL,AVBP, all successful. Run 40932728198 restored that artifact state and selected AVTX,AVX,BBCI,BDRX,BENF,BMEA,BMGL,BNC, all successful, disjoint from prior batch. Both packets independently downloaded; all 139 symbols retained and all executable/trade flags false. Total unique successful SEC metadata checks 24, remaining first-check coverage 115. Metadata checks are not completed catalyst/counterevidence research.

CBRS/RAPP/SPTX were present in both current scopes, with usable delayed SIP and successful SEC metadata in the first expanded run; their IEX trades were stale. Latest packet: 24 fresh IEX trades, 115 stale; delayed SIP 108 fresh at safe cutoff, 23 stale, 8 missing. No real-time consolidated claim. No actionable signal or prediction accuracy established.

Read-only workflow serializes runs, restores compatible successful artifact state, does not roll back a newer repository snapshot, and uploads packet plus updated state together. Reviewed state snapshot persisted separately at backtest/evidence/free-quant-sec-rotation.json. No automated Git write permission or auto-push is enabled. Artifact expiry can require safe repeat checks from the reviewed durable snapshot; no silent state reset. Two early verification runs were cancelled before source collection because full-history checkout stalled; shallow checkout fixed the prerequisite.

Local regression suite: 891 passed plus 27 subtests; both live runs also passed offline tests before collecting sources. No new recurring schedule; rotation advances whenever the existing manual workflow is run. Full raw packets and state remain in the linked Actions artifacts; compact hashes, batches, coverage, run URLs and source commit provenance recorded here.
