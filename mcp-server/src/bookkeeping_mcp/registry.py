"""Searchable registry for the bookkeeping MCP tools.

Why this exists: a client pays for every tool schema it lists, and small or
cheap models pick worse when 20+ tools are in front of them. ``search_tools``
turns "which tool do I need?" into one natural-language query.

The registry is hand-written rather than derived from docstrings, because the
words a user types ("how much tax do I owe this quarter") rarely appear in a
tool description ("prior-year uplift and safe-harbour comparison"). A test
asserts the registry and the live tool set stay in step.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Tools that implement the search layer itself. They are never returned as
# search results, and they are the only tools kept in search mode besides the
# "always cheap and always needed" core.
META_TOOLS = frozenset({"search_tools", "run_tool"})

CORE_TOOLS = frozenset(
    {"search_tools", "run_tool", "get_constants", "list_jurisdictions", "calculate", "run_python"}
)


@dataclass(frozen=True)
class ToolEntry:
    name: str
    group: str
    summary: str
    use_when: str
    params: tuple[str, ...] = ()
    example: dict = field(default_factory=dict)
    kind: str = "tool"  # "tool" or "skill"
    resource: str | None = None

    def to_dict(self) -> dict:
        out = {
            "kind": self.kind,
            "name": self.name,
            "group": self.group,
            "summary": self.summary,
        }
        if self.kind == "skill":
            out["read_resource"] = self.resource or f"skill://{self.name}"
            out["note"] = "This is a procedure, not a calculator. Read the resource instead of calling run_tool."
        else:
            out["required_params"] = list(self.params)
            if self.example:
                out["example_arguments"] = self.example
        return out

    def haystack(self) -> str:
        return f"{self.name} {self.group} {self.summary} {self.use_when}".lower()


REGISTRY: tuple[ToolEntry, ...] = (
    # ---------------------------------------------------------- constants
    ToolEntry(
        name="list_jurisdictions",
        group="constants",
        summary="Which country packs exist, and whether each is out of date.",
        use_when="which countries do you support; is the tax data current; jurisdiction list; us au nz",
        example={},
    ),
    ToolEntry(
        name="get_constants",
        group="constants",
        summary="Read current-law figures from a jurisdiction pack: mileage, Section 179, 1099, GST, ACC, standard deduction.",
        use_when="tax rate; threshold; limit; penalty; mileage rate; 1099 threshold; GST rate; ACC rate; standard deduction; what is the current figure",
        params=("jurisdiction",),
        example={"jurisdiction": "us", "query": "mileage"},
    ),
    # -------------------------------------------------------------- money
    ToolEntry(
        name="sum_amounts",
        group="money",
        summary="Add a list of amounts exactly and round once.",
        use_when="add up; add up invoices; total; sum; subtotal; how much altogether; total the invoices",
        params=("amounts",),
        example={"amounts": [12.5, 40, 7.25]},
    ),
    ToolEntry(
        name="round_amount",
        group="money",
        summary="Round an amount with an explicit mode and report the exact adjustment.",
        use_when="round to two decimals; rounding difference; banker's rounding",
        params=("amount",),
        example={"amount": 12.345, "places": 2, "mode": "half_up"},
    ),
    ToolEntry(
        name="percent_calculation",
        group="money",
        summary="Apply a percentage: find the portion, add it, subtract it, or reverse it out of a gross.",
        use_when="percentage; percent; discount; increase by; what is 15 percent; reverse a percentage",
        params=("amount", "rate_percent"),
        example={"amount": 200, "rate_percent": 7.5, "operation": "of"},
    ),
    ToolEntry(
        name="margin_and_markup",
        group="money",
        summary="Gross profit, gross margin % and markup % from cost and price.",
        use_when="margin; markup; profit on a job; charge out rate; how much profit",
        params=("cost", "price"),
        example={"cost": 60, "price": 100},
    ),
    ToolEntry(
        name="sales_tax",
        group="money",
        summary="Split an amount into net, tax and gross for any sales tax, GST or VAT rate.",
        use_when="GST; VAT; sales tax; tax inclusive; tax included; including tax; including GST; tax exclusive; add GST; extract GST from a total; what is the tax component",
        params=("amount", "rate_percent"),
        example={"amount": 110, "rate_percent": 10, "inclusive": True},
    ),
    ToolEntry(
        name="allocate_amount",
        group="money",
        summary="Split a total across weights so the parts sum exactly, with no lost cents.",
        use_when="split a receipt; split a payout; apportion; distribute across categories; divide proportionally",
        params=("total", "weights"),
        example={"total": 347.82, "weights": [89.99, 42.99, 54.95, 19.89, 34.0, 106.0]},
    ),
    ToolEntry(
        name="verify_line_items",
        group="money",
        summary="Check that line items reconcile to a stated total and explain a mismatch.",
        use_when="does this add up; receipt lines do not match the total; out by a few dollars; duplicate line; transposed digits",
        params=("total", "line_items"),
        example={
            "total": 347.82,
            "line_items": [
                {"amount": 89.99, "category": "Equipment"},
                {"amount": 42.99, "category": "Office"},
            ],
        },
    ),
    # ------------------------------------------------------------- domain
    ToolEntry(
        name="mileage_deduction",
        group="domain",
        summary="US standard-mileage deduction across one or more rate periods.",
        use_when="mileage; business miles; IRS standard mileage rate; deductible driving; cents per mile",
        params=("segments",),
        example={
            "segments": [
                {"label": "Jan-Jun", "miles": 4000, "rate_per_mile": 0.725},
                {"label": "Jul-Dec", "miles": 6000, "rate_per_mile": 0.76},
            ]
        },
    ),
    ToolEntry(
        name="home_office_simplified",
        group="domain",
        summary="US simplified home-office deduction, with the per-square-foot rate and area cap applied.",
        use_when="home office; work from home deduction; square feet; simplified method",
        params=("office_sqft",),
        example={"office_sqft": 200},
    ),
    ToolEntry(
        name="home_office_actual",
        group="domain",
        summary="US actual-expense home office: direct costs at 100%, indirect at business-use %.",
        use_when="home office actual method; Form 8829; apportion rent and utilities; business use percentage",
        params=("office_sqft", "home_sqft", "expenses"),
        example={
            "office_sqft": 200,
            "home_sqft": 1800,
            "expenses": {"direct": {"office paint": 400}, "indirect": {"rent": 28800, "utilities": 1800}},
        },
    ),
    ToolEntry(
        name="straight_line_depreciation",
        group="domain",
        summary="Straight-line depreciation, annual and monthly, at a business-use percentage.",
        use_when="depreciation; straight line; prime cost; spread the cost over years",
        params=("cost", "salvage", "life_years"),
        example={"cost": 30000, "salvage": 3000, "life_years": 5, "business_use_percent": 80},
    ),
    ToolEntry(
        name="declining_balance_depreciation",
        group="domain",
        summary="Declining-balance depreciation for one year, with the schedule to date.",
        use_when="declining balance; diminishing value; DV method; MACRS accelerated; double declining",
        params=("cost", "salvage", "life_years", "rate_percent", "year"),
        example={"cost": 1000, "salvage": 100, "life_years": 5, "rate_percent": 200, "year": 2},
    ),
    ToolEntry(
        name="first_year_asset_expense",
        group="domain",
        summary="US first-year asset expense in the correct order: business use, Section 179, bonus, remainder.",
        use_when="Section 179; bonus depreciation; capitalise or expense; write off equipment; de minimis",
        params=("cost",),
        example={"cost": 10000, "business_use_percent": 100, "bonus_rate_percent": 100},
    ),
    ToolEntry(
        name="self_employment_tax",
        group="domain",
        summary="US self-employment tax: 92.35% base, 12.4% capped, 2.9% Medicare, 0.9% surtax.",
        use_when="self employment tax; SE tax; 15.3 percent; social security and medicare on profit",
        params=("net_profit",),
        example={"net_profit": 100000},
    ),
    ToolEntry(
        name="estimated_tax_safe_harbor",
        group="domain",
        summary="US estimated payments: prior-year 100%/110% safe harbour and the current-year 90% route.",
        use_when="quarterly tax; estimated tax; 1040-ES; safe harbour; how much should I pay this quarter; avoid underpayment penalty",
        params=("prior_year_tax",),
        example={"prior_year_tax": 30000, "prior_agi": 200000, "current_year_tax_estimate": 26000},
    ),
    ToolEntry(
        name="reconciliation_check",
        group="domain",
        summary="Reconcile adjusted bank balance against adjusted book balance, with diagnostics for the difference.",
        use_when="reconcile; bank statement; balance does not match; outstanding cheques; deposits in transit; why is it out",
        params=("bank_ending", "book_ending"),
        example={
            "bank_ending": 24567.89,
            "book_ending": 25674.39,
            "deposits_in_transit": 3200.0,
            "outstanding_payments": 1845.5,
            "book_additions": 248.0,
        },
    ),
    ToolEntry(
        name="ar_aging",
        group="domain",
        summary="Receivables aging buckets from invoice records.",
        use_when="who owes me money; overdue invoices; aged debtors; outstanding receivables; AR report",
        params=("records",),
        example={
            "records": [
                {"status": "open", "total_amount": 1000, "due_date": "2026-12-15"},
                {"status": "overdue", "total_amount": 500, "due_date": "2026-11-01"},
            ],
            "as_of": "2026-11-30",
        },
    ),
    ToolEntry(
        name="acc_work_levy_rates",
        group="nz-acc",
        summary="New Zealand ACC work levy rates by classification unit, searched by trade or job title.",
        use_when="ACC levy; work levy; tradie ACC rate; classification unit; sparky; roofer; builder ACC; how much is ACC for",
        example={"trade": "carpenter"},
    ),
    ToolEntry(
        name="acc_levy_estimate",
        group="nz-acc",
        summary="Estimate a NZ self-employed ACC invoice: work levy, Working Safer levy, earners' levy, capped and GST-added.",
        use_when="ACC invoice; how much will ACC charge me; ACC cost; self employed ACC cost; levy on my income; what will ACC cost for a roofer; sparky; builder; carpenter; tradie on 120k",
        params=("liable_income", "trade"),
        example={"liable_income": 120000, "trade": "roofer"},
    ),
    # --------------------------------------------------------- calculation
    ToolEntry(
        name="calculate",
        group="calculation",
        summary="Evaluate an arithmetic expression exactly, using Decimal, with no side effects.",
        use_when="calculate; arithmetic; formula; expression; what is 1234.56 minus 200 times 0.7",
        params=("expression",),
        example={"expression": "(1234.56 - 200) * 0.7"},
    ),
    ToolEntry(
        name="run_python",
        group="calculation",
        summary="Run Python in an isolated child process with a timeout and captured output.",
        use_when="script; loop; reshape csv or json; compute over many rows; anything arithmetic cannot do",
        params=("code",),
        example={"code": "sum(range(1, 11))"},
    ),
)


# Skills are procedures, not calculators. They are searchable because the right
# answer to a small model's question is often "read this", not "run that" — and
# returning only tools made queries like "is this deductible" resolve to the
# nearest calculator, which is wrong.
SKILL_ENTRIES: tuple[ToolEntry, ...] = (
    ToolEntry(
        name="bookkeeping-setup",
        group="skill",
        summary="Establish business context before any bookkeeping: entity, tax jurisdiction, accounting method, chart of accounts, approval boundaries.",
        use_when="set up my books; first time; accounting method; cash or accrual; chart of accounts; what do you need to know",
        kind="skill",
    ),
    ToolEntry(
        name="income-invoicing",
        group="skill",
        summary="Revenue side: sales capture, invoice numbering, receivables, refunds, prepayments, gross-vs-net processor payouts.",
        use_when="invoice a client; record a sale; who owes me; accounts receivable; stripe payout; refund; prepayment",
        kind="skill",
    ),
    ToolEntry(
        name="receipt-processing",
        group="skill",
        summary="Extract structured data from receipts and bills: email, photos, PDFs, OCR; dedupe and exception queues.",
        use_when="process receipts; extract from email; scan invoices; capture expenses; receipt backlog",
        kind="skill",
    ),
    ToolEntry(
        name="expense-categorization",
        group="skill",
        summary="Assign transactions to tax-aligned categories with vendor matching, split categorization and confidence scoring.",
        use_when="categorize expenses; what category is this; amazon receipt; mixed order; personal or business",
        kind="skill",
    ),
    ToolEntry(
        name="bank-reconciliation",
        group="skill",
        summary="Match book entries to statements with tiered matching, classify unmatched items and prove the balance.",
        use_when="reconcile bank statement; match transactions; books do not match the bank; find missing transactions",
        kind="skill",
    ),
    ToolEntry(
        name="monthly-close",
        group="skill",
        summary="Nine-step month-end close: cut off, capture, categorize, reconcile, adjust, review, 1099 check, P&L, lock.",
        use_when="close the month; month end; monthly bookkeeping; lock the period; produce a P&L",
        kind="skill",
    ),
    ToolEntry(
        name="tax-prep",
        group="skill",
        summary="Compile a tax-ready package: P&L mapped to return lines, quarterly breakdown, contractor summary, schedules.",
        use_when="prepare for taxes; get ready for my accountant; tax package; year end; schedule c",
        kind="skill",
    ),
    ToolEntry(
        name="schedule-c-categories",
        group="skill",
        summary="US Schedule C line-by-line reference: what belongs on each line and what does not.",
        use_when="is this deductible; is a laptop deductible; laptop; computer; phone; tools; equipment; which line does this go on; schedule c line; can I claim this expense; business expense or personal",
        kind="skill",
    ),
    ToolEntry(
        name="home-office",
        group="skill",
        summary="US home office: qualification, exclusive use, simplified vs actual, depreciation and recapture.",
        use_when="home office deduction; work from home; can I claim my spare room; form 8829",
        kind="skill",
    ),
    ToolEntry(
        name="vehicle-expenses",
        group="skill",
        summary="US vehicle: standard mileage vs actual, method lock-in, mileage logs, luxury auto and heavy vehicle rules.",
        use_when="car deduction; mileage log; business vehicle; can I claim my ute; standard mileage or actual",
        kind="skill",
    ),
    ToolEntry(
        name="meals-deduction",
        group="skill",
        summary="US meals: 50% rule, the five documentation elements, entertainment at 0%, on-premises meals from 2026.",
        use_when="business lunch; client dinner; can I deduct a meal; entertainment; coffee for the office",
        kind="skill",
    ),
    ToolEntry(
        name="depreciation-assets",
        group="skill",
        summary="US assets: de minimis, Section 179, bonus depreciation, MACRS class lives, disposition and recapture.",
        use_when="depreciate an asset; capitalize or expense; section 179; bonus depreciation; asset register",
        kind="skill",
    ),
    ToolEntry(
        name="contractor-1099",
        group="skill",
        summary="US contractors: W-9 collection, 1099-NEC thresholds, deadlines, penalties, worker classification.",
        use_when="do I need to file a 1099; contractor or employee; w9; backup withholding; subcontractor",
        kind="skill",
    ),
    ToolEntry(
        name="estimated-taxes",
        group="skill",
        summary="US quarterly estimated tax: self-employment tax, safe harbours, payment timing, state rules.",
        use_when="quarterly taxes; 1040-ES; self employment tax; how much tax should I set aside",
        kind="skill",
    ),
)


# Words that carry no signal about *which* tool is wanted. "new" is here
# because it only ever matched "New Zealand", which hijacked unrelated queries.
STOPWORDS = frozenset(
    {
        "a", "an", "the", "this", "that", "these", "those", "my", "our", "your",
        "is", "are", "was", "be", "been", "it", "its", "to", "of", "for", "and",
        "or", "on", "in", "at", "by", "with", "from", "do", "does", "did", "i",
        "we", "you", "me", "can", "should", "would", "how", "what", "which",
        "new", "please", "help", "need", "want", "get", "up",
    }
)

# Numeric tokens are usually amounts ("110") rather than keywords, and a stray
# amount colliding with a percentage in a description is pure noise. Form and
# section numbers are the exception, because they are genuine identifiers.
TAX_IDENTIFIERS = frozenset({"179", "1099", "1040", "1042", "8829", "4562", "1099k", "1099misc"})


QUESTION_MARKERS = frozenset(
    {"is", "are", "can", "should", "could", "does", "do", "am", "may", "allowed", "allowedto"}
)


def _question_like(text: str) -> bool:
    words = set(_tokens(text))
    return bool(words & QUESTION_MARKERS) or text.strip().endswith("?")


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9'.]+", text.lower()) if t]


def _stem(word: str) -> str:
    """Crude suffix stripping so 'invoices' matches 'invoice' and 'roofing' matches 'roof'.

    Deliberately not a real stemmer: it only needs to make plurals and gerunds
    line up, and a real one would start merging unrelated trade terms.
    """
    for suffix in ("ing", "ers", "er", "ies", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _vocabulary(text: str) -> set[str]:
    """Whole words plus stems, so 'on' no longer matches inside 'bonus'."""
    words = set(_tokens(text))
    return words | {_stem(word) for word in words}


def search_registry(query: str, limit: int = 5) -> list[tuple[float, ToolEntry]]:
    """Rank registry entries for a natural-language query.

    Terms are weighted by inverse document frequency so a distinctive word
    ("1099", "roofer") dominates a common one ("tax", "amount"), and a hit on a
    tool's own name or summary outranks a hit on its trigger phrases.
    """
    entries = [e for e in (*REGISTRY, *SKILL_ENTRIES) if e.name not in META_TOOLS]
    text = (query or "").strip().lower()
    if not text:
        return []

    terms = []
    for token in _tokens(text):
        if token in STOPWORDS:
            continue
        if token.isdigit() and token not in TAX_IDENTIFIERS:
            continue
        if len(token) < 2:
            continue
        terms.append(token)
    if not terms:
        return []

    vocabularies = {e.name: _vocabulary(e.haystack()) for e in entries}
    stems = {term: _stem(term) for term in set(terms)}
    frequency = {
        term: max(sum(1 for v in vocabularies.values() if term in v or stems[term] in v), 1)
        for term in set(terms)
    }

    scored: list[tuple[float, ToolEntry]] = []
    for entry in entries:
        vocab = vocabularies[entry.name]
        name_words = set(_tokens(entry.name))
        summary_words = _vocabulary(entry.summary)

        score = 0.0
        for term in terms:
            if term in vocab or stems[term] in vocab:
                score += 1.0 / frequency[term]
                if term in name_words:
                    score += 1.0 / frequency[term]
                elif term in summary_words or stems[term] in summary_words:
                    score += 0.5 / frequency[term]
        if score > 0 and text in entry.haystack():
            score += 1.0
        if score > 0:
            scored.append((round(score, 4), entry))

    # Ties are common on short queries. When the user is asking a question
    # ("is a laptop deductible"), the procedure is the safer answer than the
    # nearest calculator; otherwise prefer the tool.
    asks = _question_like(text)

    def tie_break(pair: tuple[float, ToolEntry]) -> tuple:
        _score, entry = pair
        kind_rank = 0 if (asks and entry.kind == "skill") else (1 if entry.kind == "tool" else 2)
        return (-_score, kind_rank, entry.name)

    scored.sort(key=tie_break)
    return scored[: max(1, limit)]


def groups() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for entry in REGISTRY:
        if entry.name in META_TOOLS:
            continue
        out.setdefault(entry.group, []).append(entry.name)
    return {group: sorted(names) for group, names in sorted(out.items())}
