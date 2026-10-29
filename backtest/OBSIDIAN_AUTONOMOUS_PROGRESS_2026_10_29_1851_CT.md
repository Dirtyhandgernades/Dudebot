# OBSIDIAN Central Engineering — 2026-10-29 18:51 CT

**RESEARCH_ONLY_NOT_AN_ORDER.** Isolated P0-1 source-contract shadow hardening only. No market capture, prospective marker, trading action, main/production modification, credential access, or frozen-policy change.

## Verified branch and ownership
- Started from research branch head `84005490d3c22a2244a4e82a57f3fc054fa76a89`, after checking the October 28 validation roadmap, current code, protected schedule, October 29 Rug Proof delayed-SIP verification, and existing after-hours independent-monitor marker. The separate Rug Proof run 40939489402 is an authenticated **delayed** SIP research observation, not a real-time quote or official close. No duplicate anchor or issuer/day prediction was created.
- October 29 original protected 14:47 CT IEX capture and separate after-hours monitoring had already been completed; neither was rerun or backfilled. Outside 12:47 and 14:45–14:58 CT authorized windows, no new capture marker was created.

## Isolated P0-1 correction
- Found that `backtest/obsidian_forward_source_contract_shadow.py::_decimal` accepted arbitrarily large finite Decimal exponents. During parent/source comparison, a malicious or malformed price could overflow Decimal subtraction and abort a whole shadow source audit. The primary EOD preflight had an exponent guard, but this separate shadow layer did not.
- Also found that a malformed `collected_at` caused the preflight to raise ValueError and interrupt the shadow evaluation rather than censoring the affected observation.
- Implementation commit [f824465f9ec2883fe8bf08cc5837940646dd3fa3](https://github.com/Dirtyhandgernades/Dudebot/commit/f824465f9ec2883fe8bf08cc5837940646dd3fa3) bounds untrusted shadow prices to a deliberately generous Decimal exponent envelope (-100..100), consistent with the existing primary preflight. This is **not** an SMG eligibility floor. Invalid collection timestamps now produce `SOURCE_PREFLIGHT_INVALID_COLLECTION_OR_INPUT` and a blocked source-contract result. The original supplied-report count is retained.
- Added three synthetic regressions for extreme top-level price, extreme source price, and invalid collection timestamp. Hosted [GitHub Actions run 40976042427](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40976042427), job `123804197995`, completed **success** on exactly that implementation SHA: **484 prospective offline tests + 4 ABC board tests passed**. The three new tests individually passed in the downloaded job log. No live vendor calls or official exchange close was authenticated.

## Remaining blockers and guardrails
- No independently authenticated two-organization official regular-session close evidence, no complete provider-conflict/source-ownership proof, no verified issuer identity or corporate-action adjustment parity, and no complete 0/+1/+2/+3 trading-session outcome set. Vendor agreement and delayed SIP bars cannot satisfy the frozen outcome gate.
- Frozen original 136-name cohort, JDZG stale/halt failure analysis, historical denominator/labels, and protected time gates are unchanged. Missing observations remain censored. **No verified prospective >=20% collapse prediction success established.** Durable raw evidence backup beyond Actions retention remains `BACKUP_UNVERIFIED`.
