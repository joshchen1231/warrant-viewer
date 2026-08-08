"""Realtime quote tests: payload parsing (frozen fixture), batched fetch (mocked), router guard."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, db
from app.collectors.realtime import RealtimeQuotes, parse_payload
from app.main import app

FIX = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8-sig")


def test_parse_payload_normalizes_fields():
    quotes = parse_payload(json.loads(_fixture("twse_mis_realtime.json")))
    assert len(quotes) == 4
    by_code = {q.code: q for q in quotes}
    ts = by_code["2330"]
    assert ts.close == 2370.0
    assert ts.prev_close == 2365.0
    assert ts.date == "20260807"
    w = by_code["03001T"]
    assert w.close is None  # no trade on non-trading day -> '-'
    assert w.prev_close == 0.86
    assert w.bid == 1.07
    assert w.ask == 1.17


def test_fetch_batches_and_caches(monkeypatch):
    import requests as _req

    payload = json.loads(_fixture("twse_mis_realtime.json"))
    calls: list[list[str]] = []

    def fake_get(url, params, headers, timeout):
        calls.append(params["ex_ch"].split("|"))
        return _Resp(payload)

    monkeypatch.setattr(_req, "get", fake_get)
    rt = RealtimeQuotes()
    codes = ["2330", "03001T", "03002T", "2317"] + [f"0{i:04d}T" for i in range(116)]
    quotes = rt.get_quotes(codes)
    assert len(calls) == 3  # 120 codes / 50 per batch
    assert all(len(batch) <= 50 for batch in calls)
    assert len(quotes) == 4  # only codes present in the payload are returned
    rt.get_quotes(codes[:4])
    assert len(calls) == 3  # all four cached, no new fetch


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "warrant.db")
    conn = db.connect()
    db.migrate(conn)
    conn.close()
    with TestClient(app) as c:
        yield c


def test_router_validation(client):
    r = client.get("/api/realtime")
    assert r.status_code == 422
    r = client.get("/api/realtime", params={"codes": ""})
    assert r.status_code == 400
    r = client.get("/api/realtime", params={"codes": "03001T,!!!"})
    assert r.status_code == 400
    r = client.get("/api/realtime", params={"codes": ",".join(f"0{i:04d}T" for i in range(201))})
    assert r.status_code == 400
