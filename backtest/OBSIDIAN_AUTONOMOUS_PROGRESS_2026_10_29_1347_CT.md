# OBSIDIAN Research Engineering — October 29, 2026, 13:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Authorized research branch only; no main/production, trading, credential, frozen-label, capture, or scheduled-marker modifications.

## P0-1 source receipt integrity fix

- Read the Oct28 validation roadmap, original source-contract audit, current EOD preflight, all-source conflict inventory, current research branch, prior Rug Proof and intraday capture markers, and recent hosted CI/artifact metadata before editing.
- Found a narrow independent-source preflight integrity gap: two supplied reports with the **same `source_id`** but different self-asserted provider groups and URL hosts could receive `CONSISTENT_SOURCES_ONLY_NOT_OFFICIAL_CLOSE`. The separate all-source conflict inventory already detects duplicate source IDs; the preflight did not.
- Updated `backtest/obsidian_eod_source_preflight.py` to fail closed with `DUPLICATE_SOURCE_ID` for any repeated nonblank source identifier, including when the second report also fails price-as-of validation.
- Added two synthetic tests in `tests/test_obsidian_prospective_eod_source_preflight.py`. Commit `5a1890ae6e2fcd467d318f8b920669363070c20d` landed via expected-head GitHub lease.
- **Hosted CI verified:** GitHub Actions run [40934135546](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40934135546), completed success; **473 offline prospective tests passed**, including both new duplicate-ID regressions. No live market data was requested by this test workflow.
- Independently checked latest free quant packet run [40932728198](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40932728198), artifact 12924110275: 139-row scope, 24 fresh/115 stale IEX trades, 108 delayed-SIP bars fresh at their delayed cutoff, 23 stale, 8 missing, 8 SEC metadata reviews under budget. These are **not** official exchange closes, causal bearish signals, or SMG permissions.
- Existing Oct29 intraday IEX and independent monitor markers and Rug Proof morning/intraday anchors were already present. No new markers, retries, or duplicate ownership claims. This pass was outside the protected 14:45–14:58 CT preclose gate.

## Outstanding P0 blocker

The stricter preflight now rejects duplicate source IDs but still relies on **self-asserted provider identities**. Neither this software test nor vendor historical daily-bar agreement authenticates independent underlying feeds, official exchange closing auction/regular-session definitions, issuer security identity, corporate-action adjustment, exact exchange calendar, or complete third-source conflict provenance. Therefore **zero 20%+ prospective prediction successes are independently established**; missing 0/+1/+2/+3 actual-session outcomes remain censored, and the frozen 136-name baseline and JDZG stale/halt analysis are unchanged.
