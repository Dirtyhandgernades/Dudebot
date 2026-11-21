import hashlib,json,sys,zipfile
from datetime import datetime,timezone
from backtest.obsidian_candidate_pipeline import build
with zipfile.ZipFile(sys.argv[1]) as z:
 raw=z.read("outputs/backtest/free-quant-44864611244.json")
 packet=json.loads(raw)
 original=json.loads(z.read("outputs/backtest/free-quant-board-44864611244.json"))
 sha=hashlib.sha256(raw).hexdigest()
 for label,clock in [("original-board-clock",datetime.fromisoformat(original["created_at"])),("actual-receipt",datetime.now(timezone.utc))]:
  board=build(packet,clock,sha)
  assert board["denominator"]==139
  assert set(board["requested_symbols"])==set(packet["requested_symbols"])
  assert not board["recommendations"] and not board["delivery_verified"]
  print(label,clock.isoformat(),board["classification_counts"],board["publication_role"])
 print("packet",sha,packet["finished_at"])
 print("original board hash",hashlib.sha256(z.read("outputs/backtest/free-quant-board-44864611244.json")).hexdigest())
 row=board["rows"][0]
 print("sample",row["ticker"],"rank available",row["trained_rank_available"],"classification",row["classification"],"execution",row["executable"])
 print("downstream",board["position_review_status"],"metrics",board["performance_metrics"])
