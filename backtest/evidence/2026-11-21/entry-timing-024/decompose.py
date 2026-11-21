import gzip,json,sys,zipfile
from collections import defaultdict
from statistics import median
with zipfile.ZipFile(sys.argv[1]) as z:
 p=json.loads(gzip.decompress(z.read("firm-timing-inputs.json.gz")))
 events=json.loads(z.read("2025-hybrid-signals.json"))
labels={(r["day"],r["ticker"]):r["group"] for r in json.load(open(sys.argv[2]))}
groups=defaultdict(list)
for day,batch in events.items():
 i=p["sessions"].index(day)
 for e in batch:
  raw=p["raw"][e["ticker"]]; adj=p["split"][e["ticker"]]
  span=p["sessions"][i:i+4]
  if len(span)!=4 or span[-1]>"2025-12-05" or any(d not in raw or d not in adj for d in span):continue
  decision=e["decision_price"]; close=raw[day]["c"]
  pre=1-close/decision
  post=max(1-adj[d]["c"]/adj[day]["c"] for d in span[1:])
  group=labels[day,e["ticker"]]
  groups[group].append((pre,post))
  if group=="miss": print(day,e["ticker"],"decision to close short return",round(pre*100,3),"subsequent max close decline",round(post*100,3))
for group,rows in sorted(groups.items()):
 print(group,len(rows),"median decision-close short return",round(100*median(a for a,b in rows),3),"already down 20%",sum(a>=.2 for a,b in rows),"subsequent median favorable",round(100*median(b for a,b in rows),3))
