# OBSIDIAN Research Engineering — November 2, 2026, morning checkpoint

**RESEARCH_ONLY_NOT_AN_ORDER.** P0-1 vendor receipt-integrity correction on `research/obsidian-early-rug-20261025` only. No protected prospective source capture, intraday/preclose marker, retry, backfill, production/main change, credentials, trading notification, SMG account access, or order.

## Verified engineering correction

The bounded Massive/Twelve Data JSON decoder already constrained floating-point tokens to 100 significant digits and bounded exponent range, but default `json.loads` integer parsing still accepted arbitrarily long integer tokens in auxiliary fields (or raised only at the Python runtime's separate digit limit). Such a body could be treated as a usable vendor bar even though its numeric receipt was outside the intended bounded evidence policy.

Commit `93dc5336dd9efd14592cc30100b2b53c3cdcd321` adds `_bounded_vendor_int` and installs it as `parse_int` for every nesting level. More than 100 integer digits, including negative and 5,000-digit auxiliary claims, now cause the entire affected JSON payload to be censored before any vendor price is admitted. The bounded raw-body SHA256 remains available; ordinary integer status codes and at-most-100-digit numeric tokens remain parseable. This is synthetic defensive validation, not a demonstrated live-provider defect or official-close verification.

**Hosted CI independently inspected:**
- Two-provider/ABC workflow [41476174377](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41476174377): completed **SUCCESS**, runner log **66/66 tests passed**, including the new malformed-integer regression. Live vendor retrieval was **skipped**; no vendor API entitlement or actual closing-price coverage was established. The optional output artifact was not generated.
- EOD calendar/source-contract workflow [41476174337](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41476174337): completed **SUCCESS**, runner log **36/36 tests passed**.

## Cross-task source separation and retained evidence

The separate November 2 MORNING IEX discovery run `41469642987` and independent halt/optional Massive monitor run `41469643116` both completed successfully; their artifacts `13153818511` and `13154712094` were checked against GitHub metadata and remain unexpired. Neither substitutes for an independently authenticated official regular-session close or for the distinct Rug Proof morning source. Rug Proof's November 2 09:20 CST MORNING window was missed and explicitly documented fail-closed in `OBSIDIAN_RUG_PROOF_MISSED_MORNING_CHECKPOINT_2026_11_02.md`; do not create a retroactive anchor or count the IEX discovery as that source.

Rechecked GitHub artifact metadata for original Oct30 protected preclose `13006897253`, independent monitor `13010065001`, maturity replay `13018333034`, delayed SIP `13006191628`, Rug Proof intraday anchor `12995764777`, and After-Hours discovery `13008429628`: all are present and unexpired, with January 28, 2027 expiry dates. These were metadata checks only, **not** ZIP byte rehashes or durable off-platform backups.

The frozen 8,510-security preclose cohort and 34,040 original 0/+1/+2/+3 session slots were not reprocessed or relabeled. The 136-name watchlist, JDZG stale/halt investigation, baseline and untouched matched future-cohort requirements remain unchanged. Do not count same issuer/day twice.

## Open validation gate

**P0-1 remains BLOCKED.** No two genuinely independent provider organizations have supplied independently authenticated official completed regular-session and previous-session closes with complete exchange-calendar/source timestamp, source/parent ownership, security/issuer identity, corporate-action parity and third-source conflict provenance for the prospective cohort. All missing outcome rows remain censored; no verified 20%+ prediction success, false-positive rate, precision/recall, SMG shortability, or profit is established. Vendor parser tests cannot discharge those external source obligations. Durable backup/restore remains unverified.
