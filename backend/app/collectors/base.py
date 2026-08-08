"""Collector base contract. Implements PSM §8 M0: swappable providers (G2)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CollectResult:
    date: str
    masters: list[dict] = field(default_factory=list)
    quotes: list[dict] = field(default_factory=list)
    source: str = ""


def to_float(v) -> float | None:
    if v is None:
        return None
    s = str(v).replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def roc_date_to_iso(v: str) -> str | None:
    """ROC year (1150807 or 115年08月07日) -> ISO (2026-08-07)."""
    if not v:
        return None
    s = str(v).strip()
    m = None
    if s.isdigit() and len(s) == 7:
        y, mm, dd = int(s[:3]) + 1911, int(s[3:5]), int(s[5:7])
        return f"{y:04d}-{mm:02d}-{dd:02d}"
    import re
    m = re.fullmatch(r"(\d{3})年(\d{1,2})月(\d{1,2})日?", s)
    if m:
        y, mm, dd = int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mm:02d}-{dd:02d}"
    if s.isdigit() and len(s) == 8:
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return None


class WarrantSource(ABC):
    name: str = ""
    market: str = ""

    @abstractmethod
    def fetch(self) -> CollectResult:
        raise NotImplementedError
