# OBSIDIAN — P0-1 untrusted numeric source claim guard (2026-10-29 17:47 CT)

**RESEARCH_ONLY_NOT_AN_ORDER.** This is an isolated offline source-evidence preflight correction, not a new market observation, official-close receipt, trading signal, or forward success.

## Verified problem and correction

The source preflight accepted any finite positive Decimal. A vendor-supplied finite previous-close claim such as `1e999999999999999` could reach the 20% threshold calculation and raise `decimal.Overflow`, aborting the complete-source audit rather than preserving its missingness and censoring the invalid row. The same class of malformed current-close claims must not be accepted as evidence.

The preflight now rejects prices outside a deliberately broad Decimal exponent envelope (-100 to +100) before threshold arithmetic, retaining the original supplied-report denominator and recording `INVALID_SOURCE_PROVENANCE_OR_PRICE` plus insufficient-source evidence. The envelope is an arithmetic guard, **not** an SMG eligibility price floor. Two regression cases cover extreme current and prior close claims. No provider API calls were made for this patch.

## Source and outcome restrictions

The underlying provider names, domains, 16:00 timestamp claims, security identity, calendar, corporate actions, source ownership, and official exchange close remain **externally unauthenticated** by this offline module. Never feed the preflight result directly into frozen scoring. Forward 0/+1/+2/+3-session outcomes remain censored until independently authenticated. No prospective 20%+ prediction successes established.

## Coordination

No new morning, after-hours, early-board, intraday, preclose, or Rug Proof markers were created or replayed. The frozen 136-name cohort and JDZG stale/halt analysis are unchanged. The separate 18:20 CT Rug Proof audit retains ownership of its own checkpoint. Research branch only; no production, secrets, orders, notifications, or SMG execution.
