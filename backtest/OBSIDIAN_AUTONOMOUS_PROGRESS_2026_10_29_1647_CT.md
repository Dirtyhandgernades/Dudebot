# OBSIDIAN Central Engineering — October 29, 2026, 16:47 CT

**Mode:** RESEARCH_ONLY_NOT_AN_ORDER. Research branch only. No market capture, preclose rerun, Rug Proof anchor, order, or production change.

## Fresh evidence and coordination
- Refreshed research branch and latest hosted Actions; initial head `91a222c656ed67ce90dfbf9ec616b1d114070311`. October 29 protected IEX preclose capture and afterhours captures were already completed by their respective owners; did not duplicate them.
- Roadmap priority P0-1 remains authenticated independent regular-session official closes with complete source, identity, corporate-action, session-calendar, and conflict proof. The present source preflight is **structural only**; no vendor or exchange close was authenticated during this checkpoint.
- Original 136-name retained watchlist, JDZG stale/halt forensic analysis, frozen baseline, and 0/+1/+2/+3 trading-session policy remain untouched.

## Concrete source-consistency integrity fix
- Found a threshold-boundary gap: two source close prices `8.000` and `8.005` with prior close `10.000` agreed within the $0.005 tolerance, yet disagree on whether a >=20% decline occurred. The previous source preflight could report this pair structurally consistent.
- Research-only commit [38c494be0f69f28e24721a9affce457affcf2069](https://github.com/Dirtyhandgernades/Dudebot/commit/38c494be0f69f28e24721a9affce457affcf2069) now explicitly blocks `TWENTY_PERCENT_THRESHOLD_STRADDLED`. Any differing previous-close claims, even sub-tolerance, block `THRESHOLD_REFERENCE_PREVIOUS_CLOSE_DISAGREEMENT`, because the reference denominator is not settled.
- Added two targeted regression tests. First hosted [run 40960334926](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40960334926) failed because an older half-cent tolerance fixture itself sat exactly on the newly blocked 20% boundary. This was a legitimate test expectation conflict, not hidden.
- Follow-up commit [25095ecd2bb929de5e9d26244cd7dc6e68632500](https://github.com/Dirtyhandgernades/Dudebot/commit/25095ecd2bb929de5e9d26244cd7dc6e68632500) moved the pure-tolerance fixture away from the classification threshold, preserving the half-cent tolerance while explicitly censoring threshold ambiguity.
- Verified hosted [run 40960410454](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40960410454): **479 prospective offline tests + 4 ABC tests passed**. No live vendor requests or new market capture occurred.

## Outcome and remaining blockers
This closes a **synthetic structural evidence loophole**, not an actual vendor conflict and not a validated forecast. Two independently authenticated official regular-session closes, provider/source ownership, corporate-action parity, issuer identity, complete third-source conflict receipts, and a durable approved raw evidence archive remain unproven. All unverified forward outcomes remain censored. **Verified prospective 20%+ prediction successes: zero established.** No historical relabeling or scoring policy change was made.
