# OBSIDIAN iteration 060 — transitive import closure and offline safety audit (2026-11-23)

RESEARCH ONLY. Authorized branch `research/obsidian-early-rug-20261025`. Continues iteration 059; no trading, secrets, portfolio desk, production, baseline, deployment, alerts or main changes.

## Direct source evidence
Read the original `backtest/target_rank_research.py` at Git blob `e574c908eeb5fafbf918200296b01eeaf8dafbdd`, and re-fetched all eleven dependency modules recorded in iteration 059, verifying their same Git blob IDs. Read registered protocol, discovery playbook, proof gate, and diagnostic negative control. The historical result documents reside under `backtest/` (not repository root); root-level lookups returned 404.

GitHub Actions run `37386241124` currently lists original artifact `11378995592`, `pre-close-firm-37386241124`, 11,294,854 bytes, `expired=false`. Listing alone is **not** a fresh checksum verification or local archive recovery. Registered ZIP SHA256: `a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e`.

## New blocker identified: indirect imports
The eleven direct modules are **not** an import-complete executable checkout. `smg.intraday_replay` imports `smg.cli` and `smg.backtest`, and these transitively import additional repository modules:
- `smg.providers`, `smg.rules`, `smg.firm_first`
- `smg.storage`, `smg.extraction`, `smg.discovery`, `smg.runner`, `smg.notify`
- `smg.firm_search`, `smg.source_replay`

Third-party import requirements observed directly include `numpy`, `pydantic`, `pandas`, `exchange_calendars`, `requests`, `PyYAML` (`yaml`) and `beautifulsoup4` (`bs4`). Additional transitive requirements may exist. A partial eleven-file reconstruction would risk import failure or altered behavior; do **not** patch/stub the original ranker or imports. Importing source with `notify` and provider modules must occur in a network-disabled isolated environment; import presence alone does not authorize calls or external side effects.

## Actual execution state
Container check: `git ls-remote https://github.com/Dirtyhandgernades/Dudebot.git refs/heads/research/obsidian-early-rug-20261025` failed `Could not resolve host: github.com`. The original ZIP and complete checkout are not established in this container. **No original ranker execution or 54-output reconciliation occurred.** No new historical P&L or ending equity computed. Synthetic experiment capital remains $100,000, not an observed balance. Previously identified August and late-December gaps remain unresolved.

## Reproduction and next bounded step
Next iteration: retrieve and hash the additional transitive modules (or preferably acquire a single pinned full branch checkout), verify complete import closure in an offline container with the registered ZIP, then run `python -m backtest.target_rank_research` unchanged and compare all 54 result configurations, trade CSVs, normal/stress and position counts with `backtest/FAST_DUMP_RANK_RESULTS.md`. Do not run with substituted/synthetic inputs. Original September 8–December 5 replay cannot cover August–December. No challenger hypothesis registered; promotion **UNVALIDATED**. Historical 2023–25 observations are already inspected, not fresh holdouts.
