"""UAT item-3 evidence: sample 5 warrants from DB, compare against live official payloads."""
import json
import sqlite3
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent.parent
conn = sqlite3.connect(str(ROOT / "data" / "warrant.db"))
conn.row_factory = sqlite3.Row

rows = conn.execute(
    """
    SELECT w.code, w.market, w.underlying_code, w.strike_price, w.exercise_ratio,
           w.expiry_date, q.close, q.date AS quote_date
    FROM warrant_master w JOIN daily_quote q ON q.code = w.code
    WHERE q.date = (SELECT MAX(date) FROM daily_quote)
    ORDER BY w.market, w.code
    """
).fetchall()

tse = [r for r in rows if r["market"] == "TSE"][:2]
otc = [r for r in rows if r["market"] == "OTC"][:3]
sample = tse + otc

h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.twse.com.tw/zh/products/securities/warrant/infomation/stock.html",
}
twse = requests.get(
    "https://www.twse.com.tw/rwd/zh/stock/warrantStock", params={"lang": "zh"},
    headers=h, timeout=90,
).json()
tpex_m = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_warrant", timeout=90).json()
tpex_q = requests.get(
    "https://www.tpex.org.tw/openapi/v1/tpex_warrant_daily_quts", timeout=90
).json()

twse_by_code = {str(r[0]).strip(): r for r in twse["data"]}
tpex_m_by_code = {str(r.get("Code", "")).strip(): r for r in tpex_m}
tpex_q_by_code = {}
for r in tpex_q:
    code = str(r.get("Code", "")).strip()
    if code not in tpex_q_by_code:
        tpex_q_by_code[code] = r

def _f(v):
    if v is None:
        return None
    s = str(v).replace(",", "").strip()
    if s in ("", "-", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


print("| code | field | DB | official | match |")
print("|---|---|---|---|---|")
all_match = True
for s in sample:
    if s["market"] == "TSE":
        off = twse_by_code[s["code"]]
        checks = [
            ("close", s["close"], _f(off[2])),
            ("strike", s["strike_price"], _f(off[15])),
            ("ratio", s["exercise_ratio"], _f(off[14])),
        ]
    else:
        om = tpex_m_by_code.get(s["code"])
        oq = tpex_q_by_code.get(s["code"])
        checks = []
        if om is not None:
            checks.append(("strike", s["strike_price"], _f(om.get("LatestStrikePrice"))))
            checks.append(("ratio", s["exercise_ratio"], _f(om.get("LatestExercise Ratio"))))
        if oq is not None:
            checks.append(("close", s["close"], _f(oq.get("Close"))))
    for field, dbv, offv in checks:
        if dbv is None or offv is None:
            ok = dbv is None and offv is None
        else:
            ok = abs(dbv - offv) < 0.005
        all_match = all_match and ok
        print(f"| {s['code']} ({s['market']}) | {field} | {dbv} | {offv} | {'OK' if ok else 'MISMATCH'} |")

print()
print("ALL MATCH" if all_match else "HAS MISMATCH")
