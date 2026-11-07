"""bookkeeping-mcp — a calculation companion for the bookkeeping-skills pack.

The server has three jobs:

1. **Stop the guesswork on current-law figures.** ``get_constants`` reads the
   ``Current-law constants`` table out of the repository's jurisdiction packs,
   so a figure is never recalled from a model's memory.
2. **Do money arithmetic exactly.** Every calculation is Decimal-based and
   quantized once, with no float drift and no silent rounding.
3. **Give the agent a calculator.** ``calculate`` for safe arithmetic,
   ``run_python`` for anything else, sandboxed with a timeout.

Run it over stdio (the default) for Claude Code, Codex, Cursor or any MCP host:

    bookkeeping-mcp
    python3 -m bookkeeping_mcp
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from . import calc
from .constants import (
    RepositoryError,
    find_repo_root,
    get_acc_levy_schedule,
    get_jurisdiction,
    load_jurisdictions,
    search_constants,
    search_levy_rows,
)
from .models import (
    AccLevyEstimate,
    AccLevyRates,
    AgingResult,
    AllocationResult,
    ConstantsResult,
    ConstantRow,
    EvaluationResult,
    ExecutionResult,
    JurisdictionList,
    JurisdictionSummary,
    LevyRowOut,
    LineCheckResult,
    ReconciliationResult,
    SalesTaxResult,
    SelfEmploymentTaxResult,
)
from .registry import (
    CORE_TOOLS,
    REGISTRY,
    SKILL_ENTRIES,
    groups as registry_groups,
    search_registry,
)
from .runner import evaluate_expression, run_python as exec_python
from .money import MoneyError

INSTRUCTIONS = """\
You are connected to the bookkeeping-skills calculation server.

Rules for using it:

1. Before quoting any tax rate, threshold, limit, penalty or mileage figure,
   call `get_constants` for the user's jurisdiction. Never state one from
   memory. If the pack reports `stale: true`, say so and treat every figure as
   unverified.
2. Do arithmetic for money with the tools here, not mentally and not with
   floats. Use `sales_tax`, `percent_calculation`, `allocate_amount`,
   `verify_line_items`, `mileage_deduction`, the home-office tools, the
   depreciation tools, `self_employment_tax` and `reconciliation_check` where
   they apply; use `calculate` for anything else.
3. Use `run_python` only when a calculation genuinely needs a loop or data
   manipulation. It runs locally with a timeout and no network guarantees.
4. These tools compute. They do not decide tax treatment, and they never post
   to an accounting system. A result is a draft for review, not a filing
   position.
