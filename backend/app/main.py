"""FastAPI app. Implements PSM §6/§9: loopback binding, validation layer, scheduler, static frontend."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config
from .collectors.scheduler import start_scheduler
from .db import connect, latest_quote_date, migrate

FRONTEND_DIST = config.BASE_DIR.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    conn = connect()
    migrate(conn)
    conn.close()
    if "PYTEST_CURRENT_TEST" not in __import__("os").environ:
        config.SCHEDULER = start_scheduler()
    yield
    if hasattr(config, "SCHEDULER"):
        config.SCHEDULER.shutdown(wait=False)


app = FastAPI(title="warrant-viewer", lifespan=lifespan)


@app.get("/api/health")
def health():
    conn = connect()
    try:
        data_date = latest_quote_date(conn)
    finally:
        conn.close()
    return {"status": "ok", "data_date": data_date}


from .routers import data as data_router  # noqa: E402
from .routers import realtime as realtime_router  # noqa: E402
from .routers import warrants as warrants_router  # noqa: E402

app.include_router(warrants_router.router)
app.include_router(data_router.router)
app.include_router(realtime_router.router)

if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
