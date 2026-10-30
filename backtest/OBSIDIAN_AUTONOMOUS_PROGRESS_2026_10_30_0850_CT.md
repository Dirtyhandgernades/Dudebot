# OBSIDIAN Research Engineering — October 30, 2026, 08:50 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only; no main/production, credentials, market orders, account access, alerts, historical labels or original capture edits.

## P0-1 correction: local/private and malformed EOD source hosts

Roadmap priority P0-1 remains authenticated, independent official regular-session closing-price evidence. The offline EOD source receipt guard and separate preflight had duplicated permissive URL-host syntax checks. Previously an alleged provider source such as `https://127.0.0.1/close`, `https://[::1]/close`, `https://localhost/close`, `https://a.local/close` or a malformed DNS label could pass the structural hostname screen and count toward claimed independent providers. This was **not** an actual live fetch/SSRF, but was misleading structural evidence.

Code commit `e6febbcfaf4b64a28ec22ad0654d31e799967362` adds an external public-DNS host syntax requirement to the shared receipt guard: reject IP literals (including loopback/link-local), single-label and local/internal names, malformed/non-ASCII DNS labels and oversized labels. The offline EOD preflight now reuses that same guard, avoiding divergent validation rules. It still permits documented synthetic `.example` fixture hosts; no URL check establishes provider ownership or independence. The complete conflict ledger keeps rejected third-party price assertions and 20% threshold disagreements visible rather than discarding their rows.

Three synthetic regression tests cover receipt rejection, preflight rejection, and third-source conflict retention. **Hosted Actions run 41066763121 succeeded** on the code commit: **520 prospective offline tests plus 4 ABC-board tests passed (524 total)**. This verifies code contracts, not official prices, prediction accuracy or market data entitlements. Run: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41066763121 .

## Coordination and protected evidence

Read the frozen roadmap, previous October 30 Engineering note and October 29 Rug Proof morning verification. The research branch had advanced to `0f6917cad8ad530ffdad9def3cc22fd435b2f24f` after the distinct 08:09 CT Morning Movers audit; Engineering did not replace its work. Rechecked GitHub Actions metadata for October 29 original preclose IEX run `40943205148` / artifact `12928470853`, after-hours IEX run `40947825425` / artifact `12930640520`, and Rug Proof delayed SIP run `40939489402` / artifact `12925833012`: each completed successfully, currently unexpired, expires January 27, 2027. These checks **did not rehash ZIP bytes**.

At 08:50 CT no authorized 12:47 INTRADAY IEX or 14:45–14:58 protected preclose gate was open. No new marker, capture, independent monitor trigger, Morning Movers, After-Hours, Early Board or Rug Proof artifact was created. The separate Rug Proof 09:20/12:20/14:20/18:20 anchors remain its owner's responsibility; no issuer/day double counting.

Original 136-name retained watchlist, JDZG stale/halt/price-floor diagnostic, frozen historical denominators and labels, 0/+1/+2/+3 actual trading-session outcomes, future untouched cohort matching, false positives, late/exhausted cases, squeezes, costs and missingness were not changed.

## Unresolved external evidence

There are still no two genuinely independent authenticated official regular-session close sources with exact prior/current session closes, complete source/conflict inventory, provider ownership, issuer/security identity, corporate actions, official exchange-calendar proof and receipt timestamps. No Massive live quote entitlement, actual SMG blocked-symbol/security table or account permissions are verified. Missing outcomes remain **censored**. No prospective 20%+ collapse success, precision, recall or profitability is established. Durable raw-source backup remains unverified.

**Next P0 gate:** Obtain independently authenticated source-owned official-close receipts and complete corporate-action/source-identity evidence without touching frozen scoring.
