# OBSIDIAN Research Engineering — October 30, 2026, 10:47 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only. No trading, production/main, secrets, account permissions, notifications, original market captures, frozen baseline/denominators, 136-name watchlist, JDZG analysis, or separate scheduled checkpoint ownership changed.

## P0-1 — fail closed on redirected vendor-source receipts

The Massive/Twelve Data research-only two-provider daily-bar reconciliation used Python urllib's default redirect-following behavior. A vendor response redirecting to another host could otherwise yield a successful JSON bar labeled as the original vendor, despite an unverified final data source. This is a **source-independence/provenance** defect, not a demonstration that such a redirect occurred in a live run.

Research-only implementation commit `ef555b7981b7f5d946462b09a0bbf624567a7b94` adds a redirect-denying HTTP handler for the diagnostic vendor collector. It fails closed on **all** 3xx redirects (including same-host), classifies such receipts `UNTRUSTED_REDIRECT`, preserves their HTTP status and body hash without copying untrusted Location headers or echoed credentials into artifacts, and records `vendor_redirect_policy=DENY_ALL_REDIRECTS`. Two new regression tests verify redirect denial and censored, secret-free response normalization. No provider API call or workflow-dispatch live fetch was made.

GitHub Actions run **41083653368** on the implementation SHA completed **successfully**, with **26 offline tests passed** (22 vendor-reconciliation tests + 4 ABC-board tests). The vendor-fetch step was skipped on push; no reconciliation JSON artifact was produced, as expected. Evidence: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41083653368 .

## Original-source coordination

Before the change, refreshed exact branch head, roadmap, October 30 09:50 Engineering note, recent workflows, and morning Rug Proof/Morning Movers evidence. Original October 30 Rug Proof morning anchor run **41071432540**, artifact **12985950392**; Morning Movers discovery run **41069835420**, artifact **12985125331**; independent source monitor run **41069835376**, artifact **12984821795**. All three artifacts were still present and unexpired in GitHub metadata (expiry January 28, 2027); their raw ZIP bytes were not newly downloaded/rehashed here. No morning/after-hours IEX marker was created or duplicated. At this checkpoint, neither the original 12:47 CT INTRADAY gate nor 14:45–14:58 CT preclose gate was open.

## Evidence limitations and next gate

This corrects a **software source-identity safeguard only**. It does not authenticate the legal independence of Massive/Twelve Data, prove an independent underlying market feed, establish official regular-session auction closes, identify issuer/security continuity, or verify corporate actions, calendar, source timestamps, entitlements, or the complete third-source conflict inventory. Massive/Twelve Data daily OHLC prices remain **diagnostic vendor bars**, not admissible verified official-close outcomes. All missing prospective outcomes remain **censored**. Forward 0/+1/+2/+3 actual trading-session horizons, original frozen denominator, false positives, late/exhausted cases, squeezes, costs, and untouched future-cohort comparison remain unchanged. **No verified 20%+ collapse prediction success or profitability is established.** Durable independent raw-receipt backup remains unverified.

Next P0-1 work: obtain two separately authenticated independent organizations' actual official session-close receipts, source/issuer/action/calendar proof, and immutable conflict inventory; do not treat URL or provider-name checks as evidence of independence.
