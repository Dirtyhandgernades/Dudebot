# OBSIDIAN October 27 after-hours research capture — missed authorized checkpoint

**Research-only; not an order or trading signal.** This note records an actual missing observation, not a simulated or retrospectively reconstructed market snapshot. No changes to main, production, secrets, live alerts or orders.

## Source audit at 2026-10-27 15:43 CT
- The dedicated after-hours automation's run was **scheduled for 2026-10-27 15:22 CT** (20:22 UTC), but the runtime began at **15:17:22 CT** and completed at **15:19:06 CT**, *before its nominal scheduled clock time*.
- Its output explicitly declined to create the after-hours research trigger because it considered 15:22 CT not yet reached, despite being the scheduled 15:22 checkpoint and already inside the separately authorized 15:00–15:45 CT window.
- A subsequent GitHub branch tree check found **no** `backtest/OBSIDIAN_IEX_RESEARCH_DISCOVERY_TRIGGER_2026_10_27_AFTERHOURS.md` on `research/obsidian-early-rug-20261025`.
- The branch's research-discovery workflow runs on October 27 were morning **40516649174** and intraday **40553266211**. The separate protected preclose IEX capture **40572768800** succeeded. **No authenticated after-hours IEX capture artifact** was present as of this audit.
- The hourly Research Engineering pass at 15:43 CT is NOT the uniquely authorized after-hours 15:22 scheduled run. Do not create the marker now, backfill after-hours prices or retry this session. Missing after-hours data must remain **missing** in the provenance ledger.

## Reliability fix for future sessions (no capture retry)
Clarified the existing After-Hours Audit automation prompt to recognize its authoritative `scheduled_for=15:22 CT` as the unique permitted checkpoint when the runtime starts a few minutes early, provided actual time remains inside 15:00–15:45 CT, a real NYSE/Nasdaq session is independently verified, and the one-time marker is absent. Existing schedule, branch and conversation destination are preserved. This does not authorize an additional checkpoint, off-window trigger, retrospective capture or new trading action.

## What remains proven and what remains unknown
- October 27 protected 14:51 CT raw capture remains verified: **8,515** symbols, **433** price-only early-weakness watches, **9** exhausted, **4,252** stale/future IEX trades, raw universe SHA-256 `10a3d8f30726759105394dac6eeaf6bccc208932d43e1faa51507809aa8c0bb4`.
- INOD, CLW, ARTV and ACRS remain research timing examples; IEX price/reference differences are NOT independent official prior/regular-session closing returns.
- The frozen forward outcome study requires two independently timestamped agreeing official regular-session closing sources plus corporate-action/security-identity comparability; a complete validated outcome input for the original captured universe has **not** been found in this branch audit. Missing outcomes remain censored, so confirmed early-hit count, recall, precision and simulated after-cost P&L are **not measurable**.
- October 27 after-hours-only movers cannot be independently scored from a non-existent after-hours raw capture. Next permitted attempt is a **future** authorized session, never October 27.
