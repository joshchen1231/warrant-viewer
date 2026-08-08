"""TPEx (OTC) warrant collector. Endpoints verified live 2026-08-08. Implements G1, INV-2, INV-4."""
from __future__ import annotations

import json
from datetime import date

import requests

from .base import CollectResult, WarrantSource, roc_date_to_iso, to_float

MASTER_URL = "https://www.tpex.org.tw/openapi/v1/tpex_warrant"
QUTS_URL = "https://www.tpex.org.tw/openapi/v1/tpex_warrant_daily_quts"

_TIMEOUT = 90


def _exercise_style(raw: str) -> str:
    s = raw or ""
    if "美" in s:
        return "AMERICAN"
    if "歐" in s:
        return "EUROPEAN"
    return s


def _warrant_type(m: dict) -> str:
    if (m.get("CallableBullOrBearStyle") or "").strip():
        return "BULLBEAR"
    if (m.get("WithCeiling-floorStyleOrNot") or "").strip():
        return "LIMIT"
    if (m.get("WithResetStyleOrNot") or "").strip():
        return "RESET"
    return "GENERAL"


def parse_master(rows: list[dict], fetched_at: str, data_date: str) -> list[dict]:
    out = []
    for r in rows:
        code = str(r.get("Code", "")).strip()
        if not code:
            continue
        ratio = to_float(r.get("LatestExercise Ratio"))
        if not ratio or ratio <= 0:
            continue
        expiry_iso = roc_date_to_iso(str(r.get("ExpirationDate") or ""))
        out.append({
            "code": code,
            "name": r.get("Name") or "",
            "market": "OTC",
            "underlying_code": str(r.get("UnderlyingCode") or "").strip(),
            "underlying_name": "",
            "call_put": "CALL" if (r.get("Call /Put") or "").upper() == "C" else "PUT",
            "exercise_style": _exercise_style(str(r.get("ExerciseStyle") or "")),
            "warrant_type": _warrant_type(r),
            "issuer": "",
            "strike_price": to_float(r.get("LatestStrikePrice")),
            "exercise_ratio": ratio,
            "listed_date": None,
            "expiry_date": expiry_iso,
            "last_trading_date": None,
            "cap_price": to_float(r.get("LatestCeilingPrice")) if "LatestCeilingPrice" in r else None,
            "floor_price": to_float(r.get("LatestFloorPrice")) if "LatestFloorPrice" in r else None,
            "reset": 1 if "RESET" in _warrant_type(r) else 0,
            "active": 1 if expiry_iso and expiry_iso >= data_date else 0,
            "source": "tpex",
            "fetched_at": fetched_at,
        })
    return out


def parse_quotes(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        code = str(r.get("Code", "")).strip()
        qdate = roc_date_to_iso(str(r.get("Date") or ""))
        if not code or not qdate:
            continue
        close = to_float(r.get("Close"))
        if close is None:
            continue
        out.append({
            "code": code,
            "date": qdate,
            "open": to_float(r.get("Open")),
            "high": to_float(r.get("High")),
            "low": to_float(r.get("Low")),
            "close": close,
            "change": to_float(r.get("Change")),
            "volume": to_float(r.get("TradeVol.")),
            "trade_value": to_float(r.get("TradeValue")),
            "underlying_close": to_float(r.get("UnderlyingStockClosePrice")),
            "source": "tpex",
        })
    return out


class TpexSource(WarrantSource):
    name = "tpex"
    market = "OTC"

    def fetch(self) -> CollectResult:
        fetched_at = date.today().isoformat()
        m = requests.get(MASTER_URL, timeout=_TIMEOUT)
        m.raise_for_status()
        master_raw = m.json()
        q = requests.get(QUTS_URL, timeout=_TIMEOUT)
        q.raise_for_status()
        quts_raw = q.json()
        data_date = str(master_raw[0].get("Date", "")) if master_raw else ""
        data_date = roc_date_to_iso(data_date) or date.today().isoformat()
        masters = parse_master(master_raw, fetched_at, data_date)
        quotes = parse_quotes(quts_raw)
        return CollectResult(date=data_date, masters=masters, quotes=quotes, source=self.name)


def parse_master_from_json(text: str, fetched_at: str, data_date: str) -> list[dict]:
    return parse_master(json.loads(text), fetched_at, data_date)


def parse_quotes_from_json(text: str) -> list[dict]:
    return parse_quotes(json.loads(text))
