# OBSIDIAN iteration 028 — authenticated artifact/source inventory (2026-11-22)

RESEARCH_ONLY. Authorized branch: research/obsidian-early-rug-20261025. No SMG login, account data, order operations, production changes, baseline edits, or automatic promotion.

## Verified this iteration
- GitHub Actions run 37386241124 artifact 11378995592, name pre-close-firm-37386241124: GitHub API reports expired=false, 11,294,854 bytes, created 2026-10-05T23:04:09Z, expiry 2027-01-03T23:03:15Z, digest sha256:a53ffdb85d7d373912a3483d6894c4e841ce0c54a42c77987f3f121aa7f20e6e. This is **API metadata**, not a new downloaded-byte checksum verification or new execution. Previous iteration reported byte verification; this iteration does not repeat that claim.
- Original backtest/target_rank_research.py Git blob e574c908eeb5fafbf918200296b01eeaf8dafbdd; fetched source, no modification. Direct imports: smg.intraday_replay, smg.models, smg.risk_model, smg.swing_backtest, backtest.confirmation_comparison, numpy. Source reads five artifact files in outputs/backtest/hybrid-37386241124 and emits results to outputs/backtest/target-rank-2026-10-05.
- Reference report blobs: backtest/FAST_DUMP_RANK_RESULTS.md 617d7606b11b92e0ccc87bfc70f44eb7544102d6; backtest/FIRM_TIMING_VALIDATION.md 88ed3dc7fc6cb0c539fa1dfaeab11f6b97f9e178. Protocol 45d49fb811827d5d614d05b30d7fac8a7bd5d771; playbook c3b0873774cab2afc352d542d98db5e6565af032; proof gate 7c232327e5d6fd4d1b1b4532a624a0f3f34dbb79; diagnostic negative control 9a9ba45a4485bed1d924e99d50c5a905b04e71de. All fetched from authorized branch.
- Artifact was generated on main at head b8fbd035543611f49992d6df3b619af7a6ddf548. This provenance differs from current research-branch ranker blob and requires explicit source/version compatibility review; never silently call artifact producer and ranker identical.

## Actual computation and limits
No baseline execution or newly computed P&L in iteration 028. Synthetic capital specification $100,000, Aug 1–Dec 31 2025 target, but archive reference ranker evaluates Sep 8–Dec 5 and 2023/24/25 are already inspected, not fresh holdouts. The original 54 configurations are **expected**, not reproduced here. Exact historical SMG eligibility/shortability, full-universe denominator, Aug and late-Dec signals and official closes remain unresolved. Original ranker must be reproduced before challengers.

## Bounded repair completed
This append-only inventory persists artifact ID, expiry, digest, source blobs, dependency list and source-version mismatch in the authorized research branch, so future iterations can resume assembly without rediscovering identifiers.

## Next registered action, not yet executed
In isolated scratch workspace, download artifact 11378995592; SHA256-verify ZIP bytes against the digest; inventory its members and date coverage; extract to outputs/backtest/hybrid-37386241124; fetch unmodified ranker and recursively required imports at pinned research-branch commit; hash inputs and source before running python -m backtest.target_rank_research. Compare all 54 outputs (including stress, positions) against original report. Do not tune challenger until reproduction succeeds. If artifact cannot be transferred to execution environment, log exact transport error rather than report a run.

Promotion: UNVALIDATED. No newly fresh windows, no admissible performance proof.
