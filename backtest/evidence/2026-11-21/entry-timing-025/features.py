import gzip,json,sys,zipfile
import numpy as np
from smg.risk_model import feature_row,predict,FEATURES
with zipfile.ZipFile(sys.argv[1]) as z:
 p=json.loads(gzip.decompress(z.read("firm-timing-inputs.json.gz")))
 events=json.loads(z.read("2025-hybrid-signals.json"))
with zipfile.ZipFile(sys.argv[2]) as z:
 m=json.loads(z.read("backtest/target-rank-2026-10-05/2025-model.json"))
labels={(r["day"],r["ticker"]):r["group"] for r in json.load(open(sys.argv[3]))}
rows=[]
for day,batch in events.items():
 i=p["sessions"].index(day)
 for e in batch:
  x=np.asarray(feature_row([p["split"][e["ticker"]][d] for d in p["sessions"][i-22:i]]))
  z=(x-np.asarray(m["model"]["mean"]))/np.asarray(m["model"]["scale"])
  contributions=z*np.asarray(m["model"]["weights"])
  score=predict(m["model"],[{"x":x}])[0]
  assert np.isclose(score,1/(1+np.exp(-(contributions.sum()+m["model"]["bias"]))))
  rows.append(dict(ticker=e["ticker"],day=day,x=x,z=z,c=contributions,score=score,group=labels[day,e["ticker"]]))
selected=[r for r in rows if r["score"]>=m["thresholds"]["top_half"]]
for r in rows:
 if r["group"]!="miss":continue
 neighbor=min(selected,key=lambda n:(np.linalg.norm(r["z"]-n["z"]),n["day"],n["ticker"]))
 diff=r["c"]-neighbor["c"]
 order=np.argsort(diff)
 print(r["ticker"],r["day"],"nearest",neighbor["ticker"],neighbor["day"],"group",neighbor["group"],"distance",round(float(np.linalg.norm(r["z"]-neighbor["z"])),3))
 print("largest negative logit differences",[(FEATURES[j],round(float(diff[j]),4)) for j in order[:3]])
print("rows",len(rows),"selected",len(selected),"threshold",m["thresholds"]["top_half"])
print("model metadata",list(m))
