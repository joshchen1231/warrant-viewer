"""Router API tests: underlying search (T-004), warrant list + validation (INV-10)."""
import pytest
from fastapi.testclient import TestClient

from app import config, db
from app.main import app


def _master(code: str, name: str, market: str, underlying: str, underlying_name: str) -> dict:
    return {"code": code, "name": name, "market": market,
            "underlying_code": underlying, "underlying_name": underlying_name,
            "call_put": "CALL", "exercise_style": "AMERICAN",
            "warrant_type": "GENERAL", "issuer": "永豐金", "strike_price": 900.0,
            "exercise_ratio": 0.02, "listed_date": "2026-01-01",
            "expiry_date": "2026-12-31", "last_trading_date": "2026-12-30",
            "cap_price": None, "floor_price": None, "reset": 0, "active": 1,
            "source": "test", "fetched_at": "2026-08-08"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "warrant.db")
    monkeypatch.setattr(config, "COLLECT_TOKEN", "test-token")
    conn = db.connect()
    db.migrate(conn)
    db.upsert_warrant_master(conn, [
        _master("03001T", "台積電永豐38購01", "TSE", "2330", "台積電"),
        _master("03002T", "台積電凱基38購02", "TSE", "2330", "台積電"),
        _master("70001", "群創永豐38購01", "OTC", "3481", "群創"),
    ])
    conn.commit()
    conn.close()
    with TestClient(app) as c:
        yield c


def test_search_by_code(client):
    r = client.get("/api/underlying/search", params={"q": "2330"})
    assert r.status_code == 200
    rows = r.json()["results"]
    assert {"code": "2330", "name": "台積電", "market": "TSE"} in rows


def test_search_by_chinese_name(client):
    r = client.get("/api/underlying/search", params={"q": "台積電"})
    assert r.status_code == 200
    rows = r.json()["results"]
    assert any(x["code"] == "2330" and x["name"] == "台積電" for x in rows)


def test_search_by_partial_name(client):
    r = client.get("/api/underlying/search", params={"q": "台積"})
    assert r.status_code == 200
    codes = {x["code"] for x in r.json()["results"]}
    assert codes == {"2330"}


def test_search_dedupes_multi_market(client, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "warrant.db")
    conn = db.connect()
    db.migrate(conn)
    db.upsert_warrant_master(conn, [
        _master("03001T", "台積電永豐38購01", "TSE", "2330", "台積電"),
        _master("70002", "台積電永豐38購02", "OTC", "2330", "台積電"),
    ])
    conn.commit()
    conn.close()
    with TestClient(app) as c:
        r = c.get("/api/underlying/search", params={"q": "2330"})
    assert r.status_code == 200
    assert len(r.json()["results"]) == 1
    assert r.json()["results"][0]["code"] == "2330"


def test_search_rejects_invalid_chars(client):
    r = client.get("/api/underlying/search", params={"q": "ab c"})
    assert r.status_code == 400
    r = client.get("/api/underlying/search", params={"q": "!!!"})
    assert r.status_code == 400


def test_search_requires_q(client):
    r = client.get("/api/underlying/search")
    assert r.status_code == 422


def test_warrants_list_filter_and_sort(client):
    r = client.get("/api/warrants", params={"underlying_code": "2330"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert {x["code"] for x in body["rows"]} == {"03001T", "03002T"}

    r = client.get("/api/warrants", params={
        "underlying_code": "2330", "exercise_ratio_min": "0.05"})
    assert r.status_code == 200
    assert r.json()["count"] == 0

    r = client.get("/api/warrants", params={"underlying_code": "2330",
                                            "sort": "code", "descending": "true"})
    codes = [x["code"] for x in r.json()["rows"]]
    assert codes == sorted(codes, reverse=True)


def test_warrants_rejects_bad_input(client):
    r = client.get("/api/warrants", params={"underlying_code": "2330",
                                            "iv_min": "-1"})
    assert r.status_code == 400
    r = client.get("/api/warrants", params={"underlying_code": "2330",
                                            "sort": "bogus"})
    assert r.status_code == 400
    r = client.get("/api/warrants")
    assert r.status_code == 422


def test_warrant_detail_404(client):
    r = client.get("/api/warrants/NOPE99")
    assert r.status_code == 404


def test_data_status_shape(client):
    r = client.get("/api/data/status")
    assert r.status_code == 200
    body = r.json()
    assert "data_date" in body and "markets" in body and "collect_log" in body


def test_data_collect_requires_token(client, monkeypatch):
    from app.routers import data as data_router
    monkeypatch.setattr(data_router, "run_collection", lambda: {"TSE": {"status": "SUCCESS"}})
    r = client.post("/api/data/collect")
    assert r.status_code == 403
    r = client.post("/api/data/collect", headers={"x-collect-token": "wrong"})
    assert r.status_code == 403
    r = client.post("/api/data/collect", headers={"x-collect-token": "test-token"})
    assert r.status_code == 200
    assert r.json()["job"] == "accepted"
