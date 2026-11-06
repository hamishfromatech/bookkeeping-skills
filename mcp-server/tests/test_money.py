from __future__ import annotations

from decimal import Decimal

import pytest

from bookkeeping_mcp.money import (
    MoneyError,
    as_number,
    cents,
    from_cents,
    money_str,
    pct_of,
    quantize,
    to_decimal,
)


def test_float_input_is_not_binary_corrupted():
    assert to_decimal(0.1) == Decimal("0.1")
    assert to_decimal(0.1) + to_decimal(0.2) == Decimal("0.3")


def test_parses_formatted_strings():
    assert to_decimal("$1,234.56") == Decimal("1234.56")
    assert to_decimal("(250.00)") == Decimal("-250.00")
    assert to_decimal(" 42 ") == Decimal("42")


def test_rejects_booleans_and_nan():
    with pytest.raises(MoneyError):
        to_decimal(True)
    with pytest.raises(MoneyError):
        to_decimal("NaN")
    with pytest.raises(MoneyError):
        to_decimal("not-a-number")


@pytest.mark.parametrize(
    ("value", "mode", "expected"),
    [
        ("2.5", "half_up", "3"),
        ("2.5", "half_even", "2"),
        ("2.4", "up", "3"),
        ("2.9", "down", "2"),
        ("-2.5", "floor", "-3"),
        ("-2.5", "ceiling", "-2"),
    ],
)
def test_rounding_modes(value, mode, expected):
    assert quantize(value, 0, mode) == Decimal(expected)


def test_unknown_mode_rejected():
    with pytest.raises(MoneyError):
        quantize("1.0", 2, "bankers")


def test_cents_roundtrip():
    assert cents("1234.56") == 123456
    assert from_cents(123456) == Decimal("1234.56")
    assert cents("0.005") == 1


def test_pct_of():
    assert pct_of("200", 7.5) == Decimal("15.0")


def test_money_str_groups_and_pads():
    assert money_str("1234.5") == "1,234.50"
    assert money_str("-1234.5") == "-1,234.50"


def test_as_number_is_plain_float():
    assert as_number("1234.5") == 1234.5
    assert isinstance(as_number("1"), float)
