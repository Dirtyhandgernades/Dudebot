# OBSIDIAN October 28, 2026 after-hours authenticated IEX research discovery — single authorized checkpoint

**Research-only, non-trading, source-limited.** This marker was created at the October 28 Wednesday **15:22 America/Chicago scheduled After-Hours Audit checkpoint** (actual start 15:25 CT, within the independently authorized 15:00–15:45 CT window). NYSE and Nasdaq official 2026 exchange calendars confirm October 28 is an ordinary trading session. The independent `.github/workflows/obsidian-iex-research-discovery.yml` last succeeded at run 40739809362, including offline CI, source-limited capture, verification and artifact upload. Research-only journal CI also passed run 40748516089. The branch was inspected for this exact after-hours marker and no prior marker or after-hours discovery run existed.

**Purpose:** trigger exactly ONE branch-only GET-only Alpaca IEX single-venue after-hours observation. Preserve all requested symbols, hashes, freshness/missingness and original IEX reference limitations; never promote IEX prior bar to official regular-session previous close. No backfill, retry, main, production, protected preclose capture, credentials inspection, live alerts or orders. Keep original frozen forward-rug scoring policy unchanged. If this run fails, preserve failure evidence and do not create another marker for the same date/phase.

Official exchange calendars:
- https://www.nasdaq.com/market-activity/stock-market-holiday-schedule
- https://www.nyse.com/trade/hours-calendars
