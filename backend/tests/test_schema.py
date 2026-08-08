"""Schema + invariants tests. Implements INV-1, INV-6, INV-2."""
import sqlite3

from app import db


def _fresh_conn(tmp_path):
    conn = db.connect(tmp_path / "test.db")
    db.migrate(conn)
    return conn


def test_migrations_apply_and_are_idempotent(tmp_path):
    conn = _fresh_conn(tmp_path)
    db.migrate(conn)
    names = {r["name"] for r in conn.execute("SELECT name FROM schema_migrations")}
    assert "0001_schema.sql" in names
    conn.close()


def test_inv1_daily_quote_unique_per_code_date(tmp_path):
    conn = _fresh_conn(tmp_path)
    row = {"code": "03001T", "date": "2026-08-07", "open": 1.0, "high": 1.1,
           "low": 0.9, "close": 1.0, "change": 0.1, "volume": 1000,
           "trade_value": 10000, "underlying_close": 233.0, "source": "twse"}
    inserted = db.insert_daily_quotes(conn, [row, row])
    assert inserted == 1
    assert conn.execute("SELECT COUNT(*) AS n FROM daily_quote").fetchone()["n"] == 1
    conn.close()


def test_inv6_append_only_never_overwrites(tmp_path):
    conn = _fresh_conn(tmp_path)
    r1 = {"code": "A", "date": "2026-08-07", "close": 1.0, "source": "twse",
          "open": None, "high": None, "low": None, "change": None,
          "volume": None, "trade_value": None, "underlying_close": None}
    r2 = dict(r1, close=99.0)
    db.insert_daily_quotes(conn, [r1])
    db.insert_daily_quotes(conn, [r2])
    val = conn.execute("SELECT close FROM daily_quote WHERE code='A'").fetchone()["close"]
    assert val == 1.0
    conn.close()


def test_inv2_exercise_ratio_positive_constraint(tmp_path):
    conn = _fresh_conn(tmp_path)
    m = {"code": "X", "name": "n", "market": "TSE", "underlying_code": "2330",
         "underlying_name": "u", "call_put": "CALL", "exercise_style": "AMERICAN",
         "warrant_type": "GENERAL", "issuer": "", "strike_price": 100.0,
         "exercise_ratio": -1, "listed_date": None, "expiry_date": "2026-12-31",
         "last_trading_date": None, "cap_price": None, "floor_price": None,
         "reset": 0, "active": 1, "source": "test", "fetched_at": "2026-08-08"}
    try:
        db.upsert_warrant_master(conn, [m])
        failed = False
    except sqlite3.IntegrityError:
        failed = True
    assert failed
    conn.close()
