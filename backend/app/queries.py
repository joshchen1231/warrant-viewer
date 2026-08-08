"""Query layer for the warrant list API. Implements PSM §6 filters over PIM schemas."""
import sqlite3
from datetime import date, datetime


def search_underlying(conn: sqlite3.Connection, q: str, limit: int = 20) -> list[dict]:
    like = f"%{q}%"
    rows = conn.execute(
        """
        SELECT underlying_code AS code, underlying_name AS name,
               GROUP_CONCAT(DISTINCT market) AS market
        FROM warrant_master
        WHERE active = 1 AND (underlying_code LIKE ? OR underlying_name LIKE ?)
        GROUP BY underlying_code, underlying_name
        ORDER BY CASE WHEN underlying_code = ? THEN 0 ELSE 1 END, underlying_code
        LIMIT ?
        """,
        (like, like, q, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_warrant_detail(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute(
        """
        SELECT w.*, q.date AS quote_date, q.open, q.high, q.low, q.close, q.change,
               q.volume, q.trade_value, q.underlying_close,
               a.iv_close, a.delta, a.moneyness, a.premium, a.leverage, a.theoretical_price,
               a.breakeven, a.status AS analysis_status
        FROM warrant_master w
        LEFT JOIN daily_quote q ON q.code = w.code
            AND q.date = (SELECT MAX(date) FROM daily_quote WHERE code = w.code)
        LEFT JOIN analysis a ON a.code = w.code
            AND a.date = (SELECT MAX(date) FROM analysis WHERE code = w.code)
        WHERE w.code = ?
        """,
        (code,),
    ).fetchone()
    return dict(row) if row else None


def list_warrants(conn: sqlite3.Connection, underlying_code: str,
                  market: str | None = None, call_put: str | None = None,
                  issuer: str | None = None, warrant_type: str | None = None,
                  exercise_ratio_min: float | None = None,
                  exercise_ratio_max: float | None = None,
                  iv_min: float | None = None, iv_max: float | None = None,
                  moneyness_min: float | None = None, moneyness_max: float | None = None,
                  days_min: int | None = None, days_max: int | None = None,
                  sort: str = "code", descending: bool = False) -> list[dict]:
    where = ["w.underlying_code = ?"]
    params: list = [underlying_code]
    if market:
        where.append("w.market = ?")
        params.append(market)
    if call_put:
        where.append("w.call_put = ?")
        params.append(call_put)
    if issuer:
        where.append("w.issuer LIKE ?")
        params.append(f"%{issuer}%")
    if warrant_type:
        where.append("w.warrant_type = ?")
        params.append(warrant_type)
    if exercise_ratio_min is not None:
        where.append("w.exercise_ratio >= ?")
        params.append(exercise_ratio_min)
    if exercise_ratio_max is not None:
        where.append("w.exercise_ratio <= ?")
        params.append(exercise_ratio_max)

    rows = conn.execute(
        f"""
        SELECT w.*, q.date AS quote_date, q.close, q.underlying_close,
               a.iv_close, a.delta, a.moneyness, a.premium, a.leverage,
               a.theoretical_price, a.breakeven, a.status AS analysis_status
        FROM warrant_master w
        LEFT JOIN daily_quote q ON q.code = w.code
            AND q.date = (SELECT MAX(date) FROM daily_quote WHERE code = w.code)
        LEFT JOIN analysis a ON a.code = w.code
            AND a.date = (SELECT MAX(date) FROM analysis WHERE code = w.code)
        WHERE {" AND ".join(where)}
        """,
        params,
    ).fetchall()

    today = date.today()
    out = []
    for r in rows:
        d = dict(r)
        expiry = d.get("expiry_date")
        d["days_to_maturity"] = None
        if expiry:
            try:
                d["days_to_maturity"] = (datetime.strptime(expiry, "%Y-%m-%d").date() - today).days
            except ValueError:
                pass
        if days_min is not None and (d["days_to_maturity"] is None or d["days_to_maturity"] < days_min):
            continue
        if days_max is not None and (d["days_to_maturity"] is None or d["days_to_maturity"] > days_max):
            continue
        if iv_min is not None and (d["iv_close"] is None or d["iv_close"] < iv_min):
            continue
        if iv_max is not None and (d["iv_close"] is None or d["iv_close"] > iv_max):
            continue
        if moneyness_min is not None and (d["moneyness"] is None or d["moneyness"] < moneyness_min):
            continue
        if moneyness_max is not None and (d["moneyness"] is None or d["moneyness"] > moneyness_max):
            continue
        out.append(d)

    sort_keys = {
        "code": lambda d: d["code"],
        "close": lambda d: d["close"] if d["close"] is not None else -1e18,
        "exercise_ratio": lambda d: d["exercise_ratio"] if d["exercise_ratio"] is not None else -1e18,
        "iv_close": lambda d: d["iv_close"] if d["iv_close"] is not None else -1e18,
        "moneyness": lambda d: d["moneyness"] if d["moneyness"] is not None else -1e18,
        "days_to_maturity": lambda d: d["days_to_maturity"] if d["days_to_maturity"] is not None else 10**9,
        "premium": lambda d: d["premium"] if d["premium"] is not None else -1e18,
        "leverage": lambda d: d["leverage"] if d["leverage"] is not None else -1e18,
    }
    if sort in sort_keys:
        out.sort(key=sort_keys[sort], reverse=descending)
    return out
