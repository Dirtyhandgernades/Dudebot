# Historical replay status

The requested window is July 29, 2022 through July 28, 2025. Comparison uses
the preceding 20 trading sessions, excludes the event date, and retains all
230 reference events (137 symbols). These are analysis parameters, not added
screening requirements. Reference drop percentages never enter the screener.

**The full historical backtest is incomplete.** The new code provides an
independent SEC index collector, replay of prepared point-in-time research
records, and an event comparison report. It does not yet turn the index leads
into a complete historically mapped and reviewed candidate universe. There
are no committed real research packets or historical halt archives.

An audit with no packets reports `NOT_RUN`, null detections/misses/rate, and
`NOT_EVALUABLE` for each event. That means unknown, not 230 strategy misses.
Candidate records alone cannot establish complete universe coverage, so the
current implementation deliberately leaves the overall miss count and rate
null even after a partial replay. Extra alerts are not labeled false positives.

The user clarified the surge rule during continuation: at least 12% over the
existing 21 trading sessions; 12% through 23% inclusive stays eligible at low
priority, above 23% has normal priority. Age and entity ordering remains within
each IPO surge band. The direct-offering pipeline has no added surge requirement.
`SURGE_RETURN_MIN_PCT`, if set, still overrides the configured floor.

## Commands

Run from the repository root, with Python 3.11+ and the existing dependencies:

```bash
python -m smg.backtest audit
python -m smg.backtest collect-indexes --max-quarters 2
python -m smg.backtest replay --packets backtest/packets.jsonl --max-records 25
```

`audit` is offline. `collect-indexes` checks a single AAPL minute for historical
SIP access, then collects at most two SEC quarterly indexes. The AAPL response
is an access check, never a strategy result. SEC collection includes older IPO
history (three years before the replay, plus 150 days of context), annual and
event filings, with no present-day ticker filter or reference-list filter.
These raw leads include non-Nasdaq issuers and nonqualifying transactions;
index completion alone does not imply candidate or market coverage.

State lives under `backtest/runtime/`, never live `runtime/` or `smg-state`.
Each SEC quarter commits atomically to SQLite. Replay checkpoints include
strategy, entity list, input, engine, rule, market and provider fingerprints.
Market failures retry on the next run; successful requests use atomic caches.
Changed inputs produce a separate checkpoint. Requests use the existing
rate-limited HTTP client, pagination, SIP, split adjustment, and a historical
symbol `asof` date. No account/order or Discord endpoint is used.

The manual **Historical backtest (bounded, no messages)** workflow limits
runs to 15 minutes, two quarters or 25 candidate decisions. A push on its
development branch also starts one bounded collection run. It uses only the
Alpaca and SEC secrets, preserves state in an Actions cache, and uploads
reports and an index checkpoint for 30 days. Caches can be evicted; download
checkpoints to preserve long backfills. There is no automatic repeating job.

## Research packet contract

Each JSONL line describes one candidate at one permitted noon decision.
This explicit input boundary is a temporary research interface, not a claim
that historical discovery is automated. See `tests/test_backtest.py` for
synthetic examples; do not use those examples as real research inputs.

- `decision_at`: exact timezone-aware simulated noon timestamp.
- `candidate`: production `Candidate`, including the review timestamp,
  original IPO date/terms or separate direct-offering terms, and evidence.
  The replay never refreshes `reviewed_at` merely to pass the freshness rule.
- `documents`: source `url`, `filed_at`, `raw_text`, and optional `accepted_at`.
  SHA256 and quoted passages are checked against source content. Acceptance
  timestamps take precedence; date-only documents become available at
  midnight New York on the following calendar day. Context cannot be future.
- `mapping`: ticker, CIK, exchange, share_class, source_url,
  original_listing_source, known_at, and the inclusive `valid_from` / exclusive
  `valid_to` dates. A current symbol map cannot stand in for historical mapping.
- `filing_review_source` and `filing_review_through`: evidence of a review
  through exactly the simulated decision, including status/cancellation
  review. These attestations still require source review by the researcher;
  they are not independently inferred or authenticated by the packet validator.
- `corporate_actions_verified` and `corporate_action_source`: explicit review
  of splits and ADS units. Unknown actions suppress qualification.
- Optional `halt`: status CLEAR or HALTED, `historical_archive: true`, source_url,
  and a coverage interval `from` / `through` containing the decision. This must
  describe actual historical coverage, not today's RSS feed. Absence is UNKNOWN.

The replay reuses production structural and market rules, the fixed 20:00 UTC
clock and the 16-minute delay. It skips holidays and early closes. A candidate
passing all other criteria without historical halt coverage is reported as
`MATCH_EXCEPT_UNKNOWN_HALT`; it never receives a fabricated CLEAR check.

Reports include each event's first verified prior alert, calendar and trading
session lead time, pipeline, evidence, repeated alerts, same-day ambiguity,
and missing-data reasons. Ticker matching is exact: renamed-symbol aliases
are not guessed. Complete issuer/share-class histories and event aliases are
still needed before interpreting nonmatches as misses. Five-letter symbols in
the event list are flagged as rule conflicts; this does not prove that the
issuer used that symbol throughout the lookback.

## Work still required

Build and validate historical exchange/CIK/share-class mappings; download and
review indexed prospectuses and their then-public context; produce candidate
versions without resetting original listing dates or terms; establish
cancellation and halt coverage; generate the full ordinary-market decision
universe; and run the real replay. The prepared-packet engine and its offline
tests do not substitute for these tasks.

Provider references: [Alpaca bars and symbol mapping](https://docs.alpaca.markets/us/reference/stockbars),
[SEC indexes and fair access](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data),
[Nasdaq halt search](https://nasdaqtrader.com/Trader.aspx?id=TradingHaltSearch).
