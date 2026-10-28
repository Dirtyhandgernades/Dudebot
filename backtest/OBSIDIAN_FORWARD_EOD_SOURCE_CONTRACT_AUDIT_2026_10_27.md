# OBSIDIAN October 27, 2026 — 20:47 CT forward-outcome source-contract audit

**RESEARCH_ONLY_NOT_AN_ORDER.** This is an outcome-blind code-contract finding. It does **not** claim a validated collapse, change the frozen 2026-10-27 policy, or modify an authenticated raw capture.

## Verified code-level gap

The frozen forward study (`backtest/obsidian_forward_collapse_study.py`) delegates external source agreement to `backtest/obsidian_iex_outcomes.py::corroborated`. That function verifies two distinct source IDs/hosts, post-close observation timestamps and matching numbers, but **does not require per-source** `regular_close_asof`, `provider_group`, `symbol`, `session_date`, `previous_session_date`, `kind`, or `session_complete`. Its parent `valid_closes` checks top-level `close_at` to the minute, not exact 16:00:00 ET.

By contrast, the separate, later-added `backtest/obsidian_eod_source_preflight.py` requires explicit exact 16:00 ET price-as-of evidence and independent provider groups and security/session provenance. The two contracts are **not connected**. Merely adding a stricter preflight file does not automatically make a legacy scorer enforce it. A synthetic source pair missing the provenance fields can satisfy `corroborated` while the new shadow preflight blocks it.

This is a **potential future scoring-integrity bypass**, not proof that any October 27 outcome was actually mis-scored: no qualifying externally corroborated Oct27 outcome JSONL is currently available. The full 8,515-symbol write-once capture remains the denominator; stale/missing cases remain censored.

## Isolated research response

- Added `backtest/obsidian_forward_source_contract_shadow.py` to audit source-level provenance without writing or mutating outcomes, predictions, baseline, or the frozen evaluator.
- Added synthetic tests for legacy acceptance vs shadow rejection, missing exact 16:00 as-of, provider aliases, third-source conflicts, top-level mismatches, security identity, source publication timing, and fail-closed malformed evidence.
- Added both files to research-only offline CI path filters. All shadow outputs explicitly keep `eligible_for_frozen_forward_scoring=false`, `trade_authorized=false`, and external corporate-action/inventory proof unresolved.
- **No changes** to `backtest/obsidian_forward_collapse_study.py`, `backtest/obsidian_iex_outcomes.py`, `backtest/OBSIDIAN_IEX_FORWARD_STUDY_FROZEN_2026_10_27.md`, main, production, credentials, alerts, orders, or original captures.

## Required next gate

Only score a future session after independently collected source-level 16:00 ET regular closes agree, all available conflicting reports are retained, security identity/corporate actions are reviewed, and the frozen policy is applied without post-hoc threshold changes. This shadow diagnostic is not a retroactive repair of the frozen scorer. Report a validation blocker rather than inventing hits, false positives, recall, or after-cost P&L.

No new preclose, intraday, or after-hours trigger was created outside the authorized windows. October 27 after-hours remains an explicitly missed observation, not a backfilled capture.
