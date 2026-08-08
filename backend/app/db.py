"""SQLite access layer. Implements PIM §5 schemas; INV-1, INV-6, INV-8."""
import sqlite3
from datetime import date
from pathlib import Path

from . import config


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    applied = {r["name"] for r in conn.execute("SELECT name FROM schema_migrations")}
    for sql_file in sorted(Path(config.MIGRATE_DIR).glob("*.sql")):
        if sql_file.name.endswith("_down.sql"):
            continue
        if sql_file.name in applied:
            continue
        conn.executescript(sql_file.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
            (sql_file.name, date.today().isoformat()),
        )
    conn.commit()


def upsert_warrant_master(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """G6: master = latest disclosure wins (upsert)."""
    sql = """
        INSERT INTO warrant_master (code, name, market, underlying_code, underlying_name,
            call_put, exercise_style, warrant_type, issuer, strike_price, exercise_ratio,
            listed_date, expiry_date, last_trading_date, cap_price, floor_price, reset,
            active, source, fetched_at)
        VALUES (:code, :name, :market, :underlying_code, :underlying_name, :call_put,
            :exercise_style, :warrant_type, :issuer, :strike_price, :exercise_ratio,
            :listed_date, :expiry_date, :last_trading_date, :cap_price, :floor_price, :reset,
            :active, :source, :fetched_at)
        ON CONFLICT(code) DO UPDATE SET
            name = excluded.name, underlying_code = excluded.underlying_code,
            underlying_name = excluded.underlying_name, call_put = excluded.call_put,
            exercise_style = excluded.exercise_style, warrant_type = excluded.warrant_type,
            issuer = excluded.issuer, strike_price = excluded.strike_price,
            exercise_ratio = excluded.exercise_ratio, listed_date = excluded.listed_date,
            expiry_date = excluded.expiry_date, last_trading_date = excluded.last_trading_date,
            cap_price = excluded.cap_price, floor_price = excluded.floor_price,
            reset = excluded.reset, active = excluded.active, source = excluded.source,
            fetched_at = excluded.fetched_at
    """
    conn.executemany(sql, rows)
    return len(rows)


def insert_daily_quotes(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """INV-6: append-only; existing (code, date) rows are never overwritten."""
    sql = """
        INSERT OR IGNORE INTO daily_quote (code, date, open, high, low, close, change,
            volume, trade_value, underlying_close, source)
        VALUES (:code, :date, :open, :high, :low, :close, :change, :volume, :trade_value,
            :underlying_close, :source)
    """
    cur = conn.executemany(sql, rows)
    return cur.rowcount if cur.rowcount is not None and cur.rowcount > 0 else 0


def insert_underlying_daily(conn: sqlite3.Connection, rows: list[dict]) -> int:
    sql = """
        INSERT OR IGNORE INTO underlying_daily (code, date, open, high, low, close, volume)
        VALUES (:code, :date, :open, :high, :low, :close, :volume)
    """
    cur = conn.executemany(sql, rows)
    return cur.rowcount if cur.rowcount is not None and cur.rowcount > 0 else 0


def insert_collect_log(conn: sqlite3.Connection, date: str, market: str, status: str,
                       row_count: int, message: str) -> None:
    """INV-8: one row per (date, market) job attempt."""
    conn.execute(
        "INSERT INTO collect_log (date, market, status, row_count, message) VALUES (?, ?, ?, ?, ?)",
        (date, market, status, row_count, message),
    )
    conn.commit()


def latest_quote_date(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT MAX(date) AS d FROM daily_quote").fetchone()
    return row["d"]


def status_by_market(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT q.market, MAX(dq.date) AS last_date, COUNT(DISTINCT dq.code) AS codes
        FROM (SELECT DISTINCT market FROM warrant_master) q
        LEFT JOIN daily_quote dq ON 1 = 0
        GROUP BY q.market
        """
    ).fetchall()
    out = []
    for r in rows:
        last = conn.execute(
            """
            SELECT MAX(dq.date) AS d
            FROM daily_quote dq JOIN warrant_master w ON w.code = dq.code
            WHERE w.market = ?
            """,
            (r["market"],),
        ).fetchone()["d"]
        codes = conn.execute(
            """
            SELECT COUNT(DISTINCT dq.code) AS n
            FROM daily_quote dq JOIN warrant_master w ON w.code = dq.code
            WHERE w.market = ? AND dq.date = ?
            """,
            (r["market"], last or ""),
        ).fetchone()["n"]
        out.append({"market": r["market"], "last_date": last, "codes": codes})
    return out


def recent_collect_logs(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    rows = conn.execute(
        "SELECT date, market, status, row_count, message FROM collect_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
