# OBSIDIAN iteration 044 — 2026-11-22 — transitive import blocker identified

RESEARCH_ONLY_NOT_AN_ORDER. Continuation of 043. Authorized branch research/obsidian-early-rug-20261025 only. No private account access, orders, production workflows, alerts, protected baselines or main changes.

## Source and prior evidence checked
Read protocol, FAST_DUMP_RANK_RESULTS, FIRM_TIMING_VALIDATION, trade discovery proposal, prospective proof gate and diagnostic cycles 1–2 negative control directly from authorized branch. Read 043 append-only ledger and unchanged target_rank_research.py (Git blob e574c908eeb5fafbf918200296b01eeaf8dafbdd). Existing 2023–25 tests are retrospective and already inspected.

## Material source dependency finding
Previous 041 source pin lists five direct imports, but **those are not a self-contained executable checkout**. Inspected all five plus their immediate transitive modules. Original ranker imports smg.intraday_replay -> smg.cli, smg.game_firm_replay, smg.market, smg.transport, smg.backtest; smg.swing_backtest -> smg.market, smg.transport, smg.game_rules. In turn smg.cli imports smg.storage, smg.providers, smg.extraction, smg.discovery, smg.runner, smg.notify; smg.game_firm_replay imports smg.firm_first, smg.firm_search, smg.rules, smg.source_replay. smg.backtest imports smg.providers, smg.firm_first, smg.rules. Thus assembling only six files would fail before model execution or inadvertently require unpinned transitive source.

Observed Git blob pins: smg/backtest.py 1779ecf369d976684252a7d458564702d2ada649; smg/cli.py 036b90a4ac2d11c0e4088fac106b5e746a43e251; smg/game_firm_replay.py 34b9c30d366c2c5f83f11cc3e6bf0c76aa6141df; smg/market.py 845865aad5ed1ec1d69f9b5d050ef661cb0c65b4; smg/transport.py 7c2e876144cab9c41b9d13c546cc93a30e2e4258; smg/game_rules.py 76451c59bb2c54837f76c135b0b150f87a14d69c. Third-party imports observed include numpy, pydantic, pandas, exchange_calendars, requests, yaml and bs4. These are *import inventory*, not an audited lockfile or proof of installed versions.

## Actual environment check
The current disposable container /mnt/data has no staged ZIP or repository checkout; /mnt/data/obsidian_iteration043 is absent; github.com DNS resolution returned no address. GitHub connector can read UTF-8 branch source but not supply executable ZIP bytes into this container. The prior verified archive SHA256 remains a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, artifact 11378995592, run 37386241124. No assertion that previous staging persists.

## Bounded repair decision
**Use a full pinned authorized-branch checkout** in the same isolated runner as the authenticated, checksum-verified archive; do not reconstruct a partial six-module source tree. Run preflight, staging and guard, then original unmodified `python -m backtest.target_rank_research` once only if dependency resolution and safe output-path checks pass. No unreviewed production workflow launches. This closes the source-assembly specification gap, but not the actual environment/data blocker.

## Performance / next
$100,000 synthetic starting balance; no newly computed P&L, ending equity, trades, stress, or challenger. Historical 2025 reported +$103,258.54 aggressive and +$73,815.54 lower exposure remain *unreproduced* retrospective values. Aug and Dec 6–31, 2025 coverage remains missing/unverified. Next registered work: co-locate full pinned checkout with verified archive and execute original 54-case reproduction; no challenger hypothesis until reconciled. Promotion UNVALIDATED.
