"""TWSE (TSE) warrant collector. G2 solved 2026-08-08: /rwd/zh/stock/warrantStock returns the
whole listed-warrant market (paging ignored). Implements G1, INV-2, INV-4."""
from __future__ import annotations

import json
from datetime import date

import requests

from .base import CollectResult, WarrantSource, roc_date_to_iso, to_float

WARRANT_STOCK_URL = "https://www.twse.com.tw/rwd/zh/stock/warrantStock"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.twse.com.tw/zh/products/securities/warrant/infomation/stock.html",
}
_TIMEOUT = 90

# field indices of the 18-column warrantStock payload
_COL = {
    "code": 0, "name": 1, "close": 2, "change": 3,
    "underlying_code": 4, "underlying_name": 5, "underlying_close": 6,
    "call_put": 8, "style": 9, "listed_date": 10,
    "last_trading_date": 12, "expiry_date": 13, "exercise_ratio": 14,
    "strike_price": 15, "cap_price": 16, "floor_price": 17,
}


def parse_payload(obj: dict, fetched_at: str) -> CollectResult:
    data_date = roc_date_to_iso(str(obj.get("date", ""))) or date.today().isoformat()
    masters: list[dict] = []
    quotes: list[dict] = []
    for row in obj.get("data", []):
        code = str(row[_COL["code"]]).strip()
        if not code:
            continue
        ratio = to_float(row[_COL["exercise_ratio"]])
        if not ratio or ratio <= 0:
            continue
        call_put_raw = str(row[_COL["call_put"]] or "")
        style_raw = str(row[_COL["style"]] or "")
        expiry_iso = roc_date_to_iso(str(row[_COL["expiry_date"]] or ""))
        masters.append({
            "code": code,
            "name": str(row[_COL["name"]] or "").strip(),
            "market": "TSE",
            "underlying_code": str(row[_COL["underlying_code"]] or "").strip(),
            "underlying_name": str(row[_COL["underlying_name"]] or "").strip(),
            "call_put": "CALL" if call_put_raw == "認購" else "PUT",
            "exercise_style": "AMERICAN" if "美" in style_raw else ("EUROPEAN" if "歐" in style_raw else ""),
            "warrant_type": "BULLBEAR" if (to_float(row[_COL["floor_price"]]) or to_float(row[_COL["cap_price"]]))
            else "GENERAL",
            "issuer": "",
            "strike_price": to_float(row[_COL["strike_price"]]),
            "exercise_ratio": ratio,
            "listed_date": roc_date_to_iso(str(row[_COL["listed_date"]] or "")),
            "expiry_date": expiry_iso,
            "last_trading_date": roc_date_to_iso(str(row[_COL["last_trading_date"]] or "")),
            "cap_price": to_float(row[_COL["cap_price"]]),
            "floor_price": to_float(row[_COL["floor_price"]]),
            "reset": 0,
            "active": 1 if expiry_iso and expiry_iso >= data_date else 0,
            "source": "twse",
            "fetched_at": fetched_at,
        })
        close = to_float(row[_COL["close"]])
        if close is None:
            continue
        quotes.append({
            "code": code,
            "date": data_date,
            "open": None,
            "high": None,
            "low": None,
            "close": close,
            "change": to_float(row[_COL["change"]]),
            "volume": None,
            "trade_value": None,
            "underlying_close": to_float(row[_COL["underlying_close"]]),
            "source": "twse",
        })
    return CollectResult(date=data_date, masters=masters, quotes=quotes, source="twse")


class TwseSource(WarrantSource):
    name = "twse"
    market = "TSE"

    def fetch(self) -> CollectResult:
        """No date param: TWSE returns the latest trading day's payload (verified 2026-08-08,
        weekend requests with an explicit date return empty closes)."""
        fetched_at = date.today().isoformat()
        r = requests.get(
            WARRANT_STOCK_URL,
            params={"lang": "zh"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return parse_payload(r.json(), fetched_at)


def parse_payload_from_json(text: str, fetched_at: str) -> CollectResult:
    return parse_payload(json.loads(text), fetched_at)
