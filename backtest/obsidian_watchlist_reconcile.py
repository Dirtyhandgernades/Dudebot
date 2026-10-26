"""Research-only persistent watchlist reconciliation, never a trading signal.

Never silently remove a structural watch when it is absent from a ranked scan.
Missing records and missing provider bars are distinct from screened rejection.
"""
from datetime import datetime

STATES={"SCREENED_REJECTED","SCREENED_WATCH","NOT_SCREENED",
        "MISSING_DATA","RENAMED","INELIGIBLE","UNKNOWN_RECONCILIATION"}
def reconcile(watchlist, scan_rows, aliases=None):
    """Every archived ticker gets one row; unknown is not equivalent to rejected."""
    aliases=aliases or {}
    observed={}
    for row in scan_rows:
        ticker=row["ticker"]
        if ticker in observed:
            raise ValueError("DUPLICATE_SCAN_TICKER")
        if row.get("status") not in STATES-{"NOT_SCREENED","RENAMED","UNKNOWN_RECONCILIATION"}:
            raise ValueError("INVALID_SCAN_STATUS")
        observed[ticker]=row
    result=[]
    for ticker in dict.fromkeys(watchlist):
        target=aliases.get(ticker,ticker)
        if target!=ticker and target not in observed:
            status="RENAMED"
            detail="ALIAS_KNOWN_BUT_NEW_SYMBOL_NOT_SCREENED"
        elif target in observed:
            status=observed[target]["status"]
            detail=observed[target].get("reason","")
        else:
            status="NOT_SCREENED"
            detail="NO_AS_OF_SCREEN_RECORD"
        result.append({"historical_ticker":ticker,"screen_ticker":target,
                       "status":status,"reason":detail,
                       "retain_structural_watch":True})
    return result
