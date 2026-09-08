# Validation record

- Latest DECA update: 121 Python tests and 5 dispatcher tests pass. Both profiles and both senders enforce current price > $3 and market cap >= $25M, with Nasdaq/NYSE scope. Boundary, unknown/future cap and independent source-selection tests are included.
- Cloudflare activation verified durable storage and successfully edited the existing practice message in run 34281212506. The free Worker is selected as delivery owner; the first qualified noon alarm is not yet validated.
- Today’s GitHub noon run 34279293529 started late and logged MISSED_SEND_WINDOW. Cloudflare final delivery does not eliminate the remaining dependency on GitHub preparing fresh data.

- September 8 update: 113 Python tests and 5 hosted-dispatcher tests pass locally. Embed size/mention handling, reformatting the existing practice message, Pacific daylight-saving time, stale-data rejection, and durable duplicate suppression are covered.
- Practice run 34250065854 returned Discord receipt SENT, message ID 1546917333065408734. Current reference overlap: HPAI, JBDI, LNKS, WCT. These use current filings and are not historical detections. The later embed edit and Cloudflare deployment require their own receipts.
- Cloudflare deployment validates authenticated durable storage and edits the existing practice message through Cloudflare before selecting it as the delivery owner. A successful deployment is not proof that a future noon alarm or qualified-stock send has occurred.

- 107 offline tests passed with `python -m pytest -q` on September 8, 2026, including live firm-watch formatting, unknown terms, negative role statements, SPAC exclusions, durable activation receipts, context-backlog resumption, and fresh discovery during older backfill.
- Added historical availability/timestamp checks, strict and firm-first comparison, unknown-halt handling, query checkpoints, SEC server-error date splitting, and wider market-gap probes. Synthetic tests are not historical detections.
- The synthetic end-to-end demo produces two qualified alerts, three excluded records, and one RVOL rejection. It cannot send messages.
- Tested cases include both local SEC parsing pipelines, exact evidence provenance, five-letter and acquisition-company exclusions, original IPO dates, offering boundaries, entity roles, bundled warrants, same-time RVOL, missing history, declared data delays, stale prices/halts, noon timing, one-ping payloads, restart deduplication, pagination, and SHA-guarded state writes.
- The four workflow YAML files were checked locally. The published GitHub Actions Offline tests run passed: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/34186918206
- Nasdaq's public halt RSS returned HTTP 200 during development and its field names matched the parser.
- Authenticated historical Alpaca SIP access and SEC downloads succeeded in the bounded GitHub backtest workflow. Initial five-minute probes found bars for 180 of 230 reference events and empty intervals for 50; these are availability results only. Wider gap checks retain the historical cutoff and do not infer halt clearance.
- Live Discord activation succeeded in run https://github.com/Dirtyhandgernades/Dudebot/actions/runs/34192293139. Discord returned message ID 1546760331131625533. This was an activation receipt without mentions, not a qualified stock alert. Initial discovery reviewed 55 source records and stored 19 research candidates; coverage is partial.
- No real historical market replay has been completed. Offline unit tests and fictional examples are not backtest evidence. The user-supplied event list is retained as unverified comparison labels.
- Dependency versions used locally are recorded in `requirements-tested.txt`.
