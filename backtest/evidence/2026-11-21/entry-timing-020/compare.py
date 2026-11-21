import datetime as dt, gzip, json, statistics, sys, zipfile
from collections import Counter
hybrid, lab = map(zipfile.ZipFile, sys.argv[1:3])
packet = json.loads(gzip.decompress(hybrid.read("firm-timing-inputs.json.gz")))
days = packet["sessions"]
for case in ("base", "stress"):
    run = json.loads(lab.read(next(n for n in lab.namelist() if n.endswith("2025-BASE-" + case + ".json"))))
    changes = []
    skipped = Counter()
    for trade in run["trades"]:
        day = trade["entry_date"]
        later = days[days.index(day) + 1]
        if later >= trade["exit_date"]:
            skipped["original exit reached"] += 1
            continue
        ticker = trade["ticker"]
        raw = packet["raw"][ticker]
        adj = packet["split"][ticker]
        if any(d not in raw or d not in adj for d in (day, later)):
            skipped["missing close"] += 1
            continue
        old, new = raw[day]["c"], raw[later]["c"]
        if abs(old - trade["entry_price"]) > 1e-6 or abs(new / old - adj[later]["c"] / adj[day]["c"]) > 1e-5:
            skipped["price basis mismatch"] += 1
            continue
        qty = trade["shares"]
        elapsed = lambda a,b: (dt.date.fromisoformat(b)-dt.date.fromisoformat(a)).days
        exit_day = trade["exit_date"]
        saved_borrow = qty * run["borrow_rate"] / 365 * (old * elapsed(day,exit_day) - new * elapsed(later,exit_day))
        changes.append(qty * (new-old) * (1-run["cost_bps_each_way"]/10000) + saved_borrow)
    print(case, len(run["trades"]), len(changes), dict(skipped), round(sum(changes),2), round(statistics.median(changes),2))
    if case == "base":
        groups = {}
        for event in run["signal_events"]:
            day, ticker = event["signal_date"], event["ticker"]
            i = days.index(day)
            span = days[i:i+4]
            series = packet["split"][ticker]
            if len(span)!=4 or span[-1]>"2025-12-05" or any(d not in series for d in span): continue
            p = [series[d]["c"] for d in span]
            key = "hit" if min(p[1:])/p[0] <= .8000000001 else "false alarm"
            groups.setdefault(key,[]).append((p[1]/p[0]-1, p[3]<p[0]))
        for key, rows in groups.items():
            print(key,len(rows),"median next close change",round(100*statistics.median(x for x,y in rows),3),"positive gross original at third close",sum(y for x,y in rows))
