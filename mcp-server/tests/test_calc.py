from __future__ import annotations

import pytest

from bookkeeping_mcp import calc
from bookkeeping_mcp.money import MoneyError


# --------------------------------------------------------------- arithmetic


def test_sum_amounts_rounds_once():
    result = calc.sum_amounts(["0.1", "0.2"])
    assert result["total"] == 0.3
    assert result["count"] == 2


def test_sum_amounts_rejects_empty():
    with pytest.raises(MoneyError):
        calc.sum_amounts([])


@pytest.mark.parametrize(
    ("operation", "expected"),
    [("of", 15.0), ("add", 215.0), ("subtract", 185.0)],
)
def test_percent_operations(operation, expected):
    assert calc.percent_calculation("200", 7.5, operation)["result"] == expected


def test_percent_reverse():
    # 121 gross at 10% implies 110 net
    assert calc.percent_calculation("121", 10, "reverse")["result"] == 110.0


def test_margin_vs_markup_differ():
    result = calc.margin_and_markup(cost=60, price=100)
    assert result["gross_profit"] == 40.0
    assert result["gross_margin_percent"] == 40.0
    assert result["markup_percent"] == pytest.approx(66.6667, abs=0.0001)


# ---------------------------------------------------------------------- tax


def test_sales_tax_exclusive():
    result = calc.sales_tax(100, 10)
    assert (result["net"], result["tax"], result["gross"]) == (100.0, 10.0, 110.0)


def test_sales_tax_inclusive_extracts():
    result = calc.sales_tax(110, 10, inclusive=True)
    assert (result["net"], result["tax"], result["gross"]) == (100.0, 10.0, 110.0)


def test_sales_tax_inclusive_with_awkward_rate():
    result = calc.sales_tax("107.50", 7.5, inclusive=True)
    assert result["net"] == 100.0
    assert result["tax"] == 7.5


def test_sales_tax_rejects_absurd_rate():
    with pytest.raises(MoneyError):
        calc.sales_tax(100, 5000)


# ---------------------------------------------------------------- allocate


def test_allocate_distributes_every_cent():
    result = calc.allocate_amount(100, [1, 1, 1])
    assert result["parts"] == [33.34, 33.33, 33.33]
    assert result["sum_of_parts"] == 100.0
    assert result["exact"] is True


def test_allocate_respects_weights_and_stays_exact():
    result = calc.allocate_amount("347.82", [89.99, 42.99, 54.95, 19.89, 34.00, 106.00])
    assert round(sum(result["parts"]), 2) == 347.82
    assert result["exact"] is True


def test_allocate_rejects_zero_weights():
    with pytest.raises(MoneyError):
        calc.allocate_amount(10, [0, 0])


# ------------------------------------------------------------- line checks


def test_line_items_that_reconcile():
    result = calc.verify_line_items(
        "347.82",
        [
            {"amount": 89.99, "category": "Equipment"},
            {"amount": 42.99, "category": "Office"},
            {"amount": 54.95, "category": "Education"},
            {"amount": 19.89, "category": "Equipment"},
            {"amount": 34.00, "category": "Supplies"},
            {"amount": 106.00, "category": "Personal"},
        ],
    )
    assert result["reconciles"] is True
    assert result["difference"] == 0
    assert result["by_category"]["Equipment"] == 109.88
    assert result["by_category"]["Personal"] == 106.0


def test_line_items_flag_transposition():
    result = calc.verify_line_items(100, [40, 24])
    # 100 - 64 = 36, divisible by 9
    assert result["reconciles"] is False
    assert any("transposed" in hint for hint in result["hints"])


def test_line_items_flag_duplicate_hypothesis():
    result = calc.verify_line_items(100, [50, 50, 50])
    assert result["difference"] == -50.0
    assert any("twice" in hint or "single line" in hint for hint in result["hints"])


# ------------------------------------------------------------------- vehicle


def test_mileage_across_two_rate_periods():
    result = calc.mileage_deduction(
        [
            {"label": "Jan-Jun", "miles": 4000, "rate_per_mile": 0.725},
            {"label": "Jul-Dec", "miles": 6000, "rate_per_mile": 0.76},
        ]
    )
    assert result["total_miles"] == 10000
    assert result["total_deduction"] == 7460.0


def test_mileage_accepts_cents_form():
    result = calc.mileage_deduction([{"miles": 100, "rate_cents": 91}])
    assert result["total_deduction"] == 91.0


def test_mileage_requires_a_rate():
    with pytest.raises(MoneyError):
        calc.mileage_deduction([{"miles": 100}])


# ---------------------------------------------------------------- home office


def test_simplified_caps_area():
    result = calc.home_office_simplified(350)
    assert result["usable_sqft"] == 300
    assert result["deduction"] == 1500.0
    assert result["capped"] is True


def test_actual_method_splits_direct_and_indirect():
    result = calc.home_office_actual(
        200,
        1800,
        {
            "direct": {"office paint": 400},
            "indirect": {"rent": 28800, "utilities": 1800, "home depreciation": 855},
        },
    )
    assert result["business_use_percent"] == pytest.approx(11.1111, abs=0.0001)
    assert result["indirect_allowed"] == 3495.0
    assert result["deduction_before_income_limit"] == 3895.0


