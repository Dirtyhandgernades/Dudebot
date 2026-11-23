# Durable retrieval failure observations

Added observe wrapper used by retrieval CLI. Each call writes distinct immutable observation with runID/intent/start/end/status, distinguishing WAITING_FOR_RUN, INTAKE_VERIFIED and RETRIEVAL_FAILED. Error type and validation reason retained; generic subprocess output/credentials not copied into observation. Atomic fsynced publication. Underlying exception still returns failure to monitor. Waiting/error observation never creates success receipt.

11retrieval tests passed including waiting/success/failure state records and no fabricated receipt. Refreshed installed versioned runtime via Provision; actual Python imports passed. No real new collection or platform action. Existing monitor cadence provides bounded per-call reads; an attempt's failed state retained even if a later read succeeds. Source freshness/deadline/decision review remain separate.

Next verify actual installed observation CLI on a safe read-only known nonmatching run to confirm failure record from real GitHub authentication without dispatch. Then inspect source collection and missing artifact termination at current head, retaining private data constraints. Full goal remains active.
