# Iterations 016–018 | November 21, 2026

Development replay of September 8 through December 5 in each inspected year. Registration commit 609f693. Code commit f158347fb0225e0824a659d39ccb94e8e6cb9e07. Executed 24 full chronological portfolios. Six archived quartile-$30k benchmarks are included separately in the JSON. Each portfolio starts with $100,000. Entries, allocation and costs use the original simulator. The daily learning target assumes a fixed three-session hold. Actual simulations also apply the existing exit rules.

|Year|Selection|Net, base / stress|Closed trades, base / stress|Drawdown %, base / stress|Mean daily gross/equity, base|Worst closed loss, base|
|---|---|---:|---:|---:|---:|---:|
|2023|baseline|18,658 / 16,488|3 / 3|3.06 / 4.07|3.0%|-3,754|
|2023|adverse|18,658 / 16,488|3 / 3|3.06 / 4.07|3.0%|-3,754|
|2023|expectancy|30,194 / 25,960|5 / 5|3.06 / 4.07|5.8%|-4,118|
|2023|valuation|18,658 / 16,488|3 / 3|3.06 / 4.07|3.0%|-3,754|
|2024|baseline|39,125 / 25,305|16 / 16|25.69 / 29.49|21.1%|-30,147|
|2024|adverse|-10,946 / -17,040|10 / 10|26.15 / 29.65|13.6%|-19,347|
|2024|expectancy|9,870 / -4,935|21 / 21|22.26 / 28.24|27.5%|-24,978|
|2024|valuation|39,125 / 25,305|16 / 16|25.69 / 29.49|21.1%|-30,147|
|2025|baseline|103,259 / 64,021|36 / 37|19.97 / 25.17|40.7%|-7,646|
|2025|adverse|65,014 / 39,417|26 / 26|6.56 / 11.21|31.2%|-5,790|
|2025|expectancy|80,955 / 45,597|34 / 33|7.99 / 13.69|38.0%|-5,663|
|2025|valuation|103,259 / 64,021|36 / 37|19.97 / 25.17|40.7%|-7,646|

016 rejected. In 2024 the risk filter discarded profitable opportunities while increasing stressed drawdown. The 2025 drawdown improvement came with fewer trades and lower profit.

017 rejected. The expectancy gate improved 2023 and reduced 2025 drawdown. In 2024 it changed a positive stressed baseline to a loss. The training population differs from the hybrid cohort. Prior completed daily bars are the available inputs. Historical vendor adjustments lack independent vintage authentication. Scores are ordinal.

018 retained for valuation provenance only. Repairing 113 marks produced identical reported net profits, closed entries and quantities in all six comparisons. No historical performance improvement attributed to renames.

Acceptance: both challengers failed the 2024 positive stress and maximum 20% drawdown gates. Neither has 100 closed base trades, three untouched positive periods, authenticated historical eligibility or official outcome proof. The evidence supplies no replacement for the baseline. Per-year profit factors, insolvency, issuer concentration, monthly results, wins/losses and largest-winner removals are in metrics.json. Close-based excursions omit intraday extremes.

The actual GitHub cache inventory query for intraday-bars-v1-37386241124 returned zero visible records. The five-minute source remains unavailable from this cache. August and late December require a new source.

Resume from the repository root with the pinned virtual environment and original source and baseline paths specified in the operating guide. The command actually executed was:

    .venv/bin/python -m backtest.obsidian_adverse_expectancy --repair /workspace/obsidian-overhaul/valuation-repair-local/valuation-continuity-inputs.json.gz --out /workspace/obsidian-overhaul/iteration-018-results.json

For a replay choose an unused output filename. The repair file is also in hosted lab artifact 14691551088 under backtest/obsidian-continuity-44864565861/. Input and raw output hashes are in metrics.json.

Next registered hypothesis: among negative-prior-return names, a dated disclosure of actual discounted issuance and weak tape can distinguish continuation from recovery. First inventory historical issuer documents, decision-time mappings and contradictory disclosures for the unchanged denominator. The price packet alone cannot establish this mechanism. Preserve unknowns. Build short and long labels separately. Subsequent backlog includes earnings/guidance, IPO supply, clinical/regulatory outcomes, positive momentum and fundamental recoveries, then unused forward periods with authenticated closing outcomes.
