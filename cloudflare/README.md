# Free hosted Discord delivery

Cloudflare now performs the near-noon market refresh and sends the Discord report.
GitHub continues SEC filing discovery and uploads the source-reviewed candidate
pool. No Discord bot user, paid feed, paid AI service or always-on PC is required.

The persistent hosted clock refreshes at 11:58 a.m. Pacific and dispatches at noon
Pacific / 2 p.m. Central on weekdays, following daylight-saving time. Each day it
schedules the next wake-up before attempting delivery. Late alarms beyond the noon
minute are suppressed; network/provider outages can still prevent delivery.

The hosted refresh fetches free Alpaca SIP bars with a 16-minute delay, current
Nasdaq/NYSE screener market caps, and the current halt feed. It uses at most 30
source-reviewed firm candidates. Source reviews older than 26 hours are withheld;
GitHub delays that also prevent filing-review refresh can therefore still limit
coverage. Current cap values have retrieval timestamps, but the vendor publishes
no individual valuation timestamp. Pump and relative-volume context are explicitly
unavailable in the small hosted refresh and remain preferences. The Python path
can still prepare richer reports for the same daily dispatcher.

Both paths preserve firm-first classification, Nasdaq/NYSE common equity, price
strictly above $3, market cap at least $25 million, the halt/SPAC/five-letter hard
exclusions, source freshness and market-data freshness. Cards show matched firms,
filing evidence, price, cap and the minimum 10-share cost before fees. They make no
orders. Unknown required checks never become stock picks.

A missing, invalid or empty prepared report produces a clearly labeled noon status
embed without mentions. Stock digests allow one @everyone mention. The daily
Durable Object atomically claims the receipt before Discord POST, so competing
alarms cannot duplicate a report. Uncertain delivery and rate-limit rejections are
recorded without automatically resending possibly delivered messages.

Deployment uses the existing GitHub Actions secrets CLOUDFLARE_API_TOKEN,
CLOUDFLARE_ACCOUNT_ID, DISCORD_WEBHOOK_URL, ALPACA_API_KEY and ALPACA_SECRET_KEY.
SEC_USER_AGENT stays in the filing-discovery job. Never put secret values in code
or chat. Deployment tests the code, installs the runtime secrets, verifies durable
storage, edits the existing practice message, uploads candidates, tests the hosted
provider connections, and arms the clock. The receipt records all results.

The account-scoped Cloudflare token needs Workers Scripts Edit and Account Settings
Read, plus User Details Read and Memberships Read for Wrangler. No custom domain,
KV, R2, Pages or paid Worker plan is needed. Keep the account on Free.
[Cloudflare pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/)

Authenticated endpoints: GET /status reads today's delivery receipt; GET /clock
reads the next hosted wake-up and last preparation/delivery; POST /verify checks
storage; POST /practice-format edits the existing practice message; POST /seed
stores reviewed candidates; POST /preparation-check probes providers without arming
or sending a report; POST /clock arms the recurring clock while respecting pause;
POST /pause cancels the clock and today's pending bundle; POST /resume explicitly
restarts the clock without clearing delivered receipts.

Repository stop variables only stop GitHub jobs/uploads. To stop hosted delivery,
open GitHub Actions, choose **Control hosted Dudebot delivery**, run the workflow
with `pause`, and inspect the returned PAUSED state. Use `status` to inspect it or
`resume` to restart. Disabling the public workers.dev route does not cancel Durable
Object alarms. Explicit pause survives ordinary deployments and blocks in-flight
preparation from re-arming delivery. An already-issued Discord request cannot be
recalled; remaining cards are suppressed.

September 9 live delivery is confirmed in run 34400550008: hosted preparation at
18:58:06 UTC qualified three of eight fresh candidates from nine stored candidates.
The daily receipt was claimed at 19:00:00.504 UTC and finished SENT with three
Discord message IDs. The next refresh is September 10 at 18:58 UTC. Fifteen reviewed
candidates were uploaded afterward. A later provider probe is diagnostic and does
not change the noon report. These runtime checks do not prove historical strategy
performance or guarantee future zero-delay delivery.
