# OBSIDIAN iteration 056 — recovered and verified original Actions ZIP (2026-11-23)

RESEARCH ONLY. Continuation of iteration 055; authorized branch `research/obsidian-early-rug-20261025`. No SMG, credentials, private data, orders, production, Portfolio Desk, protected baseline, or promotion.

## New verified evidence
GitHub Actions run `37386241124`, artifact `11378995592` (`pre-close-firm-37386241124`) is **not expired** (API expiry 2027-01-03). The GitHub connector downloaded the original ZIP into an isolated container at `/mnt/data/github-actions-artifact-11378995592.zip` (11,294,854 bytes per GitHub API). Executed `sha256sum` on downloaded bytes: **a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e**, exactly matching the registered archive SHA256 and GitHub API artifact digest. Python `zipfile.ZipFile.testzip()` returned `None` (no CRC errors); archive has 30 entries. This repairs the binary-artifact access blocker from iteration 055.

Verified original input members and SHA256 of uncompressed ZIP members:
- `firm-timing-inputs.json.gz`: 11,118,396 bytes, SHA256 `e4863623bf73ca18b51ee7cf85be891bc2f7a787bedc598722037d3413cc29bb`
- `discovery-decisions.json`: 713,142 bytes, SHA256 `71da2032f7c88dcb0d02023f65b7cdfb8beb5cf9494b0391557469929f003737`
- `2023-hybrid-signals.json`: 5,209 bytes, SHA256 `2566401df1ba8c82a4804e4d3bc8b00810316a968e6493500b0634c57c4f24ee`
- `2024-hybrid-signals.json`: 28,252 bytes, SHA256 `c785649b6ebcf048331137993ec83a7e1fd5c7e3492b1b09be6fc980a7c0923b`
- `2025-hybrid-signals.json`: 51,454 bytes, SHA256 `8bb5de127613f1b47eb49b0028d8f2a1460b323a0204b7df7fbdb088475f0f42`

## Reproduction and next step
Exact original ranker source remains `backtest/target_rank_research.py` (branch Git blob `e574c908eeb5fafbf918200296b01eeaf8dafbdd`), unmodified. The downloaded ZIP has not yet been colocated with a byte-identical complete branch checkout and dependencies, so **no ranker execution or 54-output reconciliation is claimed**. Next bounded step: stage verified ZIP safely in `outputs/backtest/hybrid-37386241124` within isolated checkout, run checked-in regression, execute `python -m backtest.target_rank_research` unchanged and reconcile all 54 configurations. Do not interpret original Sep 8–Dec 5 scope as full Aug–Dec coverage.

Synthetic starting capital $100,000; new net P&L/ending equity: **not computed**. Missing August hybrid signals and late-December sessions remain unresolved. No challenger registered; historical 2023–25 are already inspected. Promotion: **UNVALIDATED**.

Reproduce archive check: `sha256sum /mnt/data/github-actions-artifact-11378995592.zip`; `python -c "import zipfile; z=zipfile.ZipFile('/mnt/data/github-actions-artifact-11378995592.zip'); print(len(z.namelist()), z.testzip())"`. Local path is an ephemeral working-container artifact, not a persistent repository input.
