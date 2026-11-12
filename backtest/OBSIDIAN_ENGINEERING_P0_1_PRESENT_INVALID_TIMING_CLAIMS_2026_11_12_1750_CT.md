# OBSIDIAN Research Engineering — P0-1 present-invalid timing provenance (2026-11-12 17:50 CT)

**RESEARCH_ONLY_NOT_AN_ORDER.** Scope: `research/obsidian-early-rug-20261025`; read-only research. This note does not authenticate a market outcome.

## Verified engineering change
- Starting branch head `594bdfc6c77fa71332f84c8df8e26a5a2171d812`.
- Research-only code and regression commit `055676aa2a699e825c91b76cbd4ec02561987bd5`, committed using expected-head lease.
- [Hosted CI run 43332312907](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/43332312907) completed **success** on the exact code commit. The job logs independently report **771 prospective offline tests and 4 board tests passed**, four new regression tests compared with the prior 767.
- Scope: `backtest/obsidian_eod_source_body_binding_shadow.py` and `tests/test_obsidian_prospective_eod_source_body_binding_shadow.py` only. No live provider request or account access.

## Corrected evidence classification
The body-binding auditor formerly marked unsupported-precision nonempty strings as invalid, but present `null`, empty or nonstring source publication/action-check timestamps had no distinct invalid-source index; malformed `corporate_action` containers also appeared as missing timing claims. The new source-indexed `invalid_body_timing_claim_source_indices` includes these present malformed values, and `explicitly_absent_body_timing_claim_source_indices` distinguishes fields omitted from otherwise parseable JSON bodies. The existing `missing_body_timing_claim_source_indices` remains unchanged for compatibility, including entirely unparseable bodies. The original rejected source indices remain censored; untrusted values are not echoed. Passing offline tests is not provider authenticity or official closing-price proof.

## Other research workflows and capture ownership
- Re-read the original [Rug Proof November 12 delayed-SIP source-quality receipt](https://github.com/Dirtyhandgernades/Dudebot/blob/research/obsidian-early-rug-20261025/backtest/OBSIDIAN_RUG_PROOF_SOURCE_QUALITY_2026_11_12_1420_CT.md), its `OBSIDIAN_RUG_PROOF_SIP_2026_11_12.md` marker and original intraday anchor. The delayed SIP is not an official close or real-time signal; its original 8,492-row denominator and missingness are preserved.
- November 12 after-hours IEX run `43310308440` artifact `13985601925` (GitHub-reported sha256 `b38dcf4e51de540149f387f93c1b719b02182b8cfd216abaac2f68cf127fe437`) and independent-monitor run `43310308370` artifact `13986355792` (GitHub-reported sha256 `e8d19ef1d871af281a1ae3707037f7d9e15080d151ac937c3445d8d15d06008a`) remain present, both expiring 2027-02-10. These digests were re-read from GitHub metadata, **not** independently rehashed from ZIP bytes. Durable backup remains **BACKUP_UNVERIFIED**.
- Existing November 12 12:47 CT IEX and independent-monitor markers already exist. This 17:50 CT checkpoint is outside both authorized 12:47 intraday and 14:45–14:58 CT protected preclose gates. No late marker, retry, backfill, Morning Movers, After-Hours or Rug Proof duplicate was created.

## P0-1 external blockers and frozen evaluation
Two authenticated, genuinely independent provider organizations' **official 16:00 ET regular-session closes**, exact previous-session references, complete third-source conflict ledger, exchange calendar, issuer/security/share-class identity, and corporate-action proof remain **unverified**. Massive live entitlement and actual SMG platform blocked-symbol/security/account short permission remain **unverified**; Alpaca borrow does not establish SMG approval. All unsupported outcomes remain **CENSORED**. Preserve the original 136-name watchlist, JDZG stale/halt failure analysis, frozen historical labels and denominator, and untouched future cohorts at 0/+1/+2/+3 actual trading sessions, including false positives, late/exhausted cases, squeezes, costs and missingness. No 20%+ prediction success or profitability is claimed.

No main, production, credentials, orders, trading notifications, fills or policy changes.
