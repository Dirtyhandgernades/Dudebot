# November 24 session readiness

## Recovery and handoff repair

The original private vault was found in the Windows Recycle Bin and copied back
to its configured location. All 4,194 recovered files matched their original
SHA256 hashes before refreshes; the Recycle Bin source was preserved. Registry
and snapshot/link validation passed, and both SQLite databases passed integrity
checks. A fresh public GitHub source sync succeeded. Existing paper events,
historical closed lots and research rules were preserved. Current scoped account
reads were attached privately with their original observation windows; no fill
prices or complete-history audit were inferred.

The existing Windows monitor now has an optional configured desk-vault handoff.
It revalidates the exact artifact, original intake receipt, roster and source
clock, then preserves packet/board bytes and a separate first-delivery receipt
in the existing vault. A repeat does not refresh source/intake/delivery clocks;
an older artifact cannot replace a newer pointer. Corruption and missing vaults
fail visibly. No new schedule, executor, order permission or strategy is created.

The installed monitor was tested against real run 45420416729 in an isolated
manual probe, reusing the original verified archive and original intake receipt.
Delivery into the real restored vault passed at 15:35:05.162165 UTC. The morning
source remains 15:00:46.181375 UTC, not a fresh afternoon observation. Today's
production dispatch state was not marked accepted by the probe, preserving the
planned 14:20 Central collection. Existing Portfolio Desk ownership is unchanged.
Actual scheduled afternoon receipt and completed desk review remain unverified,
as do platform method permission and the Preview/Confirm/reconciliation path.

Validation: 45 focused Python tests passed, plus the Windows monitor's pending,
success, failure, surfaced desk-delivery failure and missed-deadline checks.
Provision and upgrade preserved the configured desk vault; installed monitor
and all four runtime modules matched source. The paper event count was unchanged.
Hosted prospective and account/intake checks also passed on commit `1ce5e26`:
[run 45427922806](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/45427922806).
Private source files, credentials, account identifiers and holdings stay outside
this repository. The observations below describe the earlier preflight state.

Live morning collection and local artifact intake passed. This is not an
unattended trading readiness approval. The research board has 139 BLOCKED rows
and zero recommendations; no strategy was promoted and no order was submitted.

Initial run [45419964542](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/45419964542)
completed, but the Nasdaq RSS response contained `GPMT-A`, which the source
symbol parser rejected. All 139 rows consequently retained halt-source failure.
The retained response SHA256 is
`9d3485d08609816ee0ce454641391f5c89fe55916d56d4d46c2a376be752656f`.

Commit `f4c308157cd8d0cc7ae976a909c677440934fbda` preserves this preferred-share
source identity without changing the trading-symbol allowlist or treating
missing halt rows as clearance. Replaying the retained response parsed 32 events.
Focused local validation passed 80 tests and 40 subtests. Hosted parser regression
[45420415176](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/45420415176)
also passed.

Repaired live run [45420416729](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/45420416729)
passed. Its board and source packet were downloaded through the installed
authenticated retrieval runtime and hash/identity/roster/clock checked. Source
time was 15:00:46.181375 UTC; actual local receipt was 15:01:09.187644 UTC,
23.006269 seconds later. All 139 rows have no halt parse error: 136 have no RSS
row (not proof open), and three require halt-event review. See `receipt.json`.
This morning receipt is not the scheduled afternoon desk review.

The existing Windows research task is enabled and executing; installed runner,
monitor, reconciliation, hidden launcher and session-map files match repository
sources. Today's planned dispatch is 14:20 Central, with a 14:35 intake deadline.
The machine must remain awake and signed in. No November 23 local dispatch state
or later hosted scheduled feed run was found. A successful off-window task exit
does not prove a scheduled collection occurred. Today's afternoon dispatch and
decision-consumer receipt are still unverified.

The configured private desk vault directory was absent at preflight. Its journal
and current execution-owner delivery cannot be certified from this checkout.
The order preparation/journal modules remain offline components, without a
platform submission adapter. Authenticated account access alone does not verify
Preview/Confirm, successful execution, or reconciliation after an ambiguous
submission. Existing Portfolio Desk ownership and automations remain unchanged.
Account-read results and credentials are deliberately excluded from this record.

Read-only browser validation: a broad summary contained contradictory holdings
counts and was quarantined. Narrow followups returned actual visible holdings
rows from both pages, pending-table evidence, and recent transaction-note rows.
Saved authentication and blank stock-form access worked. These reads do not
restore the missing journal, certify a complete history audit, or validate
automated submission. A later final-URL/form-state contradiction was also kept
as a limitation instead of accepting the summary's pass label. Detailed account
evidence is retained privately outside Git.
