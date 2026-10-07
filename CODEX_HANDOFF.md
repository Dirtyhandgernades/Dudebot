# Dudebot continuation handoff

## October6: confirmed season target and year-balanced source rebuild

User clarified$70k+PERSEASON with eachtradeheld1–3sessions, not$70kin3days.
Current source/price audit shows real asymmetry:2023/24/25knownfirm symbols
189/268/515; source records327/324/657; priortraining141/686/1730.
Completehistory symbol-days9255/12830/22963, ofwhichrawpriorprice>3 only
1706/2753/7720 (18.4%/21.5%/33.6%). No-game-price counts31/52/125 include
not-yet-listed/renamed/delisted/invalidsymbols, not all pure download failures.
Matched pre2023 sourcecohort2025profit~$11.7k vsfull75.5k: newer issuers/dated
discoveries drive much ofthegain; do not claim missingdataalonecausedall gaps.

Found concretecollectionbias: game_firm_replay's nightly gather searchedNEW
2025filings only and depended on old cached sources for prior years. It now
gives2021–2025independent resumable querycursors,12pages/year,balanced slices,
roundrobin sourceprocessing andequalnewdoc quotas(maxdocs//5). Reportsactual
per-yeardownloads/reviews andpendingcoverage. Gather-only no longerdownloads
unused/expiringhistorical baselineartifacts. Existinglive rules/weights unchanged.

Research-only entries extendD.Boral toEFHuttonLLC/E.F.HuttonLLC (samelegalentity
rebrandNov8,2024,officialD.Boralnotice) and WWCpunctuation. Rawsourcepartyname
retained, duplicatesdeduped; no unrelated1980sHuttonbrand, no liveentitiesedit.
This is disclosed retrospective identity research, not a claim the2024identity
noticewas known2021. Existing hard exclusions remain. New balanced_packet
quarantines conflictingCIKs/tickerreuse, retains earliest actually sourced
dates, fillsmissingolderprices with rawrevision/splitunit checks. References/
friendtickers NEVERselectnew sources/prices.

New balanced-research.yml collects200documents(40/year), mergesindependent
sources with existingpacket, fills earliertraininghistory, replays2023–25
with SAME trailing2yearlookback, tests allcheckpoint/timing variants andaudits
remainingcoverage. Cached old minute queries primepersymbol caches so changing
auniverse doesn't force everyalready-fetchedsymbol toredownload. Max500new
minute requests; no Discord/order secrets or live policy change. Pinned live
benchmark/corpus remain untouched until validation. Tests304expectedafter
finalcheck; source rebuild/replay resultsnotyet available. Usertarget NOTyet
consistentlyvalidated. See outputs/backtest/year-coverage/summary.json.

## Verified final hosted repair cycle

On5c059e4: full evidence/archive37558699573 SUCCEEDED (legacy alert included),
CI37558699433 SUCCEEDED, daily-adaptive37558700071 SUCCEEDED. Daily status
FROZEN_CHALLENGER_STAGED adaptive-f844e351924316621181; active_modelnull,
fresh_outcomes0, historical_probability59episodes. Artifacts under
outputs/verification-37558700071. This verifies repaired hosted workflow;
do not claim every futureGitHubfailure impossible or that the fallback code
path necessarily ran (no per-transport log). PracticeSENT receipt remains
1557198276921393235 from37555586890. First actual market sessionOct7pending.
Next meaningful work is fresh prospective timing/probability/outcome evidence,
not repeatedly tuning inspected2025to force a higher advertised return.

## October6evening: large-state API denial fallback

Immutable restore repair run37557745033 passed archive/enrich/ranked/timing
steps, but the LEGACY alert checkpoint still got genericGitHub403. No confirmed
subtype; do not call it a rate limit. Added a same-credential compressedGit
fallback ONLY after a403ACCESS_DENIED write AND read-only metadata confirms
the remote file still has the original expectedSHA. Git fetches current branch,
checks that sameblob guard, uses an isolated index preserving other files,
creates a commit on that parent and makes an ordinary fast-forward push.
Never forcepush/adopt a changed file/bypass branch rules. The actualcheckout
HTTPSremote must match the configuredrepo. It uses checkout's existing token;
stdout/stderr and secrets are not printed. Same-run memo remembers recovered
transport to avoid repeating rejected Base64 uploads. Terminal failures stop
same-process retries. This is a transport workaround, not relaxed policy.

Latest contracts ranked-firm-2026-10-07-v5 / firm-shadow-2026-10-07-v6;
prior versions archived, sameweights/screen/horizon/probabilityreference.
No actual live-session forecasts yet (market stillclosed).301tests passed,
including mockedGit tree/isolated-index/no-force protections. Await hosted
evidence/archive validation of the fallback; Discord practice alreadySENT.

## October6evening: verified GitHub state failure and guarded repair

While testing timing sidecar, live evidence run37556348137 failed at archive-enrich
withHTTP409, then ranked finally-checkpoint withHTTP403. Daily37556436282 and
practice/Discord succeeded; this was a persistence problem, not proof of a
Discord outage. Exact historical409/403subtypes weren't logged; don't claim
a confirmed rate-limit or stale-cache root cause merely from the status.

Storage now resolves object metadata then downloads the immutable Git blob,
verifies itsSHA before replacing local SQLite, and requestsno-cache. Same-run
memo still avoids repeated downloads. On failed write it reconciles read-only:
accept exactdesired remote bytes; onlyretry409once if remote still equals the
original expectedSHA, retaining that guard; never adopt another writer'sSHA.
Terminal failure is remembered so finally cannot hammer the same mutation.
HTTP adds bounded transientGET retries, at least1s between GitHub mutations,
safe secondary-limit/SHA-conflict classification without logging token/body.
Secondary limit withoutRetryAfter is NOTretriedearly. Sources: GitHub official
RESTcontents/blob and APIbest-practices docs.300tests pass including CAS,
concurrent writer, lost acknowledgement, corruptedblob and read interruption.

Explicit contracts now ranked-firm-2026-10-07-v4 and original
firm-shadow-2026-10-07-v5, archived v3/v4 respectively; weights, firstsession,
calibration evidence and exclusions unchanged. No live-session forecasts existed
before these protocol changes. Earlier staged challenger retires/restages on
context change, not a hidden live model change. Latest source hashes published.

## October6: practice verified and timing research continued

Simplified-card practice37555586890 SUCCEEDED and Discord receiptSENT,
message1557198276921393235, channel1546733107846324254. Two explicit practice
embeds, mentionsdisabled; stored research card plus a labeled sizing illustration.
CI37555586860 and Cloudflare deployment37555586867 succeeded. Adaptive37555631612
succeeded: new source-context challenger adaptive-3a103b0c5053c8d07e31 STAGED,
not promoted; empirical probability reference59episodes. Live ranked lane's
first actual market session remainsOct7; do not call a practice receipt an
observed qualified live recommendation. ClientdateOct6; receiptUTC01:09Oct7
isOct6Central20:09.

User then explicitly asked to keep improving timing. Cached4-policy research
in backtest/firm_timing_study.py, outputs/backtest/firm-timing-2026-10-06:
baseline2023/24/25 profits3373.47/40180.81/75549.15;
current-only180.98/36682.90/38142.37 (2023zero trades;interestonly);
prior<=0%180.98/41211.79/91047.33;
prior<=+2%2859.18/41211.79/95491.11.
Last rule stress2211.40/28100.19/60770.48;2025drawdown14.630%base/19.661%stress.
It retains7filled20%dump hits in2025 with38trades vsbaseline7/44. It loses
one of2023's only2trades and regresses that sparse year's profit15.25%, so
the established minimum2trades/no>10%regression gate forbids live promotion.
Do not silently relax gates or market a reused2025result as consistent profit.

Added smg.timing_shadow prospective sidecar, shared state queue, no provider
requests or orders. Records all four keep/reject decisions on base-qualified
preclose events BEFORE outcomes; review saves immutable policy outcomes and
issuer-nonoverlapping paired-paper comparisons. It validates its own published
source contract and cannot change alerts or active models. Evidence workflow
captures eachlive scan; daily-adaptive reviews and repeats the cached4-policy
comparison eachweekday. Core v3/v4 fingerprints are unchanged by this research
sidecar.295tests pass. Follow evidence until a justified new policy can pass
all validation; no artificial probabilities or forced daily trades.

## October6: simple cards, empirical probability and bounded paper shares

User requested simple Discord cards, actual historical drop probability
alongside strength, exact paper share sizing, more capital on well-supported
strong firm setups, and an explicitly authorized practice upload.

`smg.trade_card` gives ticker/firm flag, short rationale, strength0–99,
historical20% closing-drop probabilities for1/2/3 sessions,50% target reference,
uncertainty/sample count,1–3-session maximum hold and exact integer paper shares.
Strength is NOT a probability. Weights firm35/chart25/prior rank15/pump-volume10/
fresh checks10/news2.5/FINRA context2.5. Missing/future context adds no points.
FINRA short volume is context, never a borrow or misconduct finding.

Probability corpus:59 issuer-nonoverlapping independently sourced timestamped
preclose entry episodes,51 issuers, no reference/friend ticker selection. Pooled
Jeffreys estimates20%drop1/2/3 sessions:5.8%/10.8%/19.2%;3-session approximate
Wilson95% interval10.7–30.4%;50%within3sessions7.5%. Fixed rank bands require30
episodes/5issuers or explicitly fall back to the pooled firm-setup reference.
It is not live-calibrated stock-specific certainty. Rolling past-matured-only
2025 probability backtest24forecasts:3d predicted18.7%,observed25%,Brier.2006.
All previously inspected periods and historical eligibility/borrow limits
remain explicit. See outputs/backtest/drop-probability/summary.json.

Nightly adaptive review now stores immutable drop labels and updates the
empirical reference from new base-qualified entries. It cannot use intraday
lows or a later rug to call an earlier closing-entry trade profitable.
Suggested sizing assumes$100k equity/$150k FREE buying power (not a connected
SMGaccount):targets10k/20k/50k;30%equity cap,20%reserve,$5fee,30bpsentry friction,
minimum10shares. Largest tier requiresfirm+strength>=80 AND >=35% estimated
3d20%drop with lower interval>=20%; a high score alone does NOT unlock it.
Quotes are delayed, closing fill/existing holdings unknown. This reduces weaker
paper suggestions within the existing validated cap; no trading orders or
new probability-based simulation sizing is enabled. Watches allocate0.

Notify and forming-watch cards share the simpler format. Practice uses stored
evaluation as WATCH plus a clearly marked sizing-math illustration, no mentions
or actual order. Unique receiptpractice-simple-probability-2026-10-06-v1.
Ranked contract explicitly versioned to v3;v2 archived. Original entry model,
firstOct7session,hard exclusions and frozen originalv4 remain unchanged.
Old staged challenger is retired/restaged on source-context change; do not
pretend it was promoted.293 local tests pass; published hashes updated.

## October 6: autonomous daily research, replay and gated promotion

User explicitly authorized automatic research/backtesting/improvement daily.
New `.github/workflows/daily-adaptive.yml` runs each weekday23:55UTC (18:55
Central during daylight time,17:55 in winter), shared serialized state queue.
It refreshes bounded completed live prices, reuses a single immutable cached
historical bundle, replays2023/24/25 and writes full reports. No Discord webhook
or order API is available to the research job. Historical replay itself makes
ZERO provider requests. Existing daytime SEC discovery/news/fundamental
enrichment remains the automatic source research; do not claim a new LLM news
researcher or news-trained model. Inputs have pinned SHA256 hashes.

`smg.adaptive_firm` trains three disclosed profit-policy logistic recipes with
L2=.02/.1/.5 and median threshold selected on prior training only. Historical
timestamped corpus was prefiltered by the incumbent rank, so the only allowed
automatic live change is an EXTRA rank filter on already fully qualified firm
signals, never a replacement universe, looser rules, bigger sizes or orders.
All losing variants remain in reports. First historical gate selectedL2=.5:
base profits2023/24/25 $3,373.47 /$41,569.54 /$74,537.40; aggregate full-stress
improvement $2,313.71. Other two recipes rejected. This is conditional,
reused-history evidence, not certified profit or an untouched test.

One challenger stays frozen in durable `adaptive_staged`. Base-qualified
decisions (including later rejected ones) and challenger scores are recorded
BEFORE outcomes. Completed3-session policy labels and higher-cost labels are
saved immutably before the90-day provider cache rolls off. Missing inventory
or prices are unknown. Training takes only matured observations strictly
before creation date. Candidates incorporate new costed paper outcomes.

Automatic promotion requires all3-year base/stress/same-trade gates, >=50
fresh issuer-nonoverlapping decisions, >=10 issuers, >=20 sessions, >=20 kept
and10 rejected outcomes, positive kept net returns, positive paired base and
stressed improvement, and improvement in both chronological halves. Subsequent
challengers must beat the CURRENT active model's validated paired decisions,
not only the original baseline. Retrain daily; start another frozen challenger
after25 additional training outcomes. A >=10-outcome paired regression rolls
back to the original fully gated strategy; model/context changes also roll back.
Each lifecycle event and exact model id is persisted. No calibrated confidence
or confidence sizing is introduced. Old frozen experimentv4 is untouched.

Published base ranked contract now `ranked-firm-2026-10-07-v2`, source fingerprints
updated for the explicit adaptive extension; v1 archived underconfig/experiments.
Read-only remote state check found ZERO ranked contracts/observations and ZERO
forward forecasts before versioning. First session remainsOct7.287 tests pass;
local full daily replay ~3seconds,0 provider requests. See
`backtest/AUTOMATIC_IMPROVEMENT.md` and outputs/backtest/daily-adaptive-first.

Hosted first full cycle37538298985 SUCCEEDED on7066661; CI37538249984 also
SUCCEEDED. Durable challenger adaptive-8b797d36e3d29902c3a9 was STAGED, trained
3868 available costed historical outcomes through2025-12-05. Active modelnull,
fresh live outcomes0, orders0, replay requests0. Reports downloaded to
outputs/daily-adaptive-37538298985. Do not call this a live promotion. Updated
the existing local first-session verification heartbeat for v2/daily-adaptive.

## October 6: live verification follow-up and failure isolation

Verified Cloudflare workflow_dispatch cadence at 15-minute intervals on main
02cfe65. Latest runs37534345097 and37536081899 succeeded. Earlier runs37532549257
and37523132196 failed in the legacy alert command with GitHub HTTP403
(ACCESS_DENIED);37521324397 had HTTP500. Do not relabel these as rate limits or
claim their API cause is repaired. The default Actions success condition also
skipped the later evidence/ranked steps. Those independent steps now explicitly
run unless cancelled, retaining shared state serialization, SHA guards and
visible failed job status. Nightly backfill/learning similarly survive earlier
review failure. Seven focused workflow/policy tests pass; no model changes.

Local heartbeat `dudebot-first-live-session-verification` checks this chat daily
at18:45 America/Chicago, reports meaningful delivery/failure/outcome changes,
and should pause after the post-Oct12 three-session report. It requires the
desktop app/computer to be available; hosted bot scheduling remains Cloudflare
and GitHub and does not depend on this follow-up. First ranked policy date is
stillOct7; today's inactive result is expected. Verify actual live receipts
and future closes when available, not before. Preserve frozen fingerprints.

## October 6: ranked firm layer approved and enabled for October 7

Read `backtest/RANKED_FIRM_DEPLOYMENT.md`. User explicitly authorized judging
backtest quality and deployment without further approval. Approved ranked
pre-close exhaustion because all three seasons are positive in base, full
stress and identical-trade stress, with stressed drawdown <25%; rejected early
and return/core variants despite some larger 2025 results. This is gated
advisory notification, not orders or calibrated confidence sizing.

Final corrected checkpoint replay 37516775704 succeeded, reused cache with
ZERO new requests (initial whole-session minute gather used424 requests once).
PRECLOSE_ONLY base profits2023/24/25: $3,373.47 /$40,180.81 /$75,549.15;
full stress $2,179.15 /$27,004.55 /$35,622.07; base trades2 /18 /44.
2025 ending $175,549.15. Worst stressed drawdown22.919%. Sparse2023 sample
and historical eligibility/borrow/cap/halts remain limitations; do not claim
certified executable profits, untouched tests, 70% capture or guaranteed90k.

`config/ranked_firm_alerts.json` enabled, first session2026-10-07, policy
ranked-firm-2026-10-07-v1. Model trained4013 prior daily observations /457
positives, latest label2025-12-05; threshold0.43827250876096624, training
median rank not probability. Source fingerprints include the exact published
implementation. Do not edit these policy inputs after registration without
a new version. Old failed `firm_timing_trade_alerts_enabled` remains false.

`smg.ranked_firm --prepare`: batch prior daily bars, rolling cache, prioritizes
firm shortlist. `--send`: current delayed5Min actual candles, formal source/
game/halt/borrow gates, early forming-watch embeds with no mentions, qualified
short-entry phase alerts in validated pre-close window. Hard exclusions and
free SIP16m delay preserved. Watches are explicitly not trade recommendations.
Ticker/side/phase claims shared with existing sender; no ambiguous retries.

Nightly `smg.action_learning` learns policy returns and tail losses from
separate basis/contract groups, never silently retunes deployed weights.
New ranked observations and cache share future outcome review; no new provider
request for fitting. Proposed candidate models remain research-only. Full
early price/market/focus enrichment run37502827341 made only4 requests:
7335 earlier raw symbol-days added for59 issuers already public before2023,
plusSPY context which never enters the candidate universe. 2023–25 return
models failed consistency; all variants and failures preserved in artifacts.

Fixed price-only alias correction: adjusted volume divides by price scale,
VWAP multiplies by it; old packets upgrade once via repair_legacy_volume.
Borrow/halt archive receipt timestamps no longer assume request-start access.
Frozen original experiment v4 startsOct7; source changes versioned before
any forecast existed. Read-only nightly review keeps empty superseded versions
explicit and does not bypass populated changed contracts.

276 tests passed; enabled policy fingerprint test added (277 tests). Main
commit67a430c matches published ranked implementation; preflight45b7c65.
Message-free production preflight37518437950 SUCCEEDED:98 structurally screened
firm candidates, two daily +two intraday requests, no delivery, zero orders.
Results86 review-required /8 market-not-confirmed /4 halted exclusions;48
prior prices below model scope,38 unavailable fresh minute windows,6 rank
rejections,2 no current setup. No current trade was invented to pass the test.
CI and enabled policy fingerprint tests pass (277 tests). First-session startup and fresh
three-session outcomes cannot be asserted in advance. Existing daily archive,
ranked scan steps and nighttime feedback workflow are installed.

## October 6: repair cycle and wider timing replay

Read `backtest/REPAIR_RESULTS_2026_10_06.md`. 265 tests pass. Verified repairs:
same-day post-close role exclusion; news pagination resumes past cached pages
and preserves articles when batches change; unknown future bars retain earlier
candidates; next-close timing; CIK-disjoint issuer tests and overlap purging;
BREA -> SLMT Oct3 dated price continuity and warm-up without old-symbol
post-rename selection; strict actual boolean/active-approved asset borrow gates.

Two live failures (37492353072 / 37494177550) were GitHub HTTP403, exact subtype
not retained. State was 16 MB. GitHubState now restores raw bytes in one call,
computes the Git blob SHA, caches identical same-run successful checkpoints,
skips no-op writes and preserves conflicting-write protection. Short hinted
GET rate limits retry; mutations / permission failures / long waits do not.
CI 37496712776 and fixed live/archive 37496712779 succeeded; archive failures
empty, current asset indications 134 available / one unavailable. Practice
37497135644 SENT embed-v1, message 1557069379341123708, mention-free.

New hosted dataset 37495259370: 623 audit symbols / 515 independently sourced
identities / 6,728 closing episodes / 5,740 stock-linked news rows / 57 missing
provider histories. Only four price + capped40 news requests. Artifacts under
`outputs/mechanism-audit-37495259370`. FINAL updated local study is
`outputs/backtest/repair-final-37495259370` (14,016 observations / 317 sampled
symbols / 27 unavailable future labels retained). Hosted study inside the
artifact predates final sizing/state code; do not quote it as the final result.

Base net profits 2023 / 2024 / 2025:
core $34,527.74 / -$16,238.78 / $134,327.78;
expanded $37,305.62 / -$4,187.39 / $78,189.90;
cooling guard -$2,612.00 / $12,687.91 / $15,062.31.
Expanded SAME-BASE-TRADES cost-only stress $20,144.20 / -$41,702.65 /
$31,426.23. Full higher-cost portfolio paths select different later positions
and can be nonmonotonic; do not imply higher borrow improves the strategy.
Strict historical evidence: zero trades / $100k, not validated executable
profits. Selected next-close entry-window hits expanded29.41% /16.67% /30.16%.
All reused years; all new candidate models blocked from live deployment.

Sizing now reserves 20% BEFORE an order. A fill overshoot is recorded, never
retrospectively cancelled by an assumed target (would be hindsight). Actual
buying-power rejection remains separate. Original simulator defaults preserve
buffer1.0 for old comparisons; new study / forward paper profiles use1.2.
No calibrated confidence sizing, orders or paid provider was enabled.

Forward v3 `firm-shadow-2026-10-07-v3` frozen before Oct7; v1/v2 archived in
config/experiments. Live state download verified zero forecasts before
migration. Empty changed contracts report SUPERSEDED_EMPTY_CONTRACT;
populated changed contracts remain blocked. Weights/threshold unchanged;
new hash manifest includes state/transport/borrow and repaired simulator.
First full Oct7 target label can mature Oct12. Do not edit frozen files without
a NEW version after publication. Existing nightly archive/review stays active.
Future data cannot be claimed fixed/available today. See report for residual
current/former firm, cap/float/borrow/halt/SMG/news and consistency gaps.

## October 6: full roster mechanism research completed

Read `backtest/MECHANISM_FINDINGS.md` and research-only
`backtest/mechanism_taxonomy.json`. Hosted audit 37409948746 succeeded;
local artifacts are `outputs/mechanism-audit-37409948746`, including
`audit-inputs.json.gz`, stocks/episodes CSV and JSON, reference checks,
firm rates and separate 2026 examples. Roster 540 / independent symbols 420;
6,145 closing-collapse episodes, not confirmed frauds. All 137 reference
and 60 friend short tickers have some bars; 220/230 reference dates have
close data, 187 have >=20% prior-close declines. 28 price histories missing.

Partial scope is price >$3, prior independent public firm evidence and hard
symbol rules; historical cap/halt/borrow/full SMG eligibility are unverified.
Broad short-or-63-session ramp watch: 559/873 episodes (64.03%) preceded by
a warning, but 360/3,861 sampled windows (9.32%) meet next-three-session 20%
close decline; 11,619 symbol-days flagged. SMG seasonal coverage/precision:
2023 58.33%/16.52%, 2024 69.05%/13.07%, 2025 59.17%/7.99%.
Four stricter chart confirmations combined: 10.08% recall / 9.03% precision.
No new portfolio profit result, fresh holdout claim or live activation.

Source identity parser accepts explicit issuer listing approval and quoted
ticker punctuation, normalizes invisible whitespace, rejects mere application
or customer listings. Parsed cache v4 retries old negative v3 results.
Cache-only run 37409766543 succeeded: same 1,720 reviewed docs, 647 candidate
records (was 484), unresolved 755 (was 978), zero downloads, 344.38 seconds.
This newer source snapshot is NOT included in the above market audit; next
source-coverage replay must explicitly use it. 3,559 documents still deferred.
CI 37409766530 passed, local 249 tests passed for 72d5b62.

Verified TJGC is MCTR renamed effective Dec 10, 2025, notice public after
the opening. Keep MCTR in the Sep–Dec5 game; do not reset IPO age or use TJGC
retroactively. Lineage saved in `backtest/issuer_lineage.json`, forensic only.
DTCK's OneStop engagement ended Aug30,2024, replaced by AOGB; old audit
reports must not imply current engagement. Research audit has dated correction;
live frozen implementation is unchanged. WCT later labels WWC previous auditor;
replacement interval remains a gap. Do not infer wrongdoing from firm names.

Frozen forward implementation/config files remain unchanged. Any production
relationship/timing model changes need a new experiment version, not edits
that break the existing published fingerprint. Longs remain review-only.

## October 5: all five validation work streams implemented

See `backtest/VALIDATION_AND_FORWARD_PLAN.md`. Offline audit/export:
`python -m backtest.complete_validation`; reports at
`outputs/backtest/validation-2026-10-05`. Audit uses distinct three-session
20% closing decline episodes, never after-drop advance signals. 2025 reasons:
315 price-below-$3, 39 firm evidence not yet public, 157 no setup or unavailable
old minute provenance, 9 missing signal histories, 3 ranking rejections,
1 selected without position, 7 with a position. Full corpus: 531 episodes;
this is not whole-market eligible recall or proof of a 20% profitable entry.

Nonoverlapping calibration: 172 windows in 2024 / 419 reused 2025 evaluation
windows. Brier 0.2263 raw ->0.0985 calibrated, versus ~0.101 constant base
rate. Confidence sizing is disabled; calibration gains are modest and no
80%/90% prediction claim is supported.

`config/frozen_forward.json` freezes the prior-trained rank for prospective
October 6–December 5 research. `smg.shadow` checks immutable semantic config
and implementation hashes; it captures only actual pre-close delayed quotes,
logs gaps, separates current eligibility/borrow from detection, and never
places orders or sends messages. Prior regular-session minute features are
derived from scanner downloads without extra API calls. They differ from
historical daily-provider training; prospective validation is required.

Nightly `review` now exports forward counts, mature outcomes, calibration
gate and two conditional paper portfolios. Raw/split close data are collected
for new forward symbols; missing raw entry prices are not imputed. Open paper
positions are retained between reviews. Fixed profiles: $30k/25% equity cap
and $50k/30% cap; both $100k initial / $150k assumed buying power. No live
confidence or firm timing activation. First full three-session outcome for
an October 6 forecast is October 9, not yet available at implementation.

Historical source gather has a bounded gather-only mode and earlier-year
priority. Weekday-night workflow cap is 200 new documents, six-minute parsing budget;
it resumes caches and does not repeat market/profit runs. New minute audits
record per-symbol failure/setup reasons. Data coverage remains incomplete.

Local verification: 241 tests passed. Do not change the frozen source/config
files without a new experiment version; a fingerprint mismatch blocks shadow
capture/review while normal alerts continue. Documentation-only changes do
not affect the policy hash. Tests use fixtures and are not new market outcomes.

Hosted commit 17b7af6: CI 37399904375, intraday 37399904292, source replay
37399904321, Cloudflare 37399904307 and practice 37399904339 succeeded.
Live archive 37399904325 registered the frozen contract, correctly outside
the forward window. Review 37399952559 confirmed zero forecasts / zero mature
outcomes / confidence gate NOT_READY. Artifacts downloaded to local
outputs/hosted-validation-37399904325 and -37399952559. The first gather
37399950644 was cancelled while queued without steps; switched research
runner to ubuntu-22.04, multi-pending queue and gather-only push behavior.
Replacement gather 37400698858 succeeded: 200 new documents, source work
66.91 seconds, reviewed 1,720 (was 1,520), extracted candidate source records
484 (was 414), verified dated firm records 300, records before 2025 179.
Outstanding: 3,559 deferred sources, 978 unresolved identity/exchange records.
Outputs: `outputs/backtest/gather-37400698858`. No new trade/profit claim;
frozen weights unchanged. CI 37400675267 also succeeded for 39280f2.

## October 5: chronological fast-dump rank and learning corrections

See `backtest/FAST_DUMP_RANK_RESULTS.md`. Fixed calendar continuity in
`risk_model.samples` (seasonal December–June gaps cannot create labels) and
purged labels that mature after a fold cutoff. The live learning review now
uses the next three actual exchange sessions, reports missing bars, leaves
partial negatives pending, uses unrounded 20% labels, and excludes incomplete
current-day daily outcomes.
One timestamped feature snapshot per symbol/lane/day is retained for future
forward learning; missing later quotes preserve its original observation time.
No additional provider requests or per-scan history growth is introduced.

`backtest.target_rank_research` uses the independently gathered packet's firm
dates; 233 mappings differ from the older discovery-decisions file.
Chronological model training, fixed top-quartile training-score entry gate,
hold three, target $30k: 2023 +$2,859.18 (one trade; 98 training samples /
4 positives), 2024 +$35,277.28 (14 trades), 2025 +$67,549.55 (26). Stress:
+$2,211.40 / +$26,233.91 / +$49,488.44. Twenty-percent drops within three
sessions: 0/1, 5/14, 5/26. No calibrated confidence, no robust 2023 sample.

Fixed $50k target (same 25% decision-equity cap) lifts 2025 profit to
$76,849.99 but worsens 2024 profit/drawdown. It is a sensitivity, not a live
switch. All 54 portfolios/model cutoffs saved at
`outputs/backtest/target-rank-2026-10-05`. All years reused; fresh holdout and
historical eligibility/borrow gaps persist. Live firm timing remains disabled.

The broader top-half training-score entry gate with $50k target and a fixed
30% decision-equity cap produced 2023 +$18,658.11 (3 trades), 2024
+$39,124.52 (16), 2025 +$103,258.54 (36; ending $203,258.54). Stress profits:
+$16,487.95 / +$25,305.11 / +$64,020.56. Base drawdowns: 3.059%, 25.691%,
19.966%. Twenty-percent closing declines within three sessions: 1/2, 5/16,
6/35; season-end entries are censored. The conditional 2025 target is met
in this aggressive inspected-data sensitivity; reliable $90k seasons and
massive-dump prediction remain unproved. Default allocation cap remains 25%.
Local verification: 230 tests passed.

## October 5: consistency candidate and timing audit

See `backtest/CONFIRMATION_RESULTS.md`. Added a research-only observed-price
confirmation filter: decision quote <=102% of prior raw close. Baseline firm
signals and live rules are preserved; pre-close workflow records this as an
additional comparison. Three-session confirmed profits: 2023 +$18,622.15
(2 trades), 2024 +$20,700.90 (17), 2025 +$36,482.87 (32). Stress remains
positive: +$17,313.34 / +$9,298.25 / +$14,648.23. The filter is motivated
by reused data and requires fresh validation; 2023 has only two trades.

Forward timing is now measured independently from hold limit and realized
profit. Confirmed 20% closing-price drops within 1/2/3 sessions in 2025:
1/32, 1/30, 3/30; any lower close within three sessions: 23/30. Two terminal
entries are censored. These are simulated entry counts, not live alerts or
calibrated prediction probabilities. The baseline had 9/53 twenty-percent
drops within three sessions. Confirmation improves portfolio consistency but
removes some fast rugs; do not claim the rug detection or $189k target achieved.

Also tested retaining continuing-up-move signals at fixed half target. Base
profits are positive across 2023–2025, but 2024 stress loses $12,157.45, so
it is not promoted. Optional per-signal position scales are validated (finite,
0–1) and applied before share sizing; no percentage confidence is inferred.

Reproduce with `python -m backtest.confirmation_comparison`. All 36 results
and ledgers are local at `outputs/backtest/confirmation-2026-10-05`; tests
pass 224. Existing production config still disables firm timing trade alerts.

## October 5: SMG accounting replay

Added optional SMG daily cash-interest accounting to `smg/swing_backtest.py`:
positive cash earns 0.75% annualized and negative cash is charged 7%
annualized between simulated sessions. Existing research defaults remain
unchanged; the pre-close replay now enables this mode and records
`interest_pnl`. The implementation is covered by the full local suite: 221
tests passed.

Using the existing independently discovered hybrid firm-watch signals and the
same $100,000 start / $150,000 buying-power assumption, with $30,000 target
positions and risk controls enabled:

- 2023 base: ending $113,780.91 (+$13,780.91), 6 closed trades.
- 2024 base: ending $89,073.70 (-$10,926.30), 32 closed trades.
- 2025 base: ending $175,079.35 (+$75,079.35), 56 closed trades.
- Stress (100 bps slippage, 100% borrow): 2023 $109,676.60; 2024
  $72,367.08; 2025 $136,345.66.

The fixed friend-style concentration sensitivity (risk controls disabled,
still with SMG cash interest) did not validate the $189,000 target across
periods. A $30,000 target ended 2025 at $185,626.10 but ended 2024 at
$121,028.51; $40,000 ended 2025 at $165,966.04; $50,000 ended 2025 at
$178,204.88 and raised 2024 drawdown to 32.356%. These are research
sensitivities only and do not justify enabling unbounded sizing. The $189,000
goal and 70% firm-watch coverage remain unmet; no performance claim should be
made from the 2025 result alone.

Hold-period sensitivity with the guarded $30,000 policy was also run without
changing production behavior. Five sessions produced the strongest 2025
result at $190,525.87 (+$90,525.87, 49 closed trades, 14.171% drawdown), but
the same fixed rule lost $10,052.33 in 2024; seven sessions ended 2025 at
$189,156.59 and lost $20,780.68 in 2024. The 2025 five-session result is
therefore a candidate research configuration, not a validated live switch.
Its largest 2025 realized shorts were DTCK (+$23,491.02), MSGY (+$22,561.32),
SWAG (+$9,302.74), ZDGE (+$8,829.46), and SCLX (+$7,651.70). These are
observed replay outcomes, not guarantees or evidence that any issuer is
fraudulent. The live policy remains hold-three until multi-period validation
improves.

Selecting the hold length from 2023–2024 aggregate replay profit would choose
five sessions (+$4,701 combined versus the other tested holds); its previously
inspected 2025 replay ended at $190,525.87. This is a retrospective selection
exercise, not an untouched walk-forward validation. The same 2025 run under the declared stress
case ended at $157,684.65. That retrospective result is useful evidence for a
research candidate, but it is not enough to claim a stable $189,000 outcome.

The October 5 other-year comparison is reproducible offline with
`python -m backtest.compare_cached_years`. Outputs are under
`outputs/backtest/other-years-2026-10-05`, including all twelve portfolio
replays and trade CSVs. Both three- and five-session settings are fixed across
2023–2025. Five sessions: 2023 +$14,753.85 / 6 trades / 8.918% drawdown;
2024 -$10,052.33 / 30 trades / 34.073% drawdown; 2025 +$90,525.87 /
49 trades / 14.171% drawdown. Stress profits respectively: +$10,274.64,
-$29,215.85, +$57,684.65. No simulated positions remain unresolved, but
379/569/1,311 candidate-session minute windows are missing or stale in the
source audits. Borrow evidence remains unavailable for all 7/48/90 signals.
These runs are conditional research; historical eligibility and the simulator
collateral ledger prevent calling them fully SMG-compliant executable profits.
No live strategy was enabled or changed by this comparison. Earlier-year
intraday signal packets are unavailable, so 2022 and earlier are untested.

## October 5: live repair verification

Failure annotations on runs 37370164409 / 37363838674 say GitHub never
acquired a hosted runner: no application step ran. Successful scan
37365455705 selected zero firms because all 129 stored firm watches still
had Friday reviews, which failed the 26-hour freshness gate on Monday.

The repair refreshes up to eight stale issuers before each scan, after checking
current listing and newer filings. Failed/incomplete context stays stale;
SPAC evidence survives refresh. New annual reports and amendments must
reconfirm current auditor/counsel. Borrow archive now records current evidence
for known research watches even if filing review is stale; it does not qualify
them for trading. Borrow and enrichment have time budgets and explicit gaps.
Live workflows use ubuntu-22.04; discovery also runs before the open.

The old shared single-pending concurrency group canceled waiting discovery,
practice and deployment jobs. After old deployment 37385073635 finished,
migrated ALL state writers to smg-state-writer-v2 with queue:max and
cancel-in-progress:false. Keep that common serial group. Quarter GitHub
schedules now respect CLOUDFLARE_CRON_ENABLED; daily fallbacks remain.

Completed repair scan 37385073546 refreshed/scanned eight firms: TJGC, FTFT,
RPGL, CD, GOW, PUSA, GSIW, PDC. Discord confirmed firm-watch message
1556801190488969382. 121 firms remained stale after the bounded first pass;
later scans/discovery resume. Cloudflare deployment 37385073635 succeeded.
V2 live scan 37385436221, practice 37385436217 and Cloudflare deployment
37385436271 completed successfully without queue cancellation. The live scan
selected 24 firms +4 broad names; current asset lookup succeeded for 134/135
symbols (not a borrowability count). Practice Discord receipt is confirmed
SENT as message 1556802827584806983 and persisted in immutable state commit
144a290a. Local tests: 219 Python +23 worker. Read raw state at a commit SHA
when auditing: branch raw URLs can return an older CDN-cached database.

Pre-close research run 37098678759 independently caught DTCK November 6,
2025 before its November 7 dump (+$21,389.80 conditional P&L). Portfolio
2025 +$31,736.36; 2024 -$4,711.36; 2025 stress +$3,554.66. Friend watch
coverage 13/60, trade overlap 3 and aligned entry 2. Inputs remain independent,
volume is a uniform-time projection; historical eligibility/borrow unavailable.
Files: outputs/backtest/intraday-37098678759. Pending hybrid research is saved
in stash@{0}, labeled Pending hybrid research preserved during October 5 live
repair; it was not deployed after Windows execution was interrupted.

Failed firm trade qualification remains disabled. Broad alerts are independent;
longs review-only. Profit and 70% detection targets remain unmet.

## October 2: completed bounded coverage/risk repair

See `backtest/GAME_COVERAGE_REPAIR.md` and final successful run 37081288053.
Outputs: `outputs/backtest/game-firm-37081288053`. Independent discovery now
extends through game end, admits sources after their dated evidence, and reviews
one issuer before repeated context. The 1,200-new-document gather and cache-only
corrected-parser check reviewed 1,520 sources; 415 eligible firm symbols are
independently selected. No friend/reference tickers feed discovery/simulation.
882 documents have unresolved identity; 3,759 selected documents remain unread.
Verified corporate former-name aliases remain a separate unresolved coverage gap.

2025 breakdown timing with risk controls: -$9,337.67, 111 trades, 52.248% drawdown.
Predeclared exhaustion research: +$49,504.00, 49 trades, ending $149,504;
2024 exhaustion loses $17,707.11. Cost stress reduces 2025 profit to $15,718.20.
Both remain unvalidated; do not enable firm timing alerts. Friend coverage is
13/60 before entries (target 42), exhaustion ticker overlap 3/60 and aligned
entry 1/60. Exhaustion has prior signals for 7/92 large drops, positions open
before 3/92. Friend source audit separates 42 absent, 3 classification gaps,
2 dated hard exclusions. Zero reference-event dates fall inside this game.

XHLD/WCT are below $3 throughout this 2025 game, despite prior firm evidence.
Do not confuse their 2026 examples with this period. DTCK signals November 6
but the November 7 closing fill is $1.41, so it is correctly rejected. Next
priority is a pre-close intraday/delayed-data timing validation, plus dated
issuer identification/classification, not hindsight fills or larger sizing.

Historical borrow/cap/halts/SMG availability/fees/margin remain unverified.
Ranking scores are explicitly uncalibrated; threshold precision is 18.5% in
2024 and 30.5% in reused 2025. The updated cache reuses complete per-symbol
market histories when the universe expands; failed pagination never commits
complete coverage. 206 local Python tests pass. Final hosted parser run used
zero SEC downloads and 46 market requests under the older batch cache.

## October 2: firm timing policy failed; research-only gate

The follow-up Cloudflare verification rejected a seed with HTTP 400: its JS
firm-role schema still omitted `placement_agent`, which Python now preserves.
The schema is aligned without relabeling placement agents as underwriters.
The legacy hosted refresh also now withholds all otherwise eligible names
because it lacks validated entry-timing history; eligibility alone cannot
qualify a firm trade if the paused legacy noon clock is accidentally resumed.

Run 37054630140 completed the September 8–December 5, 2025 price-proxy
replay, with SWIN/AXG exit coverage repaired and buying power declining with
marked equity. The revised live firm timing proxy lost $189,510.63 on 85
closed trades at $30k targets / three-session holds: account insolvency,
not a verified executable game balance. SMX was a $167,915.33 short loss.
The one-session diagnostic lost $21,117.41; the older adaptive comparison
gained $10,337.14 but also lost in 2024. The profit target is unmet.

Production config disables qualification by the failed firm timing policy;
verified firm research/watch embeds continue. Do not present these scores as
probabilities or promote trades from firm association alone. Broad alerts
are separate and not validated by this firm-policy report; longs stay review.
Historical borrow is unavailable for all 155 firm symbol-day signals.
Point-in-time cap/halt/game availability and margin liquidation are still
unverified. 2025 is repeatedly inspected and no longer a clean holdout.

Final outputs: `outputs/backtest/firm-validation-final`, with an 85-trade
CSV ledger and nine cached simulations. Comparison after selection finds
four friend-short ticker overlaps (ASST, MFH, MTEN, NUKK); 52 of 60 friend
short tickers are outside the 248-symbol frozen cohort, and four in-cohort
tickers have no timing trigger on the friend's entry dates. All 230 reference
event dates are outside this game, so ticker overlap is not event recall.
See `backtest/FIRM_TIMING_VALIDATION.md`; `smg.offline_firm_validation`
reproduces the results without market/API downloads. Next priorities are
independent date-indexed firm coverage and validated entry/exit/squeeze risk,
not larger sizing or optimizing repeatedly inspected 2025 to the target.

## October 1: firm coverage and prospective miss audit

Live state showed 126 stored firm watches, but only 16 selected per scan. The
latest evaluated set had no qualified firm watch, four qualified volatility
names, WCT blocked on unknown issuer classification, and XHLD stale with
non-executable current borrow. Firm discovery now prioritizes active/stale
issuers, reuses verified historical underwriter evidence when a newer filing
does not repeat it, and checks a recent annual filing for missing issuer
classification. Live selection scans up to 24 firms and four broad names.
Nothing bypasses current borrow, halt, exchange, price or market-cap gates.

The scanner now stores a dated watch census and decisions. A nightly review
compares subsequent daily closes, reports flagged/missed 20% declines and
data gaps, and prioritizes recent missed firm names for research only. This is
prospective diagnostic feedback, not online training of trade thresholds.
The daily firm-watch Discord embed is a mention-free research status even
when a volatility alert was sent. Validate GitHub CI and a live scheduled run
after deployment before claiming successful production delivery.

## September 22: live timeout repair

The first production market-day runs exposed a real ordering/runtime bug. Two
`Point-in-time evidence archive` runs exhausted the 12-minute job timeout while
performing fundamentals and three sentiment-source requests across the full stored
watchlist. Because alerting followed archiving, Discord never ran; durable state
confirmed zero evaluations and zero trade claims. The repaired workflow alerts
first, offsets cron minutes away from the top of the hour, and allows 15 minutes.
Live scanning is bounded to eight volatility candidates, 16 market-ranked firm
candidates, and eight recent strict-profile events. Current borrow rejects
unexecutable shorts before expensive minute history. Market/borrow/halt archiving
remains fast; slow SEC-cap, Finviz, Stocktwits, news and FINRA enrichment resumes in
eight-symbol batches with per-day completion keys. A source outage cannot erase the
last valid broad shortlist.

## September 20: bounded broad volatility lane

The live universe is no longer limited to supplied firms. `smg.broad_discovery`
runs two batched daily-bar passes over current SEC-mapped NASDAQ/NYSE stocks that
already pass price, cap, symbol and obvious SPAC-name filters. It prefilters pump
failures/high-volatility reversals, considers at most 3× the configured shortlist
for SEC annual/registration filing enrichment, and persists at most eight positively
classified common equities. `smg.volatility` requires stronger live confirmation
when no listed firm matches. All halt, SPAC, five-letter, user-symbol, price, cap,
freshness and Alpaca borrow gates remain hard. Firm matches receive a ranking bonus.
Trade-alert deduplication is ticker/side/phase based, so discovery in both lanes
cannot double-ping. This design adds roughly batched daily-universe requests twice
per day and only eight names to the 15-minute intraday scan.

## September 20: event-driven alerts and evidence archive

The user replaced fixed-noon stock delivery with alerts whenever a newly qualified
trade is found. `.github/workflows/evidence-archive.yml` runs every 15 minutes
across U.S. market hours, archives timestamped price/volume/asset/borrow/halt
evidence, then runs `smg.cli alert --send`. Delivery state is keyed by candidate
and market phase, checkpointed before Discord, and prevents the same continuing
signal from pinging every scan. The old noon workflow is manual-only and Cloudflare
deployment registration explicitly pauses the legacy noon alarm.

Live shorts now fail closed unless Alpaca reports tradable, shortable and
`borrow_status=easy_to_borrow`. The archive begins prospectively; historical
borrow before collection remains unavailable. SEC identity/share facts, market-cap
proxies, FINRA short volume, Nasdaq halt events, and timestamped optional sentiment
are archived separately. A 2022-2023/2024/2025 train-validation-holdout ranking
experiment was added but is not a live eligibility gate. Re-run the hosted
walk-forward workflow and inspect actual artifacts before reporting model results.

## September 19: improved replay completed

Run 35415517622 at commit 4474adb completed successfully. Artifact 10575693002
(SHA-256 1b7d64e576731c862c1412e6278e6f4aec7d727afefb1771ead7f224002bd2cc)
processed 2608/2608 sources. Common-equity/exchange parsing raised firm candidates
from 788 to 961 and decisions from 133081 to 168689. The reference comparison did
not improve: 41 conditional firm/price matches, 30 sampled nonmatches, 159
uncovered. WETH was the only changed event and became a sampled nonmatch. There
are still zero verified eligible detections.

The separately reported strict pass extracted 274 transaction candidates and
evaluated 73345/73345 decisions. All 230 reference events are NOT_EVALUABLE; no
strict decision became QUALIFIED or MATCH_EXCEPT_UNKNOWN_HALT. Most records lack
complete transaction terms, point-in-time context, or required structural facts.
Historical cap, halt, borrow, symbol interval and corporate-action certification
remain unavailable. See backtest/COMBINED_REPLAY_RESULTS.md and
backtest/combined_event_comparison.csv. Do not call conditional matches detections.

A three-period walk-forward price-outcome backtest completed in run 35453983958.
The 4-, 5- and 7-session pump-failure short variants were positive in all three
fall periods. Seven-session ending balances from separate $100k starts were
$109868.16, $111389.68 and $124096.71; sequential compounding is about $151.9k,
below the $160k-$170k objective. The long breakout rule was unstable and remains
review-only. See backtest/WALK_FORWARD_RESULTS.md. These are not verified
executable returns because historical cap, halt, borrow and SMG availability are
still gaps. The report generator and 142 local tests pass.

## September 18: identity and strict replay follow-up

Completed source replay 35395039136 processed 2608/2608 sources and 133081/133081
firm-watch decisions. See backtest/SOURCE_REPLAY_RESULTS.md and the per-event CSV:
41 conditional events, 29 sampled nonmatches, 160 uncovered. All 230 message.txt
rows matched the reference CSV. No verified eligible detections or verified misses.

Next revision fixes common-equity identity ambiguity from unit/warrant rows and
normalizes full Nasdaq exchange names and invisible table whitespace. It extracts
IPO/direct-offering transactions using the existing LocalParser, runs original
strict rules separately, and writes strict_decisions.json, strict_summary.json and
strict_event_comparison.json. This is a PARTIAL_STRICT_REPLAY: historical provenance,
cap, halt, corporate action/context evidence, monthly return and RVOL remain gaps.
Do not describe this as a completed certified packet replay. Source availability
uses filing public-at time, not extracted transaction event date. Holdout references
are read after decisions. Cache keys retain per-run suffixes because checkpoints
must grow even when code is unchanged. 140 tests pass on bundled Python; system
Python 3.14 crashed while importing exchange_calendars. Use bundled Python.


## Continuation update, September 8, 2026

September 9 UTC continuation: broader replay run 34303054242 at commit
6c0435cf7af024c7d568a376dceee9954b82d3ae is processing the independent primary
filing corpus, replacing the six-issuer-per-quarter selection. Exhibits no longer
stand in for primary reports; registered symbols override obsolete prose symbols;
registration tables supply dated common-equity mappings. Pre-window 2022 sources
are included. Runtime/checkpoints still bound coverage. Inspect the actual artifact
before claiming broader matches. 124 Python tests pass.

Cloudflare now also has a persistent weekday noon clock. Deployment registration
arms its next Pacific noon independently of GitHub. It invokes the same daily
dispatcher with atomic receipt claims. A missing, stale or empty prepared report
produces a clearly labeled status embed without a mention or stock picks. It does
not solve GitHub-dependent fresh stock preparation. Late alarms beyond the minute
are suppressed. Eight dispatcher tests cover DST, fallback status and duplicate
alarm races. Verify deployment/clock receipt before claiming the clock is armed.

Expanded daily replay completed successfully in run 34282115089 at commit
772882394821da2db10ff8177e25ff9152b6b5b7. Artifact 10078229629 contains all
6,421 planned decisions for the same 78 selected filings / 17 distinct tickers.
Comparison: 2 conditional firm/price matches (BTOG before 2024-06-28 via WWC;
MTC before 2024-05-20 via WestPark), 2 sampled without a firm/price match
(GVH and JZ: sampled prices below $3 plus missing sessions), 226 not covered.
Zero fully verified detections; misses and full detection rate remain undefined.
Historical cap, halt, later source context and symbol intervals remain gaps.
52/78 sampled filings had unresolved ticker/exchange, so discovery coverage is
the main next priority. The user benchmark of finding most examples is unmet.
Do not call this a completed full-universe backtest. The 439-decision results
below are superseded by this daily-watch run. Local outputs/backtest/daily-replay
contains the downloaded evidence; outputs/backtest/progress_report.md is updated.
Rough overall remaining effort is 50%, an estimate, not a measured progress score.

First independent replay completed: 78 filings processed, 23 candidate records /
17 distinct tickers, 439 historical decisions. Eight independently found tickers
are in the reference file: BTOG, GVH, IFBD, JBDI, JZ, MTC, TKLF, ZJYL. None of
the first-20-session-after-filing samples overlapped reference lookbacks, so no
timely detections were established. This sampling limitation is now corrected:
daily watch continues through END using the latest selected source already public
for each issuer. Inspect the next workflow's results; don't reuse the initial
439-decision batch as if it were the expanded run. Cap, halt, full context and
historical mapping gaps remain unverified and prevent eligible alert claims.

Latest user requirement: independent discovery must not read message.txt/reference
tickers to select stocks. The file is a holdout comparison. Finding most is the
benchmark, not a result already achieved. Hard DECA gates now apply to both
profiles: Nasdaq/NYSE, current price > $3, reported market cap >= $25M, minimum
opening order planning 10 shares. Missing historical market cap is a gap, never
filled using today's cap. Free current Nasdaq screener caps covered all 19 earlier
live candidates in a local data-access check. 121 Python + 5 dispatcher tests pass.

Cloudflare activation succeeded in run 34281212506. Endpoint:
https://dudebot-dispatch.dudebot-dirtyhandgernades.workers.dev
It verified storage and edited existing practice message 1546917333065408734,
then set cloud_dispatch.enabled=true in smg-state. First real noon alarm still
pending. GitHub remains the data preparer and can delay it: today's scheduled
noon run 34279293529 started at 21:12 UTC and reported MISSED_SEND_WINDOW.
Do not claim the whole pipeline is independent of GitHub or guarantees no delays.

Independent source replay run 34281212486 uses the prior 15,054-document firm
corpus, selects 78 sources across 13 quarters / 60 issuers, then screens following
sessions before reading labels. Inspect its result before claiming any matches.
This is a bounded partial source-triggered replay, not a full daily universe run.
Historical market cap, halt history, source context and symbol intervals remain
unverified. Report conditional firm/price matches separately from verified alerts.

Targeted alias audit run 34252502063 recovered same-session bars for MDJH (UOKA
label) and HRYU (GITS label). Both lacked a fresh sampled noon price. These are
retrospective data-gap resolutions, not discovery or detections.

Latest user decisions supersede the old clock instructions below: noon Pacific /
2 p.m. Central must follow local daylight-saving time. Account creation for the
free Cloudflare dispatcher is complete; API token/account-ID connection and
deployment must be verified. The optional worker moves the final send off GitHub,
but Python preparation still depends on GitHub and no zero-delay guarantee exists.
See cloudflare/README.md for deployment and current limitations.

The user requested Discohook-style embeds. Live alerts now use stock cards; the
practice command edits its existing message into an embed instead of posting twice.
Confirmed practice receipt: run 34250065854, message 1546917333065408734,
channel 1546733107846324254. Its HPAI/JBDI/LNKS/WCT overlap is present-day
research, not historical detection. 113 Python and 5 dispatcher tests pass locally.

Historical audit: 220/230 events have some sampled pre-event market bars after
wider probes. Ten retain specific gaps (renames, first trading days and de-SPACs).
Actual historical replay detections and misses are still not established. Do not
turn availability, source-only firm matches, or current ticker overlap into hits.

PR #1 merged to main as 4820eaad100e590c1d6dd8c13c83507d921f29b6.
Live activation run 34192293139 succeeded: 19 firm-watch candidates stored,
55 source records reviewed, Alpaca ACCESS_VERIFIED, and Discord receipt SENT
with message ID 1546760331131625533 in channel 1546733107846324254.
These are research candidates and an activation receipt, not stock detections.
A follow-up removes a permanent three-context-document backlog gate, caches
context review results, reserves refresh capacity and searches fresh filings
independently of backfill. 107 offline tests pass. Full historical replay remains
incomplete and must not be described as completed or profitable.

Latest user authorization: finish the bot and deploy live into Discord. Firm-first
is integrated into live discovery, Scanner and digest formatting. The new
FIRM_WATCH pipeline accepts documented issuer-level firm history without treating
it as a later direct offering. Unknown hard exclusions still suppress delivery.
Live workflows default on, with explicit repository-variable false stop switches.
An idempotent activation receipt is authorized outside noon without mentions;
stock alerts retain the original noon schedule. 105 offline tests pass. Deployment
receipt and live discovery results must be checked before claiming activation.
Prior paragraphs describing firm-first as research-only are superseded.

Development is pushed to `codex/historical-backtest`, draft PR #1. The latest
gap-resolution workflow is https://github.com/Dirtyhandgernades/Dudebot/actions/runs/34191049268.
100 offline tests pass. Initial Alpaca probes found bars for 180 events and empty
five-minute intervals for 50; `reference_gap_audit.json` records wider checks.
An empty five-minute probe is not proof of missing whole-session history.
SEC full-text HTTP 500 errors now split into smaller date ranges and preserve
checkpoints. All 27 SEC index quarters are collected; source review is incomplete.

`backtest/reviewed_firm_findings.json` verifies pre-drop IPO firm relationships for
RAYA and GDHG, covering five reference events. Their $12M and ~$7M base proceeds
fail the original strict IPO floor but are preferences under firm-first. These
source findings are not replay detections. Do not fabricate point-in-time filing
review or historical halt clearance. Actual screening replay remains incomplete.
The firm-first module is research/backtest only; production still uses the strict
entrypoint until explicitly integrated. No changes have been merged to main.

The later user clarification adds a separate firm-first research screen: one
verified listed underwriter/auditor/counsel is central; price, proceeds, geography,
IPO age, RVOL and pump status are preferences. The user explicitly reconfirmed
halts/suspensions, SPAC/acquisition corporations and five-letter tickers as hard
exclusions. Keep the original strict result alongside the firm-first comparison.
Wei, Wei & Co. has SUPER priority. Retain the existing counsel list. The supplied
message.txt exactly matches all 230 committed reference events.

The user clarified the surge threshold: retain 12%–23% gains at low priority.
The implementation now uses a 12% floor and a 23% inclusive low-priority ceiling
over the existing 21 trading sessions. This supersedes the unresolved threshold
statements below. The user also reported adding all repository secrets; provider
access must be checked by the bounded historical workflow, not assumed locally.

`smg.backtest` now collects independent SEC index leads and replays prepared
point-in-time research packets with event comparison. See `backtest/README.md`.
Full historical candidate construction, mapping, filing review and halt coverage
remain incomplete. No real detection rate or miss count is established. The
earlier handoff below remains the requirements record, not a current progress report.

Continue development of **Dirtyhandgernades/Dudebot**, a DECA Stock Market Game research notifier. The user asked to move the ongoing work into Codex after the initial implementation was published. Preserve the existing work and finish the historical backtest next.

## What the user wants next

> Backtest the bot across approximately three years of real, ordinary market history, then determine whether it found the stocks in the uploaded reference list before their listed drops.

The reference list is already committed at **`backtest/reference_events.csv`**: **230 dated events across 137 distinct tickers**, from **2024-01-03 through 2025-07-28**. Repeated symbols on different dates are intentional. The reported declines are user-supplied, unverified labels; the definition of their percentage measurement and intraday drop times was not supplied.

**No real historical replay has been implemented or run yet. No detection rate, hit count, profitability result, or claim that the bot found these events has been established.** At the handoff, `backtest/` contains the reference CSV only. The existing demo is fictional and the 59 tests verify software behavior, not investment performance.

## Published and verified

- Python notifier, free Alpaca market-data adapter, local SEC text parser, current Nasdaq halt checks, deterministic screening and ranking, evidence/rationale reports, and time-gated Discord digest.
- Independent IPO and direct-offering discovery pipelines.
- GitHub Actions for offline tests, setup checks, daily discovery, and noon delivery.
- State persistence on `smg-state`, with SHA-guarded writes and a durable claim before a Discord ping. Repeated or uncertain sends do not blindly retry.
- 59 offline tests passed locally. The published GitHub Actions run also succeeded: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/34186918206
- Verified source-code commit: `e751a4b6bd1277e3a715fed815f2ece442c5bff7` (subsequent commits add this handoff/documentation).
- No user credentials were available during development and no real Discord message was sent. Authenticated Alpaca access and live SEC/Discord integration still need smoke testing.
- The repo is public. Standard hosted GitHub Actions currently have no public-repository runner charge; do not promise all services remain free or available indefinitely.

Read `README.md`, `SETUP.md`, `VALIDATION.md`, `config/strategy.yaml`, and `config/entities.yaml` before changing behavior.

## User constraints to preserve

1. **Notification only.** No trading, order submission, account mutation, or automatic entry/exit logic.
2. **No paid AI or credit-based extraction.** No Anthropic/OpenAI/model API key and no hosted model calls in the running bot. The user chose free Alpaca after asking about Massive. Local Python rules and text parsing are the intended implementation.
3. **Separate IPO and direct-offering pipelines.** Find the qualifying transaction/issuer facts first, then apply market confirmation. Direct offerings must use their own transaction terms.
4. **Exclude halted/suspended stocks, acquisition corporations/SPACs, and every exactly-five-letter ticker independently.** A shorter ticker does not prove an issuer is not a SPAC. Do not weaken exclusions just to match reference examples.
5. **Recent IPOs:** maximum three calendar years old. Prioritize 30–100 days, then other IPOs within the past year. Original listing age must not reset with a ticker change.
6. **Any one** verified listed underwriter/placement agent, auditor, or counsel is sufficient. Categories in `entities.yaml` set priority. Historical IPO underwriter membership alone does not qualify a later direct offering.
7. **Offering price $4–$10 and base gross proceeds $15M–$30M, inclusive.** Original IPO terms for IPOs, separate transaction terms for direct offerings. Current share price is not the offering price. Share/ADS units and bundled warrants need correct treatment.
8. **RVOL at least 1.0.** Compare volume with recent months on a consistent basis. Stronger recent volume can affect context/ranking; no invented fixed 3× threshold. Current engineering implementation uses same-session-minute cumulative volume, up to 60 prior sessions, at least 20 usable sessions, and a 20-session comparison for context.
9. **Big monthly price surge for IPOs**, but the user has not supplied a numeric minimum. `surge_return_min_pct` remains null. `SURGE_RETURN_MIN_PCT` can override it. Do not silently use the demo's 100% threshold. Ask for the real number when required, or clearly label a separate sensitivity analysis without changing the production rule.
10. Reversal/exit decisions remain case by case. No requirement to wait for a reversal before recognizing a qualifying surge.
11. Discord integration requests `@everyone`, with rationale, metrics, timestamps, firm/category matches, and source links. Only send at the configured noon time, never from tests or historical replays.
12. The firm list is a research screen, not proof of wrongdoing or a guaranteed stock outcome. State matched facts directly without inventing future certainty.

## Working interpretations already visible to the user

These are the current code defaults, not grounds for silently adding new requirements:

- Nasdaq listing scope.
- China principal operations for the IPO pipeline. Direct offerings prefer operations outside the U.S./Canada but do not exclude U.S./Canadian operations.
- No three-year IPO-age restriction or mandatory monthly surge for the separate direct-offering pipeline.
- Trailing 21 trading sessions defines the monthly price-return window. Direct-offering backfill is 30 calendar days.
- Literal **12:00 PST, fixed UTC−08:00 year-round** (20:00 UTC), rather than a daylight-saving-adjusted Pacific clock. This is **1 p.m. PDT during summer**. The user said “12pm PST” but has not explicitly resolved the daylight-saving ambiguity. README explains switching to `America/Los_Angeles` and changing both cron entries.
- Free consolidated Alpaca SIP data is deliberately **16 minutes delayed**, stated in every alert. Free live IEX is single-exchange coverage and is not the default. Historical backtests should reproduce this configured delay and clock, rather than evaluate market-close data that would not yet have been available.
- GitHub schedules can be delayed or dropped. Sending is suppressed outside the configured noon minute; exact network delivery time is not guaranteed.

## Credentials and activation

The user said they would add secrets after publication. Check current setup rather than assuming they are still absent. Never ask them to paste secret values into the conversation.

| GitHub Actions secret | Value |
|---|---|
| `ALPACA_API_KEY` | Alpaca API key ID |
| `ALPACA_SECRET_KEY` | Matching Alpaca secret key |
| `SEC_USER_AGENT` | Team label plus real contact email; not an SEC-issued API key |
| `DISCORD_WEBHOOK_URL` | Incoming webhook URL for the chosen Discord channel |

Repository variables: `SMG_LIVE_ENABLED=true` enables scheduled live research; `DISCORD_ENABLED=true` enables noon pings; `SURGE_RETURN_MIN_PCT` supplies the still-unresolved monthly threshold. The two enable flags are initially unset/false. GitHub supplies `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, and `GITHUB_ACTIONS` automatically.

GitHub Actions secrets are consumed by workflows. Do not assume a separate Codex execution environment has their values. A dedicated backtest workflow can use the Alpaca/SEC secrets without exposing them. Backtesting must never require a Discord webhook or send notifications.

## Backtest work to implement

Build a reproducible historical replay, not a claim based solely on the supplied winners/losers or on synthetic tests.

1. Select and record an approximately three-year real-data window that includes every reference event. A reasonable proposed default is **2022-07-29 through 2025-07-28**, ending on the latest supplied event. This window has not yet been user-approved or executed. Include sufficient pre-window history for RVOL, monthly returns, and then-eligible older IPO prospectuses.
2. Construct a historical candidate universe independently of the supplied drop list. The current `Discovery` uses today's Nasdaq universe and latest filings; it cannot be reused unchanged as a point-in-time historical universe. Account for delisted/renamed issuers and historical exchange/CIK/share-class mappings. Report uncovered issuers and survivorship limitations explicitly.
3. Use only filing facts that were public by each simulated decision time. Prefer SEC acceptance timestamps; when only a filing date is available, a documented conservative next-day availability rule avoids same-day look-ahead. Never backfill a newly learned fact into earlier dates. Keep original IPO dates and offering terms distinct from later offerings.
4. Reuse the production rule engine and market calculations where appropriate. Replay only the permitted noon decisions and the declared 16-minute SIP delay. Handle holidays, early closes, splits, ADS ratios, missing bars, and ambiguous ticker histories.
5. Preserve the halt exclusion. **A current-day halt feed cannot verify historical status.** Nasdaq's public halt search exposes only the past year, which is insufficient for the whole requested period. Unknown historical status must remain unknown, never be fabricated as clear. Distinguish fully verified matches from matches that pass the other criteria but lack historical halt verification. Supporting historical halt records can be added with documented source/coverage.
6. Produce an event-by-event comparison with ticker/date, first prior alert date, lead time, pipeline, qualification evidence, rejection reason or missing-data reason. Do not count after-the-drop signals as advance detection. The reference has dates but no drop times, so same-day alerts cannot be assumed to precede the drop. A proposed analysis window is the preceding 20 trading sessions; label it as an evaluation parameter, not a new production rule.
7. Report event-level and distinct-symbol coverage separately, repeated alerts, unmatched reference events, extra alerts, and incomplete coverage. The list is not an exhaustive set of all market declines, so an extra alert is not automatically a false positive. Do not infer trading profit without defined entry/exit rules and costs.
8. Keep user-supplied drop percentages out of screening features and thresholds. Do not optimize the strategy to this labeled list and then present the fit as out-of-sample validation. A sensitivity table for unresolved thresholds must be clearly separate from the fixed-rule result.
9. Add meaningful tests for look-ahead prevention, timestamp/lag parity, reference matching, splits, delisted/renamed coverage, unknown halts, and missing-data reporting. Offline test success must remain separate from real replay results.
10. Add a bounded, resumable GitHub Actions backtest workflow with progress and downloadable reports. Large SEC/minute-data backfills need pagination, rate limits, caching, and persistent checkpoints. Use separate historical state so live notification/dedup state cannot be changed by the replay. Do not start an unbounded paid compute job or add a model dependency.
11. Run the real replay once the necessary provider access and numeric threshold are available, inspect failures, and deliver the actual comparison. Until then report **not run/incomplete**, not zero hits or a success percentage.

## Implementation review priorities

The initial implementation has passing tests but has not had authenticated integration validation. Review these concrete risks while adding history:

- Local extraction intentionally recognizes a limited set of filing phrases. Exact quote provenance is not proof of semantic correctness. Original-transaction scope, current versus historical roles, currency/ADS units, subsequent cancellations, and multiple offerings need stronger fixtures drawn from real public filings.
- Some historical IPO covers will not establish an actual first-trading date until a later filing. Do not substitute the prospectus date or treat a future announcement as already public.
- Current discovery can be incomplete while capped backfill is pending. Preserve backlog and expose coverage; do not label every unprocessed symbol a strategy rejection.
- Three-year full-market history is substantially larger than a targeted test on 137 symbols. Avoid claiming full-market coverage from a present-day universe or from only the reference set.
- The SQLite/GitHub Contents backend has finite file-size limits. Large bar histories should not be committed wholesale; choose bounded cached/derived records and a reproducible data manifest.
- Alpaca pagination is implemented. Historical `asof` symbol mapping and streaming/aggregation may be needed to avoid repeatedly downloading entire minute histories for each day.

## Local verification commands

```bash
python -m pip install -e '.[test]' -c requirements-tested.txt
python -m pytest -q
python -m smg.cli demo
python -m smg.cli doctor
```

`demo` and `doctor` require no credentials and do not send messages. Live discovery and scanning require the applicable secrets. Run from the repository root. `.env` is not automatically loaded.

## Technical sources already checked

- Alpaca historical data, free SIP lag, authentication, and symbol mapping: https://docs.alpaca.markets/us/docs/market-data-faq
- Alpaca bar parameters and split-adjusted price/volume: https://docs.alpaca.markets/us/reference/stockbars
- SEC public indexes and access: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- SEC APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Nasdaq halt search (past year): https://nasdaqtrader.com/Trader.aspx?id=TradingHaltSearch
- Nasdaq halt RSS: https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS
- GitHub Actions schedules: https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule

The original strategy PDF and a prior Word specification were supplied in the earlier chat, but are not required to locate the code or comparison list. The current repository configuration and this handoff preserve the implemented rules, remaining ambiguities, and next work. The earlier Word document described a superseded paid-extraction approach; do not reintroduce it.
