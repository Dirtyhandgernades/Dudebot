# OBSIDIAN Research Engineering — 2026-10-30 01:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only. No main, production, credentials, orders, alerts, historical capture changes, or scoring policy modifications.

## P0-2 independently checked calendar URL provenance — fail-closed repair

Read the October 28 autonomous roadmap, existing October 29 Rug Proof original anchors and 18:20 postclose audit, latest branch head, and recent Actions. The P0-1 official-close authentication blocker remains external: the current AAPL/MSFT paired historical vendor bars do not prove two independently sourced official exchange closes, source ownership, corporate-action/issuer continuity, or full frozen-cohort coverage. No source entitlement or authentic new official-close receipt was established at this checkpoint.

The separately registered 0/+1/+2/+3 trading-session calendar shadow previously accepted a claimed `http://www.nyse.com/...` calendar URL because it checked the hostname but not the HTTPS scheme. A credential-bearing `https://user@www.nyse.com/...` authority and nonstandard port could also pass the structural host check; malformed bracketed hosts could raise an exception instead of being rejected as unverified. This is a **caller-supplied provenance weakness**, not evidence of an actual provider compromise.

- Implementation commit: `4ea2eb0e381e40852e7311a97d18109a52c9a502`.
- A shared research-only `trusted_exchange_calendar_host` guard now requires HTTPS, approved NYSE/Nasdaq host, no userinfo/fragment/control characters, and standard HTTPS port. Invalid authority syntax is censored instead of crashing. Applied consistently to the forward-calendar assumption audit and the separate four-session horizon study.
- Two new synthetic regression tests cover HTTP, userinfo, nonstandard port, malformed bracketed host, and fragment cases. Hosted GitHub Actions run **41016307015** completed **success** on the implementation commit: **502 prospective tests + 4 ABC-board tests passed**. https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41016307015

## Immutable evidence and outcome limitations

No original morning, 12:47 intraday, 14:47 protected preclose, 14:20 Rug Proof, after-hours IEX or independent halt marker was created or replayed outside its authorized window. The October 29 original 8,502-row capture denominators, 136-name retained watchlist, JDZG stale/halt and $3 floor failure analysis, and distinct cross-task source anchors remain unchanged.

The calendar guard is **not** a live URL fetch, redirect audit, authoritative exchange calendar authentication, or a source receipt. The four-session shadow remains non-scoring. No two independent organization-level authenticated official regular-session closes, complete conflict/identity/corporate-action chain, Massive live entitlement, or actual SMG borrow/platform permission have been established. All unverified h0/+1/+2/+3 outcomes remain censored; **verified prospective 20%+ collapse prediction success and accuracy are unestablished**. Preserve every original row, false-positive and late/exhausted denominator, source timestamp, and missingness category.

Next P0-1 gate: externally authenticated provider-owned official regular-session close receipts from at least two genuinely independent organizations with issuer/security identity, corporate-action basis, independently verified exchange calendar, as-of/publication timestamps, complete third-source conflict inventory, and durable raw-byte provenance. Do not promote caller-supplied calendar URL or synthetic tests to market proof.
