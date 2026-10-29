# OBSIDIAN Research Engineering — October 29, 2026, 08:47 CT checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** Scope strictly `research/obsidian-early-rug-20261025`. No market order, advice, notification, protected capture, main/production change, or credential operation.

## Verified research-only P0-1 change

- Read October 28 autonomous validation roadmap, Rug Proof's distinct anchor/SIP protocol, October 28 retention ledger, original marker directory, latest Morning Movers commit and 07:47 Engineering report before changing code. The branch was at `226ac5c2effb1984d582c62e5b6c7daa86220ab2`.
- Patched `backtest/obsidian_eod_source_body_binding_shadow.py` to **fail closed instead of crashing** when untrusted supplied JSON contains extreme finite Decimal exponents. The JSON parser now catches Decimal arithmetic exceptions; the positive-price parser rejects magnitudes outside an intentionally vast ±100 base-ten exponent arithmetic safety envelope. This is a numerical robustness guard, **not** an SMG price rule, official exchange price certification, or change to any frozen prediction policy.
- Added **three synthetic regression tests** covering an enormous current-close exponent, an unparseable JSON exponent, and an extreme tiny previous-close exponent. All preserve original source row indexing, censor affected claims and prevent a false 20%-threshold conclusion.
- Code commit `8a357075aeaa15d55812c14d7a15d7ee0b0a14ba` advanced using the expected-head branch lease. **GitHub Actions [run 40884755887](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40884755887) completed successfully on that exact commit; hosted job logs show 461 offline tests passed** (previously 458). The run produced **no artifacts**; it is a code-validation run, not a market-data capture.

## Outstanding source and execution gates

- No two independently authenticated provider-owned official 16:00 ET regular-session closes or corporate-action/issuer identity evidence for matched forward cohorts were retrieved in this checkpoint. Caller-supplied JSON and hashes remain unauthenticated. **P0-1 BLOCKED_EXTERNAL_EVIDENCE**; missing outcomes stay censored. No 20%+ prospective success, precision/recall or profitability is established.
- Preserve 0/+1/+2/+3 actual trading-session horizons, historical frozen baselines, untouched matched denominators, false positives, late/exhausted cases, squeezes, costs, and missingness. Preserve the original **136-name watchlist** and **JDZG stale/halt failure analysis**.
- Nasdaq Trader RSS is halt evidence, not a second official-close provider; optional Massive data access/real-time entitlement is unverified. SMG's actual account block table and short permissions are unverified; Alpaca borrowing cannot establish SMG approval.
- Rug Proof owns 09:20/12:20 anchors, 14:20 delayed SIP, and after-close review. Engineering's only original capture windows are **12:47 INTRADAY IEX** and **14:45–14:58 CT protected preclose**. This early morning engineering checkpoint was outside both; **no capture marker, duplicate anchor, after-hours or morning IEX trigger was created**.
- Original GitHub artifact ZIPs still have **BACKUP_UNVERIFIED** status and documented January 2027 expiry. No external archive destination was approved or written.

**Next gate:** obtain provider-owned independently authenticated closing-price evidence with complete conflict, identity, action, calendar and timestamps for genuinely untouched forward cohorts; do not score from synthetic fixtures or single-venue IEX.
