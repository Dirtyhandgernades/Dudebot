# Iteration 009 — read-only cache inventory repair (2026-11-21)

RESEARCH ONLY. Continues iteration 008. No trading, private data, production or baseline changes, strategy challenger, P&L, or promotion.

## Prerequisites and inspected evidence
Read the registered continuous protocol, FAST_DUMP_RANK_RESULTS, FIRM_TIMING_VALIDATION, trade discovery v2 proposal, prospective proof gate, and iteration 008. The original 54 ranked portfolio configurations were previously reproduced in hosted Actions run 44864565861; no redundant rerun was initiated. All 2023–25 periods remain inspected. Iteration 008 established that original run 37386241124 saved 5,338,144 compressed bytes under Actions cache key `intraday-bars-v1-37386241124`; this is distinct from artifact 11378995592. No cache bytes have been recovered.

## Bounded repair actually completed
Committed `backtest/obsidian_walk_forward/inventory_original_cache.py` as a read-only exact-key GitHub Actions cache inventory tool. It queries the documented GitHub REST cache-list endpoint using a separately supplied actions:read token; it does not print credentials, restore bytes, dispatch workflows, contact SMG, or modify existing automation. It reports exact key/ref/size/creation/access metadata and distinguishes missing token, HTTP errors, missing cache and present cache. The file was created on the existing research branch only, commit `542f4f10d1f1a6f6a2558bbcd7361c36a154f59f`.

Attempted unauthenticated network access from the isolated compute container to the GitHub API. DNS/network access failed before an HTTP response. The connected GitHub tool exposes workflow artifacts and job logs but no Actions cache inventory or restore endpoint. Therefore cache presence/eviction is **NOT CHECKED**, not a confirmed cache miss. No privileged token was requested or accessed.

## Reproduction
In an approved read-only research environment with an existing scoped GH_TOKEN:
```sh
python backtest/obsidian_walk_forward/inventory_original_cache.py
```
Output is JSON metadata only. Do not copy tokens into reports. If exact key exists, recover through a separately reviewed research-only workflow with `actions/cache/restore@v4`, exact key and `fail-on-cache-miss: true`, then independently hash and validate original raw/split five-minute requests and pagination before changing any missed-signal attribution. If absent, document eviction and separately label any historical provider reconstruction.

## State and blockers
Original historical baseline: archived modeled normal profits $18,658.11 / $39,124.52 / $103,258.54 for 2023/24/25; not a fresh execution and not independently verified SMG fills. Current iteration starting capital assumption $100,000; new net/ending equity **NOT COMPUTED**. Missing authentic intraday responses, August and late-December coverage, point-in-time eligibility, full-market denominator and fresh independent validation windows block full replay and promotion. Next registered hypothesis remains source-recovery-first, no rule change. Promotion: UNVALIDATED. No live desk, protected baselines, production workflows, alerts, main or orders touched.
