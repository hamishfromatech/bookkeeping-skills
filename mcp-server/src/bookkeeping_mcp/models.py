"""Pydantic output models for tools where a schema helps the caller.

Tools that return a handful of scalars return plain dicts; the models here are
for the results a model is most likely to reason over and chain.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConstantRow(BaseModel):
    topic: str = Field(description="What the row describes, e.g. 'Standard mileage — business'")
    tax_year: str = Field(description="Tax or income year the value applies to")
    value: str = Field(description="The value exactly as written in the jurisdiction pack")
    numbers: list[float] = Field(
        default_factory=list,
        description="Numbers extracted from the value, in reading order",
    )
    source: str = Field(description="Source label from the pack")
    source_url: str | None = Field(default=None, description="Primary source URL when present")
    verified: str | None = Field(default=None, description="Date the figure was last verified")


class ConstantsResult(BaseModel):
    jurisdiction: str
    name: str
    last_reviewed: str | None
    age_days: int | None
    stale: bool
    query: str | None = None
    matched: int
    rows: list[ConstantRow]
    warning: str | None = Field(
        default=None,
        description="Present when the pack is stale and every figure must be treated as unverified",
    )
    available_topics: list[str] = Field(default_factory=list)


class JurisdictionSummary(BaseModel):
    code: str
    name: str
    last_reviewed: str | None
    stale: bool
    constant_count: int
    path: str


class JurisdictionList(BaseModel):
    repo_root: str
    jurisdictions: list[JurisdictionSummary]


class SalesTaxResult(BaseModel):
    net: float
    tax: float
    gross: float
    rate_percent: float
    inclusive: bool
    net_formatted: str
    tax_formatted: str
    gross_formatted: str


class LineCheckResult(BaseModel):
    stated_total: float
    sum_of_lines: float
    difference: float
    tolerance: float
    reconciles: bool
    line_count: int
    hints: list[str] = Field(default_factory=list)
    by_category: dict[str, float] = Field(default_factory=dict)


class ReconciliationResult(BaseModel):
    adjusted_bank_balance: float
    adjusted_book_balance: float
    difference: float
    reconciles: bool
    diagnostics: list[str] = Field(default_factory=list)
    components: dict[str, float]


class AgingResult(BaseModel):
    as_of: str
    invoice_count: int
    status_counts: dict[str, int]
    currencies: list[str]
    gross_invoiced: float
    outstanding_total: float
    buckets: dict[str, float]
    missing_due_date_count: int
    overdue_total: float


class SelfEmploymentTaxResult(BaseModel):
    net_profit: float
    se_tax_base_92_35_percent: float
    social_security_wage_base: float
    wages_already_using_base: float
    social_security_base: float
    social_security_tax_12_4_percent: float
    medicare_tax_2_9_percent: float
    additional_medicare_0_9_percent: float
    total_se_tax: float
    deductible_half: float
    note: str


class AllocationResult(BaseModel):
    total: float
    parts: list[float]
    sum_of_parts: float
    remainder_cents_distributed: int
    exact: bool


class EvaluationResult(BaseModel):
    expression: str
    exact: str
    value: float
    value_2dp: float
    formatted: str


class ExecutionResult(BaseModel):
    ok: bool
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    stdout: str
    stderr: str
    truncated: bool


class LevyRowOut(BaseModel):
    cu: str = Field(description="ACC classification unit number")
    classification: str = Field(description="Classification unit name")
    rate_per_100: float = Field(description="Work levy per $100 of liable earnings, excluding GST")


class AccLevyRates(BaseModel):
    jurisdiction: str
    year: str
    basis: str
    source_url: str | None
    matched: int
    rows: list[LevyRowOut]
    note: str | None = None


class LevyComponent(BaseModel):
    rate_per_100: float
    amount: float


class AccLevyEstimate(BaseModel):
    cu: str
    classification: str
    liable_income: float
    liable_base: float = Field(description="Liable income after the maximum liable earnings cap")
    capped: bool = Field(description="True when the cap reduced the liable base")
    work_levy: LevyComponent
    working_safer_levy: LevyComponent
    earners_levy: LevyComponent
    subtotal_excluding_gst: float
    gst_percent: float
    gst: float
    total_including_gst: float
    notes: list[str] = Field(default_factory=list)
