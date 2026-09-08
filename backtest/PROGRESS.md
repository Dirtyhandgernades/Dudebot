# Dudebot backtest progress — September 8, 2026

The three-year screening replay is **not complete**. Actual detections, misses,
lead times, and a detection rate have not been established. All 230 events remain
not evaluable as replay results; missing evidence is not a strategy miss.

The supplied message.txt matches all 230 reference events across 137 tickers.
The declared window is July 29, 2022 through July 28, 2025, with comparison against
the 20 trading sessions preceding each listed drop. Same-day signals cannot be
counted as advance detections because the labels contain no intraday drop times.

## Verified source findings

These are targeted relationship findings, not historical alerts:

| Stock | Listed underwriters | Listed issuer counsel | Original IPO terms | Consequence |
|---|---|---|---|---|---|
| RAYA | Craft Capital; R.F. Lafferty | Ortoli Rosenstadt | $4/share; $12M base gross | Below the strict $15M floor; retained by firm-first pending remaining checks |
| GDHG | Revere; R.F. Lafferty | Hunter Taubman Fischer & Li | $4/share; ~$7M base gross | Below the strict $15M floor; retained by firm-first pending remaining checks |

Sources: [RAYA pricing announcement, December 14, 2022](https://www.sec.gov/Archives/edgar/data/1825875/000121390022080911/ea1703536kex99-1_eravakpower.htm)
and [GDHG closing announcement, April 14, 2023](https://www.sec.gov/Archives/edgar/data/1928340/000121390023030234/ea177003ex99-2_goldenheaven.htm).
Together these findings cover two tickers and five reference rows. They do not
establish that either stock passed every check before any drop. An IPO relationship
does not automatically qualify a later direct offering.

## Market data gaps

The initial five-minute probes returned bars for 180 events and no bars for 50.
This is a narrow availability sample, not full history or an RVOL calculation.
Empty samples were widened to the same session before the delayed cutoff, then
to earlier daily history if necessary. Daily fallback excludes the sampled day.

| Wider check result | Events |
|---|---:|
| NO_BARS_IN_WIDER_INTERVAL | 10 |
| SAME_SESSION_HISTORY_AVAILABLE | 40 |

The ten remaining empty symbols have specific reference-history issues:

- UOKA and GITS are later ticker labels; the historical names to investigate are
  MDJH and HRYU. Their bars have not yet been re-requested under those names.
- CLIK and ROMA first traded on their listed event dates, so the prior-session
  query precedes their traded history.
- CURR, HPAI, NIVF, FAAS and SELX correspond to first trading under the new symbol
  following a business combination. Predecessor SPAC records require the hard
  exclusions and cannot silently become operating-company history.
- TWG's pricing release announces trading for its event date, but the closing
  exhibit contains a conflicting year. Exchange confirmation remains pending.

See reference_gap_review.json and the source links in reference_progress.csv.
These are retrospective label diagnoses. Some sources were published after the
event and must not be used as pre-drop screening evidence. No original label was
overwritten. First-day events cannot be counted as prior-day detections using
traded history that did not yet exist.

Recovered bars establish availability in that interval only. They do not establish
a fresh price at the decision, complete monthly/RVOL coverage, a historical clear
halt status, or a detection. Remaining empty results may involve symbol history,
provider coverage, delisting, or inactivity; the cause has not been established.

## Rules and remaining work

The research implementation reports the original strict screen alongside the new
firm-first screen. Any verified listed firm is central; offering terms, geography,
age, RVOL and pump status become preferences in firm-first. Wei, Wei & Co. has
SUPER priority. Halts/suspensions, SPAC/acquisition corporations, and exactly
five-letter tickers remain hard exclusions. The strict IPO surge configuration
retains 12%–23% at low priority over 21 trading sessions.

Remaining work is point-in-time issuer/share-class mapping, source/role and filing
status review, corporate-action review, historical halt coverage, and the actual
candidate replay. Unknown halt status stays unknown. The independent SEC index
contains 769,683 filing leads across all 27 requested quarters, but filing-index
coverage is not a completed historical stock universe.

The free Alpaca configuration and notification-only design are preserved. The
development branch contains the firm-first research code; it has not been merged
into the live bot. No Discord messages or trades were sent.

Validation: 100 offline tests pass. Tests verify software behavior, not performance.
See reference_progress.csv for every event, reviewed_firm_findings.json for source
details, and summary.json for the downloaded run's machine-readable status.
