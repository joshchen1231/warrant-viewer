"""Realtime quote endpoint. GET /api/realtime?codes=03001T,03002T (max 200, TSE only)."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Query

from ..collectors.realtime import realtime
from ..validation import ValidationError, v_str

router = APIRouter(prefix="/api")


@router.get("/realtime")
def realtime_quotes(codes: str = Query(..., max_length=2000)):
    raw = [c.strip() for c in codes.split(",") if c.strip()]
    if not raw:
        raise _bad("codes: required")
    if len(raw) > 200:
        raise _bad("codes: at most 200")
    try:
        for c in raw:
            v_str("codes", c, min_len=1, max_len=10, pattern=r"[0-9A-Za-z]+")
    except ValidationError as exc:
        raise _bad(str(exc))
    quotes = realtime.get_quotes(raw)
    return {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(quotes),
        "rows": [asdict(q) for q in quotes],
    }


def _bad(detail: str):
    from fastapi import HTTPException
    return HTTPException(status_code=400, detail=detail)
