# OBSIDIAN autonomous research engineering — November 1, 2026, 09:48 CST

**RESEARCH_ONLY_NOT_AN_ORDER.** Sunday is not a U.S. cash-equity trading day. No IEX, protected preclose, Morning Movers, After-Hours, Early Decision Board, Rug Proof, delayed SIP or independent-monitor marker/capture was created, retried or backfilled. No trading, credential, main or production change.

## P1-5 material milestone — actual ZIP bytes independently restored and rehashed

Unlike earlier metadata-only audits, this checkpoint **downloaded the actual original bytes of all seven pinned October 30 GitHub Actions ZIP artifacts**. All **7/7 original ZIP SHA256 hashes matched** their frozen receipts; all seven ZIPs passed CRC and exact member checks. Original inner payload hashes, status denominators and cross-artifact source links matched. The ZIPs were restored only into a **temporary working environment**: this is **NOT** a verified durable off-platform backup, and raw market data was not committed to public GitHub.

| Role | Run | Artifact | Rehashed original ZIP SHA256 |
|---|---:|---:|---|
| Protected preclose IEX | 41118123273 | 13006897253 | ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4 |
| Maturity ledger | 41140665058 | 13018333034 | 956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc |
| Rug Proof morning IEX | 41071432540 | 12985950392 | 4baaa22217c1cdf157fc102e1aaed3238513bb94ba2c61ff3d1c72a590f18eb1 |
| Rug Proof intraday IEX | 41097562159 | 12995764777 | f04e948242abbc6c6f87e36149bdd327bca3b3dadb2032be685696df95a43a96 |
| Rug Proof historical delayed SIP | 41114832467 | 13006191628 | 059ae485699813b940a18a3d124cd7e26ec9a817c179ce52d487b05c8c4d00b6 |
| After-hours IEX | 41122875045 | 13008429628 | a305c830924abda6da875efaa918db6d34730298dda7394d7033df3735a8eead |
| Independent halt/optional Massive | 41122875006 | 13010065001 | f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359 |

Refreshed GitHub run-artifact metadata: all seven are present on the authorized research branch, matching the rehashed digests, with expired=false. All expire January 28, 2027 (earliest 14:25:11Z). Retention metadata does not prove durable backup.

**Restored inner-file evidence:** protected preclose, morning, intraday, delayed SIP and after-hours raw files each contain **8,510 rows with 8,510 unique symbols**, and every original status partition sums to 8,510. The protected preclose universe inner SHA256 is 169f3c51659cc43ab3385b1b88c6730ee2559eaa6602f7bdf23bde67bc8eaaf3. Morning/intraday/after-hours attention and universe hashes match their original manifests. Delayed SIP rescue hash matches, and its original intraday manifest/universe source links match. Maturity ledger SHA256 is acae4f164adc9ff35518258b3992bd8bc935dfc8e743846c986762d9f7089925; its source ZIP/universe hashes match the protected preclose artifact. Maturity ledger retains **8,510 unique issuers × four 0/+1/+2/+3 slots = 34,040**, including **1,653 original price-only watch / 6,857 nonwatch**. The independent monitor retains **136 unique original symbols and zero independently connected Massive quotes**.

At original October 30 capture time, h0 was **8,510 CENSORED_MISSING**, and each future +1/+2/+3 horizon was **8,510 NOT_YET_MATURE**. These frozen classifications are not retrospectively rewritten or scored as current-day predictions. No issuer/day is counted twice.

## Reproducible isolated research code and hosted CI

Added offline read-only ZIP integrity verifier (backtest/obsidian_pinned_zip_restore_audit.py), tests (tests/test_obsidian_pinned_zip_restore_audit.py) and dedicated offline research-only workflow. It checks original ZIP SHA256, CRC, exact members, duplicate/missing issuers, inner payload hashes, fixed denominators and source links; it fails closed and never accesses market data, credentials or orders. Local offline fixtures **3/3 passed**; complete seven-original-ZIP restore audit also passed locally. Implementation [2e8a577](https://github.com/Dirtyhandgernades/Dudebot/commit/2e8a5775ecd9c9567555ef787dbf07bff4ba6f52). Hosted [Actions run 41323119811](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/41323119811) **SUCCESS**, including the offline regression step. CI uses synthetic fixtures; original ZIP rehash was separately performed in the temporary checkpoint environment.

## Unchanged blockers and next dependency

**P0-1 remains blocked:** zero independently authenticated completed official regular-session closes from two genuinely independent underlying provider organizations. Original exchange event timestamps, prior official closes, issuer/security class, corporate-action parity, actual sessions and complete third-source conflicts remain unverified. Massive key/real-time entitlement and actual SMG blocked-security/account permissions remain unverified. Alpaca borrow is not SMG approval. Missing outcomes remain censored; no verified 20%+ prospective prediction accuracy, false-positive rate, SMG short, fill, share count, cost-adjusted profit or trading edge.

**P1-5 split status:** seven pinned original ZIP-byte restorations **VERIFIED**; durable off-platform storage/restore **BACKUP_UNVERIFIED**. Original 136-name watchlist, JDZG stale/halt/$3-floor investigation, frozen baseline and protected checkpoint gates unchanged. Separate Rug Proof ownership preserved. Next priority: independently authenticated official-close sources and separately approved durable raw ZIP storage with verified restore before January 28, 2027.
