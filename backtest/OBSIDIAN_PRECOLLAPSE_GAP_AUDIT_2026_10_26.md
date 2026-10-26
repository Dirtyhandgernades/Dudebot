# OBSIDIAN sharp-collapse pre-detection gap audit — 2026-10-26 14:40 America/Chicago

**Scope:** research/obsidian-early-rug-20261025 only. **No trading authorization.**
This is a source-verified *partial* reconciliation and an isolated research fix, NOT proof that the full persistent watchlist was screened or that a future >=20% collapse can be forecast.

## Evidence refreshed
- Historical recovery Actions #24: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40251252851 ; 4731 checked, 2472 timely, 2259 empty/stale, zero original ticker/date gap repairs verified.
- Corrected paired diagnostic #28: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40260569154 ; fixed -2% challenger has no proven edge on reused 2023–25.
- Most recently verified pre-audit journal CI #29: https://github.com/Dirtyhandgernades/Dudebot/actions/runs/40343287176 ; 54 offline tests passed. NEW mechanism and watchlist tests committed subsequently: HOSTED CI PENDING, do not claim passing yet.
- Research-only snapshot workflow: .github/workflows/obsidian-prospective-capture.yml ; only permitted 14:45–14:58 CT, previous #2 was gate CLOSED, no real prospective artifact yet.
- Existing capture code: backtest/obsidian_prospective_capture.py; only price-only A [-15%,-2%] and B <=-25%, all other changes were unclassified; no C, no morning/intraday/after-hours independent discovery.
- New isolated code: backtest/obsidian_early_mechanism_audit.py and backtest/obsidian_watchlist_reconcile.py; neither changes production/frozen strategy.

## Gap-by-gap findings
1. **Persistent watchlist — PARTIAL FIX / unresolved full reconciliation.** New pure reconciler never drops a historical ticker and distinguishes SCREENED_REJECTED, SCREENED_WATCH, NOT_SCREENED, MISSING_DATA, RENAMED, INELIGIBLE. The nine named historical watches below are NOT screened by this audit. Full authoritative archive, identity changes, and actual as-of scan results must be imported before any claim of complete coverage. Existing config/historical_symbol_changes.csv documents only SWIN->AXG and BREA->SLMT; it cannot justify renaming any of the nine below.
2. **Market coverage — OPEN.** Reported 57 CURRENT_PRICE_WINDOW_UNAVAILABLE out of 98 names (58.2%) is a historical audit observation needing original archive validation and ticker/date-level provider diagnosis. It is NOT evidence of absence of opportunity. Require per-symbol last successful bar, data feed, request/response clock, raw/adjusted split basis, rename lookup, error and retry outcome. Do not mark original gaps repaired.
3. **Discovery versus execution — OPEN.** Current prospective collector runs only 14:45–14:58 CT. Morning, intraday, after-hours read-only discovery must have separate as-of timestamps, and must not assert the closing execution gate is open. The isolated mechanism taxonomy can evaluate externally supplied observations, but is NOT a connected market scanner.
4. **Classification — ISOLATED FIX / NOT INTEGRATED.** New taxonomy explicitly covers -15% to -25% as INTERMEDIATE, price-only early A, exhausted B, and evidence-based C failed-breakdown LONG watches. It does NOT silently relabel an ordinary decline as an imminent collapse. All rows BLOCKED; frozen capture classifier unchanged until separate forward validation.
5. **Capital structure and saleability — OPEN.** For each ATM, note, warrant, resale or lockup, require dated filing, amount remaining, actual issuances, conversion/exercise mechanics, split basis, registration effectiveness, resale restrictions, earliest saleability, current verified shares and float, and daily dollar/stock volume. Separately record 'registered', 'issued', 'eligible for sale', and 'actually sold'; none implies the next. Do not infer actual selling from registration.
6. **AEHL diagnostic — PARTIAL SEC DOCUMENT VERIFICATION, NO CURRENT TRADE.** SEC amended 424(b)(5): https://www.sec.gov/Archives/edgar/data/1470683/000149315226048027/form424b5.htm . Filing describes up to $100M ATM (capacity, NOT executed sale), 15M warrants exercisable at $0.50 outstanding as of Oct20, 2026, and $550K remaining convertible principal as of Oct20, converting at 80% of lowest daily VWAP over the three days ending on conversion. It reports 16,459,359 Class A shares as of Sep29, 2026; 15M warrant shares equal ~91.1% of that *dated* count, NOT current verified float. It describes registration of up to 12M conversion shares; registered maximum is NOT remaining note shares, actual conversion or actual selling. Sep3 private placement issued 15M Class A shares and warrants. Need current as-of shares, warrant exercise restrictions, updated note conversions, ATM actual issuance/sales, effectiveness, float, bid/borrow, halts and breakdown tape before any promotion. Historical case is diagnostic only, never training winner.
7. **Breakdown mechanism — ISOLATED FIX / NOT MARKET-VALIDATED.** New diagnostic requires as-of failed rebound + support loss + selling volume + liquidity AND verified adverse disclosure or verified saleable supply. Firm associations alone cannot satisfy it. C requires as-of failed breakdown + support reclaim + higher low + buying volume.
8. **SMG executability — OPEN.** New taxonomy always BLOCKS. Actual current and prior regular-session price, common security type, verified cap >=25M on updated share count, corporate actions, halts, real SMG short availability and actual executable bid are missing. Alpaca shortability alone insufficient. Advisory reservations are not user holdings.
9. **Prospective proof — OPEN.** Freeze policy before independent 2026+ observations. Record all candidates/rejections, outcomes over same horizon, advance warning lead time, eligible >=20% future closing-price drops, missed collapses, false positives, squeeze losses, after-cost P&L and drawdowns. Never select the universe by future winners or optimize 2023–25.

