# OBSIDIAN — first locked research cohort (2026-10-27 morning)

**Mode:** RESEARCH_ONLY_NOT_AN_ORDER. This is a **pilot cohort already inspected for candidate context**, not an untouched out-of-sample performance result. The forward-study v1 policy `backtest/OBSIDIAN_IEX_FORWARD_STUDY_FROZEN_2026_10_27.md` was committed **before the October 27 regular-session close**. No same-day independent final-closing outcomes have been applied or assumed.

## Fixed prospective source
- GitHub IEX source run: [40516649174](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40516649174), successful.
- Immutable GitHub raw discovery artifact: `obsidian-iex-research-discovery-40516649174` (artifact ID **12740246208**).
- Morning IEX observation 2026-10-27 **13:57:32.742058 UTC to 13:57:41.488370 UTC** (08:57 CT). IEX single exchange venue **not** consolidated SIP.
- All **8,501** requested NYSE/Nasdaq asset-ticker snapshots are retained in original raw universe, including unusable/missing.
- Baseline WATCH categories: **162 IEX early-reference weakness**, **2 intermediate-reference declines**, **1 already-exhausted decline**. The 164 combined are *not* verified shorts.
- Hash `manifest.json`: `58dd06d254f3a63aeca76d15024f6455301dc7f777ccd206bfc08c05b2a11f03`.
- Hash `universe.jsonl`: `dad0e857f13fba07089f1b5cb0792eedbd5d58db87f55c3f8905aa59da7fef8f`.
- Hash `attention.json`: `239c1c4627a6dd92eb8a520b47a9cac3c03f1bb0ff6d785e00732f2a3b21e45f`.
- Baseline is taken as-is; no screening based on future winners, SEC adverse releases published later, or outside historical user-referenced movers.

## Measurement and limitations
- Under the frozen v1 scorer: target a **later** independently corroborated `-20%` completed regular-session close; score the original watch as **early** only if >=50% of the eventual decline still remained at its original IEX last trade. Track watched-late, unwatched verified collapses, missingness and censoring.
- No independent 16:00 ET October 27 completed-session final closes exist at this morning lock time. The pilot job MUST report conditional precision, recall and any P&L as **null**, not 0% or any unsupported edge.
- Do not count this pilot as truly untouched future validation; first genuinely untouched cohorts must be collected AFTER the frozen v1 policy exists.
- Independently verified issuer security structure, >=$3 current/prior official price, cap/share consistency, borrow, SMG platform permission and executable market prices are unavailable; none may be inferred from Alpaca IEX-only attributes.
- File content pinned by three SHA256 checks, not replaced by after-close files, and never alters frozen SIP baseline.

## Next required execution
1. Verify the immediate no-outcomes replay of this immutable capture and confirm that metrics are **not calculated** before independent EOD.
2. After 16:00 ET on October 27, separately collect EOD records for full original universe when sources exist. Two independent source hosts/records must agree and corporate actions/identity must be cleared; all missing rows censored.
3. For new, untouched October 28+ cohorts, repeat identical policy without outcome-driven tuning. Evaluate missed verified events, actual timing, absent ticker coverage, adverse squeezes and costs only with real verified data.

No main, production workflows, credentials, live alerts, orders or frozen policy parameters modified.
