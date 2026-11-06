"""Deterministic bookkeeping calculations.

Pure functions only: no file access, no network, no clock reads except where a
date is passed in explicitly. Every function returns a plain dict of JSON-safe
values so the MCP layer stays a thin wrapper.

Design rules:

* money arithmetic is Decimal, quantized once at the boundary
* inputs are validated and raise ``MoneyError`` with an actionable message
* functions never silently "fix" a mismatch — they report it
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from .money import (
    HUNDRED,
    MoneyError,
    as_number,
    cents,
    clamp,
    from_cents,
    money_str,
    pct_of,
    quantize,
    quantize_int,
    to_decimal,
    to_rate,
)


def _money(value, places: int = 2) -> float:
    return as_number(quantize(value, places))


# --------------------------------------------------------------------------
# basic arithmetic
# --------------------------------------------------------------------------


def sum_amounts(amounts, places: int = 2) -> dict:
    if not isinstance(amounts, (list, tuple)):
        raise MoneyError("amounts must be a list")
    if not amounts:
        raise MoneyError("amounts must contain at least one value")
    values = [to_decimal(a, f"amounts[{i}]") for i, a in enumerate(amounts)]
    total = sum(values, Decimal("0"))
    rounded = quantize(total, places)
    return {
        "count": len(values),
        "total": as_number(rounded),
        "total_formatted": money_str(rounded, places),
        "min": _money(min(values), places),
        "max": _money(max(values), places),
        "places": places,
        "rounding": "half-up applied once at the end",
    }


def round_amount(amount, places: int = 2, mode: str = "half_up") -> dict:
    value = to_decimal(amount)
    rounded = quantize(value, places, mode)
    return {
        "input": as_number(quantize(value, 8)),
        "rounded": as_number(rounded),
        "formatted": money_str(rounded, places),
        "places": places,
        "mode": mode,
        "difference": _money(rounded - quantize(value, 8), 8),
    }


def percent_calculation(amount, rate_percent, operation: str = "of") -> dict:
    base = to_decimal(amount)
    rate = to_rate(rate_percent)
    op = (operation or "of").strip().lower()
    portion = pct_of(base, rate)

    if op == "of":
        result = portion
    elif op == "add":
        result = base + portion
    elif op == "subtract":
        result = base - portion
    elif op == "reverse":
        divisor = Decimal("1") + rate / HUNDRED
        if divisor == 0:
            raise MoneyError("cannot reverse a -100% rate")
        result = base / divisor
    else:
        raise MoneyError("operation must be one of: of, add, subtract, reverse")

    return {
        "base": _money(base),
        "rate_percent": as_number(rate),
        "operation": op,
        "portion": _money(portion),
        "result": _money(result),
    }


def margin_and_markup(cost, price) -> dict:
    unit_cost = to_decimal(cost, "cost")
    unit_price = to_decimal(price, "price")
    if unit_price == 0:
        raise MoneyError("price must not be zero")
    gross_profit = unit_price - unit_cost
    margin = gross_profit / unit_price * HUNDRED
    markup = (gross_profit / unit_cost * HUNDRED) if unit_cost else None
    return {
        "cost": _money(unit_cost),
        "price": _money(unit_price),
        "gross_profit": _money(gross_profit),
        "gross_margin_percent": as_number(quantize(margin, 4)),
        "markup_percent": None if markup is None else as_number(quantize(markup, 4)),
        "note": "margin is profit/price; markup is profit/cost — they are not interchangeable",
    }


# --------------------------------------------------------------------------
# tax
# --------------------------------------------------------------------------


def sales_tax(amount, rate_percent, inclusive: bool = False, places: int = 2) -> dict:
    """Split an amount into net and tax.

    inclusive=False: ``amount`` is net, tax is added on top.
    inclusive=True:  ``amount`` is the tax-inclusive total, tax is extracted.
    """
    rate = to_rate(rate_percent)
    value = to_decimal(amount)

    if inclusive:
        divisor = Decimal("1") + rate / HUNDRED
        if divisor == 0:
            raise MoneyError("rate produces a zero divisor")
        net = quantize(value / divisor, places)
        tax = quantize(value - net, places)
    else:
        net = quantize(value, places)
        tax = quantize(pct_of(value, rate), places)

    return {
        "net": _money(net, places),
        "tax": _money(tax, places),
        "gross": _money(quantize(net + tax, places), places),
        "rate_percent": as_number(rate),
        "inclusive": bool(inclusive),
        "net_formatted": money_str(net, places),
        "tax_formatted": money_str(tax, places),
        "gross_formatted": money_str(quantize(net + tax, places), places),
    }


# --------------------------------------------------------------------------
# allocation and line-item checks
# --------------------------------------------------------------------------


def allocate_amount(total, weights, places: int = 2) -> dict:
    """Split ``total`` across ``weights`` so the parts sum exactly to the total.

    Uses largest-remainder so no cent is lost or invented. Weights are relative,
    not required to be percentages.
    """
    total_dec = to_decimal(total, "total")
    if total_dec < 0:
        raise MoneyError("total must be zero or positive; allocate the sign separately")
    if not isinstance(weights, (list, tuple)) or not weights:
        raise MoneyError("weights must be a non-empty list")
    weight_values = [to_decimal(w, f"weights[{i}]") for i, w in enumerate(weights)]
    if any(w < 0 for w in weight_values):
        raise MoneyError("weights must be zero or positive")
    total_weight = sum(weight_values, Decimal("0"))
    if total_weight == 0:
        raise MoneyError("weights must not sum to zero")

    total_cents = cents(total_dec)
    raw = [(w / total_weight) * total_cents for w in weight_values]
    floors = [int(r.to_integral_value(rounding="ROUND_FLOOR")) for r in raw]
    remainder = total_cents - sum(floors)

    # largest fractional part first, stable on original order
    order = sorted(
        range(len(raw)),
        key=lambda i: (-(raw[i] - floors[i]), i),
    )
    for i in order[:remainder]:
        floors[i] += 1

    parts = [from_cents(c) for c in floors]
    return {
        "total": _money(quantize(total_dec, places), places),
        "parts": [_money(p, places) for p in parts],
        "sum_of_parts": _money(sum(parts, Decimal("0")), places),
        "remainder_cents_distributed": remainder,
        "exact": sum(parts, Decimal("0")) == quantize(total_dec, places),
    }


def verify_line_items(total, line_items, tolerance: float = 0.02) -> dict:
    """Check that line items reconcile to a stated total.

    ``line_items`` accepts numbers or objects with ``amount`` (and optionally
    ``category``). Returns a per-category rollup when categories are present.
    """
    stated = to_decimal(total, "total")
    tol = to_decimal(tolerance, "tolerance")
    if tol < 0:
        raise MoneyError("tolerance must be zero or positive")
    if not isinstance(line_items, (list, tuple)):
        raise MoneyError("line_items must be a list")
    if not line_items:
        raise MoneyError("line_items must not be empty")

    amounts: list[Decimal] = []
    categories: dict[str, Decimal] = {}
    for i, item in enumerate(line_items):
        if isinstance(item, dict):
            if "amount" not in item:
                raise MoneyError(f"line_items[{i}] is an object without an 'amount' field")
            amount = to_decimal(item["amount"], f"line_items[{i}].amount")
            category = item.get("category")
            if category:
                categories[str(category)] = categories.get(str(category), Decimal("0")) + amount
        else:
            amount = to_decimal(item, f"line_items[{i}]")
        amounts.append(amount)

    computed = sum(amounts, Decimal("0"))
    difference = quantize(stated - computed, 2)
    within = difference.copy_abs() <= tol

    hints: list[str] = []
    if not within:
        if difference != 0 and difference % 9 == 0:
            hints.append("difference is divisible by 9 — check for transposed digits")
        doubled = [f"{money_str(a)}" for a in amounts if quantize(a * 2, 2).copy_abs() == difference.copy_abs()]
        if doubled:
            hints.append(
                "difference is exactly twice line(s) "
                + ", ".join(doubled)
                + " — check for a duplicate entry or a sign error"
            )
        if difference.copy_abs() in [quantize(a.copy_abs(), 2) for a in amounts]:
            hints.append("difference matches a single line amount — a line may be missing or double-counted")

    result = {
        "stated_total": _money(stated),
        "sum_of_lines": _money(computed),
        "difference": _money(difference),
        "tolerance": _money(tol),
        "reconciles": within,
        "line_count": len(amounts),
        "hints": hints,
    }
    if categories:
        result["by_category"] = {k: _money(v) for k, v in sorted(categories.items())}
    return result


# --------------------------------------------------------------------------
# vehicle
# --------------------------------------------------------------------------


def mileage_deduction(segments) -> dict:
    """Sum mileage across rate periods.

    ``segments``: list of objects with ``miles`` and ``rate_per_mile`` (or
    ``rate_cents``). Use two segments when the IRS rate changed mid-year.
    """
    if not isinstance(segments, (list, tuple)) or not segments:
        raise MoneyError("segments must be a non-empty list of {miles, rate_per_mile}")

    breakdown = []
    total_miles = Decimal("0")
    total = Decimal("0")

    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            raise MoneyError(f"segments[{i}] must be an object")
        miles = to_decimal(seg.get("miles"), f"segments[{i}].miles")
        if miles < 0:
            raise MoneyError(f"segments[{i}].miles must be zero or positive")
        if "rate_per_mile" in seg and seg["rate_per_mile"] is not None:
            rate = to_decimal(seg["rate_per_mile"], f"segments[{i}].rate_per_mile")
        elif "rate_cents" in seg and seg["rate_cents"] is not None:
            rate = to_decimal(seg["rate_cents"], f"segments[{i}].rate_cents") / HUNDRED
        else:
            raise MoneyError(f"segments[{i}] needs rate_per_mile or rate_cents")
        if not Decimal("0") <= rate <= Decimal("10"):
            raise MoneyError(f"segments[{i}] rate looks wrong for a per-mile rate: {rate}")

        amount = quantize(miles * rate, 2)
        total_miles += miles
        total += amount
        breakdown.append(
            {
                "label": seg.get("label"),
                "miles": as_number(quantize(miles, 4)),
                "rate_per_mile": as_number(quantize(rate, 4)),
                "amount": _money(amount),
            }
        )

    return {
        "total_miles": as_number(quantize(total_miles, 4)),
        "total_deduction": _money(total),
        "segments": breakdown,
        "note": "parking and tolls are claimed separately; they are not part of the mileage rate",
    }


def home_office_simplified(office_sqft, rate_per_sqft=5.0, max_sqft=300) -> dict:
    area = to_decimal(office_sqft, "office_sqft")
    if area <= 0:
        raise MoneyError("office_sqft must be greater than zero")
    usable = clamp(area, high=to_decimal(max_sqft, "max_sqft"))
    rate = to_decimal(rate_per_sqft, "rate_per_sqft")
    allowed = quantize(usable * rate, 2)
    return {
        "method": "simplified",
        "office_sqft": as_number(quantize(area, 2)),
        "usable_sqft": as_number(quantize(usable, 2)),
        "capped": area > to_decimal(max_sqft),
        "rate_per_sqft": as_number(quantize(rate, 2)),
        "deduction": _money(allowed),
        "note": "no carryforward and no depreciation under this method; the deduction still cannot create a loss",
    }


def home_office_actual(office_sqft, home_sqft, expenses) -> dict:
    """Actual-expense method: direct 100%, indirect x business-use %.

    ``expenses``: object with ``direct`` and ``indirect`` sub-objects of
    arbitrary name -> amount. Depreciation is expected in ``indirect``.
    """
    office = to_decimal(office_sqft, "office_sqft")
    home = to_decimal(home_sqft, "home_sqft")
    if office <= 0 or home <= 0:
        raise MoneyError("office_sqft and home_sqft must be greater than zero")
    if office > home:
        raise MoneyError("office_sqft cannot exceed home_sqft")
    if not isinstance(expenses, dict):
        raise MoneyError("expenses must be an object with 'direct' and/or 'indirect'")

    direct = expenses.get("direct") or {}
    indirect = expenses.get("indirect") or {}
    if not isinstance(direct, dict) or not isinstance(indirect, dict):
        raise MoneyError("expenses.direct and expenses.indirect must be objects")

    business_pct = office / home
    direct_total = sum((to_decimal(v, f"direct.{k}") for k, v in direct.items()), Decimal("0"))
    indirect_total = sum((to_decimal(v, f"indirect.{k}") for k, v in indirect.items()), Decimal("0"))
    indirect_allowed = quantize(indirect_total * business_pct, 2)
    allowed = quantize(direct_total + indirect_allowed, 2)

    return {
        "method": "actual",
        "office_sqft": as_number(quantize(office, 2)),
        "home_sqft": as_number(quantize(home, 2)),
        "business_use_percent": as_number(quantize(business_pct * HUNDRED, 4)),
        "direct_total": _money(direct_total),
        "indirect_total": _money(indirect_total),
        "indirect_allowed": _money(indirect_allowed),
        "deduction_before_income_limit": _money(allowed),
        "line_items": {
            "direct": {k: _money(v) for k, v in sorted(direct.items())},
            "indirect": {k: _money(v) for k, v in sorted(indirect.items())},
        },
        "note": "income limitation and carryforward are not applied here — check the gross-income limit separately",
    }


# --------------------------------------------------------------------------
# depreciation
# --------------------------------------------------------------------------


def straight_line(cost, salvage, life_years, business_use_percent=100.0) -> dict:
    basis = to_decimal(cost, "cost")
    residual = to_decimal(salvage, "salvage")
    life = to_decimal(life_years, "life_years")
    use = to_rate(business_use_percent, "business_use_percent")
    if life <= 0:
        raise MoneyError("life_years must be greater than zero")
    if residual < 0 or basis < 0:
        raise MoneyError("cost and salvage must be zero or positive")
    if residual > basis:
        raise MoneyError("salvage cannot exceed cost")

    annual = quantize((basis - residual) / life, 2)
    business_annual = quantize(annual * use / HUNDRED, 2)
    return {
        "method": "straight_line",
        "annual_depreciation": _money(annual),
        "business_use_percent": as_number(use),
        "annual_deduction": _money(business_annual),
        "monthly_deduction": _money(quantize(business_annual / 12, 2)),
        "years": as_number(quantize(life, 2)),
        "note": "most tax systems apply a convention (half-year, mid-quarter, part-year); apply it outside this function",
    }


def declining_balance(
    cost,
    salvage,
    life_years,
    rate_percent,
    year,
    business_use_percent=100.0,
) -> dict:
    """Declining-balance depreciation for one year of the asset's life."""
    basis = to_decimal(cost, "cost")
    residual = to_decimal(salvage, "salvage")
    life = int(quantize_int(to_decimal(life_years, "life_years")))
    rate = to_rate(rate_percent, "rate_percent") / HUNDRED
    target = int(to_decimal(year, "year"))
    use = to_rate(business_use_percent, "business_use_percent")

    if life <= 0:
        raise MoneyError("life_years must be greater than zero")
    if not 1 <= target <= life:
        raise MoneyError(f"year must be between 1 and {life}")
    if not 0 < rate <= 3:
        raise MoneyError("rate_percent must be between 0 and 300 (200 = double declining)")
    if residual > basis:
        raise MoneyError("salvage cannot exceed cost")

    opening = basis
    charge = Decimal("0")
    schedule = []
    for y in range(1, target + 1):
        charge = quantize(max(opening * rate, Decimal("0")), 2)
        if opening - charge < residual:
            charge = quantize(max(opening - residual, Decimal("0")), 2)
        schedule.append(
            {
                "year": y,
                "opening": _money(opening),
                "depreciation": _money(charge),
                "closing": _money(opening - charge),
            }
        )
        opening -= charge
        if opening <= residual:
            break

    return {
        "method": "declining_balance",
        "rate_percent": as_number(quantize(rate * HUNDRED, 4)),
        "business_use_percent": as_number(use),
        "year": target,
        "depreciation": _money(charge),
        "deduction": _money(quantize(charge * use / HUNDRED, 2)),
        "closing_basis": _money(opening),
        "schedule": schedule,
    }


