# OBSIDIAN iteration 066 — pinned original checkout bootstrap (2026-11-23)

RESEARCH ONLY. Continuation of iteration 065; no SMG, vault, orders, production, main, protected baseline, Portfolio Desk or automation changes.

Read the registered continuous protocol (blob 45d49fb811827d5d614d05b30d7fac8a7bd5d771), FAST_DUMP_RANK_RESULTS (617d7606b11b92e0ccc87bfc70f44eb7544102d6), FIRM_TIMING_VALIDATION (88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178), trade discovery playbook (c3b0873774cab2afc352d542d98db5e6565af032), prospective proof gate (7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79), cycles 1–2 negative control (9a9ba45a4485bed1d924e99d50c5a905b04e71de), and iteration 065 (3e4e69bc81c740f3ad4b074b4fe5f266c23b00a2). Original ranker blob e574c908eeb5fafbf918200296b01eeaf8dafbdd.

Environment check: /mnt/data contains no original ZIP or pinned checkout in this run. Prior staging paths are not durable across execution environments. Therefore no authentic data was locally available for a new replay; no 54-case reproduction, net P&L or ending equity computed.

**One concrete repair:** created `backtest/obsidian_walk_forward/bootstrap_pinned_original_checkout_2026_11_23.sh` (commit 5b9a454ec7138d0409a2318ebbf2a24f231e23ea). It clones only the authorized research branch into a nonexisting isolated directory, checks out pinned iteration-065 commit 09e985643380e564f71ef31b70983bc264f3941c, verifies unchanged ranker Git blob, checks artifact SHA256 a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e, ZIP CRC and five input member names. It refuses existing destinations and does not execute ranker or touch protected data. This script was **not executed**: GitHub shell network access and original ZIP are unavailable in this runtime. It is a bootstrap recipe, not proof of successful reproduction.

Reproduction preflight in a permitted networked isolated environment:
```bash
bash backtest/obsidian_walk_forward/bootstrap_pinned_original_checkout_2026_11_23.sh /tmp/obsidian-original-pinned /path/to/verified-artifact-11378995592.zip
```
Then stage the five verified inputs at `outputs/backtest/hybrid-37386241124` under the isolated checkout; run `python -m backtest.target_rank_research` unchanged and reconcile 54 configurations, including normal/stress and positions, against the report. No rerun of the simplified diagnostic as baseline.

Historical 2025 archive coverage remains 89 packet sessions Aug 1–Dec 5; 63 hybrid-signal date keys Sep 8–Dec 4 (90 events), 26 packet sessions without keys; Dec 8–31 missing. This is previously inspected retrospective data, not a fresh holdout. Initial synthetic capital $100,000. No new net/ending equity, baseline/challenger metrics, or verified fills. No challenger hypothesis registered. Promotion UNVALIDATED.
