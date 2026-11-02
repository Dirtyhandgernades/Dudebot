# OBSIDIAN independent monitor — published-session calendar guard (2026-11-01 21:49 CST)

**RESEARCH_ONLY_NOT_AN_ORDER.** Research branch only. No production/main, credentials, orders, original prospective IEX markers, Rug Proof anchors, frozen labels, or cohort denominators are changed.

## Defect and bounded correction

The independent Nasdaq halt / optional Massive quote collector previously treated any weekday in the allowed wall-clock interval as a permissible exchange session. On an official full-day NYSE/Nasdaq holiday, that would allow unnecessary source GETs. On November 27 or December 24, 2026, the original 12:47 CT intraday interval would fall *after* the published 13:00 ET regular close.

The monitor now rejects published 2026 full closures and post-early-close INTRADAY / EARLY_BOARD windows **before constructing a network session or making a GET**. The preexisting morning and after-hours *research* phases are not redefined, and the original protected 14:45–14:58 CT prospective IEX capture remains entirely separate and untouched. Calendar year 2027+ is deliberately **not certified** by this static 2026 schedule; extending it requires a separately reviewed source update, not a guessed holiday formula. This stricter fail-closed calendar check does not establish live market-open status, unexpected closures, Massive entitlement, exchange-authoritative current halt clearance, or independently authenticated official closes.

Published exchange references: https://www.nyse.com/trade/hours-calendars and https://www.nasdaq.com/market-activity/stock-market-holiday-schedule . The dates are explicitly embedded for offline reproducibility; the calendar is not a live authenticated exchange receipt.

Four deterministic regressions cover Thanksgiving/Christmas full closures, both early-close afternoons, permitted early-close morning/postclose research, and unsupported 2027, with zero provider GETs for rejected requests.

## Evidence and unchanged blockers

Original Oct 30 Rug Proof markers and postclose audit were read before work; no duplicate capture, new issuer/day case, retroactive prediction, or replay was created. Seven protected Oct 30 artifact metadata records were rechecked (IDs 12985950392, 12995764777, 13006191628, 13006897253, 13008429628, 13010065001, 13018333034); all reported expired=false, expiry January 28, 2027, and retained original SHA-256 digest metadata. ZIP bytes were **not** rehashed; off-platform backup/restore remains **BACKUP_UNVERIFIED**.

The 8,510 frozen Oct 30 security rows, 34,040 issuer×0/+1/+2/+3 slots, 1,653 watch/6,857 nonwatch split, 136 retained names (nine off-universe references), and JDZG stale/halt/$3-floor analysis remain unchanged. Oct 30 +1/+2/+3 sessions are November 2/3/4 and had not matured on November 1. Zero two-organization authenticated official regular-session close outcomes are established; missing outcomes remain censored, not hits or misses. SMG platform borrow/blocked-symbol/account permission, verified 20%+ prediction accuracy, false positives, fills, costs, squeezes, and profitability remain unestablished.

CI status is recorded in the follow-up verified progress note, not assumed from this source change.
