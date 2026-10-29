# Free quant evidence feed v1

RESEARCH_ONLY_NOT_AN_ORDER. Manual bounded research feed, separate from frozen original capture paths and original A/B/C predictions. No orders, paid services or new clock schedule. This does not establish predictive accuracy, a live consolidated subscription, official closes or SMG execution.

## Run and consume
On branch `research/obsidian-early-rug-20261025`, dispatch **OBSIDIAN free quant evidence packet (research only)** (`obsidian-free-quant-feed.yml`). It runs offline tests first and uses existing hosted `OBSIDIAN_PAPER_API_KEY_ID`, `OBSIDIAN_PAPER_SECRET_KEY`, and `SEC_USER_AGENT` bindings. No values belong in Git or chat. Pushes run tests only; live requests require explicit dispatch. No background streaming is implied. Existing scheduled checkpoint owners can consume this packet; they have not been automatically modified or duplicated.

Local equivalent, when the same required credentials are securely available:

```sh
python -m backtest.obsidian_free_quant_feed --output outputs/backtest/free-quant-UNIQUE_CHECKPOINT.json
```

Output is write-once. Default universe is the deduplicated union of master and supplemental retained watchlists (136 unique names at validation). It is not full-market coverage; retired/unknown symbols remain in the denominator. Collector refuses duplicates, >200 symbols and the protected 14:45–14:58 Central capture window. No existing historical file is overwritten.

The quant should read `rows` by ticker, not treat `research_classification` as a signal. For price age, use `iex.trade` and `iex.quote` separately; check errors, source timestamp and retrieval time. A <=60-second IEX trade is `FRESH_SINGLE_VENUE`, not consolidated/NBBO. A current IEX quote does not freshen a stale trade. Daily volume is source-provided IEX volume, not consolidated RVOL.

SIP requests raw 1-minute historical bars, ending before the safe 17-minute delay cutoff and excluding incomplete bars. It checks duplicate/future bars through the existing SIP validator. Status fresh-at-asof means fresh at that DELAYED cutoff; never interpret it as current. `window_volume` covers only the stated recent window, not full-day volume/RVOL. Missing/incomplete pagination stays unavailable; no paid or realtime fallback. Maximum two SIP pages, 24 total requests, no retries, stop a host on HTTP 401/403/429.

Nasdaq RSS is parsed by the existing repaired halt parser. Preserve raw-event timestamps and source errors. No matching row is NOT proof of no halt; reported resumption times are not independent execution proof. Every row keeps executable halt clearance false.

SEC company ticker/exchange mapping is required before submissions lookup. At most eight symbols (deterministic first eight sorted) have SEC metadata requested per run, with a seven-day filing window; all other symbols explicitly say NOT_REQUESTED_SEC_BUDGET. Only two primary filing documents total are fetched. Symbol/CIK mismatches, missing contact identity, provider errors and future/naive publication times do not become catalysts. Exact acceptance/publication, retrieval, source URLs and response hashes are recorded. Keyword passages identify POSSIBLE adverse and contrary text for review, never prove causal mechanisms, actual sales or bearish theses. No-match keywords do not prove absence of counterevidence. Issuer-release review remains pending; filing exhibits/issuer release feeds are not fully crawled.

All rows remain blocked pending mechanism and eligibility review. Security identity, corporate actions, market cap, NBBO, complete halts, actual SMG borrow and permission are NOT established by this packet. Unknown does not become pass.

## Actual first hosted result
Run [40929567179](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40929567179), source `b4b2045`, collected Oct29 18:18:44–18:18:51 UTC (13:18 Central), artifact 12922670387 downloaded and inspected. 136 rows retained: IEX trade <=60 seconds 24, stale 112. SIP delayed-cutoff fresh 108, stale 20, missing 8. All fourteen source requests HTTP 200; official Nasdaq RSS parsed. SEC mappings/submissions checked for eight, 128 not queried under budget; two recent filings/documents collected, still unreviewed. This demonstrates free-source collection, not full catalyst coverage or rug prediction success. Artifact expiry and exact payload hash are in the durable checkpoint under `backtest/evidence/2026-10-29/free-quant-181844Z/`.
