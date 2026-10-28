# OBSIDIAN forward-study calendar assumption audit — 2026-10-27 21:46 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Outcome-blind review of the frozen forward evaluator; no outcome, policy, original capture, production, or trade modification.

## Verified code-level finding

`backtest/obsidian_forward_collapse_study.py::previous_weekday` treats the preceding weekday as the previous exchange session. It skips Saturday/Sunday, **not exchange holidays**. The same frozen evaluator requires a 16:00 ET close. These assumptions are correct for the October 27, 2026 ordinary session, but not for every future session.

Official exchange reference: [Nasdaq 2026 holiday schedule](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule?display=b2b). It lists Thursday **2026-11-26 Thanksgiving closed**, Friday **2026-11-27 early close at 13:00 ET**, Thursday **2026-12-24 early close at 13:00 ET**, and Friday **2026-12-25 Christmas closed**.

- **2026-11-27:** frozen weekday inference incorrectly selects closed **Nov 26** as the previous regular session rather than **Nov 25**. Separately, the frozen 16:00 rule correctly excludes the 13:00 early-close session under the existing written policy. This is a shadow-only diagnostic, not a request to start collecting or scoring early-close sessions.
- **2026-12-28:** the market's prior session is the **Dec 24 early-close session**, but frozen weekday inference selects closed **Dec 25**. The **Dec 28** regular session itself is a normal 16:00 close; an independently valid outcome could therefore be censored for the wrong previous date.
- **2026-10-27:** previous weekday **Oct 26** and 16:00 ET close match the normal session. No change to October 27's current validation status.

## Isolated research safeguard

Added `backtest/obsidian_forward_calendar_shadow.py` and six synthetic tests in `tests/test_obsidian_prospective_forward_calendar_shadow.py`. The shadow diagnostic requires explicitly supplied, dated exchange-calendar evidence, flags incompatible previous-session/close assumptions, and **never authenticates its own evidence, authorizes scoring, or places orders**. It does not change the frozen evaluator, target threshold, policy, or write-once captures.

Hosted [GitHub Actions run 40622858493](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40622858493) completed **success, all 309 offline tests passed**. CI paths include the isolated diagnostic and its tests.

## Open validation gate

No independent, provider-distinct, exact-price-as-of 16:00 ET October 27 EOD outcome JSONL with completed security-identity and corporate-action corroboration is available. The original **8,515-symbol** preclose denominator is preserved; early hits, recall, precision, and after-cost P&L remain **unknown**, not zero.

Do not change the frozen scorer after seeing outcomes. For a future holiday-adjacent session, record this shadow warning and censor until a prospectively specified, independently verified calendar-compatible evaluation protocol exists. No retrospective trigger or after-hours backfill. No main, production, credentials, live alerts, orders, or SMG trading changes.
