# October 11 workflow repair

The reported Gmail errors were GitHub Actions failure notifications. Some runs succeeded between failures; the bot was not completely stopped.

Verified failures on the previously deployed commit `1409df6`:

- Runs [38156888234](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38156888234) and [38141594634](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38141594634): the alert step failed with GitHub HTTP 504 and 502 respectively. Discovery run [37972726991](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37972726991) also failed with GitHub HTTP 504.
- Friday run [37990524004](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37990524004): ranked preparation and ranked publication failed with Alpaca HTTP 403 after the close. The request's current-day end timestamp was 23:59:59 UTC, extending into future/recent SIP data. The repaired end is the earlier of the historical day end and actual request time minus 16 minutes. The cause is inferred from the failing request timing; provider denial bodies were not archived.
- Cloudflare dispatched Sunday scans and omitted Friday. Its numbered weekday range `1-5` means Sunday–Thursday. It now uses `MON-FRI`, with an additional New York weekday/time guard. Preparation runs from 09:00 through 16:30 local, including delayed closing-bar collection; Python retains the exchange holiday/early-close trade gates. [Cloudflare cron documentation](https://developers.cloudflare.com/workers/configuration/cron-triggers/).

GET reads retry temporary 500/502/503/504 responses at most twice. Access denials and persistent failures remain visible. A failed state PUT is retried once only after verifying that the remote blob still equals the original expected SHA; exact already-committed content is accepted without another PUT. Concurrent writers are never overwritten. Discord mutations remain non-retrying after ambiguous delivery.

The pending delivery repair now rechecks market close and quote/halt/cap freshness after committing the claim, before every trade POST. Definitively expired unposted claims release their paper reservation; uncertain delivery keeps it. There is no new strategy, leverage or gate relaxation.

New prospective contracts start October 12: `ranked-firm-2026-10-12-v2`, `firm-shadow-2026-10-12-v2`, and research-only `entry-quality-2026-10-12-v2`. Exact previously deployed configurations are archived. The unpushed October 7 ranked-v8 and entry-v2 drafts were never deployed and are not described as live. Existing decisions/outcomes remain under their original identifiers. Entry-quality review now includes archived registered trials without recalculating their frozen keep/reject decisions.

Local verification: 344 Python checks and 25 Cloudflare checks pass. A manual preflight now performs one bounded fresh SIP request even on closed days or with a warm cache, and writes an explicit closed-market report. Deployment and Discord practice receipts must be checked separately; offline success alone does not prove hosted delivery.

The daily research run [38022091332](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/38022091332) completed before these changes. Its entry-quality report had zero matured outcomes. A staged challenger is not a promoted live model. The first full three-session window following an October 7 close ends October 12; no completed full-window result is claimed on October 11.

Hosted practice run 38168587961 exposed a persistent GitHub 504 during state transfer. The next repair adds a compressed read-only Git fallback after bounded transient API failures, validates the original blob checksum, and uses the guarded compressed writer thereafter. A known pinned blob that changed during transfer fails closed. Permission denials are not bypassed. Transient PUT failures can also reconcile through Git when the Contents API itself is unavailable. The first October 12 v1 definitions are archived; v2 includes this additional fix. Redundant pending old-code verification jobs were intentionally cancelled before restarting final checks.
