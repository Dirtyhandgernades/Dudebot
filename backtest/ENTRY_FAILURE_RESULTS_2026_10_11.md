# Entry and exit failure audit: October 11, 2026

The archived October 2 `LIVE_FIRM_TIMING_SHORT-primary` simulation lost
$189,510.63 across the 2025 game season, closing 85 trades. Each planned hold
was three sessions; the whole account did not lose that amount in just one
three-session window. Its largest loss was SMX, December 2–5: $167,915.33 on
$29,997 initial notional. The archive is preserved. This is a simulated account,
not evidence of executed SMG orders. This audit does not re-certify every legacy
price, identity or historical eligibility assumption.

The current live system already has smaller shared advisory exposure limits,
source fingerprints, delayed preclose checks, a maximum three-session horizon
and executable current borrow gates. It has not deployed the larger research
allocations or the disabled old daily-breakdown proxy. Short losses can exceed
the adverse-move sizing assumption, particularly with closing-price execution.

## What was tested

Using the completed independently discovered eight-year packet and actual
timestamped checkpoint events from run 38170602612, five fixed confirmation
rules were crossed with one-, two- and three-session holds, base and stress
costs, eight seasons, and two scheduling controls. All 480 portfolios and their
trade ledgers are retained. No provider requests, known-winner selection,
retrospective exit choices, size increases, alerts or orders are made.

The controls are decisions fifteen and five minutes before the actual exchange
close, with data at least sixteen minutes old. Confirmation uses only the
observed partial candle. The rules are baseline, nonpositive change from the
prior close, existing red/low-close confirmation, a break below the prior low,
and failed recent-high rejection with a red weak-close candle. No named loser
is blacklisted. Missing charts cannot pass a confirmation rule.

The separate learner uses seven completed daily features plus seven observed
checkpoint candle features. Prior fits use only the same checkpoint offset's
earlier two years of matured labels, with independent issuer windows and held
issuers excluded. Earlier generic daily candidate labels are not substituted
for missing matched candle labels. Expected policy returns, profitable outcomes
and large losses are fitted separately. Their ranks are not calibrated drop
probabilities. One-, two-, three-session and prior-score adaptive holds are
retained, with unchanged bounded sizing and both cost cases.

## Attribution: bounded baseline, fifteen-minute checkpoint

| 2025 filled trades | Count |
|---|---:|
| At least 20% lower close within three sessions, profitable policy exit | 5 |
| First such lower close in sessions four through ten | 12 |
| No such lower close in the complete ten-session window | 33 |
| No three-session drop; later window incomplete | 3 |

These are 53 filled-trade windows, not independent calibrated probabilities or
full-market missed-dump recall. A company with no such close within ten sessions
can still decline later. Five losing trades would have had a profitable fixed
exit at another one-, two- or three-session close in hindsight. Those diagnostic
counterfactuals never choose an entry or produce an account profit claim.

None of those 53 fills was more than 20% above its pre-entry quote. Fill drift
therefore does not explain the entire weak season. CCHH was still up 5.99% at
the checkpoint, with a green candle; PLRZ was down 7.85% but near the upper part
of its observed range; SMX was up 39.19% with a green candle. DTCK, an actual
next-session dump hit, was up 2.52% with a green candle too. Blanket green-candle
or positive-return rejection removes genuine winners as well as continuing
pumps. Waiting for any weak candle is not sufficient evidence of a collapse.

## Results

| Fifteen-minute policy | 2023 net | 2024 net | 2025 net | 2025 stress net |
|---|---:|---:|---:|---:|
| Bounded baseline, three sessions | $116.14 | -$1,135.34 | $1,647.16 | -$2,803.38 |
| Nonpositive current change, three sessions | $709.23 | -$2,276.43 | -$870.21 | -$3,232.70 |
| Observed confirmation, three sessions | $186.54 | $1,037.67 | -$470.16 | -$1,688.48 |
| Failed-high rejection, one session | $180.98 | $2,210.30 | $960.97 | $756.99 |

The failed-high row has zero 2023 trades (interest only), seven 2024 trades and
three 2025 trades. It fails coverage/consistency. All early-year failures,
alternative holds and five-minute scheduling results remain in the reports.
No fixed confirmation policy passes the eight-season consistency test.

The matched-candle learner has only 35 independent earlier two-year training
windows for its fifteen-minute 2025 model and 36 for the five-minute model.
Every earlier test year is training-unavailable under the fixed thirty-example
minimum. This is a verified data gap, not a successful cash-only backtest.

| 2025 matched-candle test | Base net | Stress net | Base trades |
|---|---:|---:|---:|
| One session, fifteen-minute checkpoint | $4,389.39 | $2,264.88 | 33 |
| One session, five-minute delay control | $1,779.82 | -$410.73 | 32 |
| Prior-score adaptive hold, fifteen-minute checkpoint | $2,756.32 | -$592.67 | 42 |
| Prior-score adaptive hold, five-minute delay control | -$788.18 | -$4,085.10 | 41 |

The one-session learner improves the matched baseline diagnostic but fails the
delay control and multi-year training/consistency requirements. It is not
promoted. None of this establishes the $70,000 seasonal target.

## What continues automatically

The existing bounded hosted daily eight-season workflow now also runs the
cached confirmation/attribution and matched-candle learning reports. It still
collects at most 100 new source documents per scheduled day, split across source
years, and reuses prices. These two new steps make zero provider requests and
retain failures, all portfolios, model counts, weights and decision scores in
the artifact. Existing live policies, sizing and separate prospective promotion
gates remain unchanged. Long alerts remain disabled/review-only; a losing short
is not evidence to reverse the trade into a long.

Historical borrow, caps, halts, full game membership and exact intraday dump
times remain unknown. Costs are the existing disclosed $5 each order, 30/100
bps each side and assumed 10%/100% annual borrow. Entry/exit fills are closes;
stops and targets observed at one close execute at the following close. No loss
is clipped or exited at an intraday low. All results are conditional paper
simulations on inspected data; fresh prospective evidence remains necessary.
