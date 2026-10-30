# OBSIDIAN prospective intraday IEX source anchor — 2026-10-30

RESEARCH_ONLY_NOT_AN_ORDER.

One new write-once 12:20 America/Chicago intraday checkpoint marker. This triggers only the independent, read-only IEX source workflow on the authorized research branch. The runner must independently verify actual America/Chicago time and the authenticated paper-broker `is_open` clock; failure must remain a failed source attempt, never a backfill. Preserve the full selected universe, source timestamps, raw observations, stale/missing/error denominators, artifact provenance, and venue coverage gaps. No trading, alerts, orders, official-close claims, or changes to frozen original evidence.
