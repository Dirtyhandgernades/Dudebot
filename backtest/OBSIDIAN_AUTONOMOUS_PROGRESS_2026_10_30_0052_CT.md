# OBSIDIAN Research Engineering — 2026-10-30 00:52 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Scope: research/obsidian-early-rug-20261025 only; no production, main, credentials, orders, protected market capture, baseline relabeling or historical denominator changes.

## P0-1 receipt source-independence alias guard
The existing receipt byte-integrity shadow counted distinct exact hostnames and caller-claimed provider groups. Two aliases such as `quotes.vendor.example` and `close.vendor.example` could appear structurally diverse even though both share the same apparent source-domain parent. That is not two independently authenticated provider organizations.

- Implementation commit: `b8180b708f479a303c3ffd343a1538baa3271bf0`. The offline, non-scoring `obsidian_eod_receipt_integrity_shadow.py` now flags shared host-parent hints and differing claimed provider groups under the same hint. It also flags an alias concealed among three supplied sources; every original source index remains in the audit.
- This is a deliberately **conservative heuristic**, not an authoritative public-suffix lookup, verified corporate-ownership mapping, or exchange data entitlement. Shared hosting can be over-censored; different parent hints still do **not** prove organizational independence. Every source remains unauthenticated and excluded from frozen scoring.
- Three new synthetic regression tests cover sibling hostnames, parent/subdomain aliases, and a third-source alias. Hosted GitHub Actions run **41010820326** completed **success** at commit `b8180b708f479a303c3ffd343a1538baa3271bf0`: **500 prospective offline tests + 4 ABC-board tests passed**. https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41010820326

## Original evidence and gates preserved
Read the original October 29 Rug Proof 09:21/12:16 IEX anchors, 14:22 delayed historical SIP and 18:20 postclose audit. Original 8,502-row denominators, the distinct 14:47 preclose IEX run, 136 retained names, JDZG stale/halt and price-floor failure, and the separate Morning/After-Hours/14:20 board remain untouched. No new intraday, preclose, morning, afterhours, halt, or Rug Proof marker was created outside its original authorized window.

**Still blocked:** No two genuinely independent, externally authenticated official 16:00 ET exchange-closing-price source organizations, complete third-source conflict resolution, authenticated security/issuer and corporate-action chain, or independent exchange calendar and source timestamps. Historical AAPL/MSFT paired vendor bars are diagnostic only. All prospective h0/+1/+2/+3 trading-session outcomes remain censored without admissible official evidence; verified 20%+ prediction successes and accuracy are unestablished. SMG platform short eligibility, Massive real-time entitlement, and durable off-platform evidence backup remain unverified.

Next P0-1 acceptance step: independently retrieve source-owned official-close and corporate-action receipts with organization ownership, exact session and publication timestamps, complete conflicting-source inventory and durable original byte provenance; do not infer official-close status from the new hostname heuristic or offline tests.
