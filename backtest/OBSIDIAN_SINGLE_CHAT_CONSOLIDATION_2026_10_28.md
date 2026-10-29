# OBSIDIAN — verified single-chat research update consolidation (2026-10-28, 19:50 CT)

**RESEARCH_ONLY_NOT_AN_ORDER.** Scope: `Dirtyhandgernades/Dudebot` research branch `research/obsidian-early-rug-20261025` only. This is a record of **ChatGPT task-routing changes**, not a market-data capture, CI result, trading instruction, or predictive-performance claim.

## Verified automation state after user authorization

- The **OBSIDIAN Research Engineering** hourly automation remains enabled and associated with the existing Research Engineering conversation; its prompt now incorporates the former Morning Movers, After-Hours Audit and Early Decision Board research duties, source-quality controls and frozen-validation rules.
- The separate **Morning Movers — Research Engineering**, **After-Hours — Research Engineering**, and **Early Decision Board** automations were disabled and their disabled states independently verified. Older duplicate OBSIDIAN tasks were already disabled.
- **Only the Research Engineering automation remains enabled among the OBSIDIAN task titles inspected.** This verifies the task routing configuration; it does **not** establish that GitHub Actions notifications or any external messaging service also route to that conversation.
- Original task chats and historical results remain in their old conversations. No historical messages were moved or deleted. GitHub is the durable common research source of truth.

## Important schedule/capture limitations (do not silently lose provenance)

The surviving Research Engineering task runs **hourly at :47 America/Chicago**. Its existing authorized intraday 12:47 and prospective preclose 14:47 checkpoints remain. The old specialized task schedules (09:12 morning IEX, 15:22 after-hours IEX, 14:20 early decision board) **are not active** and cannot be assumed to run in the Research Engineering conversation. The :47 run may review morning and after-hours sources, but it must not manufacture or backfill a protected marker at 09:47 or 15:47. Specifically:

- MORNING discovery trigger remains restricted to its separately authorized 09:12 CT checkpoint and 09:00–09:40 CT gate. **No 09:47 trigger.**
- AFTERHOURS discovery trigger remains restricted to its separately authorized 15:22 CT checkpoint and 15:00–15:45 CT gate. **No 15:47 trigger.**
- The old 14:20 decision board is no longer independently delivered by 14:35 CT; a 13:47 research review is earlier and 14:47 research is later. Never represent later data as known at 14:35.
- Original immutable captures from prior dates remain valid evidence; missing new phases are **missing observations**, not 0% returns or proof of no collapse.

## Existing forward-validation constraints unchanged

The immutable October 27/28 raw captures, complete denominators, frozen discretionary tiers and forward scorers are unchanged. The latest independently inspected research workflow run at consolidation was [Oct28 original matched-cohort replay #40790013742](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40790013742): completed successfully with derived artifact 12861206900. This verifies a code/data replay, **not** an independently authenticated future >=20% official-close collapse prediction. Independent 16:00 ET closing prices, source independence, unchanged security identity and corporate actions remain necessary before scoring. Do not infer actual SMG borrow, fills, execution or profitability.

No main, production, credentials, live alerts, orders, or original capture labels were touched by this consolidation.
