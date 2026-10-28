# OBSIDIAN P1-5 — GitHub artifact expiry and immutable evidence digest ledger (2026-10-28, 18:25 CT)

**RESEARCH_ONLY_NOT_AN_ORDER.** Scope: `Dirtyhandgernades/Dudebot`, branch `research/obsidian-early-rug-20261025`. This is a metadata/retention inventory, **NOT a long-term backup** or outcome-scoring report. All times below UTC. Capture phase is from the original manifest; for prospective preclose artifacts the phase is a capture-path label, not a fabricated manifest `phase` field.

## Independently verified current artifacts

At this checkpoint, downloaded the original eight ZIPs through the connected GitHub Actions artifact API, inspected each original `manifest.json` and all `universe.jsonl` lines, recomputed each raw universe SHA-256, compared it with its manifest, and recomputed each ZIP SHA-256 against GitHub's `digest:sha256`. All **8/8 ZIP digests and 8/8 original universe hashes matched**. For discovery ZIPs containing `attention.json`, its hash also matched the manifest. All eight artifacts were reported `expired=false` by GitHub's artifact API.

| Session | Original phase | Run ID | Artifact ID | Original capture finished UTC | Original full rows | SHA-256 original `universe.jsonl` | SHA-256 ZIP (matches GitHub digest) | GitHub expiry UTC |
| --- | --- | ---: | ---: | --- | ---: | --- | --- | --- |
| 2026-10-27 | MORNING (earlier capture) | [40516085542](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40516085542) | 12739492221 | 2026-10-27T13:53:44Z | 8,512 | `41790c82ede53cd03a568caa52fc904c3cea5f35cf442f23910b3f3c3486a997` | `89dce4db14a4a9b9632fb510b53312f0a60f782b0cdb121fb8e11c5e7950b75a` | 2027-01-25T13:53:33Z |
| 2026-10-27 | MORNING (later capture) | [40516649174](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40516649174) | 12740246208 | 2026-10-27T13:57:41Z | 8,501 | `dad0e857f13fba07089f1b5cb0792eedbd5d58db87f55c3f8905aa59da7fef8f` | `de887e0fdd1fb9591fbfe332b889c76049242891bfd4bd60825d41bf2e29319f` | 2027-01-25T13:57:25Z |
| 2026-10-27 | INTRADAY | [40553266211](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40553266211) | 12755323519 | 2026-10-27T17:43:40Z | 8,515 | `3b27abd9c50bc6ea9e1d17a1a8b4b66727bd2d8531b3f9ad8ae03f111b9b1eb3` | `76dbf6e2354254f7a1135a6f7add0f52b07b9cac5ff19e237c283b313f417cee` | 2027-01-25T17:43:30Z |
| 2026-10-27 | PRECLOSE | [40572768800](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40572768800) | 12766795149 | 2026-10-27T19:51:04Z | 8,515 | `10a3d8f30726759105394dac6eeaf6bccc208932d43e1faa51507809aa8c0bb4` | `9824ad5acd5a42c6a467d319927bbf235a734300507add488532d241691c1296` | 2027-01-25T19:50:54Z |
| 2026-10-28 | MORNING | [40704289113](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40704289113) | 12822044262 | 2026-10-28T14:16:34Z | 8,511 | `9736143a7a416063959e4d3aa1acd46ee8c8896d09e9f555159ce6c11a785880` | `581de21834482d82a2ee8e91f8077c7497141e94e5b9deec16f7d8727cde6110` | 2027-01-26T14:16:19Z |
| 2026-10-28 | INTRADAY | [40739809362](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40739809362) | 12837584509 | 2026-10-28T17:52:36Z | 8,511 | `1ca1cf79c79c8a18a7913b088dbefba655e9226b3d07f7582e48eb0fee90db9b` | `07e6d370e0a52b2c887c21f46d41273f0ea50fefbefd47dce53abf5571085801` | 2027-01-26T17:52:24Z |
| 2026-10-28 | PRECLOSE | [40757495722](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40757495722) | 12846452112 | 2026-10-28T19:48:06Z | 8,511 | `c3c61d3621bf50442acc319cd8f7081914f80393ef485f3b6a8aa65e645ba116` | `a4ea5404f4855431b1a3b7348d55627d21079f8ff8b41ab86a1a341edd6525d7` | 2027-01-26T19:47:50Z |
| 2026-10-28 | AFTERHOURS | [40763211800](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40763211800) | 12849591039 | 2026-10-28T20:26:09Z | 8,511 | `9d469faf2b6e43c8a8c5edec0eb65a4ea562261174faca8aaf0f0e6728802ebb` | `9d416ea494693baf91c5a766049c9d43621fd9ec8b99e707a29b836660833da2` | 2027-01-26T20:25:53Z |

## Retention status, non-independence and action gate

- **BACKUP_UNVERIFIED for all eight original ZIPs.** The temporary copies downloaded for this audit are not a verified durable off-platform archive. No user authorization, approved long-term destination, retention/access policy, or successful restore test has been established. **Do not** publish raw full-universe ZIPs to a public GitHub repository or upload them to unapproved storage. No archive/upload was performed.
- Earliest recorded expiry: **2027-01-25 13:53:33 UTC**, for October 27's first morning capture. Latest recorded expiry: **2027-01-26 20:25:53 UTC**. These are current GitHub API expiry timestamps, not guaranteed extension or storage promises. Recheck them before archive planning.
- October 27 has **two separate real morning ZIPs**, captured four minutes apart with **8,512** and **8,501** original rows. Preserve both hashes and run IDs; do **not** count same issuer/day as two independent predictions. Preserve Oct27 8,515 versus Oct28 8,511 denominators; do not normalize or silently drop stale/unscreened rows.
- October 28 authenticated AFTERHOURS capture has **8,375/8,511 stale/future IEX prints (98.40%)**; the source is single venue, not SIP, official prior close, official 16:00 ET close, verified SMG borrow, or executable fill.
- GitHub's ZIP digest authenticates the retrieved archive's byte identity against the artifact service; it **does not** independently authenticate external exchange closes, corporate actions, or outcome claims.
- P1-5 next gate: explicitly approved durable repository/bucket with retention and access control, independently verified copy SHA, and restoration test. Until then retain **BACKUP_UNVERIFIED**; the ledger is only a preservation index.

Frozen policies, original capture files, production, `main`, credentials, live alerts and orders remain untouched.