def first_year_expense(
    cost,
    business_use_percent=100.0,
    bonus_rate_percent=0.0,
    section_179_available=None,
) -> dict:
    """Order of operations: business-use %, then Section 179, then bonus, then MACRS."""
    basis = to_decimal(cost, "cost")
    use = to_rate(business_use_percent, "business_use_percent")
    bonus_rate = to_rate(bonus_rate_percent, "bonus_rate_percent")

    if basis < 0:
        raise MoneyError("cost must be zero or positive")

    business_basis = quantize(basis * use / HUNDRED, 2)

    if section_179_available is None:
        limit = business_basis
    else:
        limit = clamp(
            to_decimal(section_179_available, "section_179_available"),
            low=Decimal("0"),
            high=business_basis,
        )
    elected_179 = quantize(limit, 2)
    remaining_after_179 = quantize(business_basis - elected_179, 2)

    bonus = quantize(remaining_after_179 * bonus_rate / HUNDRED, 2)
    after_bonus = quantize(remaining_after_179 - bonus, 2)

    return {
        "cost": _money(basis),
        "business_use_percent": as_number(use),
        "business_basis": _money(business_basis),
        "section_179": _money(elected_179),
        "bonus_depreciation": _money(bonus),
        "bonus_rate_percent": as_number(bonus_rate),
        "remaining_for_macrs": _money(after_bonus),
        "first_year_total_expensed": _money(elected_179 + bonus),
        "note": "Section 179 cannot create a loss; it is capped at business taxable income. Bonus can.",
    }


