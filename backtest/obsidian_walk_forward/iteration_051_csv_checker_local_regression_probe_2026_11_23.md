# OBSIDIAN iteration 051 — bounded CSV checker regression probe (2026-11-23)

RESEARCH ONLY. Branch: research/obsidian-early-rug-20261025. No SMG, account/vault, production, alerts, frozen baseline, main, or Portfolio Desk access.

## Inputs inspected
Read the continuous walk-forward protocol, FAST_DUMP_RANK_RESULTS, FIRM_TIMING_VALIDATION, trade-discovery playbook, prospective proof gate, diagnostic replay negative control, iteration 049 checker and iteration 050 test file through the GitHub connector. Source blob IDs: checker a9d1a268372a74b7fd1bd635f1fca4cb90ade9b9; tests afef41c30364aab8a3d51ea9164caf63ef2c70bb.

## Actual bounded computation
Direct raw.githubusercontent.com download from isolated container failed with curl exit 6 (DNS resolution failure). To make progress, manually reconstructed the relevant checker functions and four regression tests from the connector-read text into isolated local temporary files, then executed:

`python -m unittest discover -s . -p 'test_iteration_050_csv_integrity.py' -v`

Result: 4 tests ran in 0.075 seconds, all passed. Cases: null CSV serialization; 54 consistent synthetic configuration fixtures; mismatched shares rejected; missing trade CSV rejected. Temporary reconstructed local checker SHA256: 266e9f0cd8e9b5aa894d478fb9c3937632693712800ecbf971988702ae09f418; test SHA256: 2f9d045b8d890d8d6ee9fc2182cf25f0b5d0dc0cade8e6b030415998d408da24. These are NOT the GitHub original file bytes and this is NOT proof the exact checked-in tests passed. Synthetic fixtures contain no trading-performance evidence.

## Blockers / status
Exact source-byte execution and original-ranker reproduction remain pending. No original 54 outputs available locally; archived inputs and complete pinned checkout not co-located. No new baseline/challenger P&L or ending equity. Starting synthetic capital remains $100,000. Prior coverage: August hybrid signals absent, 17 December sessions absent; no genuinely fresh windows. Promotion UNVALIDATED.

## Next bounded step
Obtain byte-identical GitHub checker/test files into an isolated execution environment (verify hashes against connector blobs), execute the checked-in tests without reconstruction, then assemble the pinned unchanged ranker with SHA256-verified artifact 11378995592. No challenger registration before original reproduction.
