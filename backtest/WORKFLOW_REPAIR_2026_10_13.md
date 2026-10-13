# October 13 intermittent state upload timeouts

Most quarter-hour scans recovered after the October 12 compression repair, but
two inspected scans still failed: 38431336767 (11:32 Chicago) and 38457550051
(14:46 Chicago). The first failed ranked preparation and archive; the second
failed archive and enrichment. Both reported an unclassified `TimeoutExpired`,
followed by a guarded `STATE_SHA_CONFLICT`. Later scheduled scans succeeded.
These are intermittent persistence failures, not Gmail failures or rate limits.
The old logs do not identify which Git subprocess exceeded its deadline.

Git read and write timeouts now have redacted, distinct error classifications.
A failed checkpoint is latched so a finally block cannot repeat an uncertain
write. When a push acknowledgement fails, one read-only reconciliation accepts
only the exact desired remote blob. Original or another writer's content remains
a failure; no second push, force push or replayed Discord send occurs. Git delta
packing is disabled for the compressed snapshots, avoiding expensive comparisons
of gzip data without increasing the network timeout. Unused index files are
removed on success and failure.

All actual October 13 v5 definitions are archived exactly. Prospective October 14
v6 contracts describe the transport change. Weights, sizing, hard exclusions,
borrow and market-data requirements, entry windows and three-session holds are
unchanged. Older observations retain their actual contract fingerprints.

Local verification: 383 tests passed. New cases cover a lost push acknowledgement
with exact, old, different and unavailable remote state, no repeated mutation,
no leaking subprocess output, preserved claims and read-timeout classification.
Hosted verification will be recorded separately after the repair is pushed.

At the inspected 14:33 Chicago scan (38455650510), the ranked lane evaluated
97 candidates: 32 outside its prior-price scope, 57 without a usable current
price window, and eight without a qualifying setup or rank. The older shortlist
also retained 17 current-borrow rejections. These are explicit eligibility/data
gaps; neither compression nor timeout recovery establishes profitable entries
or justifies treating unknown prices or unavailable borrow as executable.
