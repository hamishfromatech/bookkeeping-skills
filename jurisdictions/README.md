# Jurisdictions

Bookkeeping principles are general. Tax treatment, filing thresholds, deduction limits, sales tax/VAT/GST, payroll, and statutory record rules are jurisdiction-specific.

Use this folder when a skill needs rules for a specific country or tax system. Each pack carries a **Current-law constants** table that is the single source of truth for year-specific amounts.

## Current packs

| Jurisdiction | Status | File | Use for |
|---|---|---|---|
| United States | Active baseline | [us.md](us.md) | Schedule C mapping, 1099-NEC readiness, estimated taxes, depreciation/§179/bonus, meals, vehicle, home office |
| Australia | Active | [au.md](au.md) | GST and BAS, instant asset write-off, cents-per-km and logbook, WFH fixed rate, PAYG, TPAR, superannuation |

## Agent policy

1. Determine the user's tax jurisdiction before applying tax, deduction, filing, payroll, sales tax, VAT, GST, or statutory reporting rules.
2. If jurisdiction is unknown, continue only with jurisdiction-neutral bookkeeping work: evidence capture, transaction normalization, source trails, review queues, and reconciliation structure.
3. Load the jurisdiction file before using a jurisdiction-specific skill.
4. **Read year-specific amounts from the pack's constants table — never hardcode them in a skill or an output.** State the tax year used.
5. Treat year-specific amounts, thresholds, rates, and deadlines as current-law facts that require verification against primary sources before final use.
6. If a pack's `Last reviewed` date is more than 12 months old, treat every figure as unverified and say so.
7. Do not blend rules across countries. If a business operates in multiple jurisdictions, create separate notes for each jurisdiction and flag the case for professional review.
8. Do not translate a US concept into another jurisdiction. "Entertainment deduction", "1099-NEC", "Schedule C", "Section 179" and "de minimis safe harbor" are US-specific.

## What belongs here

- Country-specific tax forms and reporting lines
- Deduction limits and documentation requirements
- Filing thresholds, rates, and deadlines
- Payroll, contractor, VAT, GST, sales tax, or information-return rules
- Record-retention requirements
- Local terminology that affects chart-of-accounts mapping

## What stays in the main skills

- Evidence capture
- Transaction normalization
- Deduplication
- Reconciliation mechanics
- Close workflow
- Approval boundaries
- Artifact formats

## Adding a jurisdiction

Use [_template.md](_template.md). Keep the file concise and operational. Prefer primary-source links for facts that change over time, and record a `Last reviewed` date plus a per-row `Verified` date in the constants table.
