"""TWSE collector parsing tests against frozen live fixture (G2 payload)."""
from pathlib import Path

from app.collectors.twse import parse_payload_from_json

FIX = Path(__file__).parent / "fixtures"


def test_payload_parsing_full_market_shape():
    result = parse_payload_from_json(
        (FIX / "twse_warrantStock.json").read_text(encoding="utf-8-sig"), "2026-08-08"
    )
    assert result.source == "twse"
    assert result.date == "2026-08-07"
    assert len(result.masters) == 200
    assert len(result.quotes) > 100
    first = result.masters[0]
    assert first["market"] == "TSE"
    assert first["call_put"] in ("CALL", "PUT")
    assert first["exercise_ratio"] > 0
    assert first["expiry_date"] and len(first["expiry_date"]) == 10
    assert any(m["active"] == 1 for m in result.masters)


def test_quote_rows_carry_underlying_close():
    result = parse_payload_from_json(
        (FIX / "twse_warrantStock.json").read_text(encoding="utf-8-sig"), "2026-08-08"
    )
    with_close = [q for q in result.quotes if q["underlying_close"] is not None]
    assert with_close
    assert all(q["close"] is not None for q in result.quotes)
