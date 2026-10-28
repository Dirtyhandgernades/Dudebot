# OBSIDIAN IEX intraday research discovery — 2026-10-28

RESEARCH_ONLY_NOT_AN_ORDER

This is the one write-once intraday discovery trigger for Wednesday, October 28, 2026, on research/obsidian-early-rug-20261025.

Created during the 12:40–13:15 America/Chicago research checkpoint (approximately 12:52 CDT), after independent confirmation from NYSE and Nasdaq 2026 calendars that October 28 is a normal trading session. The authenticated October 28 morning observation was already completed separately; the 2026-10-28_INTRADAY trigger did not previously exist on this branch. The standalone discovery workflow and its offline tests passed in GitHub Actions run 40704289113, and research CI passed in run 40622858493.

This marker authorizes only the existing push-triggered, read-only, single-venue IEX research-discovery workflow. Do not retry this intraday phase if the workflow fails, runs late, or produces no artifact. Do not backfill, touch secrets, submit orders, trigger the protected preclose workflow, or modify frozen forward-study policy. Record requested-symbol denominator, hashes, timestamps, missingness, and source limitations without implying official closes, SIP coverage, or SMG eligibility.
