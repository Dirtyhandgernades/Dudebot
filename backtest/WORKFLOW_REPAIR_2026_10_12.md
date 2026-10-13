# October 12 state-transfer failure

The Cloudflare quarter-hour dispatcher launched scans, but the Contents API
state checkpoints started failing after the successful 13:32 UTC run
38256344361. Run 38258106254 at 13:46 UTC was the first inspected failure;
38319996184 at 23:02 UTC still failed. Both are on `b801226`.

Exact failed steps: ranked daily preparation, current market/borrow archive,
fundamental/sentiment enrichment and ranked send, each ending with GitHub HTTP
422. The normal alert step was skipped after preparation failed. Discovery and
broad-shortlist jobs also failed. These are state-save failures, not evidence
of zero opportunities, a Gmail issue or a rate-limit classification. The old
formatter did not retain the rejection body, so the exact GitHub validation
message is unavailable.

The immutable remote blob `4f2b5ad3b74c68cc1250d3f487f7d3b34015f338` is
42,094,592 bytes. Its checksum and SQLite signature were verified through a
pinned compressed archive; the transfer was 5,906,123 bytes. A separate large
raw API download failed with an incomplete read after 18,903,477 bytes. SQLite
has 10,277 pages of 4,096 bytes, with only one unused page: this is retained
data, not principally free-page waste. No logical rows are deleted.

The repaired backend persists large databases using tagged deterministic gzip,
while continuing to read legacy raw SQLite blobs. The legacy repository path
`runtime/state.sqlite` remains; repository bytes can now be gzip encoded.
The local working file is decoded SQLite. SHA checks verify the encoded remote
blob before decoding; the same-run memo separately verifies local decoded bytes.
Large logical databases use the existing authenticated compressed Git transport
before attempting a large Contents PUT. Writes retain the original expected
SHA and ordinary fast-forward push; no force push, different credential or
blind retry is introduced. Unused SQLite pages can be reclaimed losslessly when
waste is substantial. Existing forecasts, observations and uncertain claims
are retained, and ambiguous Discord sends remain non-retryable.

HTTP 422 is now labelled `API_VALIDATION_REJECTED`, not a rate limit, and is not
automatically replayed. This transport change addresses the observed large
transfer failure without claiming to know the exact unavailable rejection body.

All October 12 v4 definitions are archived exactly. Prospective transport
contracts `ranked-firm-2026-10-13-v5`, `firm-shadow-2026-10-13-v5` and the
research-only `entry-quality-2026-10-13-v5` start October 13. October 7–9 and
October 12 records remain under their actual contracts. No weights, eligibility,
position sizing, entry window, outcome calculation or three-session horizon
changes. The nightly workflow additionally publishes the existing read-only
archived-contract outcome review after refreshing prices; this makes missed or
unavailable outcomes visible without retuning the strategy.

The pre-repair snapshot contains 39 ranked candidate observations, all with
`paper_eligible=false`, and zero adaptive base-qualified decisions. It contains
one verified ranked Discord watch: CD on October 8 at 11:05 Chicago, message
1557786002737729560. It is a watch, not a qualified short or an order. Its full
three-session window ends October 13. No lost October 12 intraday observations
or historical borrow flags are invented during repair.

Local verification: 378 Python tests passed, including compressed/legacy
restore, dual SHA memo, exact-content checks, conflicts preventing retries,
lossless compaction and HTTP422 classification. Hosted verification is recorded
below when complete; no restoration of live delivery is assumed from tests alone.
