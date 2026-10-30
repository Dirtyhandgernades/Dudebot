# OBSIDIAN Research Engineering — October 30, 2026, 07:45 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated research branch `research/obsidian-early-rug-20261025`; no production/main, credentials, trades, alerts, frozen baseline or original market capture changed.

## Verified P0-1 software correction

Read `OBSIDIAN_AUTONOMOUS_VALIDATION_ROADMAP_2026_10_28.md`, October 29 Rug Proof postclose audit, October 30 07:12 CT Morning Movers note, the current EOD conflict inventory and tests. Original branch head before the code change: `033f589571a764c9bfabf6dc67f294f00dc53851`. The EOD conflict inventory previously counted claimed organization names and distinct source hostnames but did not reject distinct names on subdomains of the same apparent parent. This could yield `STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING` for two apparent provider aliases despite a separate strict preflight rejecting that pattern.

Code commit `bc5c9a8802fa7efd8edc397b989f1d35c334e0d4` adds the same conservative apparent-parent-host alias screen to the complete indexed conflict inventory. A third independent hostname cannot conceal an alias collision; all original source rows, price claim groups, contradictory third-source prices and censoring are preserved. The host-parent heuristic is **not** legal ownership verification, official exchange close authentication, or public-suffix proof. The module still sets `official_regular_close_verified=False`, `eligible_for_frozen_scoring=False` and `outcome_censored_pending_external_evidence=True`.

Two new synthetic regression tests cover two apparent provider aliases and a third-host masking attempt. **Hosted GitHub Actions run 41057795306 succeeded** on the code commit; runner log: **517 prospective offline tests + 4 ABC-board tests passed (521 total)**. Source: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41057795306 . No live provider fetch or entitlement authentication was performed.

## Independent capture and cross-task coordination

Existing original October 29 artifacts were rechecked by GitHub Actions metadata, **not rehashed ZIP bytes**: preclose IEX run `40943205148`, artifact `12928470853`; afterhours IEX run `40947825425`, artifact `12930640520`; distinct Rug Proof delayed SIP run `40939489402`, artifact `12925833012`. All three are currently `expired=false` and report January 27, 2027 expiration. October 30 07:12 Morning Movers has no original October 30 morning trigger yet; Engineering created **no** MORNING, AFTERHOURS, INTRADAY, protected preclose, independent monitor, or Rug Proof marker at this out-of-window checkpoint. Separate owners and one-shot gates remain intact.

The frozen **136-name watchlist** (113+23), JDZG stale/halt/price-floor analysis, historical original universe/denominator, 0/+1/+2/+3 actual trading-session evaluation, unmatched/late/exhausted/squeeze/cost/missingness treatment and all prior prediction labels remain untouched. No issuer/day double counting or retrospective promotion.

## Remaining external evidence gates

No two **genuinely independent, authenticated provider organizations** have furnished complete official 16:00 ET regular-session close and previous-session close receipts, source-owned retrieval and timestamps, security identity and corporate-action parity, verified exchange calendar and all-source conflict provenance. The historical Massive/Twelve Data vendor OHLC diagnostic is not proof of official independent exchange closes. No Massive live quote entitlement, current full-market halt clearance, SMG blocked-symbol/security table or actual account borrow/permissions are verified. All unsupported forward outcomes remain **censored**; no prospective 20%+ prediction success, precision, recall or profitability is established. Long-lived raw archive remains unverified.

**Next P0 gate:** authenticate actual source-owned regular-close receipts and source independence, including third-party conflicts and corporate actions, before considering any forward outcome admissible.
