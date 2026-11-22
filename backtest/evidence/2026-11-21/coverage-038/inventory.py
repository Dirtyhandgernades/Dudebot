import gzip,json,sys,zipfile
from smg.market import calendar
with zipfile.ZipFile(sys.argv[1]) as z:
 p=json.loads(gzip.decompress(z.read("firm-timing-inputs.json.gz")))
for year in (2022,2023,2024,2025,2026):
 start=f"{year}-01-01";end=f"{year}-12-31"
 expected={str(d.date()) for d in calendar(year).sessions_in_range(start,end)}
 supplied=set(p["sessions"])&expected
 raw={d for bars in p["raw"].values() for d in bars}&expected
 missing=sorted(expected-raw)
 print(year,"exchange",len(expected),"session-index",len(supplied),"any-issuer-raw",len(raw),"missing",len(missing),"first",missing[:3],"last",missing[-3:])
 print("raw outside session index",len(raw-supplied))
