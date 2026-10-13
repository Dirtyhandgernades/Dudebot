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

## Verified recovery and completed candidate review

On `a7328c3`, [full scan 38325434353](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38325434353),
[daily learning 38325434130](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38325434130),
[preflight 38325436059](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38325436059)
and [CI 38325434400](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38325434400)
all completed successfully. All scan checkpoint stages passed. CI verified 378
Python and 25 Cloudflare checks. Preflight verified five completed free SIP bars
with the sixteen-minute delay. Its market window was closed and it sent no trade.
The observed persisted compressed blob was 5,749,586 bytes. No historical row or
uncertain claim was deleted. The exact old validation rejection body remains
unavailable; successful guarded transfer verifies recovery from the save failure.

The nightly review refreshed closing prices and reviewed the actual old
`ranked-firm-2026-10-07-v7` observations: twenty October 7 candidate windows are
complete, with no invalid forecasts. All twenty have `paper_eligible=false`.
CD and MSGY reached a twenty-percent lower close within the following three
sessions. CD's earliest recorded evaluation lacked an exhaustion setup; MSGY
was below the trained rank threshold. These are tracked-candidate declines,
not two delivered qualified trade detections or certified executable misses.
No qualified paper trading profit is demonstrated. The diagnostic labels assume
an October 7 closing entry, fixed $25k research notional, $5 each order, 30 bps
each side, 10% assumed annual borrow and delayed closing stop/target execution;
they are not an executed portfolio or the user's holdings.

Nineteen October 8 candidate windows still lack the October 13 third closing
session. The verified CD research watch was sent October 8, so its own complete
three-session result remains pending. The local follow-up remains active for
that outcome rather than declaring it complete prematurely.

Daily status is a newly frozen challenger under the transport context, active
model null and zero newly matured qualified training outcomes. There was no
model promotion, allocation increase or new stock Discord message in this
closed-market recovery check. Full verification and per-candidate diagnostics
are in `WORKFLOW_VERIFICATION_2026_10_12.json`. Missing October 12 intraday records
and unverified historical borrow/cap/halt/game eligibility remain unknown.
