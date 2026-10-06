# Firm-watch collapse research — October 6, 2026

The completed audit supports a broad firm-watch list, but does **not** support shorting every watched stock or assigning 80–90% dump confidence. Combining short and longer ramps found advance watches for 559 of 873 measured collapse episodes in the partial firm-linked scope (64.03%). Only 360 of 3,861 sampled warning windows subsequently fell 20% within three trading sessions (9.32%). Monitoring coverage and profitable entry accuracy are different measures.

I used Exa to review 68 search results across 12 research workstreams, then checked primary regulatory notices and issuer filings for the documented cases below. Every stock in the assembled roster received a price/source audit row. This is not a verified causal investigation of every company or proof that every decline was manipulation.

## What the stocks have in common

The useful hypothesis is a combination of **historical firm relationships, available share supply and ownership, promotion or narrative evidence, price structure, and executable entry conditions**. None supplies a universal dump date on its own.

FINRA describes small IPOs with limited float, concentrated allocations, foreign omnibus accounts and exceptional price moves without material news. Some of the decisive warning signs concern brokerage accounts and coordinated activity that public candles cannot reveal. Its notice discusses transactions, not a finding that any firm on the user's list committed fraud. [FINRA Regulatory Notice 22-25, November 17, 2022](https://www.finra.org/rules-guidance/notices/22-25).

