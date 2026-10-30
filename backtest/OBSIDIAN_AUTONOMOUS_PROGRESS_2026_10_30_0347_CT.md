# OBSIDIAN Research Engineering — 2026-10-30 03:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated P0-1 source-contract shadow repair only. No trades, production/main, credentials, alerts, new capture markers, frozen labels, denominators, or market outcomes were changed.

## Verified source/identity and corporate-action provenance correction

Reviewed the October 28 validation roadmap, the October 29 18:20 Rug Proof postclose audit and authentic source anchors, prior October 30 progress reports, research branch head, latest CI and original artifacts. The existing action/identity shadow validator had a weaker URL syntax guard than the EOD source preflight and lacked apparent parent-host alias screening. Thus different price/action subdomains of one apparent vendor could be counted as independent provider organizations; a third apparently independent source could conceal that collision.

- Research-only implementation commit: `18ba0034bb2b3dffef44264cd2573a0ea89f39a0`. `obsidian_eod_action_identity_shadow.py` now uses the existing strict EOD URL syntax screen for **both** price and corporate-action URLs, and fails closed on cross-group apparent parent-host aliases for each source family, including three-source cases. All supplied source rows and conflict claims remain indexed; the heuristic is **not** legal ownership authentication and may over-censor.
- Added four synthetic, outcome-blind regression tests: two-source action-host alias, third-source action-host alias, third-source price-host alias, and unsafe action/price URL authorities.
- First hosted CI run `41028844426` failed one new synthetic fixture: the test contained a literal backslash-n rather than an actual newline escape. No production/provider incident or validator regression was found. Test fixture correction commit: `bbac5ea5999bc0afc3a209609bd4084a4d5a1bc3`.
- **Hosted run `41028913387` completed successfully:** 509 prospective offline tests and 4 ABC-board tests passed, including all four new regression tests. No source fetch, real market quote, official close, or trading outcome was authenticated by these tests.

CI: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41028844426 ; https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41028913387 .

## Evidence ownership and outstanding blockers

- Rechecked original Oct29 protected preclose IEX run `40943205148`: artifact `12928470853`, not expired, expires **2027-01-27 19:47:17 UTC**. Oct29 afterhours IEX run `40947825425`: artifact `12930640520`, not expired, expires **2027-01-27 20:18:20 UTC**. Separate official halt/optional quote monitor run `40947825412`: artifact `12929193915`, not expired, expires **2027-01-27 20:18:20 UTC**. These are distinct task-owned captures; no new IEX or Rug Proof marker was made here. GitHub artifact metadata alone does not validate raw ZIP integrity or authenticate underlying quotes.
- Original Oct29 prospective denominator **8,502** rows and retained watchlist **136** names (including eight outside the original provider universe) remain frozen. JDZG stale/halt/price-floor failure analysis remains unchanged. The 0/+1/+2/+3 **actual trading-session** horizons, matching untouched cohorts, false positives, late/exhausted watches, squeezes, costs, missingness, and historical baseline labels are preserved.
- **P0-1 remains blocked:** no two authenticated, genuinely independent provider organizations supplying official regular-session closes with full security identity, corporate-action parity, calendar and timestamp provenance, and complete third-source conflict reconciliation. Parent-domain heuristics and offline tests do not prove source independence. Oct29 h0 official matched outcomes remain unverified; Oct30 +1, Nov2 +2, Nov3 +3 are prospective, not backfillable. No 20%+ prospective prediction success or precision is established; outcomes remain censored.
- Optional Massive real-time entitlement, SMG platform short approval, durable off-platform original ZIP backup and live full-market halt clearance remain unverified. The official Nasdaq RSS is not a guarantee that a security is tradable.

Next engineering priority remains authenticated independent provider receipts and durable byte-preserving retention; do not change the frozen original evaluator or infer outcomes from IEX afterhours data.