## Timestamped named historical-watch reconciliation (14:40 CT)
No live quote, issuer status, current eligibility or borrow was independently verified in this audit. These are *watchlist retention/reconciliation* entries, not candidate recommendations.

| Historical symbol | As-of audit classification | Reason | Executable |
|---|---|---|---|
| AEHL | STRUCTURAL_WATCH / CURRENT_SCREEN_UNVERIFIED | SEC 424(b)(5) confirms financing overhang terms, not live selling or breakdown | NO |
| SVRN | NOT_SCREENED_IN_THIS_AUDIT | Current bar and eligibility unverified | NO |
| RGC | NOT_SCREENED_IN_THIS_AUDIT | Current bar and eligibility unverified | NO |
| JDZG | NOT_SCREENED_IN_THIS_AUDIT | Current bar and eligibility unverified | NO |
| SECZ | NOT_SCREENED_IN_THIS_AUDIT | Covered position is not reason to delete historical watch | NO |
| AVBP | NOT_SCREENED_IN_THIS_AUDIT | Historical miss remains in audit | NO |
| CPIX | NOT_SCREENED_IN_THIS_AUDIT | Current bar and eligibility unverified | NO |
| MELI | NOT_SCREENED_IN_THIS_AUDIT | Current bar and eligibility unverified | NO |
| TNGX | NOT_SCREENED_IN_THIS_AUDIT | Current bar and eligibility unverified | NO |

**Current actionable candidate count: 0 verified.** This is a verification limit, NOT evidence that the market has zero opportunities. Portfolio goal $160K does not alter entry criteria or position sizing.

## Required next implementation
Import the entire dated persistent watchlist and archived 98-name scan; reconcile each symbol and alias with immutable screen outcomes. Add timestamped independent discovery at morning/intraday/after-hours checkpoints (read-only), with complete universe and missingness. Attach dated SEC capital structure and verified saleability, then pre-decision technical mechanism and SMG execution checks. Preserve frozen baseline and challenger; measure all misses and false positives on genuinely untouched sessions. Keep the 14:45–14:58 CT execution window unchanged. Do not change production, alerts, secrets, orders or main.
