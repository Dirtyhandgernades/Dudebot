import gzip,json,sys,zipfile
from collections import Counter
from statistics import median
with zipfile.ZipFile(sys.argv[1]) as z:
 p=json.loads(gzip.decompress(z.read("firm-timing-inputs.json.gz")))
out=[]
with zipfile.ZipFile(sys.argv[2]) as z:
 for year in (2023,2024,2025):
  for policy,target in (("top_half_30pct",50000),("top_quartile",30000)):
   for case in ("base","stress"):
    r=json.loads(z.read(f"backtest/target-rank-2026-10-05/{year}-{policy}-{target}-{case}.json"))
    records=[]
    for t in r["trades"]:
     series=p["split"][t["ticker"]]
     days=[d for d in p["sessions"] if t["entry_date"]<=d<=t["exit_date"]]
     if any(d not in series for d in days):
      records.append(dict(ticker=t["ticker"],signal=t["signal_date"],unknown=True));continue
     peak=max(series[d]["c"]/t["adjusted_entry"]-1 for d in days)
     rec=dict(ticker=t["ticker"],signal=t["signal_date"],unknown=False,adverse=peak,pnl=t["pnl"],exit_reason=t["exit_reason"])
     if t["exit_reason"]=="STOP_SIGNAL_PREVIOUS_CLOSE":
      prior=p["sessions"][p["sessions"].index(t["exit_date"])-1]
      rec["trigger_adverse"]=series[prior]["c"]/t["adjusted_entry"]-1
      rec["cover_adverse"]=series[t["exit_date"]]["c"]/t["adjusted_entry"]-1
      rec["cover_change"]=series[t["exit_date"]]["c"]/series[prior]["c"]-1
     records.append(rec)
    stops=[t for t in records if "cover_change" in t]
    severe=[t for t in records if not t["unknown"] and t["adverse"]>=.2]
    item=dict(year=year,policy=policy,cost=case,closed=len(records),unknown=sum(t["unknown"] for t in records),severe=len(severe),stops=len(stops),worse_cover=sum(t["cover_change"]>0 for t in stops),median_cover_change=median([t["cover_change"] for t in stops]) if stops else None,rows=records)
    out.append(item)
    print({k:v for k,v in item.items() if k!="rows"})
json.dump(out,open(sys.argv[3],"w"),indent=2)
