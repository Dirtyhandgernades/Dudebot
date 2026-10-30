# OBSIDIAN autonomous Research Engineering — 2026-10-29 23:44 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated research-branch source-contract correction; no live market capture, trade, main/production change, provider credential, or frozen baseline edit.

## P0-1 material integrity correction
The independently supplied EOD source preflight previously required the *current* session's price-as-of to equal the 16:00 ET normal close, but did not require a source-specific **previous-session regular-close as-of**. A previous-session intraday trade or postclose print could therefore be misrepresented as the reference denominator of a purported 20% event, despite apparent two-provider price agreement.

- Commit `71bbfd1408c600fee5548f5a404b817e27ca1744` adds a required `previous_regular_close_asof` for every accepted source, equal to the previous session's exact **16:00 ET normal close**. Missing, 15:59:35, and 13:00 early-session references are **censored** with `PREVIOUS_CLOSE_NOT_EXACT_1600_ET_SOURCE`; equivalent UTC/Eastern offsets are accepted. Previous early closes require a separately registered nonfrozen calendar protocol and are never silently treated as normal-session closes.
- Initial hosted run **41004485702** failed 8 synthetic downstream tests because older test fixtures lacked the newly required timestamp. This was a genuine fixture migration failure, not a weakening of the new source gate.
- Follow-up commit `1bf88e835b1976488770a99876ef0aea4c455c5b` updates only synthetic EOD intake and +0/+1/+2/+3 horizon test fixtures and adds a downstream regression test. It preserves all untouched historical labels, original cohort denominator and prospective capture rules.
- Hosted run **41004552785** succeeded: **497 prospective offline tests + 4 ABC board tests passed**. See https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41004552785 . Offline consistency tests do **not** authenticate market data or demonstrate forecast success.

## Cross-task coordination and unchanged limitations
Read original Oct29 Rug Proof morning/intraday/SIP/postclose evidence, including the **18:20 CT** audit and its 8,502-row original denominators; did not duplicate, backfill, or alter any IEX, SIP, halt-monitor, 14:20 decision, 14:47 preclose, or after-hours markers. The original 136-name retained watchlist and JDZG stale/halt/price-floor diagnostic remain intact.

**P0-1 remains blocked:** no two independently authenticated official regular-session exchange closing-price provider organizations with complete third-source conflict inventory, security identity, corporate-action adjustment provenance, independently authenticated calendar and timestamps. AAPL/MSFT historical paired vendor daily bars are diagnostic only. **Official prospective 20%+ successes: not established; all missing outcomes remain censored.** Forward horizons stay h0/+1/+2/+3 actual sessions with matched untouched cohorts, false positives, late/exhausted cases, squeezes, costs and missingness explicitly preserved. Massive real-time entitlement, SMG platform security eligibility/borrow, and off-platform raw artifact retention remain unverified.

Next safe P0-1 step: source-owned, independently retrievable official-close and corporate-action receipts with verified organization ownership and exact exchange calendar/session provenance. Never substitute source self-attestations, identical vendor daily bars, or historical IEX prints for authenticated official outcomes.
