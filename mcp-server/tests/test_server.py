from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from bookkeeping_mcp.server import build_server
from helpers import call


EXPECTED_TOOLS = {
    "list_jurisdictions",
    "get_constants",
    "sum_amounts",
    "round_amount",
    "percent_calculation",
    "margin_and_markup",
    "sales_tax",
    "allocate_amount",
    "verify_line_items",
    "mileage_deduction",
    "home_office_simplified",
    "home_office_actual",
    "straight_line_depreciation",
    "declining_balance_depreciation",
    "first_year_asset_expense",
    "self_employment_tax",
    "estimated_tax_safe_harbor",
    "reconciliation_check",
    "ar_aging",
    "calculate",
    "run_python",
}


@pytest.fixture()
def server(repo_root: Path):
    return build_server(repo_root)


async def test_all_tools_are_registered(server):
    async with Client(server) as client:
        tools = {tool.name for tool in await client.list_tools()}
    assert tools == EXPECTED_TOOLS


async def test_every_tool_has_a_description(server):
    async with Client(server) as client:
        for tool in await client.list_tools():
            assert tool.description, f"{tool.name} has no description"
            assert len(tool.description) > 20, f"{tool.name} description is too thin"
            assert tool.inputSchema, f"{tool.name} has no input schema"


async def test_list_jurisdictions(server, repo_root: Path):
    async with Client(server) as client:
        result = await call(client, "list_jurisdictions")
    assert result["repo_root"] == str(repo_root)
    codes = {entry["code"] for entry in result["jurisdictions"]}
    assert codes == {"us", "au", "nz"}


async def test_get_constants_filters(server):
    async with Client(server) as client:
        result = await call(client, "get_constants", {"jurisdiction": "us", "query": "mileage"})
    assert result["jurisdiction"] == "us"
    assert result["matched"] >= 1
    assert result["stale"] is False
    assert all("mileage" in row["topic"].lower() for row in result["rows"])
    assert result["last_reviewed"]


async def test_get_constants_reports_available_topics_on_miss(server):
    async with Client(server) as client:
        result = await call(client, "get_constants", {"jurisdiction": "au", "query": "zzzz"})
    assert result["matched"] == 0
    assert result["available_topics"]
    assert result["warning"]


async def test_get_constants_rejects_unknown_jurisdiction(server):
    async with Client(server) as client:
        with pytest.raises(Exception, match="Unknown jurisdiction"):
            await call(client, "get_constants", {"jurisdiction": "zz"})


async def test_sales_tax_tool(server):
    async with Client(server) as client:
        result = await call(client, "sales_tax", {"amount": 110, "rate_percent": 10, "inclusive": True})
    assert result["net"] == 100.0
    assert result["tax"] == 10.0
    assert result["gross_formatted"] == "110.00"


async def test_allocate_tool_sums_exactly(server):
    async with Client(server) as client:
        result = await call(client, "allocate_amount", {"total": 100, "weights": [1, 1, 1]})
    assert result["parts"] == [33.34, 33.33, 33.33]
    assert result["exact"] is True


async def test_self_employment_tax_reads_wage_base_from_pack(server):
    async with Client(server) as client:
        result = await call(client, "self_employment_tax", {"net_profit": 100000})
    # wage base comes from jurisdictions/us.md, not from the caller
    assert result["social_security_wage_base"] > 100000
    assert result["total_se_tax"] > 0
    assert result["deductible_half"] == pytest.approx(result["total_se_tax"] / 2, abs=0.01)


async def test_calculate_tool(server):
    async with Client(server) as client:
        result = await call(client, "calculate", {"expression": "(1234.56 - 200) * 0.7"})
    assert result["value"] == pytest.approx(724.192)
    assert result["exact"].startswith("724.192")


async def test_calculate_rejects_code(server):
    async with Client(server) as client:
        with pytest.raises(Exception, match="fixed maths function whitelist|only numeric|disallowed"):
            await call(client, "calculate", {"expression": "__import__('os')"})


async def test_run_python_tool(server):
    async with Client(server) as client:
        result = await call(client, "run_python", {"code": "sum(range(1, 11))"})
    assert result["ok"] is True
    assert result["stdout"].strip() == "55"


async def test_reconciliation_tool_balances(server):
    async with Client(server) as client:
        result = await call(
            client,
            "reconciliation_check",
            {
                "bank_ending": 24567.89,
                "book_ending": 25674.39,
                "deposits_in_transit": 3200.00,
                "outstanding_payments": 1845.50,
                "book_additions": 248.00,
            },
        )
    assert result["reconciles"] is True
    assert result["difference"] == 0


async def test_verify_line_items_tool(server):
    async with Client(server) as client:
        result = await call(
            client,
            "verify_line_items",
            {
                "total": 347.82,
                "line_items": [
                    {"amount": 89.99, "category": "Equipment"},
                    {"amount": 42.99, "category": "Office"},
                    {"amount": 54.95, "category": "Education"},
                    {"amount": 19.89, "category": "Equipment"},
                    {"amount": 34.00, "category": "Supplies"},
                    {"amount": 106.00, "category": "Personal"},
                ],
            },
        )
    assert result["reconciles"] is True
    assert result["by_category"]["Equipment"] == 109.88


async def test_ar_aging_tool(server):
    records = [
        {"status": "open", "total_amount": 1000, "due_date": "2026-12-15"},
        {"status": "overdue", "total_amount": 500, "due_date": "2026-11-01"},
    ]
    async with Client(server) as client:
        result = await call(client, "ar_aging", {"records": records, "as_of": "2026-11-30"})
    assert result["outstanding_total"] == 1500.0
    assert result["buckets"]["not-yet-due"] == 1000.0
    assert result["buckets"]["1-30"] == 500.0


async def test_resources_are_listed_and_readable(server):
    async with Client(server) as client:
        resources = {str(resource.uri) for resource in await client.list_resources()}
        assert "bookkeeping://jurisdictions" in resources

        raw = await client.read_resource("jurisdiction://au")
        text = raw[0].text if isinstance(raw, list) else raw
        assert "Current-law constants" in text

        skill = await client.read_resource("skill://income-invoicing")
        skill_text = skill[0].text if isinstance(skill, list) else skill
        assert "Income and Invoicing" in skill_text


async def test_unknown_skill_resource_raises(server):
    async with Client(server) as client:
        with pytest.raises(Exception, match="Unknown skill"):
            await client.read_resource("skill://does-not-exist")
