"""Research-only two-provider same-symbol same-session daily-close comparison.
Vendor daily bars are NOT authenticated exchange official-close receipts.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from urllib import request, parse, error

SYMBOLS = ("AAPL", "FPI", "JDZG", "HDSN", "CDZI")
SESSIONS = ("2026-10-27", "2026-10-28")
OUT = Path("outputs/backtest/obsidian-two-provider-close-reconciliation.json")
def get(url, params, token):
    address=url+"?"+parse.urlencode(params)
    req=request.Request(address,headers={"User-Agent":"OBSIDIAN-research-only/1.0"})
    try:
        with request.urlopen(req,timeout=18) as response:
            body=response.read(150000)
            status=response.status
    except error.HTTPError as exc:
        body=exc.read(15000)
        status=exc.code
    except Exception:
        return {"http_status":None,"error":"NETWORK_UNAVAILABLE","body_sha256":None,"payload":None}
    digest=hashlib.sha256(body).hexdigest()
    try:
        payload=json.loads(body)
    except ValueError:
        payload=None
    return {"http_status":status,"body_sha256":digest,"payload":payload}
def error_info(obj,token):
    if not isinstance(obj,dict): return "NON_JSON_OR_UNEXPECTED"
    code=str(obj.get("code",obj.get("status","UNSPECIFIED")))
    # Never output raw provider messages: some echo key/query strings.
    return "PROVIDER_CODE_"+code[:24] if code.replace("_","").isalnum() else "PROVIDER_ERROR"
def main():
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    mkey=os.environ.get("MASSIVE_API_KEY","")
    tkey=os.environ.get("TWELVE_DATA_API_KEY","")
    result={"mode":"RESEARCH_ONLY_NOT_AN_ORDER","captured_at_utc":now,
      "sessions":list(SESSIONS),"symbols":list(SYMBOLS),"comparison_tolerance_usd":0.005,
      "provider_groups":["MASSIVE","TWELVE_DATA"],"rows":[],
      "official_exchange_close_verified":False,"corporate_action_basis_verified":False,
      "independent_underlying_exchange_feed_verified":False,
      "outcome_scoring_eligible":False,"trade_authorized":False,
      "limitations":["Vendor daily bar close is not authenticated 16:00 ET official close",
        "Both vendors may redistribute overlapping underlying feeds",
        "No verified corporate action adjustment or symbol security identity",
        "Historical retrospective bars cannot establish prospective signal timing"]}
    for symbol in SYMBOLS:
        for day in SESSIONS:
            row={"symbol":symbol,"session":day,"providers":{},"absolute_difference_usd":None,
                 "within_tolerance":None,"both_bars_present":False,"eligible_official_close":False}
            if mkey:
                a=get("https://api.massive.com/v1/open-close/"+symbol+"/"+day,{"adjusted":"false","apiKey":mkey},mkey)
                obj=a.pop("payload")
                a["close"]=obj.get("close") if a["http_status"]==200 and isinstance(obj,dict) and isinstance(obj.get("close"),(int,float)) else None
                a["adjustment_requested"]="false"
                a["provider_status"]=str(obj.get("status","UNKNOWN"))[:20] if isinstance(obj,dict) else "UNAVAILABLE"
                row["providers"]["MASSIVE"]=a
            else: row["providers"]["MASSIVE"]={"error":"SECRET_ABSENT"}
            if tkey:
                b=get("https://api.twelvedata.com/time_series",{"symbol":symbol,"interval":"1day","start_date":day,"end_date":day,"outputsize":"1","apikey":tkey},tkey)
                obj=b.pop("payload")
                bars=obj.get("values",[]) if isinstance(obj,dict) else []
                matched=[x for x in bars if isinstance(x,dict) and x.get("datetime")==day]
                try: close=float(matched[0]["close"]) if matched else None
                except (ValueError,TypeError,KeyError): close=None
                b["close"]=close
                b["returned_date"]=matched[0].get("datetime") if matched else None
                b["provider_status"]=str(obj.get("status","UNKNOWN"))[:20] if isinstance(obj,dict) else "UNAVAILABLE"
                if close is None: b["diagnostic"]=error_info(obj,tkey)
                b["adjustment_basis"]="UNVERIFIED"
                row["providers"]["TWELVE_DATA"]=b
            else: row["providers"]["TWELVE_DATA"]={"error":"SECRET_ABSENT"}
            x=row["providers"]["MASSIVE"].get("close")
            y=row["providers"]["TWELVE_DATA"].get("close")
            if x is not None and y is not None:
                row["both_bars_present"]=True
                row["absolute_difference_usd"]=round(abs(x-y),6)
                row["within_tolerance"]=abs(x-y)<=0.005
            result["rows"].append(row)
    result["both_bar_count"]=sum(x["both_bars_present"] for x in result["rows"])
    result["matching_bar_count"]=sum(x["within_tolerance"] is True for x in result["rows"])
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("x") as f: json.dump(result,f,sort_keys=True,indent=2)
    print(json.dumps({"mode":result["mode"],"both_bar_count":result["both_bar_count"],
      "matching_bar_count":result["matching_bar_count"],"total":len(result["rows"]),
      "official_exchange_close_verified":False,"outcome_scoring_eligible":False,
      "artifact":str(OUT)},sort_keys=True))
if __name__=="__main__": main()
