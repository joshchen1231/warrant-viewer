"""Data-status and collect-trigger endpoints. Implements R4/R9, INV-8, PIM §6 token guard."""
from __future__ import annotations

import hmac
import threading
from sqlite3 import Connection

from fastapi import APIRouter, Depends, Header, HTTPException

from .. import config
from ..collect_runner import run_collection
from ..db import connect, latest_quote_date, recent_collect_logs, status_by_market

router = APIRouter(prefix="/api")


def get_db() -> Connection:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


@router.get("/data/status")
def data_status(db: Connection = Depends(get_db)):
    return {
        "data_date": latest_quote_date(db),
        "markets": status_by_market(db),
        "collect_log": recent_collect_logs(db),
    }


def _check_token(x_collect_token: str | None) -> None:
    if not x_collect_token or not hmac.compare_digest(x_collect_token, config.COLLECT_TOKEN):
        raise HTTPException(status_code=403, detail="invalid collect token")


@router.post("/data/collect")
def data_collect(x_collect_token: str | None = Header(None)):
    _check_token(x_collect_token)
    result: dict = {}

    def _run() -> None:
        result.update(run_collection())

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"job": "accepted"}
