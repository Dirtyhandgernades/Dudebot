# Iteration 011 — recovered ranked-output artifact integrity (2026-11-21)

RESEARCH ONLY. Append-only continuation of iteration 010. No trading, protected baseline changes, workflow execution, deployment or promotion.

## Evidence and actual operations
Read protocol, diagnostic negative control and iteration 010 on branch research/obsidian-early-rug-20261025. Root-level FAST_DUMP_RANK_RESULTS.md, FIRM_TIMING_VALIDATION.md, trade discovery proposal and prospective proof gate were not at root; direct original report comparison remains pending (protocol has historical summary).

Downloaded GitHub Actions artifact **14691551088** from run **44864565861** using the connected GitHub artifact download action. Local isolated ZIP `github-actions-artifact-14691551088.zip` was **24,231,718 bytes**, SHA256 **95f916cdc1d988f752a49f14c38852c1f9876c5ddfd535bb915c19f840ea1ba1**, exactly matching GitHub's reported artifact digest. ZIP CRC integrity test passed (no bad entry). Contains 158 files; `backtest/target-rank-2026-10-05/` includes 54 policy-year-cost JSON results, 54 trade CSVs, three model JSON files and a summary JSON. This is an **archived hosted run**, not a new execution of unmodified target_rank_research.py.

Parsed all 54 JSON configurations and compared their net_profit, ending_balance, closed_trades, signals and max_observed_drawdown_pct against their respective summary.json rows: **270/270 fields equal, 0 mismatches**. This establishes internal archive consistency, **not** a comparison with the original FAST_DUMP report or independent ranker reproduction.

### Selected archived conditional simulations (starting $100,000 per year)
|Year|Policy|Base net|Stress net|Base trades|Base DD %|Stress DD %|
|---|---|---:|---:|---:|---:|---:|
|2023|top_half $30k/25%|15,587.70|13,809.62|3|2.550|3.395|
|2024|top_half $30k/25%|37,403.93|26,795.01|16|17.465|21.162|
|2025|top_half $30k/25%|73,815.54|48,528.08|38|15.274|20.474|
|2023|top_half_30pct $50k/30%|18,658.11|16,487.95|3|3.059|4.069|
|2024|top_half_30pct $50k/30%|39,124.52|25,305.11|16|25.691|29.486|
|2025|top_half_30pct $50k/30%|103,258.54|64,020.56|36|19.966|25.171|

The aggressive variant's figures match the numbers cited by the registered protocol. Historical results already inspected, conditional, and not SMG-confirmed fills. No new P&L or independent ending equity computed.

## Remaining blockers / next registered step
1. Retrieve original FAST_DUMP_RANK_RESULTS.md from its actual repository path and compare all 54 configurations including position/trade rows and stress. Independently execute unmodified ranker on original archived artifact 11378995592 only if inputs and safe dependencies available.
2. Original five-minute cache availability still unverified; August and late-December point-in-time coverage incomplete; eligibility/short permission unverified.
3. No fresh prospective nonoverlapping windows, no promotion proof.

**Promotion status: UNPROVEN.** Original ranker and all live systems unchanged.
