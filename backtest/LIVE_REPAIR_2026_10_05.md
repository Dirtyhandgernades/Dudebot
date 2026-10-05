# Live repair — October 5, 2026

The principal failures were hosted-runner assignment and stale firm reviews.
Runs 37370164409 and 37363838674 never executed an application step; GitHub
reported that a hosted runner was not acquired. Meanwhile Monday scans
selected zero firms because Friday reviews expired after 26 hours.

The repaired path checks current issuer listing and newer filings, then
refreshes up to eight stale issuers per scan. Failed, ambiguous or incomplete
reviews remain stale. New annual reports and amendments reconfirm current
roles; historical underwriters and previously established SPAC exclusions
are retained correctly. Full discovery also reconciles later annual roles.

[First repaired scan](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37385073546)
refreshed/scanned eight firms, including TJGC, FTFT and RPGL. Discord returned
SENT for firm-watch message 1556801190488969382. After full discovery resumed,
[the queued live scan](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37385436221)
selected 24 firms and four broad names, archived 135 current asset lookups
(134 provider responses, one unavailable), and finished successfully.
It ran after the close, so it does not establish successful intraday signals.

The shared writer group previously allowed only one waiting job, canceling
waiting discovery, practice or deployment. All state writers now share the
new serial group smg-state-writer-v2 with queue:max. The old deployment was
allowed to finish before the group migration; new live, practice and deploy
runs all completed. This preserves state serialization and waiting jobs.
[GitHub documents multi-job concurrency queues](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
Live workflows use ubuntu-22.04, a supported alternate runner label; it
cannot eliminate GitHub infrastructure outages. Discovery also runs before
market open, and the Cloudflare variable gate avoids duplicate quarter-hour
schedules while retaining GitHub fallback runs.

[Practice verification](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37385436217)
returned SENT for message 1556802827584806983, channel 1546733107846324254.
It is a labeled, mention-free practice embed, not a trade recommendation.
The receipt is durable in state commit 144a290a. Cloudflare deployment
37385436271 also succeeded, preserving event-driven quarter-hour triggers
and keeping the legacy noon alarm paused.

Known research watches continue receiving prospective borrow observations
even if their filing review is stale; this never qualifies them for trading.
Borrow lookup and sentiment/fundamental enrichment have explicit time budgets.
Unprocessed names remain pending and unknown data stays unavailable. A zero
fresh firm scan now reports a coverage failure rather than implying that no
firm setup exists. Local validation: 219 Python tests and 23 worker tests.

Failed firm trading qualification remains disabled pending validation; broad
alerts are independent, and longs remain review-only. Operational repair does
not establish the 70% pre-drop detection or $189,000 capital target. The
combined-method research is preserved in stash@{0} and resumes separately.
