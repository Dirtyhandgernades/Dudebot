# Validation record

- 100 offline tests passed with `python -m pytest -q` on September 8, 2026.
- Added historical availability/timestamp checks, strict and firm-first comparison, unknown-halt handling, query checkpoints, SEC server-error date splitting, and wider market-gap probes. Synthetic tests are not historical detections.
- The synthetic end-to-end demo produces two qualified alerts, three excluded records, and one RVOL rejection. It cannot send messages.
- Tested cases include both local SEC parsing pipelines, exact evidence provenance, five-letter and acquisition-company exclusions, original IPO dates, offering boundaries, entity roles, bundled warrants, same-time RVOL, missing history, declared data delays, stale prices/halts, noon timing, one-ping payloads, restart deduplication, pagination, and SHA-guarded state writes.
- The four workflow YAML files were checked locally. The published GitHub Actions Offline tests run passed: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/34186918206
- Nasdaq's public halt RSS returned HTTP 200 during development and its field names matched the parser.
- Authenticated historical Alpaca SIP access and SEC downloads succeeded in the bounded GitHub backtest workflow. Initial five-minute probes found bars for 180 of 230 reference events and empty intervals for 50; these are availability results only. Wider gap checks retain the historical cutoff and do not infer halt clearance.
- No actual Discord notification was sent. Live webhook delivery remains untested.
- No real historical market replay has been completed. Offline unit tests and fictional examples are not backtest evidence. The user-supplied event list is retained as unverified comparison labels.
- Dependency versions used locally are recorded in `requirements-tested.txt`.
