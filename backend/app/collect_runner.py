"""Collection runner. Implements INV-8: transaction per (date, market); per-source failure isolation."""
from __future__ import annotations

import logging

from . import config
from .collectors.tpex import TpexSource
from .collectors.twse import TwseSource
from .db import connect, insert_collect_log, insert_daily_quotes, migrate, upsert_warrant_master

logger = logging.getLogger("warrant-viewer")


def run_collection() -> dict:
    conn = connect()
    migrate(conn)
    results = {}
    for source in (TpexSource(), TwseSource()):
        try:
            res = source.fetch()
        except Exception as exc:
            logger.exception("collect %s failed", source.name)
            insert_collect_log(conn, config_today(), source.market, "FAILED", 0, str(exc))
            results[source.market] = {"status": "FAILED", "error": str(exc)}
            continue
        try:
            conn.execute("BEGIN")
            upsert_warrant_master(conn, res.masters)
            inserted = insert_daily_quotes(conn, res.quotes)
            conn.commit()
            existing = 0
            for d in {q["date"] for q in res.quotes}:
                n = conn.execute(
                    """
                    SELECT COUNT(*) AS n FROM daily_quote q
                    JOIN warrant_master w ON w.code = q.code
                    WHERE q.date = ? AND w.market = ?
                    """,
                    (d, source.market),
                ).fetchone()["n"]
                existing += n
            if inserted or existing:
                status = "SUCCESS"
                msg = (f"masters={len(res.masters)} quotes={len(res.quotes)} "
                       f"inserted={inserted} existing={existing}")
            else:
                status = "PARTIAL"
                msg = f"masters={len(res.masters)} quotes={len(res.quotes)} inserted=0"
            insert_collect_log(conn, res.date, source.market, status, len(res.quotes), msg)
            results[source.market] = {"status": status, "date": res.date,
                                      "masters": len(res.masters), "quotes": len(res.quotes)}
        except Exception as exc:
            conn.rollback()
            logger.exception("collect %s write failed", source.name)
            insert_collect_log(conn, res.date, source.market, "FAILED", 0, f"write error: {exc}")
            results[source.market] = {"status": "FAILED", "error": str(exc)}
    conn.close()
    return results


def config_today() -> str:
    from datetime import date
    return date.today().isoformat()
