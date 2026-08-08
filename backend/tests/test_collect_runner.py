"""collect_runner tests: per-source isolation, idempotent re-run status."""
from app import db
from app.collectors.base import CollectResult
from app.collect_runner import run_collection


class _FakeTpex:
    name = "tpex"
    market = "OTC"

    def fetch(self) -> CollectResult:
        return CollectResult(
            date="2026-08-08",
            masters=[{"code": "700001", "name": "n", "market": "OTC",
                      "underlying_code": "3481", "underlying_name": "",
                      "call_put": "CALL", "exercise_style": "AMERICAN",
                      "warrant_type": "GENERAL", "issuer": "", "strike_price": 10.0,
                      "exercise_ratio": 0.1, "listed_date": None,
                      "expiry_date": "2026-12-31", "last_trading_date": None,
                      "cap_price": None, "floor_price": None, "reset": 0,
                      "active": 1, "source": "tpex", "fetched_at": "2026-08-08"}],
            quotes=[{"code": "700001", "date": "2026-08-07", "open": None, "high": None,
                     "low": None, "close": 1.0, "change": None, "volume": None,
                     "trade_value": None, "underlying_close": 12.0, "source": "tpex"}],
            source="tpex",
        )


class _FakeTwse:
    name = "twse"
    market = "TSE"

    def fetch(self) -> CollectResult:
        return CollectResult(
            date="2026-08-07",
            masters=[{"code": "03001T", "name": "n", "market": "TSE",
                      "underlying_code": "2330", "underlying_name": "台積電",
                      "call_put": "CALL", "exercise_style": "AMERICAN",
                      "warrant_type": "GENERAL", "issuer": "", "strike_price": 100.0,
                      "exercise_ratio": 0.02, "listed_date": "2026-01-01",
                      "expiry_date": "2026-12-31", "last_trading_date": "2026-12-30",
                      "cap_price": None, "floor_price": None, "reset": 0,
                      "active": 1, "source": "twse", "fetched_at": "2026-08-08"}],
            quotes=[{"code": "03001T", "date": "2026-08-07", "open": None, "high": None,
                     "low": None, "close": 0.9, "change": 0.1, "volume": None,
                     "trade_value": None, "underlying_close": 950.0, "source": "twse"}],
            source="twse",
        )


def _fresh(tmp_path, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "warrant.db")
    monkeypatch.setattr("app.collect_runner.TpexSource", _FakeTpex)
    monkeypatch.setattr("app.collect_runner.TwseSource", _FakeTwse)


def test_collect_first_run_success(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    results = run_collection()
    assert results["TSE"]["status"] == "SUCCESS"
    assert results["OTC"]["status"] == "SUCCESS"
    conn = db.connect()
    assert conn.execute("SELECT COUNT(*) n FROM daily_quote").fetchone()["n"] == 2
    conn.close()


def test_collect_rerun_is_success_not_partial(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    run_collection()
    results = run_collection()
    assert results["TSE"]["status"] == "SUCCESS"
    assert results["OTC"]["status"] == "SUCCESS"
    conn = db.connect()
    log = conn.execute(
        "SELECT status, row_count, message FROM collect_log WHERE market='OTC' ORDER BY id"
    ).fetchall()
    assert [r["status"] for r in log] == ["SUCCESS", "SUCCESS"]
    assert "existing=1" in log[1]["message"]
    conn.close()
