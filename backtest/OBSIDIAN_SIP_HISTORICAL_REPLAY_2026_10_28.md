# October 28 OBSIDIAN delayed-SIP fallback feasibility experiment
RESEARCH_ONLY_NOT_AN_ORDER. **Not an earlier prospective prediction or new original capture.**

Purpose: verify whether the existing paper Alpaca connection can access **historical consolidated SIP 1-minute bars** with a 17-minute safety lag and whether such data can reduce the single-venue IEX missingness for **future** research checkpoints. Data observed after the original Oct28 intraday decision **cannot be backdated** or scored as a historical machine signal.

Locked source: original authenticated Oct28 12:52 Central intraday IEX [run 40739809362](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40739809362), artifact 12837584509, 8,511 rows, original raw SHA256 `1ca1cf79c79c8a18a7913b088dbefba655e9226b3d07f7582e48eb0fee90db9b`. This is a source-limited research replay; no frozen original IEX label is rewritten.

The workflow performs a 13-name availability probe; TP is absent from the original selected universe and therefore explicitly excluded, not quietly treated as an observed ticker, then expands to all original 8,511 if historical SIP returns valid bars. The fallback preserves original capture source timestamps, GET attempt times, 17-minute cutoff, request failures, unavailable symbols and original-universe counts. A 15-minute-lag research feed is NOT the full real-time SIP service. It does not confirm official previous close, live borrow, liquidity, halts, capitalizations, eligibility or actual trades. 
