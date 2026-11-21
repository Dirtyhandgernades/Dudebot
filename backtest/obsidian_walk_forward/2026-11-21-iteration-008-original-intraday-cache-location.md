# Iteration 008 — original five-minute cache located in Actions cache metadata (2026-11-21)

RESEARCH ONLY. Continues iteration 007. No strategy challenger, trading, SMG access, secrets, production edits, new portfolio P&L or promotion.

## Prior protocol and evidence
Read `backtest/OBSIDIAN_CONTINUOUS_WALK_FORWARD_PROTOCOL_2026_11_20.md`, `backtest/FAST_DUMP_RANK_RESULTS.md`, `backtest/FIRM_TIMING_VALIDATION.md`, `backtest/OBSIDIAN_TRADE_DISCOVERY_PLAYBOOK_V2_PROPOSAL_2026_11_20.md`, `backtest/OBSIDIAN_PROSPECTIVE_TRADE_EDGE_PROOF_GATE_2026_10_30.md`, the diagnostic replay negative control and iteration 007. Original ranked baseline was reproduced previously in hosted run 44864565861 (54 configurations), not rerun here. 2023–25 remain inspected retrospective data.

## Material new source-location evidence
Read original GitHub Actions run **37386241124**, job **112020106723** (`replay`), full job logs and artifact inventory. The workflow explicitly used `actions/cache/restore@v4` and `actions/cache/save@v4` with:
- **Cache path:** `backtest/runtime/intraday-bars`
- **Exact cache key:** `intraday-bars-v1-37386241124`
- **Restore prefix:** `intraday-bars-v1-`
- **Save log:** `2026-10-05T23:04:10.3147798Z Cache saved with key: intraday-bars-v1-37386241124`
- **Saved compressed bytes reported by job:** 5,338,144 (not independently downloaded or SHA-verified)
- **Job log URL:** https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37386241124
- **Original artifact:** `pre-close-firm-37386241124`, artifact ID `11378995592`, 11,294,854 bytes, unexpired at inspection. The artifact is separate from the Actions cache and does not contain the original five-minute response directory.

This changes the prior diagnosis from **unknown whether persisted** to **saved by Actions cache with a known exact key**. It does NOT prove that the cache is still available on November 21: GitHub Actions caches may expire or be evicted. It is not accessible through the GitHub connector's artifact-download endpoint; do not misidentify the 11 MB artifact as the 5 MB cache.

## Source validation
`smg/intraday_replay.py` Git blob `2aa2a4e2d3155325b45b34ab4da7358afaad96d3` confirms `Bars('backtest/runtime/intraday-bars',...)`. Cache files are SHA256(JSON sorted request query) plus `.json`, separate for `adjustment=split` and `adjustment=raw`, including paginated requests. Validate exact query, source run, request timestamp/provenance, all page tokens, complete five-minute session bars, raw/split pairing and SHA256 per response before claiming original signal reconstruction.

## Concrete next bounded recovery action
Use **read-only GitHub Actions cache inventory**, ideally `GET /repos/Dirtyhandgernades/Dudebot/actions/caches?key=intraday-bars-v1-37386241124`, with a permitted scoped repository token. If present, use a research-only runner with `actions/cache/restore@v4` exact key and `fail-on-cache-miss: true` to copy the original directory into a separate research-only artifact, without touching live automation or accessing SMG/private account data. Before any workflow, inspect proposed permissions and ensure no production dispatch or credential exposure. If the key is absent, document eviction and pursue a separately labeled historical public-data reconstruction. No cache bytes were retrieved in this iteration; no five-minute signal reclassification or portfolio return was computed.

## Status
New material evidence: exact persisted cache key and confirmed successful save. Historical 142 missing-signal rejection reasons remain UNKNOWN pending actual raw/split responses. Full Aug–Dec coverage and execution eligibility remain blocked. Synthetic starting balance $100,000; new net/ending equity NOT COMPUTED. Promotion NOT VALIDATED. No production or Portfolio Desk changes.
