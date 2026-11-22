import gzip,json,sys,zipfile
import numpy as np
from smg.risk_model import samples,matured_before,fit,predict
with zipfile.ZipFile(sys.argv[1]) as z:
 p=json.loads(gzip.decompress(z.read("firm-timing-inputs.json.gz")))
 records=json.loads(z.read("discovery-decisions.json"))
rows=samples(records,p["raw"],p["split"],p["sessions"],firm_dates=p["firm_dates"])
with zipfile.ZipFile(sys.argv[2]) as z:
 for year in (2023,2024,2025):
  train=matured_before(rows,f"{year}-01-01")
  archived=json.loads(z.read(f"backtest/target-rank-2026-10-05/{year}-model.json"))
  model=fit(train)
  errors={k:float(np.max(np.abs(np.asarray(model[k])-np.asarray(archived["model"][k])))) for k in ("mean","scale","weights","bias")}
  scores=predict(model,train)
  q={k:float(np.quantile(scores,v)) for k,v in (("top_half",.5),("top_quartile",.75),("top_decile",.9))}
  error=max(abs(q[k]-archived["thresholds"][k]) for k in q)
  latest=max(r["label_end"] for r in train)
  assert latest<f"{year}-01-01"
  assert max(errors.values())<1e-10 and error<1e-10
  print(year,len(train),sum(r["label"] for r in train),latest,errors,"threshold error",error,flush=True)