# --------------------------------------------------------------------------
# self-employment and estimated tax
# --------------------------------------------------------------------------


def self_employment_tax(
    net_profit,
    ss_wage_base,
    other_wages=0.0,
    additional_medicare_threshold=200000.0,
) -> dict:
    """US self-employment tax.

    ``ss_wage_base`` must come from the jurisdiction pack, not from memory.
    """
    profit = to_decimal(net_profit, "net_profit")
    wage_base = to_decimal(ss_wage_base, "ss_wage_base")
    wages = to_decimal(other_wages, "other_wages")
    addl_threshold = to_decimal(additional_medicare_threshold, "additional_medicare_threshold")

    if profit < 0:
        raise MoneyError("net_profit must be zero or positive; a loss produces no SE tax")
    if wage_base <= 0:
        raise MoneyError("ss_wage_base must be greater than zero")

    adjustment = Decimal("0.9235")
    base = quantize(profit * adjustment, 2)

    ss_room = max(wage_base - wages, Decimal("0"))
    ss_base = min(base, ss_room)
    ss_tax = quantize(ss_base * Decimal("0.124"), 2)

    medicare_tax = quantize(base * Decimal("0.029"), 2)
    combined_earnings = base + wages
    additional_medicare = quantize(max(combined_earnings - addl_threshold, Decimal("0")) * Decimal("0.009"), 2)

    total = quantize(ss_tax + medicare_tax + additional_medicare, 2)
    deductible = quantize((ss_tax + medicare_tax) / 2, 2)

    return {
        "net_profit": _money(profit),
        "se_tax_base_92_35_percent": _money(base),
        "social_security_wage_base": _money(wage_base),
        "wages_already_using_base": _money(wages),
        "social_security_base": _money(ss_base),
        "social_security_tax_12_4_percent": _money(ss_tax),
        "medicare_tax_2_9_percent": _money(medicare_tax),
        "additional_medicare_0_9_percent": _money(additional_medicare),
        "total_se_tax": _money(total),
        "deductible_half": _money(deductible),
        "note": "additional Medicare tax is not part of the deductible half",
    }


