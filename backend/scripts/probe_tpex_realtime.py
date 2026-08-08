import json
import re

import requests

h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

r = requests.get("https://www.tpex.org.tw/zh-tw/mainboard/trading/info/pricing.html", headers=h, timeout=20)
paths = set(re.findall(r'["\'`]([^"\'`]*?(?:quote|Quote|REAL|real|Price|price)[^"\'`]*?(?:\.json|\.jsp|api|\.php|\.do)[^"\'`]*?)["\'`]', r.text))
print("pricing.html paths:", sorted(paths)[:15])
print("---swagger---")
s = requests.get("https://www.tpex.org.tw/openapi/swagger.json", headers=h, timeout=20)
try:
    j = s.json()
    eps = list(j.get("paths", {}).keys())
    print("endpoints:", len(eps))
    for e in eps:
        if "warrant" in e or "Warrant" in e:
            print(" W:", e)
    for e in eps:
        if "quote" in e.lower() or "real" in e.lower() or "intra" in e.lower():
            print(" R:", e)
except Exception as exc:
    print("swagger parse err", exc, repr(s.text[:120]))
