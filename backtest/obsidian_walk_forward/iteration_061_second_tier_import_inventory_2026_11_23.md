# OBSIDIAN iteration 061 — verified second-tier import inventory (2026-11-23)

RESEARCH ONLY. Authorized branch `research/obsidian-early-rug-20261025`. Continues iteration 060. No SMG credentials, trading, live portfolio desk, alerts, deployment, main, or protected baseline modifications.

## Directly fetched and verified on branch
Re-read the registered continuous walk-forward protocol, historical FAST_DUMP_RANK_RESULTS, FIRM_TIMING_VALIDATION, trade-discovery playbook, prospective proof gate and diagnostic replay negative control under `backtest/`. The historical results remain previously inspected retrospective evidence, not untouched holdouts.

Fetched ten additional source modules from the branch and recorded Git blob SHAs:
- smg/providers.py 0043cdc7fd20a54bb20e8286932fbfdaf248e479
- smg/rules.py 5997d832da4e4ac31e404717b9967e3f69ee1895
- smg/firm_first.py a420f4feeffb9ca235672bd52f4e07fab9d8a314
- smg/storage.py 696a84953d745039cdc6f5fa306b1f04eb799ec9
- smg/extraction.py 1ed63f425ed630686d8297e44694cb5ad3c7c6a8
- smg/discovery.py 1d844e42ad9b2fef3a48a68c0b8f01fb65fbea35
- smg/runner.py 78ca9cea2d8b15e62edf8109b30727a8d4401eb2
- smg/notify.py c3f23ea67215d4175e8883cb84263d44dfbf9cb9
- smg/firm_search.py 5eceaf7e6b03a2363f2ced45eca0ccb91312f0b3
- smg/source_replay.py 240cee8325c573be3ebca98dff4810741f456f46

## New concrete evidence and remaining blockers
Static import inspection confirms this second tier imports further local modules `smg.models`, `smg.transport`, `smg.game_rules`, `smg.market`, `smg.live_firms`, and `smg.backtest`/`smg.cli` (last two already identified). `smg.source_replay` also requires `lxml` in addition to previously inventoried third-party dependencies. This confirms that the earlier eleven-module closure was incomplete and gives exact next files to verify; do not stub or modify the original ranker to bypass imports.

These Git connector reads did not stage a complete executable checkout or artifact ZIP in the Python container. The registered original artifact is run 37386241124, artifact 11378995592, expected ZIP SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e. No binary re-download, local SHA verification, original-ranker execution or 54-output reconciliation occurred in this iteration. No P&L, ending equity, baseline/challenger metrics or genuinely fresh windows computed. Starting synthetic capital $100,000. Historical August signals and late December remain missing.

## Next bounded action
Prefer a single full pinned checkout and verified original artifact colocated in an offline isolated container, rather than continuing indefinite piecemeal reconstruction. Verify full source tree and dependency lock, then run unchanged `python -m backtest.target_rank_research` only on exact original inputs and reconcile all 54 configurations including normal/stress and positions against `backtest/FAST_DUMP_RANK_RESULTS.md`. Do not register a challenger until exact baseline reproduction succeeds. Promotion UNVALIDATED.