The FBI describes investment clubs using social media and private messaging to build demand before coordinated selling; accumulation and promotion can run for weeks or months. That supports tracking a developing campaign, rather than assuming a fixed number of days after an IPO. Private campaign membership and operator inventory are missing from this audit. [FBI alert, July 3, 2025](https://www.fbi.gov/investigate/cyber/alerts/2025/fraudsters-target-us-stock-investors-through-investment-clubs-accessed-on-social-media-and-messaging-applications).

Public promotion is another mechanism. The SEC's December 2022 Atlas Trading complaint alleged that influencers sold while publicly encouraging followers to buy or hold. These are allegations described in that release, not a current adjudication of guilt. [SEC announcement](https://www.sec.gov/newsroom/press-releases/2022-221).

Underwriter, auditor and counsel names remain the primary discovery features requested by the user. Their roles must be dated: an IPO underwriter is a historical transaction relationship; company counsel and underwriter counsel are different; an old audit report does not prove the auditor is still engaged. Selected-corpus firm rates in `firm-rates.csv` are diagnostics, not fraud probabilities or causal estimates. There is no adequate unselected-market comparison here.

## Mechanisms to distinguish

| Research category | Evidence to collect before a decision | What cannot be concluded from candles alone |
|---|---|---|
| Limited-float IPO / concentrated allocation | Original prospectus, issuer versus selling-holder shares, economic ownership, resale registration, trading history | Actual distribution among coordinated brokerage accounts |
| Private investment-club ramp | Timestamped public solicitation, issuer-specific reports, abrupt demand and turnover | Contents of private chats, participants' inventory or planned sale date |
| Public influencer or paid promotion | Original posts, compensation disclosures, archived edits and timestamps | Whether the speaker sold, or whether a campaign is criminal |
| Narrative and financing / resale overhang | Dated business claims, shelf and resale filings, effective registrations, actual sale notices | A shelf's maximum capacity is not an executed sale or a dump countdown |
| Distress, dilution and reverse-split cycle | Dated financing terms, cash runway, going-concern notices, share changes | A large decline does not establish manipulation |
| Fundamental or regulatory shock | Earnings, trial/regulatory decisions, bankruptcy and exchange notices | Often there is no public pre-event warning that predicts the surprise |
| Rebound failure / squeeze unwind / waterfall | Prior drawdown, short and longer ramps, failed breakout, support and volume | A similar chart can have a different cause and remain dangerous to short |

These categories can overlap. The machine-readable research registry is `backtest/mechanism_taxonomy.json`; it is not an activated trading classifier. News keyword topics in the audit are candidate tags, not verified mechanisms. Public Reddit/Stocktwits posts do not establish coordinated manipulation; incomplete archives cannot establish their absence.

## Issuer checks that changed the interpretation

**DTCK.** Its November 7, 2025 episode measured a 77.934% closing collapse; the previous decision-day raw close was $6.39. A short-burst ramp, exhaustion wick and failed breakout were visible in the pre-drop daily features. However, OneStop was a **former** auditor by this period: the company disclosed termination and replacement by AOGB on August 30, 2024. The filing was accepted after the close; the audit applies the change from the next trading session. A later document containing an older auditor's report must not turn the old firm into the current auditor. [DTCK 6-K](https://www.sec.gov/Archives/edgar/data/1949478/000168316824006129/davis_6k.htm), [acceptance record](https://www.sec.gov/Archives/edgar/data/1949478/000168316824006129/0001683168-24-006129-index.html).

DTCK's March 2025 preliminary $30 million shelf was financing capacity, not evidence of actual selling on a later dump date. Stories published after the drop are excluded from advance news features. [DTCK F-3](https://www.sec.gov/Archives/edgar/data/1949478/000168316825001820/davis_f3.htm).

**MSGY.** The prospectus described 1.5 million IPO shares at $4, D. Boral as sole underwriter, 82.14% voting control and J&S Associate PLT as auditor. This example therefore cannot be reduced to the watched auditor list. Voting control is not the same as freely tradable economic float. Its October 2, 2025 episode measured an 85.526% fall from the preceding three-session peak, after an extended ramp; it had a ramp watch but none of the four stricter chart confirmations at the preceding decision point. [MSGY prospectus](https://www.sec.gov/Archives/edgar/data/2020228/000121390025062117/ea0207245-17.htm).

**WCT.** The IPO consisted of 1.1 million issuer shares and 900,000 selling-holder shares at $4: $4.4 million gross issuer proceeds, not $8 million. Dominari was lead underwriter and Revere co-underwriter. Ortoli Rosenstadt was company U.S. counsel; Hunter Taubman represented the underwriters. WWC was the IPO auditor, but a January 2025 filing calls WWC the previous auditor. Its exact later engagement interval remains unresolved in this packet. [IPO prospectus](https://www.sec.gov/Archives/edgar/data/1990251/000121390024084652/ea0201626-09.htm), [IPO pricing release](https://www.sec.gov/Archives/edgar/data/1990251/000121390024085035/ea021611502ex99-1_wellchange.htm), [later filing](https://www.sec.gov/Archives/edgar/data/1990251/000121390025004093/ea0225030-04.htm).

WCT had no measured 20% collapse episodes during the September–December 2025 game in this packet. The separately inspected 2026 history does contain a major October 1 collapse. Neither observation justifies substituting 2026 prices into the 2025 game.

**XHLD / TEN Holdings.** This is a U.S. event-services issuer with Japanese parent V-Cube, which disproves treating the whole cohort as Chinese companies. The IPO offered 1,667,000 shares at $6; Bancroft represented the underwriters. Hunter Taubman was company counsel and TroyGould underwriter counsel. The prospectus describes 83.3% voting control and 4.4 million registered resale shares; its 180-day lockup has selling-holder exceptions. Registered shares and lockup terms do not establish actual sales. [IPO prospectus](https://www.sec.gov/Archives/edgar/data/2030954/000149315225006531/form424b4.htm), [IPO completion filing](https://www.sec.gov/Archives/edgar/data/2030954/000149315225007870/form8-k.htm).

XHLD's measured 2025 game collapses had preceding prices below $3, so those particular decision points cannot become SMG entries under the user's price rule. The separately inspected September 28, 2026 collapse is not a 2025 missed executable trade.

**TJGC / MCTR.** The same security changed ticker from MCTR to TJGC at the December 10, 2025 opening, after the game's December 5 end. CUSIP stayed unchanged. The SEC notice was accepted after that opening, so the audit preserves its later publication time. Search MCTR for the 2025 game; do not retroactively screen for TJGC or reset IPO age. MCTA is a separate ticker. The verified lineage is saved in `backtest/issuer_lineage.json`. [Ticker-change 6-K](https://www.sec.gov/Archives/edgar/data/1969928/000121390025120275/ea0269188-6k_tjgc.htm), [acceptance record](https://www.sec.gov/Archives/edgar/data/1969928/000121390025120275/0001213900-25-120275-index.html).

## Completed price and source audit

Hosted run [37409948746](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37409948746) succeeded. Reproducible inputs and per-stock/per-episode outputs are saved locally under `outputs/mechanism-audit-37409948746`.

- 540 audit symbols; 420 independently discovered firm candidates. Reference and friend symbols extend the **audit roster only** and cannot select the independent warning population.
- All 137 reference tickers and all 60 friend short-sale tickers have some provider bars. Independent firm evidence was found for 65 reference tickers and 13 friend tickers. Those overlaps are not advance detection rates.
- 28 roster symbols have no provider bars. TJGC additionally has no valid old-symbol interval during the 2025 audit; MCTR is a separate historical row.
- 220 of 230 reference events have date-specific closing data; 187 show at least a 20% prior-close decline on that date. This does not verify the reference's reported intraday percentage figures.
- 6,145 distinct closing-collapse episodes across 2023–2025: 561 short-burst ramps, 553 modest ramps, 435 extended ramps, 863 recovery bounces, 3,290 without a measured recent pump and 443 with insufficient feature history. These are price episodes, **not 6,145 proven frauds**. No recent pump does not rule out an older campaign.
- 2,274 stock-linked news records, potentially linking one article to several stocks. Every queried group was pagination-limited. A missing article means incomplete coverage, not no news or promotion.

The comparison below is restricted to independently discovered firm evidence available before the decision, price above $3 and the hard symbol exclusions. Historical market cap, halt intervals, borrow and full SMG security eligibility are unverified. Consequently this is **partial-scope recall**, not executable whole-market recall.

| Watch / confirmation rule | Collapse episodes with advance warning | Sampled three-session warning precision | Symbol-days flagged |
|---|---:|---:|---:|
| Four chart confirmations combined | 88 / 873 = 10.08% | 27 / 299 = 9.03% | 779 |
| Short ramp with volume gate | 371 / 873 = 42.50% | 174 / 1,188 = 14.65% | 3,549 |
| Short ramp without volume gate | 542 / 873 = 62.08% | 343 / 3,380 = 10.15% | 10,155 |
| Longer 63-session ramp watch | 268 / 873 = 30.70% | 156 / 1,717 = 9.09% | 5,183 |
| Short or longer ramp watch | 559 / 873 = 64.03% | 360 / 3,861 = 9.32% | 11,619 |

The broad combined watch covered at least one episode for 203 of 241 partial-scope tickers. That does not mean every episode was caught or that 84% of all reference/friend trades were identified. Warning windows are sampled on nonoverlapping three-session blocks; episode recall asks whether a warning preceded the episode within three sessions. Their numerators and denominators deliberately differ. Outcomes are closes, not assured pre-close short fills.

| September 8–December 5 season | Combined watch episode coverage | Sampled window precision | Symbol-days flagged |
|---|---:|---:|---:|
| 2023 | 28 / 48 = 58.33% | 19 / 115 = 16.52% | 343 |
| 2024 | 58 / 84 = 69.05% | 37 / 283 = 13.07% | 859 |
| 2025 | 100 / 169 = 59.17% | 59 / 738 = 7.99% | 2,257 |

These comparisons use already inspected periods. There is no fresh holdout or new portfolio profit result in this warning experiment. The previously reported 2025 $103,258.54 historical portfolio profit is a separate reused-period experiment; it is not proved repeatable by these numbers.

## Repairs and efficient implementation

The historical identity parser now handles invisible whitespace, a period inside a quoted ticker, and explicit approval to list the issuer's own shares. Mere application, reserved symbols and customer listings remain insufficient. Parsed cache version v4 retries old negative results. Tests also enforce news creation/revision cutoffs, independent selection and dated former-auditor treatment.

Cache-only run [37409766543](https://github.com/Dirtyhandgernades/Dudebot/actions/runs/37409766543) succeeded: the same 1,720 reviewed documents produced 647 candidate source records versus 484 previously; unresolved identity/exchange records fell from 978 to 755. There were zero new downloads and 344.38 seconds of source processing. These are source records, not that many new stocks. The 540-symbol market audit uses the earlier source snapshot; the additional reprocessed records have **not** been included in its reported market results. There are still 3,559 deferred source downloads.

The final market audit reused cached price/news data and made four new provider requests. No paid service, order execution, confidence sizing or live policy was enabled. All 249 tests passed, and hosted CI passed at commit `72d5b62`. The frozen prospective strategy's implementation/config fingerprints remain unchanged.

## What the evidence supports next

Keep a persistent broad firm-watch queue, then distinguish **watched**, **timing evidence**, **eligible/borrowable**, and **executable entry**. Firm associations alone should not trigger a large short. A longer ramp improves coverage but increases stale watches; stricter daily confirmations miss most collapses and do not solve timing alone.

Before a new predictive version, finish dated current/former firm relationships, historical security/symbol intervals, actual float and financing events, and complete targeted news archives for missed cases and matched non-dump controls. Alpaca provides historical news, but the bounded retrieval here is incomplete. [Alpaca historical-news documentation](https://docs.alpaca.markets/us/docs/historical-news-data).

Missing historical borrow inventory cannot be inferred from today's shortable flag. Preserve unavailable labels, collect the daily archive going forward and test detected versus executable outcomes separately. Use intraday structure only where the original observation time and free-feed delay are documented. Evaluate any new combined features on untouched dates and issuers, including false warnings, squeeze losses and costs; freeze a new version before prospective comparison.

The present work finishes the broad research/audit and the historical identity repair. It does **not** finish reliable dump-date prediction, validate $70k–$100k profit per game, or establish that all manipulation is publicly predictable. The active frozen forward experiment stays intact while that evidence is collected.
