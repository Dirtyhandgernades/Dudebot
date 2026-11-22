import gzip,json,sys,zipfile
from pathlib import Path
from smg.risk_model import feature_row,predict
from smg.models import Config
from smg.swing_backtest import simulate
from backtest.obsidian_strategy_lab import stats
with zipfile.ZipFile(sys.argv[1]) as z:
 packet=json.loads(gzip.decompress(z.read("firm-timing-inputs.json.gz")))
 events={y:json.loads(z.read(f"{y}-hybrid-signals.json")) for y in (2023,2024,2025)}
out=[]
with zipfile.ZipFile(sys.argv[2]) as z:
 for year in (2023,2024,2025):
  model=json.loads(z.read(f"backtest/target-rank-2026-10-05/{year}-model.json"))
  for name,target,cap,threshold in (("reduced",50000,.15,"top_half"),("quartile",30000,.25,"top_quartile")):
   selected={}
   for day,batch in events[year].items():
    i=packet["sessions"].index(day)
    for e in batch:
     x=feature_row([packet["split"][e["ticker"]][d] for d in packet["sessions"][i-22:i]])
     rank=predict(model["model"],[{"x":x}])[0]
     if rank>=model["thresholds"][threshold]:selected.setdefault(day,[]).append({**e,"historical_rank":rank})
   for hold in (3,):
    for case,bps,borrow in (("base",30,.1),("stress",100,1.)):
     r=simulate(packet["raw"],packet["split"],packet["cohorts"][f"{year}-09-08"]["short"],packet["sessions"],start=f"{year}-09-08",end=f"{year}-12-05",hold=hold,strategy="FIRM_HYBRID_EXHAUSTION_RESEARCH",cost_bps=bps,borrow_rate=borrow,position_target=target,buying_power=150000,firm_dates=packet["firm_dates"],firm_cfg=Config(**packet["config"]),risk_controls=True,signal_share_sizing=True,intraday_signals=selected,smg_cash_interest=True,max_position_equity_fraction=cap)
     if name=='quartile':
      policy="top_half_30pct" if name=="aggressive" else "top_quartile"
      archived=json.loads(z.read(f"backtest/target-rank-2026-10-05/{year}-{policy}-{target}-{case}.json"))
      assert abs(r["net_profit"]-archived["net_profit"])<1e-6
      assert r["closed_trades"]==archived["closed_trades"]
     out.append(dict(year=year,benchmark=name,hold=hold,cost=case,metrics=stats(r,packet)))
Path(sys.argv[3]).write_text(json.dumps(out,indent=2))
print("Completed",len(out),"simulations; 6 quartile archive reconciliations passed")
for row in out:
 print(row["year"],row["benchmark"],row["cost"],{k:row["metrics"][k] for k in ("net_profit","max_observed_drawdown_pct","closed_trades","profit_factor","largest_issuer_fraction_of_net_profit")})

