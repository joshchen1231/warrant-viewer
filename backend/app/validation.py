"""Unified input-validation layer. Implements INV-10: the only place that parses user input."""
from __future__ import annotations

import re
from typing import Any


class ValidationError(ValueError):
    pass


def v_str(name: str, value: Any, *, min_len: int = 1, max_len: int = 64,
          pattern: str | None = None) -> str:
    if value is None:
        raise ValidationError(f"{name}: required")
    s = str(value).strip()
    if not (min_len <= len(s) <= max_len):
        raise ValidationError(f"{name}: length must be {min_len}..{max_len}")
    if pattern and not re.fullmatch(pattern, s):
        raise ValidationError(f"{name}: invalid format")
    return s


def v_float(name: str, value: Any, *, gte: float | None = None,
            lte: float | None = None) -> float | None:
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name}: must be a number")
    if gte is not None and f < gte:
        raise ValidationError(f"{name}: must be >= {gte}")
    if lte is not None and f > lte:
        raise ValidationError(f"{name}: must be <= {lte}")
    return f


def v_int(name: str, value: Any, *, gte: int | None = None,
          lte: int | None = None) -> int | None:
    if value is None or value == "":
        return None
    try:
        i = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name}: must be an integer")
    if gte is not None and i < gte:
        raise ValidationError(f"{name}: must be >= {gte}")
    if lte is not None and i > lte:
        raise ValidationError(f"{name}: must be <= {lte}")
    return i


def v_enum(name: str, value: Any, choices: list[str]) -> str | None:
    if value is None or value == "":
        return None
    s = str(value).strip().upper()
    if s not in choices:
        raise ValidationError(f"{name}: must be one of {choices}")
    return s
