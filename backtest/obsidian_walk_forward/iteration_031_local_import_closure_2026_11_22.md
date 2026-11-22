# OBSIDIAN iteration 031 — local import closure inventory (2026-11-22)

RESEARCH ONLY. Continuation after iteration 030, authorized branch `research/obsidian-early-rug-20261025`. No trading, private data, protected baseline or production changes.

## Read first
Read continuous protocol, discovery playbook, prospective proof gate, diagnostic negative control, iteration 030 manifest. The referenced historical reports are located under `backtest/`, not repository root; root requests returned 404. Existing 2023–25 results are previously inspected, not unseen validation.

## Newly verified Git blobs
| File | Blob SHA |
|---|---|
| smg/providers.py | 0043cdc7fd20a54bb20e8286932fbfdaf248e479 |
| smg/rules.py | 5997d832da4e4ac31e404717b9967e3f69ee1895 |
| smg/firm_first.py | a420f4feeffb9ca235672bd52f4e07fab9d8a314 |
| smg/storage.py | 696a84953d745039cdc6f5fa306b1f04eb799ec9 |
| smg/extraction.py | 1ed63f425ed630686d8297e44694cb5ad3c7c6a8 |
| smg/discovery.py | 1d844e42ad9b2fef3a48a68c0b8f01fb65fbea35 |
| smg/runner.py | 78ca9cea2d8b15e62edf8109b30727a8d4401eb2 |
| smg/notify.py | c3f23ea67215d4175e8883cb84263d44dfbf9cb9 |
| smg/firm_search.py | 5eceaf7e6b03a2363f2ced45eca0ccb91312f0b3 |
| smg/source_replay.py | 240cee8325c573be3ebca98dff4810741f456f46 |
| smg/live_firms.py | 99464a3ca967b46f97228f64b576d612ef2b2c36 |

## Dependency finding
The ten unresolved local modules from iteration 030 are now retrieved and pinned; scanning their relative imports exposed one further module, `smg/live_firms.py`, which was also retrieved. Its relative imports point to previously inventoried `models`, `extraction` and `firm_search`. This closes the *observed static local-import chain for these eleven files*, not a verified complete executable environment. Dynamic imports, dependency version compatibility and archive-producer commit differences remain untested.

## Execution and evidence
No archive bytes transferred into an isolated Python runtime this iteration; no independent checksum recomputation or `python -m backtest.target_rank_research` execution. GitHub Actions artifact 11378995592 from run 37386241124 still requires exact input assembly and independent checksum validation. The artifact-producing commit `b8fbd035543611f49992d6df3b619af7a6ddf548` differs from research-branch source. No 54-configuration reproduction, challenger, new modeled P&L or ending equity. Initial synthetic capital specification $100,000. Promotion UNVALIDATED.

## Next bounded repair
Compare `backtest/target_rank_research.py` and its local dependencies at artifact-producing commit against the research branch using exact Git blob hashes. Resolve any differences without modifying frozen source. Then co-locate checksum-verified original archive and dependency tree in an isolated runtime and run the original ranker unmodified. Do not claim baseline match until all 54 output rows, stress, and positions reconcile.
