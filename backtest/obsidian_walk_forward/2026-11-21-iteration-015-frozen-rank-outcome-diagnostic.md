# Iteration 015 — Frozen rank outcome diagnostic
Research only; no order, production, baseline or protected file change.
Inputs mounted in current session: original ZIP artifact 11378995592 SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e and hosted lab ZIP artifact 14691551088 SHA256 95f916cdc1d988f752a49f14c38852c1f9876c5ddfd535bb915c19f840ea1ba1, both verified locally. Applied original risk_model.py feature_row formula and frozen model weights/training-year quantile thresholds to all 145 archived hybrid signal rows, 22 prior cached bars only. All 83 archived selected ranks matched to floating-point tolerance (max error 1.11e-16); no scores missing, no duplicate ticker/date. This is a newly executed Python diagnostic, not re-training or full portfolio simulation. For each archived same-session hybrid signal, compute gross short return at third subsequent cached close from signal-date adjusted close; target/adverse event if any of next three closes declines/rises >=20%; require all 3 sessions within Sep8-Dec5 replay window, exclude incomplete horizons. No inference of official price/actual fills, no intra-day stops, fees or capital weighting. Yearly outcomes already inspected; overlapping events correlated.
|Year|Threshold (nested)|N eval/total|Mean gross 3d|20% hits|20% adverse|
|---|---|---|---|---|---|
|2023|All|6/7|15.24%|2|1|
|2023|Below median|4/4|4.55%|1|1|
|2023|Above median|2/3|36.61%|1|0|
|2023|Upper quartile|1/1|11.31%|0|0|
|2024|All|46/48|5.27%|7|6|
|2024|Below median|18/20|-6.71%|0|3|
|2024|Above median|28/28|12.97%|7|3|
|2024|Upper quartile|20/20|17.89%|7|3|
|2024|Top decile|6/6|37.91%|4|2|
|2025|All|87/90|6.29%|12|4|
|2025|Below median|36/38|2.83%|3|1|
|2025|Above median|51/52|8.73%|9|3|
|2025|Upper quartile|34/34|11.02%|8|2|
|2025|Top decile|10/10|13.18%|2|0|
Target AUC 2023 .625 (6), 2024 .9121 (46), 2025 .6100 (87). Upper quartile 2025 worst 3d gross short return -36.82%; 2024 top decile 2/6 adverse >=20% even though eventual return positive. Stronger historical ranks improve mean gross return in 2024 and 2025; not monotonically in tiny 2023. Thresholds from earlier training only, NOT sample quantiles of evaluated hybrid rows. Never relabel as calibrated probabilities. 139/145 evaluable total, 6 censored; differs from previous audit definitions due to strict within-season horizon and same-session close reference. No new portfolio P&L. Local script rank_audit.py, signal_ledger.csv, rank_summary.json in conversation's research folder.
Next: prioritize actual unmodified reproduction and source transfer, not another archive integrity check. Register separate continuation/catalyst challenger only on actual available predecision evidence and fresh outcomes; compare ranking's 20% target to net risk-adjusted expectancy (include adverse excursion, fees, and opportunity cost). Do not loosen eligibility, automatically pick highest return from inspected bins, or promote top-decile due to small N. Preserve existing baseline.