# OBSIDIAN — Research engineering 20:47 CT checkpoint (October 29, 2026)

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only. No new market capture, prediction, trade, main/production modification, source credential access, or protected trigger.

## Highest-priority P0-1 source/calendar integrity repair

The complete all-source EOD conflict inventory previously validated that `previous_regular_close_at` belonged to the correct previous date but **did not validate its clock time**. Two agreeing provider reports could therefore reference a previous-session **intraday** or **after-hours** print, pass the structural gate, and distort the 20% reference threshold. The audit still censored official scoring, but its `STRUCTURALLY_CONSISTENT_EXTERNAL_AUTH_PENDING` status was overly permissive.

Implementation commit `146594084b260b5da8c140bd3aab0fc099ed71cf` now requires the previous close to be **exactly 16:00:00.000000 America/New_York** in this frozen normal-session protocol. A 13:00 ET previous early close is explicitly flagged as requiring a separate nonfrozen protocol rather than being silently treated as 16:00; any other prior clock is a conflict. Nonboolean `early_close` calendar claims are rejected instead of silently interpreted as normal sessions. Original source rows and denominators are preserved and the result remains censored.

## Verification and overlap review

- Hosted research-only GitHub Actions **40987910315** completed **successfully**, commit `146594084b260b5da8c140bd3aab0fc099ed71cf`, 2026-10-30 01:47 UTC (October 29 20:47 CDT). The full suite passed **489 prospective + 4 ABC = 493 offline tests**; the three new regression cases for previous intraday reference, previous early close, and malformed early-close flag all passed.
- Prior research branch head before the fix: `e24df02f581949269f7f792b1b7c2d7b8a5a91fb`. Expected-head lease succeeded; no protected baseline, original artifact, 136-name watchlist or JDZG stale/halt case was rewritten.
- Reviewed original Rug Proof October 29 18:20 postclose audit and the 20:25 CT After-Hours audit, including their distinct marker ownership and censored forward outcomes. No extra 12:47/14:47 IEX or morning/after-hours marker was created outside its authorized window.
- The hosted test workflow produces no market evidence artifact. This is a **software structural integrity regression**, not a newly authenticated price.

## Remaining acceptance blockers

Two genuinely independent organization-level **official** regular-session close sources remain unverified, as do independent exchange-calendar provenance, issuer/security identity and corporate-action continuity, full third-source conflict completeness and a durable raw-receipt archive. AAPL/MSFT historical vendor daily-bar agreement is diagnostic only. Keep all original prospective 0/+1/+2/+3 session slots and unmatched cases **censored**; no 20%+ forward collapse success, precision, recall or trade eligibility is established. No inference of SMG shortability from Alpaca or market-data API access.

Source CI: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40987910315