def estimated_tax_safe_harbor(
    prior_year_tax,
    prior_agi=0.0,
    current_year_tax_estimate=None,
    quarters_remaining=4,
) -> dict:
    prior = to_decimal(prior_year_tax, "prior_year_tax")
    agi = to_decimal(prior_agi, "prior_agi")
    quarters = int(quantize_int(to_decimal(quarters_remaining, "quarters_remaining")))

    if prior < 0 or agi < 0:
        raise MoneyError("prior_year_tax and prior_agi must be zero or positive")
    if not 1 <= quarters <= 4:
        raise MoneyError("quarters_remaining must be between 1 and 4")

    factor = Decimal("1.10") if agi > Decimal("150000") else Decimal("1.00")
    required_prior = quantize(prior * factor, 2)
    per_quarter = quantize(required_prior / 4, 2)

    result = {
        "prior_year_tax": _money(prior),
        "prior_year_agi": _money(agi),
        "safe_harbor_factor": as_number(factor),
        "required_annual_payment": _money(required_prior),
        "per_quarter": _money(per_quarter),
        "quarters_remaining": quarters,
        "remaining_amount": _money(quantize(per_quarter * quarters, 2)),
        "routes": {
            "prior_year_100_110_percent": _money(required_prior),
        },
    }

    if current_year_tax_estimate is not None:
        current = to_decimal(current_year_tax_estimate, "current_year_tax_estimate")
        ninety = quantize(current * Decimal("0.90"), 2)
        result["routes"]["current_year_90_percent"] = _money(ninety)
        result["recommended_target"] = _money(min(required_prior, ninety))
        result["recommended_per_quarter"] = _money(quantize(min(required_prior, ninety) / 4, 2))

    result["note"] = (
        "meeting either route avoids the underpayment penalty; the prior-year route is "
        "easier to plan but means overpaying when income falls"
    )
    return result


