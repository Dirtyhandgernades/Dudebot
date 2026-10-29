"""Stock Market Game public-rule / private-account evidence separation.

No login, orders, position lookup, credential use or inferred borrow. Passing
public-rule checks alone NEVER equals a confirmed SMG shortable symbol.
"""
from datetime import datetime,timezone
from urllib.parse import urlparse

PUBLIC_RULES="https://views.smgww.org/rotg.html"
MODE="RESEARCH_ONLY_NOT_AN_ORDER"


def check(symbol, public, account=None, observed_at=None):
    if not isinstance(symbol,str) or not symbol.strip():
        raise ValueError("TICKER_REQUIRED")
    if not isinstance(public,dict):
        raise ValueError("PUBLIC_RULE_INPUT_REQUIRED")
    issues=[]
    def positive(value):
        return type(value) in (float,int) and value>0
    exchange=public.get("exchange")
    if exchange not in ("NASDAQ","NYSE"):
        issues.append("NOT_A_CONFIRMED_NASDAQ_OR_NYSE_SMG_LISTED_SECURITY")
    if public.get("stock_security_class_verified") is not True:
        issues.append("COMMON_STOCK_OR_STOCK_CLASS_NOT_VERIFIED")
    prev=public.get("previous_regular_close")
    now=public.get("decision_day_price")
    if not positive(prev) or not positive(now):
        issues.append("PRICES_NOT_INDEPENDENTLY_VERIFIED")
    elif prev < 3 or now < 3:
        issues.append("SMG_3_DOLLAR_PREVIOUS_OR_CURRENT_PRICE_BLOCK")
    if public.get("price_sources_independently_checked") is not True:
        issues.append("PUBLIC_PRICE_PROVENANCE_NOT_VERIFIED")
    cap=public.get("market_cap_usd")
    if not positive(cap):
        issues.append("MARKET_CAP_UNKNOWN")
    elif cap < 25_000_000:
        issues.append("SMG_25M_MARKET_CAP_BLOCK")
    if public.get("capitalization_independently_verified") is not True:
        issues.append("SHARE_COUNT_AND_CAPITALIZATION_UNVERIFIED")
    quantity=public.get("proposed_shares")
    if quantity is not None and (type(quantity) is not int or quantity < 10):
        issues.append("SMG_MINIMUM_TEN_SHARES_BLOCK")
    if public.get("halt_source_checked") is not True or public.get("halt_unresolved") is not False:
        issues.append("EXCHANGE_HALT_NOT_EXCLUDED")
    acct=account if isinstance(account,dict) else {}
    if acct.get("platform")!="SMG":
        issues.append("NO_AUTHENTICATED_SMG_ACCOUNT_EVIDENCE")
    if acct.get("blocked_symbol_checked") is not True or acct.get("blocked_symbol") is not False:
        issues.append("SMG_BLOCKED_SYMBOL_NOT_EXCLUDED")
    if acct.get("security_table_validated") is not True:
        issues.append("SMG_SECURITY_TABLE_NOT_CONFIRMED")
    if acct.get("margin_account_short_enabled") is not True:
        issues.append("SMG_ACCOUNT_SHORT_PERMISSIONS_NOT_CONFIRMED")
    if acct.get("available_equity_verified") is not True:
        issues.append("ACCOUNT_AVAILABLE_EQUITY_NOT_CONFIRMED")
    if observed_at is None or not isinstance(observed_at,datetime) or observed_at.utcoffset() is None:
        issues.append("DECISION_TIME_NOT_RECORDED")
    account_at=acct.get("checked_at")
    if not isinstance(account_at,str):
        issues.append("ACCOUNT_CHECK_TIMESTAMP_MISSING")
    else:
        try:
            checked=datetime.fromisoformat(account_at.replace("Z","+00:00"))
            if checked.utcoffset() is None or observed_at is None or checked>observed_at or (observed_at-checked).total_seconds()>900:
                issues.append("ACCOUNT_EVIDENCE_STALE_OR_FUTURE")
        except (ValueError,TypeError):
            issues.append("ACCOUNT_CHECK_TIMESTAMP_INVALID")
    if acct.get("source_read_only_authenticated") is not True:
        issues.append("ACCOUNT_CHECK_NOT_INDEPENDENTLY_ATTESTED")
    return {
        "ticker":symbol.upper().strip(),"mode":MODE,
        "public_rules_reference":PUBLIC_RULES,
        "public_rules_compatible_assuming_inputs_valid":not any(
            x in issues for x in (
            "NOT_A_CONFIRMED_NASDAQ_OR_NYSE_SMG_LISTED_SECURITY",
            "SMG_3_DOLLAR_PREVIOUS_OR_CURRENT_PRICE_BLOCK",
            "SMG_25M_MARKET_CAP_BLOCK","SMG_MINIMUM_TEN_SHARES_BLOCK")),
        "account_checks_documented_without_external_verification":not issues,
        "smg_actual_shortability_independently_confirmed_by_module":False,
        "eligible_to_call_executable":False,
        "trade_authorized":False,
        "issues":sorted(set(issues)),
        "alpaca_or_other_broker_shortability_never_proves_smg":True,
    }


def batch(symbols, public_records, account_records=None, decision_at=None):
    if not isinstance(symbols,list) or len(symbols)!=len(set(symbols)):
        raise ValueError("UNIQUE_SYMBOLS_REQUIRED")
    pa=public_records if isinstance(public_records,dict) else {}
    ac=account_records if isinstance(account_records,dict) else {}
    output=[check(symbol,pa.get(symbol,{}),ac.get(symbol),decision_at) for symbol in symbols]
    return {"mode":MODE,"requested":len(symbols),"rows":output,
            "actual_smg_platform_verification_available":False,
            "verified_executable_shorts":None,"real_trades_or_orders":None}


if __name__=="__main__":
    raise SystemExit("NO_ACCOUNT_OR_EXECUTION_AUTOMATION_ALLOWED")
