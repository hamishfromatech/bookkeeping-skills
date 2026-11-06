# United States Jurisdiction Pack

## Scope

This pack covers US small-business bookkeeping support, especially expense-side workflows for sole proprietors, freelancers, single-member LLCs, and small service businesses.

It is the current baseline jurisdiction for this repository.

It does not replace a CPA, enrolled agent, payroll provider, attorney, or tax filing product. It should guide draft bookkeeping outputs, exception queues, and accountant-ready packages.

**Last reviewed:** 2026-11-06 (tax year 2026)

## When to load

Load this file before applying US-specific rules such as:

- Schedule C expense mapping
- Form 1099-NEC contractor tracking
- Form W-9 collection
- Form 1040-ES estimated tax planning
- home office deduction rules
- standard mileage vs actual vehicle expense rules
- business meals and entertainment rules
- depreciation, Section 179, bonus depreciation, and MACRS

## Core bookkeeping context

Capture these fields in `bookkeeping-setup` before applying US tax treatment:

- entity type: sole proprietor, single-member LLC, partnership, S corporation, C corporation, nonprofit, or unknown
- tax filing context: Schedule C, partnership return, corporate return, or unknown
- accounting method: cash, accrual, hybrid, or unknown
- home currency: usually USD
- state and local tax footprint
- sales tax registration status, if selling taxable goods or services
- payroll provider, if employees exist
- contractor payment process and W-9 status

If entity type or filing context is unknown, draft bookkeeping records but flag entity-specific tax treatment for professional review.

## Current-law constants

**This table is the single source of truth for year-specific amounts.** Skills must reference this file instead of hardcoding numbers. When a skill needs a year-specific figure, read it from here and name the tax year in the output.