# --------------------------------------------------------------------------
# reconciliation and receivables
# --------------------------------------------------------------------------


def reconciliation_check(
    bank_ending,
    book_ending,
    deposits_in_transit=0.0,
    outstanding_payments=0.0,
    book_additions=0.0,
    book_subtractions=0.0,
    candidate_items=None,
) -> dict:
    """Adjusted bank balance versus adjusted book balance."""
    bank = to_decimal(bank_ending, "bank_ending")
    book = to_decimal(book_ending, "book_ending")
    deposits = to_decimal(deposits_in_transit, "deposits_in_transit")
    outstanding = to_decimal(outstanding_payments, "outstanding_payments")
    additions = to_decimal(book_additions, "book_additions")
    subtractions = to_decimal(book_subtractions, "book_subtractions")

    adjusted_bank = quantize(bank + deposits - outstanding, 2)
    adjusted_book = quantize(book + additions - subtractions, 2)
    difference = quantize(adjusted_bank - adjusted_book, 2)

    diagnostics = []
    if difference == 0:
        diagnostics.append("reconciled exactly")
    else:
        if difference % 9 == 0:
            diagnostics.append("difference is divisible by 9 — check for transposed digits")
        d = difference.copy_abs()
        if candidate_items:
            for item in candidate_items:
                try:
                    amount = to_decimal(
                        item.get("amount") if isinstance(item, dict) else item,
                        "candidate_items",
                    )
                except MoneyError:
                    continue
                if quantize(amount, 2).copy_abs() == d:
                    diagnostics.append(
                        f"difference equals a single item ({money_str(amount)}) — likely omitted or double-counted"
                    )
                if quantize(amount * 2, 2).copy_abs() == d:
                    diagnostics.append(
                        f"difference equals twice {money_str(amount)} — likely a duplicate entry or sign error"
                    )

    return {
        "adjusted_bank_balance": _money(adjusted_bank),
        "adjusted_book_balance": _money(adjusted_book),
        "difference": _money(difference),
        "reconciles": difference.copy_abs() <= Decimal("0.01"),
        "diagnostics": diagnostics,
        "components": {
            "bank_ending": _money(bank),
            "deposits_in_transit": _money(deposits),
            "outstanding_payments": _money(outstanding),
            "book_ending": _money(book),
            "book_additions": _money(additions),
            "book_subtractions": _money(subtractions),
        },
    }


