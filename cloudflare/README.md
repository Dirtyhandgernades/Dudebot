# Free hosted Discord delivery

This small Worker uses a SQLite Durable Object to store a prepared research digest
and wake at noon Pacific / 2 p.m. Central, following daylight-saving time. It uses
the existing Discord webhook. No domain, Discord bot user, paid market feed, or
hosted AI service is required.

Cloudflare offers SQLite Durable Objects on the Workers Free plan. Free-plan
limits stop operations when exceeded; keep the account on Free. The expected
traffic here is a handful of requests per trading day, not an always-running VM.
[Cloudflare pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/)

## Connect the account

1. Create a Cloudflare API token scoped to your account. The Edit Cloudflare
   Workers template is a starting point; this workers.dev deployment needs
   Workers Scripts Edit and Account Settings Read. User Details Read and
   Memberships Read support Wrangler's account checks. It uses no zone routes,
   KV, R2, Pages, containers, builds or agents permissions. Leave IP restrictions
   empty for GitHub-hosted runners. An expiration date is optional; an expired
   token stops future deployments, not an already-running Worker.
2. Add GitHub Actions secret `CLOUDFLARE_API_TOKEN` and secret
   `CLOUDFLARE_ACCOUNT_ID`. Never commit or paste the values in chat.
3. Run **Deploy free Cloudflare dispatcher** in Actions. The workflow tests the
   code, deploys `dudebot-dispatch`, and installs the existing Discord webhook plus
   a domain-separated secret derived from that webhook. There is no third secret
   for you to generate. If the webhook rotates, rerun this deployment.
4. The workflow verifies authenticated durable storage and reformats the existing
   practice message through Cloudflare. Only after both succeed does it store the
   endpoint and select Cloudflare as the delivery owner on the `smg-state` branch.
   The receipt artifact identifies the deployed endpoint and practice-message ID.
   If Cloudflare requests a workers.dev subdomain first, choose one under Workers
   & Pages in the dashboard, then rerun deployment.

[Official GitHub deployment guide](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)

## Delivery behavior and limits

GitHub still performs the SEC and Alpaca work. Its job starts early, warms market
history, refreshes prices/halts about 90 seconds before noon, and uploads the
digest. Cloudflare's durable alarm then owns the outbound send. This removes a
GitHub job startup from the final delivery step; it does not eliminate upstream
data delays, missed GitHub preparation, API outages, rate limits or network delay.

Only firm-first / SIP / 16-minute-delay bundles are accepted. The sender rechecks
issuer exclusions, evidence markers, listed-firm matches, review freshness,
market timestamps, halt status, date and the noon window. No qualified stocks
means no Discord message. Stale, late, missing or ambiguous records never become
fallback stock alerts. Cards include actual metrics, matched firms and source
links, with one allowed `@everyone` mention per daily digest.

The Python job stores the shared daily delivery claim before uploading. The
Durable Object stores its own claim before Discord POST. Alarm retries cannot
send the digest twice. A timeout remains DELIVERY_UNCERTAIN; a Discord rate limit
or rejection is recorded and stops the digest. A failed preparation does not
silently fall back to a second sender. The current bound is 30 stock cards/day.

Authenticated GET `/status` returns today's alarm receipt. POST `/verify` checks
storage; POST `/practice-format` edits an existing message without a new ping.
Neither is a test of a future real noon alarm. The first qualified noon delivery
must be inspected separately before calling the hosted path fully validated.

`DISCORD_ENABLED=false` or `SMG_LIVE_ENABLED=false` prevents future preparation.
If a digest is already armed, disable the Worker in Cloudflare to stop that day's
send; GitHub variables cannot retroactively cancel an already-stored alarm.

[Durable alarm semantics](https://developers.cloudflare.com/durable-objects/api/alarms/)

## Historical validation remains separate

The practice message identifies HPAI, JBDI, LNKS and WCT in currently processed
filings. It does not prove pre-drop detections in the 230-event reference set.
Some historical bars are available for 220 events; ten retain diagnosed market
gaps. The full historical source/mapping/halt review and actual screening replay
remain incomplete. Offline tests verify software behavior, not trading results.
