import gzip
import json
import sys
import zipfile
from collections import Counter
from math import isclose
from pathlib import Path

with zipfile.ZipFile(sys.argv[1]) as archive:
    p = json.loads(gzip.decompress(archive.read("firm-timing-inputs.json.gz")))
    events = json.loads(archive.read("2025-hybrid-signals.json"))
labels = {(r["day"], r["ticker"]): r["group"] for r in json.loads(Path(sys.argv[2]).read_text())}
counts = Counter()
groups = Counter()
for day, batch in events.items():
    prior = p["sessions"][p["sessions"].index(day)-1]
    for e in batch:
        ticker = e["ticker"]
        group = labels[day,ticker]
        raw, adj = p["raw"][ticker], p["split"][ticker]
        if any(d not in bars or bars[d]["c"] <= 0 for bars in (raw,adj) for d in (prior,day)):
            counts["missing bars"] += 1
            continue
        # Same-day close is used solely to audit adjustment continuity retrospectively.
        factor = lambda d: adj[d]["c"]/raw[d]["c"]
        if not isclose(factor(prior),factor(day),rel_tol=1e-5):
            counts["basis change"] += 1
            continue
        change = e["decision_price"]/raw[prior]["c"]-1
        original = e.get("observed_change_from_prior_close")
        if original is not None and not isclose(change,original,abs_tol=1e-5):
            counts["recorded disagreement"] += 1
            continue
        counts["validated" if original is not None else "reconstructed"] += 1
        direction = "up" if change>0 else "down" if change<0 else "flat"
        groups[group,direction] += 1
        if group=="miss":
            print(day,ticker,round(100*change,3),e["source_policy"])
assert sum(counts.values())==len(labels)==90
print(dict(counts))
print(sorted(groups.items()))