| Topic | Tax year | Value | Source | Verified |
|---|---|---|---|---|
| Standard mileage — business | 2026 | **72.5¢/mile** (1 Jan – 30 Jun 2026); **76¢/mile** (1 Jul – 31 Dec 2026) | [IRS standard mileage rates](https://www.irs.gov/tax-professionals/standard-mileage-rates) | 2026-11-06 |
| Standard mileage — business | 2025 | 70¢/mile | IRS | 2026-11-06 |
| Standard mileage — medical | 2026 | 20.5¢/mile (1 Jan – 30 Jun); 23.5¢/mile (1 Jul – 31 Dec) | IRS | 2026-11-06 |
| Standard mileage — charity | 2026 | 14¢/mile (fixed by statute) | IRS | 2026-11-06 |
| Standard mileage — moving | 2026 | Same as medical rate; **active-duty military only** | IRS | 2026-11-06 |
| Section 179 limit | 2026 | **$2,560,000** | [IRS Rev. Proc.](https://www.irs.gov/pub/irs-drop/rp-26-15.pdf) | 2026-11-06 |
| Section 179 phase-out begins | 2026 | **$4,090,000** of total qualifying property placed in service | IRS | 2026-11-06 |
| Bonus depreciation | 2026 | **100%** (no dollar limit) for qualified property acquired after 19 Jan 2025 | OBBBA (P.L. 119-21) | 2026-11-06 |
| De minimis safe harbor | 2026 | $2,500 per invoice/item; **$5,000** if the business has an applicable financial statement (AFS) | Treas. Reg. §1.263(a)-1(f) | 2026-11-06 |
| Luxury auto cap, §168(k) bonus applied | 2026 | Y1 **$20,300**; Y2 $19,800; Y3 $11,900; Y4+ $7,160 | [Rev. Proc. 2026-15](https://www.irs.gov/pub/irs-drop/rp-26-15.pdf) | 2026-11-06 |
| Luxury auto cap, no bonus | 2026 | Lower Y1 cap — read Rev. Proc. 2026-15 Table 2 | Rev. Proc. 2026-15 | 2026-11-06 |
| Section 179 cap for heavy SUVs (>6,000 lb GVWR) | 2026 | Indexed annually — verify current-year figure before use | IRS | 2026-11-06 |
| 1099-NEC filing threshold | 2026 | **$2,000** (was $600 through 2025) | [IRS Pub. 1099](https://www.irs.gov/pub/irs-pdf/p1099.pdf) | 2026-11-06 |
| Information-return e-filing threshold | 2026 | **10 or more** returns in aggregate | IRS | 2026-11-06 |
| 1099-NEC / information-return penalty, ≤30 days late | 2026 | **$60** per form | [IRS Information return penalties](https://www.irs.gov/payments/information-return-penalties) | 2026-11-06 |
| … 31 days late through 1 Aug | 2026 | **$130** per form | IRS | 2026-11-06 |
| … after 1 Aug, or not filed | 2026 | **$340** per form | IRS | 2026-11-06 |
| … intentional disregard | 2026 | **$680** per form, **no maximum** | IRS | 2026-11-06 |
| 1099-NEC deadline | 2026 | **31 January 2027** (recipient copy and IRS copy, no extension) | IRS | 2026-11-06 |
| Back-up withholding rate | 2026 | 24% | IRS | 2026-11-06 |
| Self-employment tax | 2026 | 15.3% (12.4% Social Security + 2.9% Medicare) on 92.35% of net SE income | IRS | 2026-11-06 |
| Social Security wage base | 2026 | **$184,500** (2027: $192,300) | [SSA contribution & benefit base](https://www.ssa.gov/oact/cola/cbb.html) | 2026-11-06 |
| Additional Medicare tax | 2026 | 0.9% above $200,000 single / $250,000 MFJ | IRS | 2026-11-06 |
| Standard deduction | 2026 | $16,100 single & MFS; $24,150 head of household; $32,200 MFJ | [Congress.gov CRS RL34498](https://www.congress.gov/crs-product/RL34498) | 2026-11-06 |
| Business meals | 2026 | 50% deductible with full documentation | IRC §274(n) | 2026-11-06 |
| Entertainment | 2026 | 0% deductible (permanent since TCJA 2018) | IRC §274(a) | 2026-11-06 |
| Employer-provided on-premises meals | 2026 | **0% deductible** from 1 Jan 2026; narrow exceptions (vessels, oil/gas platforms, remote camps) | OBBBA; IRC §274(o) | 2026-11-06 |
| Home office — simplified method | 2026 | $5/sq ft, max 300 sq ft → **$1,500** | IRS Rev. Proc. 2013-13 | 2026-11-06 |
| Home office — depreciation period (actual method) | 2026 | 39 years straight-line, nonresidential real property | IRC §168 | 2026-11-06 |
| Estimated tax trigger | 2026 | Owe ≥$1,000 after withholding and credits | IRS Form 1040-ES | 2026-11-06 |
| Estimated tax safe harbor | 2026 | 100% of prior-year tax; **110%** if prior-year AGI > $150,000 ($75,000 MFS) | IRS Form 1040-ES | 2026-11-06 |

### Figures deliberately not tabulated here

**Individual income tax brackets.** These are re-indexed every year and a stale table silently corrupts estimated-tax guidance. Do not hardcode a bracket table in a skill. Read the current-year IRS brackets page or use the Form 1040-ES worksheet, and state the tax year used.

Brackets: <https://www.irs.gov/filing/federal-income-tax-rates-and-brackets>

**State-level rates, thresholds and credits.** Vary by state and change independently of federal law. Capture the state footprint in `bookkeeping-setup` and verify per state.

## Chart-of-accounts implications

For US sole proprietors and simple small businesses, map ordinary expenses to Schedule C lines where useful. Do not force all businesses into Schedule C if the entity or return type differs.

Common mappings:

| Area | US bookkeeping implication |
|---|---|
| Advertising | Schedule C Line 8 for sole proprietors |
| Car and truck | Track standard mileage vs actual expenses; support Form 4562 when needed |
| Contract labor | Track vendors, W-9 status, payment method, and 1099 exposure |
| Depreciation | Track asset basis, placed-in-service date, business-use percentage, method, and accumulated depreciation |
| Meals | Record full book expense, track deductible percentage separately |
| Travel | Separate travel from meals and entertainment |
| Home office | Keep simplified vs actual method evidence separate |
| Owner transactions | Separate owner draws, owner contributions, reimbursements, and personal expenses from business expenses |

## Current-law policy

Before finalizing a tax-sensitive recommendation, verify year-specific facts against primary sources such as IRS publications, forms, instructions, or notices — or read the constants table above and check that its `Verified` date is current.

Tax-sensitive facts include:

- standard mileage rates (note: the IRS has revised the business rate mid-year, so check both halves of the year)
- Section 179 limits and phase-out
- bonus depreciation percentage
- 1099 thresholds, penalty amounts, and e-filing thresholds
- tax brackets, standard deduction, Social Security wage base, and estimated-tax safe-harbor thresholds
- meals, entertainment, and employer-provided meal deductibility
- state and local sales tax or payroll requirements

If current-law verification is unavailable, label the output as draft and include the year assumed. If the constants table is more than 12 months past its `Verified` date, treat every figure as unverified and say so in the output.

## Forms and lines the skills reference

| Item | Where it goes | Note |
|---|---|---|
| Half of self-employment tax | Form 1040 above-the-line deduction | **Not** Schedule C |
| Self-employed health insurance | Form 1040 above-the-line deduction | **Not** Schedule C |
| Retirement contributions (SEP/SIMPLE/Solo 401k) | Form 1040 above-the-line deduction | **Not** Schedule C |
| Business use of home | Form 8829 → Schedule C Line 30 | Line numbers are stable but confirm on the current-year form |
| Depreciation | Form 4562 → Schedule C Line 13 | |
| Other expenses itemisation | Schedule C Part V | Required for Line 27a |

Avoid citing Form 1040 line numbers in outputs — the form is renumbered periodically. Refer to the deduction by name.

## Agent boundaries

Safe to draft:

- extracted receipt and invoice records
- categorized transaction tables
- Schedule C mapping suggestions
- reconciliation reports
- contractor 1099 exposure summaries
- estimated-tax worksheets
- monthly close packages
- tax-prep packets for accountant review

Requires user approval:

- posting entries to accounting software
- deleting or merging records
- locking periods
- applying manual overrides to amounts, dates, vendors, or categories
- submitting information returns or tax payments

Requires professional review:

- entity classification uncertainty
- worker classification uncertainty
- multi-state sales tax or payroll exposure
- inventory and COGS treatment
- depreciation elections
- large owner transactions
- amended returns or prior-year corrections
- any final tax filing position

## Related skills

- `bookkeeping-setup`
- `income-invoicing`
- `schedule-c-categories`
- `contractor-1099`
- `estimated-taxes`
- `home-office`
- `vehicle-expenses`
- `meals-deduction`
- `depreciation-assets`
