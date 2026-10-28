# OBSIDIAN — October 28 authenticated original cohort replay (research only)

**Purpose:** replay original untouched October 28 2026 morning and intraday authenticated single-venue IEX artifacts through the already-tested `obsidian_matched_cohort_lock.py`. This is the first *actual-artifact* matched-cohort audit, not an outcome scorer. No new provider capture, trade, secret inspection, policy tuning, production or main modification is authorized.

- Morning GitHub run 40704289113, artifact 12822044262, original ZIP SHA256 `581de21834482d82a2ee8e91f8077c7497141e94e5b9deec16f7d8727cde6110`.
- Intraday GitHub run 40739809362, artifact 12837584509, original ZIP SHA256 `07e6d370e0a52b2c887c21f46d41273f0ea50fefbefd47dce53abf5571085801`.
- Both originally requested 8,511 securities. Original price-only watches: morning 264, intraday 342. No watch is a verified future >=20% official regular-close collapse, a consolidated quote, a confirmed SMG short or a trade.
- `.github/workflows/obsidian-oct28-matched-artifact-replay.yml` runs only when its own research-branch workflow file changes. It downloads *existing* immutable GitHub artifacts with the Actions read permission, verifies original archive SHA256, refuses unexpected/duplicate/unsafe ZIP entries, replays original internal hashes and timestamps, retains every unselected symbol, and writes a derived audit artifact.
- The audit counts same-ticker morning and intraday observations **once**, preserves source-comparability quarantine, and refuses to produce precision, recall, profitability or verified outcomes without independent external closing and corporate-action evidence.
- Its own derived artifact also expires after 90 days. **BACKUP_UNVERIFIED** until an independently approved durable raw archive exists; it does not alter the source captures.
- A green offline CI result alone is insufficient. Report this replay as successful **only after its actual hosted GitHub job, logs, artifact, source ZIP digests and denominator are verified**. Any failed download, hash mismatch, missing artifact or GitHub permission error is a blocker, not permission to reconstruct or backfill.
