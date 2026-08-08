"""Validation layer tests. Implements INV-10."""
import pytest

from app.validation import ValidationError, v_enum, v_float, v_int, v_str


def test_v_str_length_and_pattern():
    assert v_str("q", "2330", pattern=r"[0-9]+") == "2330"
    with pytest.raises(ValidationError):
        v_str("q", "ab c", pattern=r"[0-9]+")
    with pytest.raises(ValidationError):
        v_str("q", "a" * 65, max_len=64)


def test_v_float_ranges():
    assert v_float("iv", None) is None
    assert v_float("iv", "0.5", gte=0, lte=5) == 0.5
    with pytest.raises(ValidationError):
        v_float("iv", 6, lte=5)
    with pytest.raises(ValidationError):
        v_float("iv", "abc")


def test_v_int_ranges():
    assert v_int("days", "30", gte=0) == 30
    with pytest.raises(ValidationError):
        v_int("days", -1, gte=0)
    with pytest.raises(ValidationError):
        v_int("days", "x")


def test_v_enum():
    assert v_enum("market", "tse", ["TSE", "OTC"]) == "TSE"
    assert v_enum("market", None, ["TSE", "OTC"]) is None
    with pytest.raises(ValidationError):
        v_enum("market", "HKG", ["TSE", "OTC"])