AGING_BUCKETS = ("not-yet-due", "1-30", "31-60", "61-90", "90-plus", "unknown-due-date")
UNPAID_STATUSES = {"open", "overdue", "partially-paid"}


def _parse_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value)[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise MoneyError(f"cannot parse date: {value!r} (use YYYY-MM-DD)")


def ar_aging(records, as_of=None) -> dict:
    """Receivables aging from invoice records.

    Only records with an unpaid status contribute to the outstanding balance.
    """
    if not isinstance(records, (list, tuple)):
        raise MoneyError("records must be a list of invoice objects")
    reference = _parse_date(as_of) or date.today()

    buckets = {name: Decimal("0") for name in AGING_BUCKETS}
    status_counts: dict[str, int] = {}
    outstanding_total = Decimal("0")
    invoiced_total = Decimal("0")
    missing_due = 0
    currencies = set()

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise MoneyError(f"records[{i}] must be an object")
        status = str(record.get("status") or "unlabeled")
        status_counts[status] = status_counts.get(status, 0) + 1
        total = to_decimal(record.get("total_amount"), f"records[{i}].total_amount")
        paid = to_decimal(record.get("amount_paid") or 0, f"records[{i}].amount_paid")
        if record.get("currency"):
            currencies.add(str(record["currency"]).upper())

        if status in {"void", "draft"}:
            continue
        invoiced_total += total
        if status not in UNPAID_STATUSES:
            continue

        open_amount = record.get("amount_outstanding")
        if open_amount is None:
            open_amount = total - paid
        open_dec = to_decimal(open_amount, f"records[{i}].amount_outstanding")
        open_dec = max(open_dec, Decimal("0"))
        outstanding_total += open_dec

        due = None
        raw_due = record.get("due_date")
        if raw_due not in (None, ""):
            try:
                due = _parse_date(raw_due)
            except MoneyError:
                due = None
        if due is None:
            missing_due += 1
            buckets["unknown-due-date"] += open_dec
            continue

        days = (reference - due).days
        if days <= 0:
            key = "not-yet-due"
        elif days <= 30:
            key = "1-30"
        elif days <= 60:
            key = "31-60"
        elif days <= 90:
            key = "61-90"
        else:
            key = "90-plus"
        buckets[key] += open_dec

    return {
        "as_of": reference.isoformat(),
        "invoice_count": len(records),
        "status_counts": dict(sorted(status_counts.items())),
        "currencies": sorted(currencies),
        "gross_invoiced": _money(invoiced_total),
        "outstanding_total": _money(outstanding_total),
        "buckets": {k: _money(v) for k, v in buckets.items() if v != 0},
        "missing_due_date_count": missing_due,
        "overdue_total": _money(
            buckets["1-30"] + buckets["31-60"] + buckets["61-90"] + buckets["90-plus"]
        ),
    }
