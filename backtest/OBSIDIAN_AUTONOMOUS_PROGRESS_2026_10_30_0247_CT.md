# OBSIDIAN Research Engineering — 2026-10-30 02:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated source-contract shadow hardening only; no orders, credentials, production/main changes, alerts, or protected source captures.

## P0-1 strict closing-price provenance: structural fail-closed repair

Reviewed the October 28 roadmap, latest branch head, October 29 Rug Proof original postclose audit/anchors, historical two-provider reconciliation, and recent GitHub Actions. The 136-name retained watchlist, JDZG stale/halt/price-floor case, frozen original 8,502-row prospective capture denominators, +0/+1/+2/+3 actual-trading-session evaluation, and distinct capture task ownership are unchanged.

The EOD preflight previously accepted HTTPS-looking caller-supplied source URLs containing userinfo, nonstandard ports, fragments, control characters, or malformed authorities. It also counted two distinct claimed provider groups at `api.vendor.example` and `data.vendor.example` as structurally independent, even though their host parent hints were identical. A third apparently independent source could mask the alias.

- Implementation commit: `0b7c59a5b5ef6fde5abbd40881ac7f08aed173e5`.
- Research-only `obsidian_eod_source_preflight.py` now rejects unsafe URL authorities and uses the existing receipt-integrity host-parent heuristic to censor cross-group aliases, including with a third source. The heuristic is **not** public-suffix/legal-ownership authentication and can over-censor.
- Added three regression tests, including malformed URL, alias and third-source alias cases. The first hosted CI run **41022191400** failed one synthetic fixture because its intended newline was represented as a literal backslash-n. This was a test-fixture mistake, not a production/provider incident.
- Fixture correction commit: `49ffde098ca4082ad691e91bc864bfe476269088`. Hosted run **41022320783** completed **success**, **505 prospective offline tests + 4 ABC-board tests passed**. The failing first run is retained in the evidence history; no test or validation requirement was weakened.

Verified hosted runs: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41022191400 and https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41022320783 .

## Explicit unresolved source and forward-evaluation blockers

This is a caller-supplied structural preflight, not an authenticated official-close fetch, provider ownership proof, live market entitlement, or market outcome. The October 29 historical AAPL/MSFT two-vendor agreement is not independently sourced official exchange close evidence for the frozen cohort. No complete third-source conflict receipts, issuer/security identity chain, corporate-action basis, authenticated exchange calendar, or independently sourced completed regular-session closes from two genuinely independent provider organizations have been established. **Official outcome scoring stays censored, and prospective 20%+ collapse prediction success/accuracy remain unestablished.**

October 29 h0 has no admissible matched official close under the strict gate; October 30 +1, November 2 +2, November 3 +3 are prospective session horizons and cannot be backfilled. Retain all false positives, late/exhausted cases, squeezes, costs, missingness, and original denominator. Nasdaq RSS is not a full-market halt-clearance guarantee; optional Massive live entitlement is not evidenced; Alpaca borrow does not prove SMG platform approval.

No 12:47 INTRADAY IEX, 14:47 protected preclose, Morning Movers, After-Hours, Early Decision Board, or Rug Proof markers were created outside their original authorized windows. Durable external raw-receipt archiving and authenticated independent official close sources remain the next material external dependencies.
