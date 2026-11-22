import json,sys
from collections import Counter
old,new=[json.load(open(p)) for p in sys.argv[1:3]]
for a,b in zip(old,new):
 assert (a["benchmark"],a["cost"])==(b["benchmark"],b["cost"])
 key=lambda t:(t["ticker"],t["signal_date"])
 x={key(t):t for t in a["trades"]};y={key(t):t for t in b["trades"]}
 assert len(x)==len(a["trades"]) and len(y)==len(b["trades"])
 common=x.keys()&y.keys()
 matched=sum(y[k]["pnl"]-x[k]["pnl"] for k in common)
 removed=-sum(x[k]["pnl"] for k in x.keys()-y.keys())
 added=sum(y[k]["pnl"] for k in y.keys()-x.keys())
 interest=b["interest"]-a["interest"]
 print(a["benchmark"],a["cost"],"matched",len(common),"removed",len(x.keys()-y.keys()),"added",len(y.keys()-x.keys()))
 print("deltas",round(matched,2),round(removed,2),round(added,2),round(interest,2),"sum",round(matched+removed+added+interest,2))
 print("exit transitions",dict(Counter((x[k]["exit_reason"],y[k]["exit_reason"]) for k in common)))
 print("matched same exit date",sum(x[k]["exit_date"]==y[k]["exit_date"] for k in common))
 print("new gaps",b["gaps"])
 print("largest paired",sorted([(round(y[k]["pnl"]-x[k]["pnl"],2),k) for k in common],reverse=True)[:3])
