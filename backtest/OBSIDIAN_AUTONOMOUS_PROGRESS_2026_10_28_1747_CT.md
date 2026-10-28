# OBSIDIAN — 2026-10-28 17:47 CT autonomous validation engineering

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only; no main, production, credential, alerts, orders or frozen-policy changes.

## Verified this pass

- Refreshed branch, original IEX capture metadata, roadmap, source-contract shadow, 1–3 session forward shadow, and recent GitHub jobs before changes. The existing independent EOD intake and 0/+1/+2/+3 session shadow are already implemented; no duplicate scorer was created.
- Implemented isolated `backtest/obsidian_matched_cohort_lock.py`, with `tests/test_obsidian_prospective_matched_cohort_lock.py` and research-only CI path registration. Commit: `2de0e3644ed152924538761a56b2fa3cdf508297`.
- **Hosted GitHub Actions run 40782588848 passed 347 offline tests**, including all seven new matched-cohort synthetic tests. Run: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40782588848
- New lock calls existing immutable morning/intraday transition verification and retains every union ticker once, preserving original status and both raw universe SHA256 identities. Records earliest *capture-finished* decision timestamp (not retrospectively earlier), separately identifies comparable threshold crossings versus stale-to-visible watches, quarantines changed security IDs/prior IEX bars, and does not aggregate correlated scans into independent events.
- The new module deliberately produces **no official-close verification, hits, precision, recall, after-cost P&L, SMG eligibility or order**. The synthetic tests validate code invariants only. It has **not yet been executed on the October 28 original raw artifacts**, so no empirical cohort counts are claimed from this new module.

## Outstanding P0 evidence gate

- No externally independently authenticated completed regular-session EOD outcome packet with exact close-as-of, calendar chain, all provider conflicts, security identity and corporate-action corroboration has been demonstrated. Earlier original October 28 morning and intraday captures are write-once evidence; IEX last prints are not official closes.
- The October 28 preclose artifact 12846452112 remains a separate original 8,511-symbol cohort; do not merge its post-14:45 observations into earlier morning/intraday decisions. October 28 afterhours artifact 12849591039 is too stale for broad discovery.
- Next safe work: run the new matched-cohort lock against authenticated original morning/intraday ZIPs once their exact extracted paths are accessible in an approved research runner; retain output artifact hash and full union denominator. Independently source EOD/corporate-action evidence before any scoring. Do not tune against the seen October 28 outcomes or modify frozen scorers.

**No capture triggers, retries, backfills, secrets, production or trading actions.**
