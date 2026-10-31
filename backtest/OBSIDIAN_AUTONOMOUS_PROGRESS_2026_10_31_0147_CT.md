# OBSIDIAN Research Engineering — October 31, 2026, 01:47 CDT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Saturday non-trading-day engineering only. No IEX, SIP, halt-monitor, protected preclose, Morning Movers, After-Hours, Early Decision Board, or Rug Proof capture/marker; no orders, credentials, main/production, original historical baselines, or watchlist changes.

## P0-1 — complete third-source numeric disagreement, including rejected evidence

Implementation commit `4778bdc2589319b407adc7baca42d4ac61612d45` on `research/obsidian-early-rug-20261025`, advanced from exact prior head `94e18a826fcdc631a39f65b1b5c270d3e9943dd2` using expected-head GitHub lease.

The all-source EOD conflict ledger already retained rejected-source price pairs and threshold-straddling claims. However, a rejected third source with a different completed-session close or prior close **that did not change the 20% classification** lacked a specific all-supplied numeric-conflict flag. The existing `ALL_SOURCE_*_CONFLICT` checks intentionally covered only structurally valid reports. This could understate the complete third-source disagreement in downstream audits.

Research-only correction in `backtest/obsidian_eod_conflict_inventory.py` adds separate, explicitly unauthenticated flags:
- `ALL_PARSEABLE_SOURCE_REGULAR_CLOSE_CONFLICT` for >$0.005 dispersion among *all* parseable current-close claims, including rejected rows.
- `ALL_PARSEABLE_SOURCE_PREVIOUS_CLOSE_CONFLICT` for >$0.005 dispersion among all parseable prior-close claims.
- `ALL_PARSEABLE_SOURCE_REFERENCE_PREVIOUS_CLOSE_DISAGREEMENT` for any parseable prior-close difference, even below the half-cent tolerance, because the 20% denominator changes.

All original indexed rows, their valid/rejected provenance, frozen denominator, and existing accepted-only checks remain intact. Rejected claims are **never** treated as authenticated closes or promoted to scoring.

Three synthetic regressions cover rejected third-party current-close conflict without threshold straddling, prior-close conflict without straddling, and agreeing prices. Hosted GitHub Actions [run 41177810412](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41177810412), exact implementation SHA, **SUCCESS**. Job `124468895498` completed all steps; log verifies **548 prospective tests + 4 ABC board tests passed**, including the three new tests. This is offline software validation, **not** proof of real provider ownership, independent closes or trading accuracy.

## Evidence retention and unresolved acceptance gates

Read-only artifact metadata rechecked: protected October 30 preclose artifact `13006897253` (ZIP SHA256 `ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`), maturity replay `13018333034` (`956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc`), independent monitor `13010065001` (`f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`) remain present, unexpired, with January 28, 2027 expiries. This checkpoint verified metadata, **not fresh downloaded ZIP bytes**; durable off-platform backup remains `BACKUP_UNVERIFIED`.

Original October 30 protected cohort remains **8,510 securities**, **1,653 preliminary price-only weakness labels**, **34,040 0/+1/+2/+3 original issuer-session slots**. No independently authenticated official regular-session closes from two genuinely independent provider organizations, with verified upstream ownership, prior closes, security identity, corporate actions, timestamps and complete source conflicts, were established. Massive live entitlement/quotes are unproven; original 136-name watchlist and JDZG stale/halt failure analysis preserved. All unavailable outcomes stay censored, including Oct30 h0; Nov2/3/4 are not yet mature. Zero **verified** 20%+ prediction hits, false-positive rates, after-cost edge, executable SMG shorts, fills or profits have been established. No actual trading actions.

**Next gate:** authenticated independent provider-level official closing-price receipts and verified source ownership/identity/action chain; preserve the original cohort and all-source conflict inventory. Do not tune on matured cases or count duplicate issuer-days.
