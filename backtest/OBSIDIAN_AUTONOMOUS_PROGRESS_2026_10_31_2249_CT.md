# OBSIDIAN autonomous research engineering — October 31, 2026, 22:49 CDT

**RESEARCH_ONLY_NOT_AN_ORDER.** Authorized branch `research/obsidian-early-rug-20261025` only. Saturday: no cash-equity regular session, no 12:47 INTRADAY IEX, 14:47 protected preclose, independent monitor, morning/afterhours or Rug Proof marker; no retries/backfills, orders, alerts, main/production/credential changes or frozen-label edits.

## P0-1 — reject known closed 2026 cash-equity dates before vendor requests

The bounded two-provider daily-bar diagnostic previously accepted weekend and published exchange-holiday dates as syntactically valid requested `sessions`. A hypothetical vendor response for such a date could become `VALID_VENDOR_BAR`, despite no regular cash-equity session. Implemented a narrow, **static scheduled-date screen for 2026** in `backtest/obsidian_two_provider_close_reconciliation.py`, with three new regression tests in `tests/test_obsidian_two_provider_close_reconciliation.py`:

- Preflight refuses Saturdays, Sundays, all ten published 2026 NYSE Group full closures, and dates outside the explicitly reviewed 2026 calendar **before any paid provider request**. The separate normalized-observation path censors the same cases as `CLOSED_OR_UNVERIFIED_EXCHANGE_SESSION`; it does not produce a vendor price or falsely claim a completed session.
- Published full closures: Jan 1, Jan 19, Feb 16, Apr 3, May 25, Jun 19, Jul 3, Sep 7, Nov 26 and Dec 25, 2026. The published Nov 27 and Dec 24 **13:00 ET early closes remain scheduled dates**, but the pre-existing conservative `request_started_at > 16:00 ET` daily-bar cutoff is intentionally **not** relaxed. October 12 and November 11 are scheduled regular trading dates, not bond-market holidays for this cash-equity gate.
- The output now identifies `STATIC_NYSE_2026_SCHEDULE_ONLY_NOT_SESSION_AUTHENTICATION`. This is a deterministic **published schedule screen**, NOT proof that any actual session traded, that no unscheduled closure occurred, that Nasdaq or an issuer was open, or that a vendor price is an exchange-official closing auction price. A future year needs separately reviewed dates; no silent calendar rollover. No changes to scoring, provider request budgets, secrets, frozen cohort, or original protected gates.

Source: NYSE Group's [2026/2027/2028 published holiday and early-close calendar](https://www.nyse.com/trade/hours-calendars), corroborated by [NYSE Group December 23, 2025 announcement](https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/). Static schedule transcription is not authenticated runtime exchange-calendar evidence.

Implementation commit `d0af0d7b6cb5b1fc7856e0134eedc487d4ab9a1e` used expected-head branch lease. [GitHub Actions run 41270800371](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41270800371) completed **SUCCESS on that exact commit**; inspected hosted job log: **48/48 offline tests passed** including all three new calendar regressions. Live provider-fetch step was **SKIPPED** (push event), artifact upload found no output, and **no new vendor data, entitlement or official close evidence** was produced.

## Cross-task and original evidence unchanged

Re-read Oct28 roadmap, Oct30 18:20 Rug Proof postclose audit, Oct31 21:51 engineering note and existing original markers. No duplicate source capture, issuer/day counted twice, or attempt to take over Rug Proof's 09:20/12:20/14:20/18:20 anchors. Rechecked GitHub Actions metadata for three protected Oct30 artifacts:
- Preclose run `41118123273`, artifact `13006897253`: present, `expired=false`, digest `sha256:ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4`, expires `2027-01-28T19:47:32Z`.
- Maturity replay run `41140665058`, artifact `13018333034`: present, `expired=false`, digest `sha256:956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc`, expires `2027-01-28T22:49:48Z`.
- Independent monitor run `41122875006`, artifact `13010065001`: present, `expired=false`, digest `sha256:f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359`, expires `2027-01-28T20:24:01Z`.

These are GitHub **metadata** digests, not newly downloaded/rehashed ZIPs. Off-platform durable copy and restore remain **BACKUP_UNVERIFIED**.

Original Oct30 **8,510 securities**, **34,040 h0/+1/+2/+3 actual-trading-session slots**, 1,653 original preclose price-only watches, 136 retained names, JDZG stale/halt/floor investigation, all frozen historical baseline labels and complete missingness denominator remain untouched. Oct30 h0: **8,510 CENSORED_MISSING**; Nov2/3/4 +1/+2/+3: **8,510 NOT_YET_MATURE each**. No verified forward hit, false positive, precision/recall, timeliness, shortability, fill, share size, after-cost P&L or 20%+ predictive success.

**P0-1 blocker unchanged:** Zero independently authenticated exchange-official regular-session closes and previous-session references from two genuinely independent source-provider organizations with security-identity, corporate-action, actual session-calendar, original timestamp, feed-ownership and third-source-conflict proof. Numeric agreement between two vendor daily OHLC bars, a static calendar, Nasdaq halt RSS, or optional Massive quotes does not satisfy that gate. Next priority: authenticated independent official-close evidence and independently verified durable artifact restore, with all unverified outcomes censored.
