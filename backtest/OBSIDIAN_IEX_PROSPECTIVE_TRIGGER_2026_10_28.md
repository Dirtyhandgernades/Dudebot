# OBSIDIAN IEX prospective preclose research trigger — 2026-10-28

RESEARCH_ONLY_NOT_AN_ORDER

- Session: Wednesday, 2026-10-28, NYSE/Nasdaq regular equity session.
- Trigger decision time: 2026-10-28 14:47 America/Chicago (15:47 America/New_York), within the protected 14:45–14:58 Central gate.
- Independent calendar checks: Nasdaq 2026 US holiday/trading schedule https://www.nasdaq.com/market-activity/stock-market-holiday-schedule ; NYSE hours and holidays https://beta.nyse.com/trade/hours-calendars . October 28 is not a scheduled holiday or early-close date; core market session ends 16:00 Eastern.
- Scope: one write-once authenticated IEX single-venue research observation for the current session, using the existing push-triggered research-only workflow.
- This marker is not a trade, alert, borrow determination, SIP capture, official close, or full market coverage.
- Exactly one trigger for this session. Do not retry, backfill, or move the capture outside its execution gate if the workflow is delayed or fails.
- Preserve original requested-symbol denominator, missingness, pre-decision timestamps, hashes, and frozen policy. No secret values or production changes.