def test_actual_method_rejects_office_larger_than_home():
    with pytest.raises(MoneyError):
        calc.home_office_actual(2000, 1800, {"indirect": {"rent": 1}})


# -------------------------------------------------------------- depreciation


def test_straight_line_annual_and_monthly():
    result = calc.straight_line(30000, 3000, 5, 80)
    assert result["annual_depreciation"] == 5400.0
    assert result["annual_deduction"] == 4320.0
    assert result["monthly_deduction"] == 360.0


def test_declining_balance_stops_at_salvage():
    result = calc.declining_balance(1000, 100, 5, 200, 4)
    assert result["closing_basis"] >= 100
    assert all(step["closing"] >= 100 for step in result["schedule"])


def test_first_year_expense_order_of_operations():
    result = calc.first_year_expense(
        cost=10000,
        business_use_percent=100,
        bonus_rate_percent=100,
        section_179_available=0,
    )
    assert result["business_basis"] == 10000.0
    assert result["section_179"] == 0.0
    assert result["bonus_depreciation"] == 10000.0
    assert result["remaining_for_macrs"] == 0.0


def test_first_year_expense_respects_business_use():
    result = calc.first_year_expense(cost=10000, business_use_percent=50, bonus_rate_percent=0)
    assert result["business_basis"] == 5000.0


# ----------------------------------------------------------------- se tax


def test_self_employment_tax_known_example():
    result = calc.self_employment_tax(100000, ss_wage_base=184500)
    assert result["se_tax_base_92_35_percent"] == 92350.0
    assert result["social_security_tax_12_4_percent"] == 11451.40
    assert result["medicare_tax_2_9_percent"] == 2678.15
    assert result["total_se_tax"] == 14129.55
    assert result["deductible_half"] == 7064.78


def test_self_employment_tax_social_security_cap():
    result = calc.self_employment_tax(400000, ss_wage_base=184500)
    assert result["social_security_base"] == 184500.0
    assert result["additional_medicare_0_9_percent"] > 0


def test_self_employment_tax_wages_consume_the_cap():
    result = calc.self_employment_tax(100000, ss_wage_base=184500, other_wages=184500)
    assert result["social_security_tax_12_4_percent"] == 0.0


def test_self_employment_tax_rejects_loss():
    with pytest.raises(MoneyError):
        calc.self_employment_tax(-1000, ss_wage_base=184500)


# ------------------------------------------------------------- safe harbour


def test_safe_harbor_uses_110_percent_above_150k():
    result = calc.estimated_tax_safe_harbor(30000, prior_agi=200000)
    assert result["safe_harbor_factor"] == 1.1
    assert result["required_annual_payment"] == 33000.0
    assert result["per_quarter"] == 8250.0


def test_safe_harbor_recommends_lower_route_when_income_falls():
    result = calc.estimated_tax_safe_harbor(30000, prior_agi=50000, current_year_tax_estimate=10000)
    assert result["routes"]["prior_year_100_110_percent"] == 30000.0
    assert result["routes"]["current_year_90_percent"] == 9000.0
    assert result["recommended_target"] == 9000.0


# ----------------------------------------------------------- reconciliation


def test_reconciliation_balances():
    result = calc.reconciliation_check(
        bank_ending="24567.89",
        deposits_in_transit="3200.00",
        outstanding_payments="1845.50",
        book_ending="25674.39",
        book_additions="248.00",
    )
    assert result["adjusted_bank_balance"] == 25922.39
    assert result["adjusted_book_balance"] == 25922.39
    assert result["difference"] == 0
    assert result["reconciles"] is True


def test_reconciliation_reports_difference_and_hint():
    result = calc.reconciliation_check(
        bank_ending=1000,
        book_ending=964,
        candidate_items=[18],
    )
    assert result["reconciles"] is False
    assert result["difference"] == 36.0
    assert any("transposed" in d for d in result["diagnostics"])


# ------------------------------------------------------------------ aging


def test_ar_aging_buckets_and_ignores_void():
    records = [
        {"status": "open", "total_amount": 1000, "due_date": "2026-12-15"},
        {"status": "overdue", "total_amount": 500, "due_date": "2026-11-01"},
        {"status": "overdue", "total_amount": 300, "due_date": "2026-08-01"},
        {"status": "paid", "total_amount": 700, "due_date": "2026-10-01", "amount_paid": 700},
        {"status": "open", "total_amount": 200},
        {"status": "void", "total_amount": 900, "due_date": "2026-01-01"},
    ]
    result = calc.ar_aging(records, as_of="2026-11-30")
    assert result["outstanding_total"] == 2000.0
    assert result["buckets"]["not-yet-due"] == 1000.0
    assert result["buckets"]["1-30"] == 500.0
    assert result["buckets"]["90-plus"] == 300.0
    assert result["buckets"]["unknown-due-date"] == 200.0
    assert result["overdue_total"] == 800.0
    assert result["status_counts"]["void"] == 1


def test_ar_aging_uses_partial_payments():
    records = [
        {"status": "partially-paid", "total_amount": 1000, "amount_paid": 400, "due_date": "2026-11-20"}
    ]
    result = calc.ar_aging(records, as_of="2026-11-30")
    assert result["outstanding_total"] == 600.0
