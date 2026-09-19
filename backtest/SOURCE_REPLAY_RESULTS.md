# Three-year independent firm-first replay — September 18, 2026

Evidence: GitHub run 35395039136, commit 34bd958, artifact 10568107637.
Artifact SHA-256: 549bc0b32eb86b9ab91985f5a3123a5a39343840c359097d6f78d38244ec5e80.
Period: 2022-07-29 through 2025-07-28.

All 230 message.txt rows match reference_events.csv in order, ticker, date and reported drop. Reported drops remain user-supplied labels, not independently verified returns. Labels are read only after source selection and replay decisions in smg/source_replay.py.

## Observed results

- Selected primary filings processed: 2608/2608.
- Extracted candidate records: 788; distinct symbols: 381. These are discovery records before exclusions, not recommended trades.
- Historical decisions evaluated: 133081/133081.
- Reference events with a conditional firm/price match in the preceding 20 sessions: 41/230 (17.8%), across 29 distinct tickers.
- Sampled without a firm/price match: 29 events.
- No sampled pre-event decision: 160 events.
- Fully verified eligible detections: 0. Verified misses and full detection rate: undetermined.

The 41 conditional matches establish listed-firm structure and a sampled price above $3. They do not establish a pump-failure entry, executable borrow, verified cap, verified halt status, or profitable trade. The 29 sampled nonmatches and 160 uncovered events must not be combined into verified strategy misses.

Conditional symbols: BTOG, CDTG, CGTL, CHSN, ELWS, GSIW, HLP, HTLM, IFBD, JZXN, LNKS, LXEH, MFH, MFI, MTC, NAMI, NTCL, OMH, OST, PCLA, PGHL, PHH, RAYA, RYDE, TWG, UBXG, WCT, WLGS, WYHG.

## Source outcomes

{
  "SOURCE_SYMBOL_OR_EXCHANGE_UNRESOLVED": 1419,
  "NO_ATTACHED_LISTED_FIRM_ROLE_RECOGNIZED": 396,
  "FIRM_CANDIDATE_EXTRACTED": 788,
  "SOURCE_ERROR": 5
}

## Decision reasons (nonexclusive)

{
  "VERIFIED_LISTED_FIRM_RELATIONSHIP": 83711,
  "PREFERENCE_GAP:FIRM_WATCH_HAS_NO_VERIFIED_TRANSACTION": 83711,
  "PREFERENCE_GAP:UNKNOWN_TRANSACTION_STATUS": 83711,
  "PREFERENCE_GAP:AMBIGUOUS_OFFERING_TERMS": 83711,
  "PREFERENCE_GAP:UNVERIFIED_USD_TERMS": 83711,
  "PREFERENCE_GAP:MISSING_OFFER_PRICE": 83711,
  "PREFERENCE_GAP:MISSING_OFFER_GROSS": 83711,
  "PREFERENCE_GAP:UNKNOWN_OPERATIONS": 83711,
  "PREFERENCE_GAP:MISSING_EVIDENCE:offer_gross": 83711,
  "PREFERENCE_GAP:MISSING_EVIDENCE:offer_price": 83711,
  "PREFERENCE_GAP:MISSING_EVIDENCE:operations_country": 83711,
  "PREFERENCE_GAP:MISSING_EVIDENCE:status": 83711,
  "MISSING_MARKET_DATA": 50346,
  "GAME_PRICE_NOT_ABOVE_3": 25593,
  "UNKNOWN_ISSUER_CLASSIFICATION": 34798,
  "GAME_MARKET_CAP_UNKNOWN": 7772,
  "ACQUISITION_CORPORATION": 14312,
  "ACQUISITION_CORPORATION_NAME": 6464,
  "FIVE_LETTER_TICKER": 5788,
  "SMG_EXCLUDED_SYMBOL": 1686
}

## Remaining work and limits

All selected filings and planned decisions finished in this pass; there is no runtime truncation within this selected corpus. Universe completeness remains false: firm-search coverage, unresolved historical identity, later filing context, historical market cap, historical halts, and ticker intervals remain limitations. Historical borrow and SMG availability also remain unverified. Current borrow snapshots cannot certify historical execution.

This artifact runs the separate firm-first research screen. It does not execute the original strict strategy, so strict-rule detections cannot be inferred from it. The strict historical replay and a combined final report remain pending. The user's benchmark of independently catching most examples is not met by this result.

Free Alpaca and notification-only operation are retained. No orders were submitted by this replay.

Per-event comparison is saved alongside this report as source_replay_event_comparison.csv. Full downloaded evidence is under outputs/backtest/source-replay-35395039136.
