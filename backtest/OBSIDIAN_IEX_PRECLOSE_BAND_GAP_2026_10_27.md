# OBSIDIAN 2026-10-27 16:47 CT — verified immutable preclose intermediate-band omission

**RESEARCH_ONLY_NOT_AN_ORDER.** This is a **deterministic classification coverage defect**, not a verified future 20% closing-price collapse, profitable short, or proof of predictive accuracy.

## Authenticated source, unmodified
- Original protected preclose run [40572768800](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40572768800), artifact **12766795149**, captured **14:51:01.669–14:51:04.119 CT**, 8,515 original rows.
- Independently downloaded the actual GitHub artifact and recomputed the raw `universe.jsonl` SHA-256: `10a3d8f30726759105394dac6eeaf6bccc208932d43e1faa51507809aa8c0bb4`, matching its manifest. Morning artifact 12740246208 and intraday artifact 12755323519 also independently match their own manifests.
- **Original preclose counts remain untouched:** 433 original early watches, 9 exhausted, 3,669 no-watch, 4,252 stale/future, 105 missing trade/reference, 44 unverified prior sessions, 3 missing snapshots.

## Reproducible defect
Frozen original `backtest/obsidian_iex_prospective.py::classify` labels IEX-reference price changes **-2% to -15%** as `IEX_EARLY_WEAKNESS_WATCH_ONLY`, and **<=-25%** as exhausted. It labels **strictly between -15% and -25%** as `IEX_NO_EARLY_PRICE_ONLY_WATCH` instead of intermediate. This is NOT a price-feed outage and NOT a ticker absent from the scanned universe. It is a code-path blind spot in the original protected preclose classifier. Do not change historical labels or frozen policy after seeing outcomes.

Offline re-evaluation of all 8,515 original preclose rows identifies **12** valid/fresh IEX prints in this intermediate band incorrectly labeled no-watch; **2** have both IEX prices >=$3 (a necessary but insufficient indicative SMG price gate): **FLXS** (-18.426% vs IEX prior) and **AZUL** (-15.423% vs IEX prior). The remaining 10 were below the $3 indicative price floor: ATYR, GME.WS, GUTS, LUCD, PBK, RCT, SXTP, TGE, WHLR, XTND. `GME.WS` is a warrant-like symbol and must not be assumed common stock.

### Independently reconciled earlier authentic observations
| Symbol | 08:57 CT morning | 12:43 CT intraday | 14:51 CT protected preclose |
|---|---|---|---|
| FLXS | Stale 08:40:55 CT IEX print, -14.70% vs IEX prior, unusable | **IEX_INDICATIVE_INTERMEDIATE_15_TO_25**, $67.51 / $82.63 = -18.30% | **Original NO WATCH**, $67.405 / $82.63 = -18.426%; fresh 14:50:11 CT IEX print |
| AZUL | IEX no-watch, $4.04 / $4.02 = +0.50% | **IEX_INDICATIVE_EARLY_2_TO_15**, $3.76 / $4.02 = -6.47% | **Original NO WATCH**, $3.40 / $4.02 = -15.423%; fresh 14:49:58 CT IEX print |

**Critical distinction:** FLXS and AZUL were not entirely unseen by OBSIDIAN: earlier intraday research had flagged both. But the protected preclose classifier dropped them from its watch list despite fresh 15%–25% weakness. Neither original preclose watch can be retroactively upgraded, and neither has an independently corroborated official 16:00 ET close outcome or complete SMG eligibility/borrow proof in this audit.

## Isolated engineering remedy
- New **read-only, offline** `backtest/obsidian_iex_preclose_band_gap_audit.py` replays the original protected capture with its original verifier, preserves its raw hash and all original status labels, and emits an explicitly separate `SHADOW_INTERMEDIATE_15_TO_25_LEGACY_NO_WATCH` research list.
- This is **shadow coverage** for future frozen-baseline-versus-challenger comparisons, **not** a reclassified baseline signal or new predictive performance claim. No original capture code, frozen policy, official-close scorer, production workflow, credentials or orders changed.
- New regression tests check the -15%/-25% band, no retroactive promotion, stale exclusions, tampering, missing snapshots, and preservation of the original capture.
- Future **untouched** prospective cohorts may independently pre-register and measure a shadow challenger with the intermediate band. The October 27 seen examples are development diagnostics, not unbiased test-set wins.

## Outcome blocker
Two independently timestamped and agreeing official previous/current 16:00 ET regular closes plus independently verified same-entitlement corporate-action reviews for original captured symbols are still missing. The 12 shadow cases are NOT verified >=20% closing collapses; early-hit rate, recall, precision, and after-cost P&L remain unknown. All 8,515 original symbols and missing/stale categories remain accounted for.
