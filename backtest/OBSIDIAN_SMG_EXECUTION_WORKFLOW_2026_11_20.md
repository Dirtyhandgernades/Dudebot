---
title: OBSIDIAN — SMG portfolio-aware execution workflow
date: 2026-11-20
status: RESEARCH_AND_USER_APPROVED_ORDER_PREPARATION_ONLY
---

# OBSIDIAN SMG execution workflow

## Verified versus unverified
A dedicated saved TinyFish browser session was successfully tested against the authenticated SMG Account Summary, holdings, pending orders, transaction history, transaction notes, trade menu and rules. Read-only inspection succeeded; no orders were entered, canceled, modified, or submitted. Detailed authenticated order form and actual confirmation behavior have not been tested. Do not store credentials, session identifiers, team identifiers or private portfolio values in this repository. Reacquire private values at runtime from the authorized account only.

Official SMG stock trade page and help show a password re-entry requirement at confirmation. A saved login session is not authority or technical capability to bypass it. Student team remains responsible for transactions and password secrecy. Local competition rules and whether unattended outside execution is authorized remain unverified. Use user/team confirmation; do not implement unattended execution, share credentials, bypass confirmation, or claim it is active.

Sources: https://www.stockmarketgame.org/rotg_cash.html ; https://www.stockmarketgame.org/enterstock_prod.htm ; https://www.stockmarketgame.org/enter-trade_b.html ; https://www.stockmarketgame.org/transaction-notes_helpc.html ; https://www.stockmarketgame.org/content_rules.htm .

## State machine
1. READ_ACCOUNT: Account Summary, Account Holdings, Pending Orders, Transaction Notes, Transaction History. Deduplicate aggregate intraday positions versus older lots. Capture timestamp and settlement status. Check cash/equity/margin/available equity/buying power, realized and unrealized P&L. Do not treat dashboard cash as unrestricted margin.
2. DISCOVER: refresh complete research universe and retained watchlist; independently screen adverse earnings, financing, clinical and regulatory disclosures, speculative exhaustion and positive catalysts. Produce ranked primary and backup candidates even when best idea is blocked. Mark research watches separately from eligible trade candidates. Evaluate both directions with documented counterevidence, including CAPR negative FDA evidence; no unsupported binary events.
3. VALIDATE: current and prior regular-session prices >= $3 for buys and new shorts, $25m minimum market cap, whole-share minimum 10 for new buys/shorts, SMG supported stock and security table, halts, local limits, fee and available buying power. Sell/cover existing positions below $3 allowed. $5 commission per trade in current rules plus SEC fee on sales; EOD execution, no partial fills. Do not assume estimated quote equals game fill. Account-specific margin follows platform.
4. SIZE: compare candidate to existing holdings and pending exposures, preserve buffer for price/margin drift, calculate whole share quantity and estimated notional under current limits. No compulsive trade quota; give ranked alternatives when feasible, and explicit reasons if all candidates fail.
5. PREPARE_TICKET: symbol, security identity, side, integer quantity, approximate price, order type, expected session, fees, estimated resulting buying power, scenario P&L, review point, counterevidence. Link to https://www.stockmarketgame.org/eat.html . User/team reviews and confirms any actual order. Do not collect password or implement autonomous submissions.
6. RECONCILE: order intent is not executed. Record confirmation number only in private account audit, match pending row and subsequently Transaction Notes. Executed price from notes is authoritative for execution record; confirm holdings and transaction history when settlement catches up. A missing pending row is NOT proof of rejection. No blind retry on timeout or ambiguous status.
7. HANDLE_REJECTION: insufficient buying power or margin exceeded -> refresh real available buying power, compute smaller permissible whole-share proposal accounting for fees, reserve and price drift; user rechecks and confirms. Max % equity -> reduce aggregate exposure within applicable local limits. Below $3 or below $25M / blocked security -> remove from new-entry shortlist until genuinely eligible; choose verified backup, do not resize to circumvent eligibility. Invalid symbol -> verify exact issuer; invalid quantity -> correct integer shares and holding constraints. System problem or ambiguous confirmation -> reconcile Pending Orders/Notes/History first, no duplicate resubmission. If definitive rejection and corrected conditions allow, propose one corrected ticket to user. Never backdate fills.
8. POST_CLOSE: compare actual accepted/rejected and closing prices, exact gross/net costs and future +1/+2/+3 sessions. Retain failed predictions including CAPR; never use future results to retroactively alter original signals.

## Scheduling
Regular markets close 15:00 America/Chicago; prepare research sufficiently before the 14:45–14:58 CT user decision window. Thanksgiving Nov 26 no session; Nov 27 early close 12:00 CT; adjust accordingly. Game ends Dec 4, 2026. A scheduled research check is not a guaranteed real-time order service. Do not start a run too late and assume a fill before closing; after-cutoff EOD entries price next session. Saved browser session can expire; handle by notifying user for private sign-in. No live automated trades or changes to frozen models, production, main or existing alerts.

## Mandatory output
Account snapshot timestamp, current positions and pending orders, realized vs unconfirmed P&L, evidence and downside/upside scenarios, shortlist and backups with whole shares and reasons, prior actual order errors, user-confirmable order sheet, and next-session verification. Keep private account data in the private chat/workspace, not public GitHub. 
