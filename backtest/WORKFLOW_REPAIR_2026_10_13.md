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
Hosted verification is recorded below.

At the inspected 14:33 Chicago scan (38455650510), the ranked lane evaluated
97 candidates: 32 outside its prior-price scope, 57 without a usable current
price window, and eight without a qualifying setup or rank. The older shortlist
also retained 17 current-borrow rejections. These are explicit eligibility/data
gaps; neither compression nor timeout recovery establishes profitable entries
or justifies treating unknown prices or unavailable borrow as executable.

## Verified recovery and completed first-watch outcome

On repair commit `625fb1e`, scan38467161860 and daily38467184995 completed
successfully. CI38467240754 on `85de83c` passed383Python/25Cloudflare tests.
The verified archive persisted142asset observations without provider failures;
it ran after the market closed and sent no stock trade. Future v6 ranked capture
correctly reported not active before October14. Source definitions are preserved.

Practice38467240544 used a distinct mention-free October13 test receipt and
confirmed `SENT` message1559672690099359887 at16:02Chicago. It is a practice
embed, not a qualified trade or order. The manually queued duplicate archive and
old-receipt practice were intentionally cancelled, not bot failures.

The October8 CD research watch, actually delivered at11:05Chicago, now has its
complete October9/12/13 closing-price window. Its assumed October8 closing entry
reached a20% lower close within three sessions. The prior-close target policy
would exit at the October12 close with33.54% conditional net return: $8385.45 on
the fixed $25k research notional after modeled costs. Assumptions remain $5 per
order,30bps each side and10% annual borrow. This watch was not qualified, had no
confirmed executed shares, and its hypothetical return is not account profit.

Old v7 review:20October7 and18October8 price outcomes observed, plus one October8
entry rejected because its raw closing price did not meet the rule. All39
observations were unqualified; only21mature nonoverlapping windows are counted.
CD and MSGY's earlier tracked declines did not become qualified entries. No
certified executable-miss percentage or live trading P&L is demonstrated.
Twenty new October13 v5 candidate outcomes are pending until October16; this is
not a provider failure. October12 missing intraday captures remain unknown.

Daily status remains `FROZEN_CHALLENGER_STAGED`, active model null, zero newly
matured qualified training outcomes and no orders or historical provider calls.
The transport-context fit does not constitute fresh live learning or promotion.
The consistent70kseason target remains unachieved. Full verification is saved in
`WORKFLOW_VERIFICATION_2026_10_13.json`. The completed first-watch local follow-up
can stop; hosted trading research and dispatch schedules continue independently.
