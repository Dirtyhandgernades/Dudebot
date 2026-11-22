# OBSIDIAN iteration 032 — artifact producer source compatibility (2026-11-22)

RESEARCH ONLY; continuation after iteration 031. Authorized branch research/obsidian-early-rug-20261025. No SMG authentication, trading, production changes, protected baseline edits or promotion.

## Required source review
Read continuous walk-forward protocol, proposed discovery playbook, prospective proof gate, diagnostic cycles 1–2 negative control, and iteration 031 inventory. Read historical FAST_DUMP_RANK_RESULTS.md and FIRM_TIMING_VALIDATION.md from backtest/ (not repository root). Existing 2023–25 seasons are inspected, not fresh holdouts.

## New verified compatibility finding
The artifact-producing commit b8fbd035543611f49992d6df3b619af7a6ddf548 does **not** contain backtest/target_rank_research.py: direct GitHub contents lookup at that commit returned 404. The authorized research branch does contain that file at Git blob e574c908eeb5fafbf918200296b01eeaf8dafbdd. The FAST_DUMP_RANK_RESULTS.md file likewise does not exist at the producer commit but exists on the research branch at blob 617d7606b11b92e0ccc87bfc70f44eb7544102d6. By contrast, backtest/FIRM_TIMING_VALIDATION.md is the same blob 88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178 at both refs. A GitHub compare reports the branch ahead of the producer commit by 990 commits, behind by zero; its file listing is capped at 300 entries, so it is not exhaustive.

**Interpretation:** the artifact archive is an *input provenance seed* generated before the later target ranker/report were added, not evidence that the target ranker itself was run at the producer commit. The requirement to reproduce the original ranker unmodified should therefore pin the research-branch ranker source and its own contemporaneous dependencies, and separately verify that the archived inputs are schema-compatible. Do not misstate producer-commit source identity or substitute another ranker. This resolves a provenance ambiguity but does not establish executable compatibility.

## Blockers / next step
Still need to assemble the pinned source tree and artifact 11378995592 (GitHub Actions run 37386241124), independently verify archive SHA-256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, inspect archived input schemas and the ranker's input expectations, then execute python -m backtest.target_rank_research unmodified in isolation and reconcile all 54 normal/stress/position outputs. Do not repeat diagnostic negative control as baseline. No actual run or new synthetic P&L this iteration. Specified starting capital $100,000; ending equity and challenger metrics unavailable. Promotion UNVALIDATED. Next registered hypothesis: none until exact baseline reproduction.
