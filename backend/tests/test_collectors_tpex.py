"""TPEx collector parsing tests against frozen live fixtures."""
from pathlib import Path

from app.collectors.tpex import TpexSource, parse_master_from_json, parse_quotes_from_json

FIX = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8-sig")


def test_master_parsing_normalizes_fields():
    rows = parse_master_from_json(_fixture("tpex_warrant.json"), "2026-08-08", "2026-08-08")
    assert len(rows) > 50
    first = rows[0]
    assert first["market"] == "OTC"
    assert first["source"] == "tpex"
    assert first["exercise_ratio"] > 0
    assert first["expiry_date"] is None or len(first["expiry_date"]) == 10
    assert any(r["active"] == 1 for r in rows)


def test_quote_parsing_roc_date_conversion():
    rows = parse_quotes_from_json(_fixture("tpex_warrant_daily_quts.json"))
    assert len(rows) > 50
    for r in rows:
        assert r["date"] >= "2020-01-01"
        assert r["close"] is not None
        assert r["source"] == "tpex"


def test_fetch_roundtrip_with_mocked_requests(monkeypatch):
    import requests as _req

    master_text = _fixture("tpex_warrant.json")
    quts_text = _fixture("tpex_warrant_daily_quts.json")

    class FakeResp:
        def __init__(self, text):
            self._text = text

        def raise_for_status(self):
            pass

        def json(self):
            import json
            return json.loads(self._text)

    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        if url.endswith("tpex_warrant"):
            return FakeResp(master_text)
        return FakeResp(quts_text)

    monkeypatch.setattr(_req, "get", fake_get)
    result = TpexSource().fetch()
    assert len(calls) == 2
    assert result.source == "tpex"
    assert result.date
    assert len(result.masters) > 50
    assert len(result.quotes) > 50
