# OBSIDIAN iteration 035 — artifact recovered into execution container (2026-11-22)

RESEARCH ONLY. Authorized branch research/obsidian-early-rug-20261025. Continues iteration 034; no orders, SMG access, production edits, or strategy promotion.

## Actual repair performed
Using the GitHub connector, downloaded artifact 11378995592 from run 37386241124 (pre-close-firm-37386241124) into the isolated execution container as /mnt/data/obsidian-original-37386241124.zip. Independent local sha256sum: a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, matching registered digest. File size 11,294,854 bytes. ZIP lists 30 members; inspected the five required inputs in memory, without executing ranker or changing archived bytes.

| Archived input | Bytes | SHA256 |
|---|---:|---|
| firm-timing-inputs.json.gz | 11118396 | e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb |
| discovery-decisions.json | 713142 | 71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737 |
| 2023-hybrid-signals.json | 5209 | 2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee |
| 2024-hybrid-signals.json | 28252 | c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b |
| 2025-hybrid-signals.json | 51454 | 8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42 |

GitHub artifact metadata: expired=false; expires 2027-01-03T23:03:15Z; source commit b8fbd035543611f49992d6df3b619af7a6ddf548. The ranker was added later, so archived inputs do not prove original ranker executed on producer commit.

## Reproduction
Read-only commands in a fresh isolated container with this downloaded ZIP:
```bash
sha256sum /mnt/data/obsidian-original-37386241124.zip
unzip -Z1 /mnt/data/obsidian-original-37386241124.zip
```
Do not treat connector file availability as durable across future isolated containers. Retrieve again if absent.

## Status
This iteration recovered and checksum-verified the original artifact in the actual execution environment, repairing iteration 034's missing ZIP blocker. The unchanged original ranker and its complete pinned dependency tree have NOT yet been assembled in this container, so no 54-configuration baseline reproduction occurred. No fresh Aug-Dec 2025 historical replay, new P&L, ending equity, challenger, or prospective evidence. Starting hypothetical capital remains $100,000; promotion unvalidated. Known August and late-December coverage gaps remain.

Next registered step: stage pinned unchanged ranker/dependencies in a disposable isolated tree, safely extract verified five inputs under outputs/backtest/hybrid-37386241124, execute python -m backtest.target_rank_research once, and reconcile all 54 configurations against backtest/FAST_DUMP_RANK_RESULTS.md. No hypothesis modification until original reproduction is proven.
