# Combined three-year replay report

Evidence: GitHub run 35415517622, commit 4474adb, artifact 10575693002.
Artifact SHA-256: 1b7d64e576731c862c1412e6278e6f4aec7d727afefb1771ead7f224002bd2cc.
Replay period: July 29, 2022 through July 28, 2025.

Holdout integrity: all 230 message rows exactly match reference_events.csv.

## Results

- Fully verified strict detections: 0.
- Strict matches blocked only by historical halt verification: 0.
- Conditional firm-first matches: 41.
- Strict transaction candidates: 274; evaluated decisions: 73345/73345.
- Firm-first candidates increased from 788 to 961 after identity parsing fixes.
- Firm-first reference coverage changed by one event: WETH moved from uncovered to sampled without a firm/price match.
- Verified strict misses and a full-universe detection rate remain undefined while universe coverage is incomplete.

Conditional firm-first matches are research evidence, not executable alerts. User-supplied drop percentages are holdout labels, not independently reconstructed returns.

## Joint outcome counts

| Firm-first result | Strict result | Events |
|---|---|---:|
| CONDITIONAL_FIRM_AND_PRICE_MATCH | NOT_EVALUABLE | 41 |
| NOT_COVERED_BY_THIS_BATCH | NOT_EVALUABLE | 159 |
| SAMPLED_WITHOUT_FIRM_PRICE_MATCH | NOT_EVALUABLE | 30 |

## Material data gaps

- Independent firm corpus only; exhibit-only leads and sources beyond runtime budget remain gaps
- No historical cap/halts or complete source-context certification
- Raw historical prices used for the $3 gate; no split-adjusted future price leakage
- Conditional firm-price matches are not eligible alerts
- Original production strict rules evaluated on independently extracted dated transaction records.
- Incomplete provenance: not a certified replay_packet run. Missing context, mapping, cap, halts and corporate actions.
- Sampled price only; monthly return and relative volume not computed. No executable-profit claim.

The per-event machine-readable comparison is combined_event_comparison.csv.

The parser recovered 173 additional candidate records, but the conditional reference-match count stayed at 41. The largest strict-rule blockers were ambiguous terms, expired direct-offering windows, unknown operations, unknown issuer classification, and missing offer price or gross proceeds. This result does not meet the benchmark of catching most reference examples.
