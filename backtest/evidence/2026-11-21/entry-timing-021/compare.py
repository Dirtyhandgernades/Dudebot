import gzip
import json
import sys
import zipfile
from collections import Counter
from datetime import date
from statistics import median

with zipfile.ZipFile(sys.argv[1]) as archive:
    packet = json.loads(gzip.decompress(archive.read("firm-timing-inputs.json.gz")))
days = packet["sessions"]
with zipfile.ZipFile(sys.argv[2]) as archive:
    for case in ("base", "stress"):
        suffix = f"/forensics/2025-BASE-{case}.json"
        run = json.loads(archive.read(next(n for n in archive.namelist() if n.endswith(suffix))))
        changes = []
        status = Counter()
        forgone_wins = avoided_losses = 0.
        for trade in run["trades"]:
            day = trade["entry_date"]
            future = days[days.index(day)+1:days.index(day)+3]
            confirmation = future[0] if future else None
            entry = future[1] if len(future)==2 else None
            exit_day = trade["exit_date"]
            ticker = trade["ticker"]
            raw = packet["raw"][ticker]
            adjusted = packet["split"][ticker]
            if entry is None and exit_day > days[-1]:
                status["unknown exit horizon"] += 1
                continue
            if entry is None or entry >= exit_day:
                reason = "expired by original exit"
            elif any(d not in adjusted for d in (day, confirmation)):
                status["unknown confirmation"] += 1
                continue
            elif adjusted[confirmation]["c"] >= adjusted[day]["c"]:
                reason = "expired on confirmation"
            else:
                if any(d not in raw or d not in adjusted for d in (day,entry)):
                    status["unknown entry"] += 1
                    continue
                old, new = raw[day]["c"], raw[entry]["c"]
                if abs(old-trade["entry_price"]) > 1e-6 or abs(new/old-adjusted[entry]["c"]/adjusted[day]["c"]) > 1e-5:
                    status["unknown price basis"] += 1
                    continue
                length = lambda d: (date.fromisoformat(exit_day)-date.fromisoformat(d)).days
                saved = run["borrow_rate"]*(old*length(day)-new*length(entry))/365
                delta = trade["shares"]*((new-old)*(1-run["cost_bps_each_way"]/10000)+saved)
                status["entered"] += 1
                changes.append(delta)
                continue
            status[reason] += 1
            pnl = trade["pnl"]
            forgone_wins += max(pnl,0)
            avoided_losses += max(-pnl,0)
            changes.append(-pnl)
        print(case, dict(status), "net delta",round(sum(changes),2),"median",round(median(changes),2),"forgone wins",round(forgone_wins,2),"avoided losses",round(avoided_losses,2))
        if case == "base":
            categories = Counter()
            for event in run["signal_events"]:
                i = days.index(event["signal_date"])
                span = days[i:i+4]
                bars = packet["split"][event["ticker"]]
                if len(span)!=4 or span[-1]>"2025-12-05" or any(d not in bars for d in span):
                    categories["unknown"] += 1
                    continue
                p = [bars[d]["c"] for d in span]
                categories[(min(p[1:])/p[0] <= .8000000001,p[1]<p[0],p[3]/p[2] <= .8000000001)] += 1
            print("original target, lower close, target from delayed entry by original expiry",dict(categories))
