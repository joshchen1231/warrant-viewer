"""TWSE realtime warrant quotes via official mis.twse.com.tw API.

Verified live 2026-08-08: getStockInfo.jsp?ex_ch=tse_03001T.tw returns five-level
quotes JSON; multiple codes in one request joined with '|'. TSE warrants only:
TPEx (OTC) has no public free intraday source (realtime requires a contracted IP
feed; swagger endpoints are all after-hours daily/monthly) - see ticket T-008.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

REALTIME_URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_TIMEOUT = 20
_BATCH = 50
CACHE_TTL = 15.0


@dataclass
class RealtimeQuote:
    code: str
    name: str
    date: str
    ts: str
    close: float | None
    prev_close: float | None
    volume: float | None
    bid: float | None
    ask: float | None


def _f(v: str | None) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-", "--", "—"):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _first_level(s: str | None) -> float | None:
    if not s:
        return None
    parts = str(s).split("_")
    return _f(parts[0]) if parts else None


def parse_payload(obj: dict) -> list[RealtimeQuote]:
    out = []
    for m in obj.get("msgArray", []):
        code = str(m.get("c", "")).strip()
        if not code:
            continue
        out.append(RealtimeQuote(
            code=code,
            name=str(m.get("n", "")).strip(),
            date=str(m.get("d", "")).strip(),
            ts=str(m.get("%", "")).strip(),
            close=_f(m.get("z")),
            prev_close=_f(m.get("y")),
            volume=_f(m.get("tv")),
            bid=_first_level(m.get("b")),
            ask=_first_level(m.get("a")),
        ))
    return out


class RealtimeQuotes:
    """On-demand fetcher with a short memory TTL; no persistence (intraday data only)."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, RealtimeQuote]] = {}

    def get_quotes(self, codes: list[str]) -> list[RealtimeQuote]:
        now = time.monotonic()
        out: list[RealtimeQuote] = []
        miss: list[str] = []
        for code in codes:
            entry = self._cache.get(code)
            if entry is not None and now - entry[0] < CACHE_TTL:
                out.append(entry[1])
            else:
                miss.append(code)
        remaining = set(miss)
        for i in range(0, len(miss), _BATCH):
            batch = miss[i:i + _BATCH]
            ex_ch = "|".join(f"tse_{c}.tw" for c in batch)
            r = requests.get(REALTIME_URL, params={"ex_ch": ex_ch},
                             headers=_HEADERS, timeout=_TIMEOUT)
            r.raise_for_status()
            for q in parse_payload(r.json()):
                self._cache[q.code] = (time.monotonic(), q)
                if q.code in remaining:
                    out.append(q)
                    remaining.discard(q.code)
        return out


realtime = RealtimeQuotes()
