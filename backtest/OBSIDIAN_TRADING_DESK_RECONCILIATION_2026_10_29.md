# Trading desk engineering reconciliation — 2026-10-29

Research only; no orders, production, secrets, frozen historical labels or source triggers changed.

## Verified repair

The shadow ABC intake previously allowed an A row from a mechanism flag, early-status flag and timestamps without requiring any weak-tape evidence. V2 now requires a separately timestamped, receipted weak-tape observation (failed rebound, support loss or selling volume). This permits partial early technical evidence without waiting for all breakdown confirmations. A mechanism alone remains blocked. Blocked rows explicitly retain their underlying category and full denominator. This changes a new shadow policy version, never past frozen outcomes.

The original ABC tests were outside the prospective CI discovery pattern. CI now explicitly watches the board and its tests and runs both original coverage/write-once tests and new prospective regressions. Local verification: 8 tests passed, including missing receipt, stale/future tape, unsupported social claims, and a valid partial-evidence early setup. Hosted CI must be checked separately; local success is not market validation.

## End-to-end completion gates (NOT completed)

1. Discovery: retrieve actual immutable candidate/rejection rows, not merely successful workflow status or summary counts. Existing ABC module is an intake, not a market scanner; writing this repair does not connect an automatic live board.
2. Enrichment: same-security SEC/issuer publication timestamps, supply stages and opposing evidence for each candidate. A financing registration or unlock is never a next-day prediction by itself.
3. Data: genuine prospective delayed-SIP collection has run, but delayed bars are not real-time NBBO. Optional independent Massive quotes were disconnected in run 40939694009. Do not claim real-time fixed or infer permissions from an HTTP success. Budget existing provider calls; do not alter secrets or retry protected captures.
4. Execution: reconcile actual SMG blocked symbols, short availability, current account exposure and permitted decision window. Broker borrow is not SMG permission. Never submit orders.
5. Prediction: immutable decision board, matched baseline/challenger and untouched matured 0/+1/+2/+3 outcomes with source receipts and costs. Validation has not established a profitable edge.
6. Backtesting: begin a new preregistered strategy evaluation only after data, identity, board and label gates pass. Preserve already inspected historical cases as diagnostics, not untouched validation.
7. Delivery: verify the actual 14:20 task artifact and delivery before the user's approximately 14:35 decision readiness. Report missing delivery, not an invented top three.

## Trading-desk attribution corrections

CBRS, RAPP and SPTX Oct28 recommendations were discretionary web/filing selections, not validated OBSIDIAN predictions. Supply-to-selling inference and timing quality require separate testing. User screenshot confirmed shorts CBRS 200, RAPP 1000, SPTX 750 on Oct29; do not assume covers or later holdings. JDZG must be reconciled against original observations, corporate actions, stale data, halts and contemporaneous eligibility; current sub-$3 quote does not prove historical eligibility or a missed executable win.

## Stop conditions / external blockers

Unknown independent real-time entitlement, unverified actual SMG access and future outcome maturation cannot be repaired by synthetic tests. No credential, vault destination or user authorization may be invented. Highest priority next deliverable is one genuinely sourced candidate board with all rejection rows and explicit missingness, followed by matured scoring. This note is not an assertion that the complete workflow or all bugs are fixed.
