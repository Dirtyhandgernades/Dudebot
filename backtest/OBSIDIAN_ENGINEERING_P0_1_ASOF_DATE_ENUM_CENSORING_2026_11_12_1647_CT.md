# OBSIDIAN Research Engineering — P0-1 exact as-of/date/action claim classification (2026-11-12 16:47 CT)

**RESEARCH_ONLY_NOT_AN_ORDER.** Branch `research/obsidian-early-rug-20261025` only.

## Independently checked engineering milestone
- Starting research branch head: `222b381065d4036392f8e205ca74a20ae2a96302`.
- Code/test commit: `b0db7f80d781f00aeb25872cfe43c3cc876b60b5` (expected-head lease succeeded).
- Hosted [prospective CI run 43323408123](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43323408123) completed **success** on that exact code commit: **767 offline prospective tests and 4 board tests passed**. Five new regression tests cover unsupported seventh-digit as-of precision, malformed previous-close as-of text, noncanonical session/action coverage dates, unknown action/basis enums, and legitimate equivalent UTC-offset close times.
- Code scope: `backtest/obsidian_eod_source_body_binding_shadow.py` and its offline regression test only. No market data provider was contacted by this change.

## Defect and guard
The body-to-receipt auditor previously distinguished absent and nonstring identity/action claims, but a **present, nonempty malformed** close as-of timestamp, noncanonical session/action coverage date, or unknown corporate-action/basis enum could appear only as a conflicting hashed string, without a separate **invalid-source index**. This hid a distinct missingness cause in the complete P0-1 evidence inventory.

The research-only auditor now adds the original source index to `invalid_body_identity_claim_source_indices` for unsupported as-of precision/syntax, noncanonical YYYY-MM-DD dates, and action/basis values outside the existing allowed enums. It still preserves source-indexed hashed conflicting claims, differentiates omitted from invalid, and never echoes untrusted source text. Equivalent aware UTC offsets remain valid. Rejected evidence cannot authenticate a close or enter the frozen scorer.

## Other workflows / one-time windows
- Read the roadmap and original November 12 Rug Proof markers and verified the separate after-hours IEX and independent-monitor workflow artifacts: runs `43310308440` / `43310308370`, artifact IDs `13985601925` / `13986355792`; GitHub-reported SHA256 digests `b38dcf4e51de540149f387f93c1b719b02182b8cfd216abaac2f68cf127fe437` and `e8d19ef1d871af281a1ae3707037f7d9e15080d151ac937c3445d8d15d06008a`, expiring 2027-02-10. No independent ZIP-byte rehash or durable backup was established.
- The existing 12:47 CT intraday marker was already present. The 14:45–14:58 CT protected preclose window had expired before this checkpoint. No new capture, retry, late marker, backfill, morning/after-hours marker, or overlapping Rug Proof work was performed.
- Preserve original 136-name roster, JDZG stale/halt/financing failure analysis, untouched historical labels and denominator, and the original 0/+1/+2/+3 actual-trading-session forward windows.

## Unresolved external P0-1 proof
No authenticated **official regular-session closing prices** from two genuinely independent provider organizations have been established. Provider ownership, complete third-source conflicts, official previous-session references, exact exchange-session calendars, security/share-class identity, and externally verified corporate actions remain unproven. Massive real-time credentials/entitlement and actual SMG blocked-symbol/account short permissions are unverified; Alpaca borrow is not SMG approval. Missing outcomes remain **CENSORED**, not successful 20%+ predictions. False positives, late/exhausted cases, squeezes, transaction costs and coverage missingness must remain in future matched evaluation.

No main/production, credentials, orders, trading alerts, fills, profit claims or policy changes.