5. State the tax year you used in your answer.
"""

JurisdictionCode = Annotated[
    str,
    Field(
        description=(
            "Jurisdiction pack code: 'us', 'au' or 'nz' "
            "(aliases: usa, united states, australia, new zealand, aotearoa)"
        )
    ),
]

Amount = Annotated[float, Field(description="Monetary amount. Strings like '1,234.56' are also accepted.")]
RatePercent = Annotated[float, Field(description="A percentage, not a fraction: 10 means 10%, 8.875 means 8.875%")]


def _repo_error(exc: RepositoryError) -> ValueError:
    return ValueError(str(exc))


def _install_direct_call_guard(mcp: FastMCP, hidden: set[str]) -> None:
    """Answer a direct call to a hidden tool with a clean, actionable error.

    In search mode the hidden tools are removed from the tool manager, so a
    direct call falls through to the low-level SDK, which logs
    "Tool '<name>' not listed, no validation will be performed" and then fails
    with a bare "Unknown tool". That is noise in a log and a dead end for the
    model. Intercepting the protocol handler lets us reply in the same shape as
    any other tool error, with the fix in the message.

    Best-effort by design: if a future SDK moves these hooks, the server keeps
    working and simply falls back to the old behaviour.
    """
    try:
        from mcp import types

        handlers = getattr(getattr(mcp, "_mcp_server", None), "request_handlers", None)
        if not isinstance(handlers, dict):
            return
        original = handlers.get(types.CallToolRequest)
        if original is None:
            return

        async def guarded(request):
            name = getattr(getattr(request, "params", None), "name", "")
            if name in hidden:
                message = (
                    f"Tool {name!r} is not listed in search mode. Call run_tool with "
                    f"name={name!r} and the arguments it needs, or use search_tools to pick "
                    "a tool. See search_tools(detail=...) for the exact parameter schema."
                )
                make_error = getattr(mcp._mcp_server, "_make_error_result", None)
                if callable(make_error):
                    return make_error(message)
                return types.ServerResult(
                    types.CallToolResult(
                        content=[types.TextContent(type="text", text=message)],
                        isError=True,
                    )
                )
            return await original(request)

        handlers[types.CallToolRequest] = guarded
    except Exception:  # pragma: no cover - cosmetic guard, never break the server
        return


def build_server(root: Path | None = None, tool_mode: str | None = None) -> FastMCP:
    """Build the server.

    ``root`` overrides jurisdiction-pack discovery. ``tool_mode`` is "all" (default,
    every tool listed) or "search" (six tools plus ``run_tool``), also settable
    with BOOKKEEPING_MCP_TOOL_MODE.
    """
    repo_root = root or find_repo_root()
    tool_mode = (tool_mode or os.environ.get("BOOKKEEPING_MCP_TOOL_MODE", "all")).strip().lower()
    if tool_mode not in {"all", "search"}:
        raise ValueError("tool_mode must be \"all\" or \"search\"")

    mcp = FastMCP(
        name="bookkeeping-calc",
        instructions=INSTRUCTIONS,
    )

    # ----------------------------------------------------------------- resources

    @mcp.resource("bookkeeping://jurisdictions")
    def jurisdictions_resource() -> dict:
        """Available jurisdiction packs, their review dates, and staleness."""
        try:
            packs = load_jurisdictions(repo_root)
        except RepositoryError as exc:
            raise _repo_error(exc) from exc
        return {
            "repo_root": str(repo_root),
            "jurisdictions": [pack.to_summary() for pack in packs.values()],
        }

    @mcp.resource("jurisdiction://{code}")
    def jurisdiction_resource(code: str) -> str:
        """The raw markdown of a jurisdiction pack."""
        try:
            return get_jurisdiction(code, repo_root).path.read_text(encoding="utf-8")
        except RepositoryError as exc:
            raise _repo_error(exc) from exc

    @mcp.resource("skill://{name}")
    def skill_resource(name: str) -> str:
        """The raw markdown of a skill's SKILL.md."""
        candidate = repo_root / "skills" / name / "SKILL.md"
        if not candidate.is_file():
            root_skill = repo_root / "SKILL.md"
            if name.lower() in {"root", "bookkeeping"} and root_skill.is_file():
                return root_skill.read_text(encoding="utf-8")
            available = sorted(p.name for p in (repo_root / "skills").glob("*/SKILL.md"))
            raise ValueError(
                f"Unknown skill {name!r}. Available: {', '.join(p.split('/')[0] for p in available)}"
            )
        return candidate.read_text(encoding="utf-8")

    # --------------------------------------------------------------- constants

    @mcp.tool()
    def list_jurisdictions() -> JurisdictionList:
        """List the jurisdiction packs available in the skills repository.

        Call this first when you do not know which packs exist.
        """
        try:
            packs = load_jurisdictions(repo_root)
        except RepositoryError as exc:
            raise _repo_error(exc) from exc
        return JurisdictionList(
            repo_root=str(repo_root),
            jurisdictions=[JurisdictionSummary(**pack.to_summary()) for pack in packs.values()],
        )

    @mcp.tool()
    def get_constants(
        jurisdiction: JurisdictionCode,
        query: Annotated[
            str | None,
            Field(description="Optional filter on topic, e.g. 'mileage', 'section 179', '1099 penalty'"),
        ] = None,
    ) -> ConstantsResult:
        """Read current-law figures from a jurisdiction pack.

        This is the only acceptable source for mileage rates, Section 179 and
        bonus limits, 1099 thresholds and penalties, self-employment tax
        parameters and standard deductions. Returns the value as written, the
        numbers extracted from it, the source URL and the date it was verified.
        """
        try:
            pack = get_jurisdiction(jurisdiction, repo_root)
        except RepositoryError as exc:
            raise _repo_error(exc) from exc

        rows = search_constants(pack, query)
        warning = None
        if pack.is_stale():
            warning = (
                f"This pack was last reviewed on "
                f"{pack.last_reviewed.isoformat() if pack.last_reviewed else 'an unknown date'}, "
                "more than 12 months ago. Treat every figure as unverified and tell the user."
            )
        if not rows:
            warning = (
                (warning + " ") if warning else ""
            ) + "No constant matched the query; see available_topics."

        return ConstantsResult(
            jurisdiction=pack.code,
            name=pack.name,
            last_reviewed=pack.last_reviewed.isoformat() if pack.last_reviewed else None,
            age_days=pack.age_days(),
            stale=pack.is_stale(),
            query=query,
            matched=len(rows),
            rows=[ConstantRow(**row.to_dict()) for row in rows],
            warning=warning,
            available_topics=sorted({row.topic for row in pack.rows}),
        )

    # ------------------------------------------------------------------- maths

    @mcp.tool()
    def sum_amounts(
        amounts: Annotated[list[float], Field(description="Amounts to add")],
    ) -> dict:
        """Add a list of amounts exactly, then round once."""
        return calc.sum_amounts(amounts)

    @mcp.tool()
    def round_amount(
        amount: Amount,
        places: Annotated[int, Field(description="Decimal places, 0-8")] = 2,
        mode: Annotated[
            str,
            Field(description="half_up (default), half_even, down, up, floor, ceiling"),
        ] = "half_up",
    ) -> dict:
        """Round an amount and report the exact adjustment made."""
        return calc.round_amount(amount, places, mode)

    @mcp.tool()
    def percent_calculation(
        amount: Amount,
        rate_percent: RatePercent,
        operation: Annotated[
            str,
            Field(description="of | add | subtract | reverse (reverse turns a gross into a net)"),
        ] = "of",
    ) -> dict:
        """Apply a percentage: find the portion, add it, subtract it, or reverse it."""
        return calc.percent_calculation(amount, rate_percent, operation)

    @mcp.tool()
    def margin_and_markup(cost: Amount, price: Amount) -> dict:
        """Gross profit, gross margin % and markup % — and why they differ."""
        return calc.margin_and_markup(cost, price)

    @mcp.tool()
    def sales_tax(
        amount: Amount,
        rate_percent: RatePercent,
        inclusive: Annotated[
            bool,
            Field(description="True if 'amount' already includes tax (GST/VAT-inclusive); False if tax is added on top"),
        ] = False,
    ) -> SalesTaxResult:
        """Split an amount into net, tax and gross for any sales tax, GST or VAT rate."""
        return SalesTaxResult(**calc.sales_tax(amount, rate_percent, inclusive))

    @mcp.tool()
    def allocate_amount(
        total: Amount,
        weights: Annotated[list[float], Field(description="Relative weights, e.g. line-item amounts or [60, 40]")],
    ) -> AllocationResult:
        """Split a total across weights so the parts sum exactly — no lost cents.

        Use this for splitting a mixed receipt across categories, or a payout
        across invoices.
        """
        return AllocationResult(**calc.allocate_amount(total, weights))

    @mcp.tool()
    def verify_line_items(
        total: Amount,
        line_items: Annotated[
            list[Any],
            Field(description="Numbers, or objects like {\"amount\": 12.5, \"category\": \"Office\"}"),
        ],
        tolerance: Annotated[float, Field(description="Allowed difference, default 0.02")] = 0.02,
    ) -> LineCheckResult:
        """Check that lines reconcile to a stated total, with per-category totals.

        Reports the difference and explains common causes (transposition,
        duplicates, sign errors). It never adjusts anything.
        """
        return LineCheckResult(**calc.verify_line_items(total, line_items, tolerance))

    # ------------------------------------------------------------------ domain

    @mcp.tool()
    def mileage_deduction(
        segments: Annotated[
            list[dict[str, Any]],
            Field(
                description=(
                    "Rate periods: [{\"label\": \"Jan-Jun\", \"miles\": 4000, \"rate_per_mile\": 0.725}]. "
                    "Read rate_per_mile from get_constants — do not recall it."
                )
            ),
        ],
    ) -> dict:
        """Compute a standard-mileage deduction across one or more rate periods."""
        return calc.mileage_deduction(segments)

    @mcp.tool()
    def home_office_simplified(
        office_sqft: Annotated[float, Field(description="Area used regularly and exclusively for business, in square feet")],
        rate_per_sqft: Annotated[float, Field(description="Per-square-foot rate from get_constants (US: 5.00)")] = 5.0,
        max_sqft: Annotated[float, Field(description="Statutory area cap (US: 300)")] = 300.0,
    ) -> dict:
        """Simplified home-office deduction, with the area cap applied."""
        return calc.home_office_simplified(office_sqft, rate_per_sqft, max_sqft)

    @mcp.tool()
    def home_office_actual(
        office_sqft: Annotated[float, Field(description="Business-use area in square feet")],
        home_sqft: Annotated[float, Field(description="Total home area in square feet")],
        expenses: Annotated[
            dict[str, Any],
            Field(
                description=(
                    'Expenses split by behaviour: {"direct": {"office paint": 400}, '
                    '"indirect": {"rent": 28800, "utilities": 1800, "home depreciation": 855}}'
                )
            ),
        ],
    ) -> dict:
        """Actual-expense home-office deduction: direct at 100%, indirect at business-use %."""
        return calc.home_office_actual(office_sqft, home_sqft, expenses)

    @mcp.tool()
    def straight_line_depreciation(
        cost: Amount,
        salvage: Amount,
        life_years: Annotated[float, Field(description="Useful life or recovery period in years")],
        business_use_percent: Annotated[float, Field(description="Business-use percentage, e.g. 100 or 75")] = 100.0,
    ) -> dict:
        """Straight-line depreciation, annual and monthly, at the business-use %."""
        return calc.straight_line(cost, salvage, life_years, business_use_percent)

    @mcp.tool()
    def declining_balance_depreciation(
        cost: Amount,
        salvage: Amount,
        life_years: Annotated[int, Field(description="Recovery period in whole years")],
        rate_percent: Annotated[float, Field(description="Declining-balance rate, e.g. 200 for 200% declining balance")],
        year: Annotated[int, Field(description="Which year of the asset's life to report")],
        business_use_percent: Annotated[float, Field(description="Business-use percentage")] = 100.0,
    ) -> dict:
        """Declining-balance depreciation for one year, plus the schedule to date."""
        return calc.declining_balance(cost, salvage, life_years, rate_percent, year, business_use_percent)

    @mcp.tool()
    def first_year_asset_expense(
        cost: Amount,
        business_use_percent: Annotated[float, Field(description="Business-use percentage")] = 100.0,
        bonus_rate_percent: Annotated[
            float, Field(description="Bonus depreciation percentage for the year, from get_constants")
        ] = 0.0,
        section_179_available: Annotated[
            float | None,
            Field(description="How much Section 179 capacity to apply. Omit for business basis."),
        ] = None,
    ) -> dict:
        """First-year asset expense in the correct order: business use %, Section 179, bonus, remainder."""
        return calc.first_year_expense(cost, business_use_percent, bonus_rate_percent, section_179_available)

    @mcp.tool()
    def self_employment_tax(
        net_profit: Amount,
        ss_wage_base: Annotated[
            float | None,
            Field(description="Social Security wage base. Omit to read it from the US jurisdiction pack."),
        ] = None,
        other_wages: Annotated[float, Field(description="W-2 wages already counted against the wage base")] = 0.0,
        additional_medicare_threshold: Annotated[
            float, Field(description="US: 200000 single, 250000 married filing jointly")
        ] = 200000.0,
    ) -> SelfEmploymentTaxResult:
        """US self-employment tax: 92.35% base, 12.4% Social Security cap, 2.9% Medicare, 0.9% surtax."""
        if ss_wage_base is None:
            try:
                pack = get_jurisdiction("us", repo_root)
            except RepositoryError as exc:
                raise _repo_error(exc) from exc
            for row in pack.rows:
                if "social security wage base" in row.topic.lower():
                    numbers = row.numbers
                    if numbers:
                        ss_wage_base = numbers[0]
                        break
            if ss_wage_base is None:
                raise ValueError(
                    "Could not read the Social Security wage base from the US pack. "
                    "Pass ss_wage_base explicitly."
                )
        return SelfEmploymentTaxResult(
            **calc.self_employment_tax(
                net_profit, ss_wage_base, other_wages, additional_medicare_threshold
            )
        )

    @mcp.tool()
    def estimated_tax_safe_harbor(
        prior_year_tax: Amount,
        prior_agi: Amount = 0.0,
        current_year_tax_estimate: Annotated[
            float | None, Field(description="Optional current-year tax estimate to test the 90% route")
        ] = None,
        quarters_remaining: Annotated[int, Field(description="Quarters left in the year, 1-4")] = 4,
    ) -> dict:
        """Prior-year 100%/110% safe harbour and, optionally, the current-year 90% route."""
        return calc.estimated_tax_safe_harbor(
            prior_year_tax, prior_agi, current_year_tax_estimate, quarters_remaining
        )

    @mcp.tool()
    def reconciliation_check(
        bank_ending: Amount,
        book_ending: Amount,
        deposits_in_transit: Amount = 0.0,
        outstanding_payments: Amount = 0.0,
        book_additions: Amount = 0.0,
        book_subtractions: Amount = 0.0,
        candidate_items: Annotated[
            list[float] | None,
            Field(description="Optional transaction amounts to test against the difference"),
        ] = None,
    ) -> ReconciliationResult:
        """Adjusted bank versus adjusted book balance, and why they differ."""
        return ReconciliationResult(
            **calc.reconciliation_check(
                bank_ending,
                book_ending,
                deposits_in_transit,
                outstanding_payments,
                book_additions,
                book_subtractions,
                candidate_items,
            )
        )

    @mcp.tool()
    def ar_aging(
        records: Annotated[
            list[dict[str, Any]],
            Field(
                description=(
                    "Invoice records: {status, total_amount, amount_paid?, due_date?, currency?}. "
                    "Statuses: paid, open, partially-paid, overdue, credited, draft, void."
                )
            ),
        ],
        as_of: Annotated[
            str | None, Field(description="Aging reference date YYYY-MM-DD; defaults to today")
        ] = None,
    ) -> AgingResult:
        """Receivables aging buckets from invoice records."""
        return AgingResult(**calc.ar_aging(records, as_of))

    # ------------------------------------------------------------ calculation

    @mcp.tool()
    def calculate(
        expression: Annotated[
            str,
            Field(
                description=(
                    "Arithmetic only: + - * / // % **, parentheses, and abs/min/max/sum/round/sqrt/log/exp. "
                    "Example: '(1234.56 - 200) * 0.7'"
                )
            ),
        ],
    ) -> EvaluationResult:
        """Evaluate an arithmetic expression exactly, using Decimal, with no side effects."""
        return EvaluationResult(**evaluate_expression(expression))

    @mcp.tool()
    def run_python(
        code: Annotated[str, Field(description="Python source. A trailing bare expression is echoed.")],
        timeout_seconds: Annotated[float, Field(description="Wall-clock limit, 0.1 to 30")] = 10.0,
    ) -> ExecutionResult:
        """Run Python in an isolated child process and return stdout/stderr.

        Use for loops, CSV/JSON reshaping and anything `calculate` cannot do.
        The process gets a scratch working directory, a minimal environment, and
        CPU/memory/file-size limits. There is no network isolation, so do not
        treat this as a security boundary against hostile code.
        """
        return ExecutionResult(**exec_python(code, timeout_seconds))

    # ------------------------------------------------------- ACC work levy (NZ)

    @mcp.tool()
    def acc_work_levy_rates(
        trade: Annotated[
            str | None,
            Field(
                description=(
                    "Trade name or CU number, e.g. 'carpentry', 'plumber', 'roofing', '42420'. "
                    "Omit for the full schedule."
                )
            ),
        ] = None,
    ) -> AccLevyRates:
        """New Zealand ACC work levy rates by classification unit.

        Rates are per $100 of liable earnings excluding GST, as published in the
        Work Account Levies Regulations. The rate is risk-rated by trade, so a
        roofer and an electrician on the same income pay very different levies.
        """
        try:
            schedule = get_acc_levy_schedule(repo_root)
        except RepositoryError as exc:
            raise _repo_error(exc) from exc

        rows = search_levy_rows(schedule, trade)
        note = None
        if trade and not rows:
            note = (
                "No classification unit matched. Call without 'trade' for the full "
                "schedule, or pass the CU number."
            )

        return AccLevyRates(
            jurisdiction="nz",
            year=schedule.year,
            basis=schedule.basis,
            source_url=schedule.source_url,
            matched=len(rows),
            rows=[LevyRowOut(**row.to_dict()) for row in rows],
            note=note,
        )

    @mcp.tool()
    def acc_levy_estimate(
        liable_income: Annotated[float, Field(description="Annual liable earnings before ACC levies")],
        trade: Annotated[
            str, Field(description="Trade name or CU number, e.g. 'carpentry' or '42420'")
        ],
        include_gst: Annotated[bool, Field(description="Add 15% GST, as ACC invoices it")] = True,
    ) -> AccLevyEstimate:
        """Estimate a New Zealand self-employed ACC invoice.

        Three levies on one capped base: the trade-specific work levy, the flat
        Working Safer levy, and the flat earners' levy. The base is capped at the
        maximum liable earnings from the pack. The statutory minimum is not
        applied — it depends on the taxpayer's circumstances.
        """
        try:
            schedule = get_acc_levy_schedule(repo_root)
            pack = get_jurisdiction("nz", repo_root)
        except RepositoryError as exc:
            raise _repo_error(exc) from exc

        rows = search_levy_rows(schedule, trade)
        if not rows:
            raise ValueError(
                f"No ACC classification unit matched {trade!r}. "
                "Call acc_work_levy_rates without a trade to see the schedule."
            )
        if len(rows) > 1:
            names = "; ".join(f"{r.cu} {r.classification}" for r in rows[:5])
            raise ValueError(
                f"{trade!r} matched {len(rows)} classification units. Be more specific or pass "
                f"a CU number. Matches: {names}"
            )

        row = rows[0]
        earners_rate = None
        safer_rate = None
        max_earnings = None
        for constant in pack.rows:
            topic = constant.topic.lower()
            if "earners' levy rate (excluding gst)" in topic and constant.numbers:
                earners_rate = constant.numbers[0]
            elif "working safer" in topic and constant.numbers:
                safer_rate = constant.numbers[0]
            elif topic.startswith("acc maximum liable earnings") and constant.numbers:
                max_earnings = constant.numbers[0]

        if earners_rate is None or safer_rate is None or max_earnings is None:
            raise ValueError(
                "The NZ pack is missing the earners' levy rate, the Working Safer rate or "
                "the maximum liable earnings; add them to jurisdictions/nz.md."
            )

        result = calc.acc_levy(
            liable_income,
            work_levy_rate_per_100=row.rate,
            earners_levy_rate_per_100=earners_rate,
            working_safer_rate_per_100=safer_rate,
            max_liable_earnings=max_earnings,
            include_gst=include_gst,
        )
        return AccLevyEstimate(
            cu=row.cu,
            classification=row.classification,
            **result,
        )

    # ------------------------------------------------------- tool discovery

    manager = getattr(mcp, "_tool_manager", None)
    live = getattr(manager, "_tools", None) if manager is not None else None
    if not isinstance(live, dict):
        raise RuntimeError(
            "This fastmcp build does not expose the tool registry, so the search layer "
            "cannot be built. Install fastmcp>=2.1."
        )

    snapshot = dict(live)

    @mcp.tool()
    def search_tools(
        query: Annotated[
            str | None,
            Field(
                description=(
                    "What you want to do, in your own words: 'how much tax do I owe this "
                    "quarter', 'split this receipt', 'ACC levy for a roofer'. Omit to list groups."
                )
            ),
        ] = None,
        detail: Annotated[
            str | None,
            Field(description="A tool name to return the full parameter schema for"),
        ] = None,
        limit: Annotated[int, Field(description="Maximum matches to return, 1-15")] = 5,
    ) -> dict:
        """Find the right tool for a job, in natural language.

        Use this first when you are unsure which of the bookkeeping tools applies.
        Returns the best matches with their required parameters and a ready-to-run
        example. In search mode, call `run_tool` with the matched name.
        """
        if detail:
            target = snapshot.get(detail)
            if target is None:
                return {
                    "error": f"Unknown tool {detail!r}",
                    "available": sorted(n for n in snapshot if n not in {"search_tools", "run_tool"}),
                }
            entry = next((e for e in REGISTRY if e.name == detail), None)
            return {
                "name": detail,
                "summary": entry.summary if entry else (target.description or "").splitlines()[0],
                "parameters": target.parameters,
                "example_arguments": entry.example if entry else None,
            }

        if not query:
            return {
                "tool_count": len([n for n in snapshot if n not in {"search_tools", "run_tool"}]),
                "groups": registry_groups(),
                "hint": "Pass a query to rank tools, or detail='<name>' for a full schema.",
            }

        limit = max(1, min(int(limit or 5), 15))
        matches = search_registry(query, limit)
        if not matches:
            return {
                "query": query,
                "matched": 0,
                "groups": registry_groups(),
                "hint": "No match. Try a different phrase or pass detail='<tool name>'.",
            }

        return {
            "query": query,
            "matched": len(matches),
            "results": [entry.to_dict() for _score, entry in matches],
        }

    def run_tool(
        name: Annotated[str, Field(description="Tool name returned by search_tools")],
        arguments: Annotated[
            dict[str, Any] | None,
            Field(description="Arguments object for that tool, as shown in example_arguments"),
        ] = None,
    ) -> dict:
        """Execute any bookkeeping tool by name.

        Use this after `search_tools` when the tool you need is not listed
        individually. Arguments are validated by the tool itself.
        """
        target = snapshot.get(name)
        if target is None:
            skill = next((entry for entry in SKILL_ENTRIES if entry.name == name), None)
            if skill is not None:
                raise ValueError(
                    f"{name!r} is a skill, not a tool. Read the resource "
                    f"{skill.resource or f'skill://{name}'} instead."
                )
            raise ValueError(
                f"Unknown tool {name!r}. Use search_tools to find one, or detail='{name}' "
                "to check the name."
            )
        if name in {"search_tools", "run_tool"}:
            raise ValueError("run_tool cannot call the search layer itself")

        args = dict(arguments or {})
        required = list((target.parameters or {}).get("required") or [])
        missing = [key for key in required if key not in args]
        if missing:
            raise ValueError(
                f"{name} is missing required argument(s): {', '.join(missing)}. "
                f"Accepted: {', '.join(sorted((target.parameters or {}).get('properties') or {}))}"
            )

        try:
            result = target.fn(**args)
        except TypeError as exc:
            raise ValueError(
                f"{name} rejected those arguments: {exc}. "
                f"Accepted: {', '.join(sorted((target.parameters or {}).get('properties') or {}))}"
            ) from exc

        payload = result.model_dump() if hasattr(result, "model_dump") else result
        return {"tool": name, "result": payload}

    if tool_mode == "search":
        mcp.tool()(run_tool)
        hidden = {name for name in snapshot if name not in CORE_TOOLS}
        for name in hidden:
            live.pop(name, None)
        _install_direct_call_guard(mcp, hidden)

    return mcp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bookkeeping-mcp",
        description="Calculation, jurisdiction constants and sandboxed Python for bookkeeping skills.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http", "sse"),
        default="stdio",
        help="stdio for local MCP hosts (default); http/sse for a long-running server",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for http/sse transports")
    parser.add_argument("--port", type=int, default=8765, help="Port for http/sse transports")
    parser.add_argument(
        "--root",
        default=None,
        help="Path to the bookkeeping-skills repo root (defaults to auto-discovery)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser() if args.root else None

    try:
        mcp = build_server(root)
    except RepositoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
