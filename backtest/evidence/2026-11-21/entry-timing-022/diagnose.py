import gzip
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median
from smg.risk_model import feature_row, predict

with zipfile.ZipFile(sys.argv[1]) as z:
    packet = json.loads(gzip.decompress(z.read("firm-timing-inputs.json.gz")))
    events = json.loads(z.read("2025-hybrid-signals.json"))
with zipfile.ZipFile(sys.argv[2]) as z:
    model = json.loads(z.read("backtest/target-rank-2026-10-05/2025-model.json"))
    book = json.loads(z.read(next(n for n in z.namelist() if n.endswith("/forensics/2025-BASE-base.json"))))
selected = {(e["ticker"], e["signal_date"]) for e in book["signal_events"]}
rows = []
for day, signals in events.items():
    i = packet["sessions"].index(day)
    for e in signals:
        ticker = e["ticker"]
        series = packet["split"][ticker]
        x = feature_row([series[d] for d in packet["sessions"][i-22:i]])
        rank = predict(model["model"], [{"x": x}])[0]
        margin = rank - model["thresholds"]["top_half"]
        assert (margin >= 0) == ((ticker, day) in selected)
        span = packet["sessions"][i:i+4]
        hit = None
        if len(span)==4 and span[-1]<="2025-12-05" and all(d in series for d in span):
            hit = min(series[d]["c"] for d in span[1:])/series[day]["c"] <= .8000000001
        group = "unknown" if hit is None else ("hit" if hit else "false alarm") if margin>=0 else ("miss" if hit else "correct rejection")
        rows.append(dict(ticker=ticker,day=day,group=group,margin=round(margin,6),change=e.get("observed_change_from_prior_close"),policy=e["source_policy"],decision=e["decision_at"],cutoff=e.get("data_cutoff")))
assert len(rows)==len({(r["ticker"],r["day"]) for r in rows})==90
print(Counter(r["group"] for r in rows))
for g in ["hit","miss"]:
    sub=[r for r in rows if r["group"]==g]
    v=[r["change"] for r in sub if r["change"] is not None]
    print(g,len(v),median(v) if v else None,Counter(r["policy"] for r in sub))
    for r in sub: print(r["day"],r["ticker"],r["margin"],r["change"],r["decision"])
Path(sys.argv[3]).write_text(json.dumps(rows,indent=2)+"\n")
