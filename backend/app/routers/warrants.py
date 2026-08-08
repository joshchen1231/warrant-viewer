"""Warrant list, detail and underlying-search endpoints. Implements PSM §6."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlite3 import Connection

from .. import queries
from ..db import connect
from ..validation import ValidationError, v_enum, v_float, v_int, v_str

router = APIRouter(prefix="/api")


def get_db() -> Connection:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def _bad_request(exc: ValidationError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/underlying/search")
def underlying_search(q: str = Query(..., max_length=20), db: Connection = Depends(get_db)):
    try:
        query = v_str("q", q, min_len=1, max_len=20,
                      pattern=r"[0-9A-Za-z\u4e00-\u9fff]+")
    except ValidationError as exc:
        raise _bad_request(exc)
    return {"results": queries.search_underlying(db, query)}


@router.get("/warrants")
def list_warrants(
    underlying_code: str = Query(...),
    market: str | None = Query(None),
    call_put: str | None = Query(None),
    issuer: str | None = Query(None, max_length=30),
    warrant_type: str | None = Query(None),
    exercise_ratio_min: float | None = Query(None),
    exercise_ratio_max: float | None = Query(None),
    iv_min: float | None = Query(None),
    iv_max: float | None = Query(None),
    moneyness_min: float | None = Query(None),
    moneyness_max: float | None = Query(None),
    days_min: int | None = Query(None),
    days_max: int | None = Query(None),
    sort: str = Query("code"),
    descending: bool = Query(False),
    db: Connection = Depends(get_db),
):
    try:
        code = v_str("underlying_code", underlying_code, max_len=10,
                     pattern=r"[0-9A-Za-z]+")
        mkt = v_enum("market", market, ["TSE", "OTC"])
        cp = v_enum("call_put", call_put, ["CALL", "PUT"])
        wtype = v_enum("warrant_type", warrant_type, ["GENERAL", "LIMIT", "RESET", "BULLBEAR"])
        iss = v_str("issuer", issuer, max_len=30) if issuer else None
        er_min = v_float("exercise_ratio_min", exercise_ratio_min, gte=0.0)
        er_max = v_float("exercise_ratio_max", exercise_ratio_max, gte=0.0)
        iv_lo = v_float("iv_min", iv_min, gte=0.0, lte=5.0)
        iv_hi = v_float("iv_max", iv_max, gte=0.0, lte=5.0)
        mn_min = v_float("moneyness_min", moneyness_min)
        mn_max = v_float("moneyness_max", moneyness_max)
        d_min = v_int("days_min", days_min, gte=0)
        d_max = v_int("days_max", days_max, gte=0)
        srt = v_str("sort", sort, min_len=1, max_len=24)
        srt_choices = {"code", "close", "exercise_ratio", "iv_close", "moneyness",
                       "days_to_maturity", "premium", "leverage"}
        if srt not in srt_choices:
            raise ValidationError(f"sort: must be one of {sorted(srt_choices)}")
    except ValidationError as exc:
        raise _bad_request(exc)

    rows = queries.list_warrants(
        db, code, market=mkt, call_put=cp, issuer=iss, warrant_type=wtype,
        exercise_ratio_min=er_min, exercise_ratio_max=er_max,
        iv_min=iv_lo, iv_max=iv_hi, moneyness_min=mn_min, moneyness_max=mn_max,
        days_min=d_min, days_max=d_max, sort=srt, descending=descending,
    )
    return {"count": len(rows), "rows": rows}


@router.get("/warrants/{code}")
def warrant_detail(code: str, db: Connection = Depends(get_db)):
    try:
        wcode = v_str("code", code, max_len=10, pattern=r"[0-9A-Za-z]+")
    except ValidationError as exc:
        raise _bad_request(exc)
    row = queries.get_warrant_detail(db, wcode)
    if row is None:
        raise HTTPException(status_code=404, detail="warrant not found")
    return row
