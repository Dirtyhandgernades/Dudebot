# November 24 execution gap and guarded controller

Status: implemented queue consumer, installed privately, DISARMED. This is not
an operational autonomous trading system or an execution-owner cutover.

## What happened during the session

The existing research dispatcher ran at 14:20 Central. Run
[45479748319](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/45479748319)
produced its source packet at 20:20:51.236168 UTC. Original local intake was
20:21:22.349903 UTC and vault delivery was 20:21:22.602826 UTC, within the
scheduled intake deadline. The 139-name research board had 139 BLOCKED rows and
zero recommendations. All rows still required counterevidence review,
independent market confirmation, security/corporate-action identity, and
source-dated mechanism review. Those are incomplete qualification stages;
this does not establish that the market offered no opportunities.

There is no verified completed decision-to-order handoff or order submission
from this workflow. The restored vault and delivery hook did not themselves
manage positions. Existing desk scheduling/consumption has not been demonstrated
by a current desk decision receipt. No after-close catch-up order was placed.

## New implementation

`smg/execution_controller.py` binds an exact decision to its account snapshot,
approved standing-policy hash, source evidence, quantities, estimated notional,
short-lived preparation, session deadline and execution authority. It reuses
the existing journal's atomic account/ticker locks. It supports short opening
assessment and stock/ETF SELL or COVER reductions; funds and bonds are not
routed through the stock form. New long entries remain unconnected. The
controller does not promote a strategy or invent exit thresholds.

`smg/tinyfish_execution.py` uses the installed authenticated CLI, the existing
selected profile and a scoped vault reference. It never retrieves a password or
API key into prompts. Every request identity is saved before dispatch. A
timeout is uncertain and is not retried. CLI run IDs belong to the personal CLI
namespace, separate from MCP runs. The adapter includes preview, account-read,
one-attempt submission and read-only reconciliation operations.

Pending is not a fill. Whole-fill confirmation requires an explicit executed
note, positive executed price and the exact previously bound confirmation
reference. A matching old executed note cannot confirm an unbound new attempt.
Ambiguity and unexpected partial fills retain their position locks.

`smg/execution_service.py` is a runnable private queue consumer. It consumes
explicit approved decisions; it does not autonomously produce the research
decisions or standing management policy. An empty wallet blocks browser work;
missing activation evidence prevents submission. Repeated cycles do not retry
claimed intents, and an uncertain attempt is not reported as zero submitted
orders. Its management inventory preserves the original account observation
time rather than making an old snapshot look current.

The separate Windows provisioner installs a pinned private runtime and the
exclusion list, preserving private authority/configuration. It does not register
a scheduler, activate the service, or replace the existing Portfolio Desk.
The installed disarmed cycle returned ACTIVATION_BLOCKED with no browser work.

## Actual browser verification and remaining work

A real supported non-submitting closing-ticket Preview succeeded during the
session. It showed a separate Confirm Trade control and official password
re-entry. No confirmation password was entered and no order was submitted.
The browser agent did not verify clearing the test fields afterward; cleanup
is explicitly still pending. Actual password-backed confirmation, accepted
submission and subsequent reconciliation have not been verified.

The last verified TinyFish wallet balance was exhausted and auto-reload was
unconfigured. No reload or paid purchase was made. Further browser checks need
funded access. The user's earlier execution brief also requires verified
platform/local-competition permission and a verified sole-owner cutover.
Neither is inferred from general account access or silence in public rules.
No approved standing sell/cover policy for the current holdings was recovered.
Those questions remain pending. Current account reads must be refreshed before
any real decision; saved morning reads are stale for execution.

Full raw account, preview and authority records remain private. No credentials,
holdings, balances, account identifiers or TinyFish session/run IDs are included
in this public record. No production alerts, frozen strategy or actual orders
were changed.

Validation: 51 focused controller/adapter/service and existing order tests
passed. The complete offline suite passed 1,384 tests and 326 subtests; two
warnings come from intentional duplicate-ZIP rejection fixtures.
Hosted prospective and controller/account tests passed on commit `15a1ce9`:
[run 45513281218](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/45513281218).
