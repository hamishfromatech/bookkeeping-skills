"""Decimal money helpers.

Every amount that enters the server is converted through ``str()`` so that a
float such as ``0.1`` becomes ``Decimal("0.1")`` and not the binary
approximation. Nothing in this package does money arithmetic in floats.
"""

from __future__ import annotations

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    localcontext,
)

ROUNDING_MODES = {
    "half_up": ROUND_HALF_UP,
    "half_even": ROUND_HALF_EVEN,
    "down": ROUND_DOWN,
    "up": ROUND_UP,
    "floor": ROUND_FLOOR,
    "ceiling": ROUND_CEILING,
}

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


class MoneyError(ValueError):
    """Raised when an amount or rate is not usable for money arithmetic."""


def to_decimal(value, field: str = "amount") -> Decimal:
    """Convert int / float / str / Decimal to Decimal without float artefacts."""
    if isinstance(value, Decimal):
        dec = value
    elif isinstance(value, bool):
        raise MoneyError(f"{field} must be a number, not a boolean")
    elif isinstance(value, (int, float)):
        dec = Decimal(str(value))
    elif isinstance(value, str):
        text = value.strip().replace(",", "").replace("$", "").replace("_", "")
        if text.startswith("(") and text.endswith(")"):
            text = "-" + text[1:-1]
        if not text:
            raise MoneyError(f"{field} is empty")
        try:
            dec = Decimal(text)
        except InvalidOperation as exc:
            raise MoneyError(f"{field} is not a number: {value!r}") from exc
    else:
        raise MoneyError(f"{field} must be a number or numeric string, got {type(value).__name__}")

    if not dec.is_finite():
        raise MoneyError(f"{field} must be finite")
    return dec


def to_rate(value, field: str = "rate") -> Decimal:
    """Convert a percentage such as 10 or \"8.875\" to a Decimal percentage."""
    dec = to_decimal(value, field)
    if dec.copy_abs() > Decimal("1000"):
        raise MoneyError(f"{field} looks out of range for a percentage: {dec}")
    return dec


def quantize(value, places: int = 2, mode: str = "half_up") -> Decimal:
    if mode not in ROUNDING_MODES:
        raise MoneyError(f"mode must be one of {', '.join(sorted(ROUNDING_MODES))}")
    if not 0 <= places <= 8:
        raise MoneyError("places must be between 0 and 8")
    exp = Decimal(1).scaleb(-places)
    with localcontext() as ctx:
        ctx.prec = 40
        return to_decimal(value).quantize(exp, rounding=ROUNDING_MODES[mode])


def quantize_int(value) -> int:
    return int(quantize(value, 0))


def as_number(value) -> float:
    """Boundary conversion for JSON output. Always quantize before calling."""
    return float(quantize(value, 8))


def money_str(value, places: int = 2) -> str:
    return f"{quantize(value, places):,.{places}f}"


def cents(value) -> int:
    """Exact integer cents, used for allocation and equality checks."""
    return int(quantize(value, 2) * 100)


def from_cents(value: int) -> Decimal:
    return (Decimal(int(value)) / 100).quantize(Decimal("0.01"))


def pct_of(amount, rate_percent) -> Decimal:
    return to_decimal(amount) * to_rate(rate_percent) / HUNDRED


def clamp(value: Decimal, low: Decimal | None = None, high: Decimal | None = None) -> Decimal:
    out = value
    if low is not None and out < low:
        out = low
    if high is not None and out > high:
        out = high
    return out
