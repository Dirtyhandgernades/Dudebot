# Validation record

- 59 offline tests passed with `python -m pytest -q`.
- The synthetic end-to-end demo produces two qualified alerts, three excluded records, and one RVOL rejection. It cannot send messages.
- Tested cases include both local SEC parsing pipelines, exact evidence provenance, five-letter and acquisition-company exclusions, original IPO dates, offering boundaries, entity roles, bundled warrants, same-time RVOL, missing history, declared data delays, stale prices/halts, noon timing, one-ping payloads, restart deduplication, pagination, and SHA-guarded state writes.
- The four workflow YAML files were checked locally. GitHub-hosted execution will be checked after publication.
- Nasdaq's public halt RSS returned HTTP 200 during development and its field names matched the parser.
- No actual Discord notification was sent. Authenticated Alpaca access, the user's SEC identity, and live webhook delivery require the user's secrets and remain untested.
- No real historical market replay has been completed. Offline unit tests and fictional examples are not backtest evidence. The user-supplied event list is retained as unverified comparison labels.
- Dependency versions used locally are recorded in `requirements-tested.txt`.
