# OBSIDIAN Research Engineering — November 2, 2026 — EOD receipt Unicode alias consistency

**RESEARCH_ONLY_NOT_AN_ORDER.** P0-1 synthetic source-evidence integrity correction only. Not official exchange-close verification, market-data entitlement, a forward-outcome hit, SMG permission, or an order.

## Reproducible defect and correction

The offline EOD byte-receipt integrity screen (`backtest/obsidian_eod_receipt_integrity_shadow.py`) previously canonicalized provider organization claims and receipt IDs by whitespace/case only. The separate EOD source preflight and complete third-source conflict ledger had already adopted NFKC Unicode normalization and rejected invisible format controls. This inconsistency allowed two NFKC-equivalent claimed organizations on distinct hosts (e.g. `independent-a` versus `independent－a`) to appear independent in the **receipt layer**. Likewise, an NFKC-equivalent source receipt ID could escape duplicate detection. Invisible U+200B could create misleadingly distinct labels.

Implementation commit `227635f58286e1f880404f2c3b1af87f3a572582` aligns the byte-receipt alias screen with the existing independent preflight and all-source inventory: NFKC normalization, casefold/whitespace canonicalization and conservative rejection of Unicode format controls. The original supplied spellings remain in indexed source rows, and every original row remains accounted for. No evidence is promoted to verified official-close status by this code change.

Three new synthetic regression methods verify (1) compatibility-equivalent provider labels do not count as independent, (2) compatibility-equivalent receipt IDs are duplicate, and (3) invisible format controls in either field censor the source record. The tests use fabricated source receipts only.

## Hosted verification and task coordination

- [Prospective research CI run 41555045745](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41555045745) completed **success** on implementation commit `227635f58286e1f880404f2c3b1af87f3a572582`. Inspected hosted job log: **656/656** prospective tests and **4/4** ABC-board tests passed; all three new receipt regressions were observed as passing.
- Read the original October 28 validation roadmap, November 2 Rug Proof 14:20 delayed-SIP source verification and 18:20 postclose audit, latest independent EOD report, branch head, marker inventory, and recent workflows before writing. This checkpoint is outside the authorized 12:47 intraday and 14:45–14:58 preclose gates. **No** source marker, IEX capture, SIP trigger, retrospective backfill, duplicate issuer/day, morning/afterhours task work, or trading order was created.
- Refreshed hosted GitHub artifact metadata: November 2 afterhours independent monitor **13179429754**, afterhours IEX **13179494453**, protected preclose **13177274914**, Rug Proof delayed SIP **13176201670**, and Rug Proof intraday **13166549888** are all **present and unexpired** with recorded ZIP SHA-256 digests, expiry January 31, 2027. ZIPs were **not** downloaded/rehashed during this pass. Durable off-platform storage remains **BACKUP_UNVERIFIED**.

## Frozen denominators and outstanding external evidence

Original frozen historical **8,510-security** cohort, **34,040** issuer×0/+1/+2/+3 actual trading-session slots, all historical labels, **136-name** retained watchlist, and JDZG stale/halt analysis remain unchanged. The November 2 separately selected **8,501** IEX securities must not overwrite the frozen historical cohort. All unverified or immature outcome cells remain **CENSORED**; no success, precision, recall, false-positive rate, squeeze, execution cost, shortability, share count, fill or profitability claim.

**P0-1 remains blocked externally:** zero authenticated official regular-session close pairs from two genuinely independent underlying provider organizations with actual exchange calendar, previous close, complete third-source conflicts, security/issuer identity, corporate actions and timestamp provenance. Live Massive entitlement remains unverified. NFKC matching only screens caller-supplied aliases; it cannot prove actual source ownership or market-data authenticity.

No main, production, credentials, notifications, accounts, trading workflow, frozen baseline, or original captures were changed.
