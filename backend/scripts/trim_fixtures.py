"""One-off fixture trimming script (raw -> trimmed, utf-8 no BOM)."""
import json
from pathlib import Path

FIX = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

tw = json.loads((FIX / "twse_warrantStock_raw.json").read_text(encoding="utf-8"))
trimmed = {k: v for k, v in tw.items() if k != "data"}
trimmed["data"] = tw["data"][:200]
(FIX / "twse_warrantStock.json").write_text(json.dumps(trimmed, ensure_ascii=False), encoding="utf-8")

tp = json.loads((FIX / "tpex_warrant_raw.json").read_text(encoding="utf-8"))
(FIX / "tpex_warrant.json").write_text(json.dumps(tp[:200], ensure_ascii=False), encoding="utf-8")

tq = json.loads((FIX / "tpex_warrant_daily_quts_raw.json").read_text(encoding="utf-8"))
(FIX / "tpex_warrant_daily_quts.json").write_text(json.dumps(tq[:200], ensure_ascii=False), encoding="utf-8")

for f in ("twse_warrantStock_raw.json", "tpex_warrant_raw.json", "tpex_warrant_daily_quts_raw.json"):
    (FIX / f).unlink()
print("fixtures trimmed ok")
