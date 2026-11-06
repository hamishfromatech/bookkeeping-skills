# Australia Jurisdiction Pack

## Scope

- Country or tax system: Australia (Commonwealth), ATO administered
- Applies to: sole traders, partnerships, companies and trusts operating a small business in Australia
- Does not cover: NZ, UK, or Australian state payroll tax in detail; Division 7A advice; FBT calculations; GST cross-border rules in detail
- Last reviewed: 2026-11-06 (income year 2026-27, 1 Jul 2026 – 30 Jun 2027)

> This pack does not replace a registered tax agent, BAS agent, bookkeeper with an ABN, lawyer, or payroll provider. It guides draft bookkeeping outputs, exception queues and accountant-ready packages.

## When to load

Load this file before applying Australian-specific rules such as:

- GST treatment, GST-free and input-taxed supplies
- BAS preparation and lodgment
- instant asset write-off and depreciation
- cents-per-kilometre vs logbook car claims
- fixed-rate vs actual-cost working-from-home claims
- PAYG withholding, PAYG instalments, and TPAR
- superannuation guarantee
- contractor vs employee classification (sham contracting)

## Core bookkeeping context

Capture these in `bookkeeping-setup`:

| Field | Options / notes |
|---|---|
| Entity type | Sole trader, partnership, company (Pty Ltd), trust, or unknown |
| ABN | Yes / no / pending — no ABN means withholding at 47% may apply to payments from other businesses |
| GST registration | Registered / not registered / unknown |
| GST accounting basis | Cash or accrual (non-cash) — the BAS basis, independent of the tax accounting method |
| BAS cycle | Quarterly (default) or monthly (required if GST turnover ≥ $20M, or optional) |
| PAYG withholding | Registered as a withholder? Employees? |
| PAYG instalments | Paying quarterly instalments? |
| Superannuation | SG obligations, frequency (payday super from 1 Jul 2026) |
| Contractor industries | Building & construction, cleaning, courier, road freight, IT, security → TPAR obligations |
| Income year | 1 July – 30 June (default) |
| Home currency | AUD |

If entity type is unknown, do not apply company or trust treatment. Draft records only and flag for review.

## Current-law constants

**This table is the single source of truth for year-specific amounts.** Skills must reference this file instead of hardcoding numbers.

| Topic | Income year | Value | Source | Verified |
|---|---|---|---|---|
| GST rate | 2026-27 | **10%** | ATO | 2026-11-06 |
| GST registration threshold | 2026-27 | **$75,000** GST turnover ($150,000 for non-profits) | [ATO registering for GST](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/registering-for-gst) | 2026-11-06 |
| GST turnover threshold for monthly BAS | 2026-27 | $20,000,000 | ATO | 2026-11-06 |
| Cents per kilometre — car | 2026-27 | **91¢/km** (2024-25 and 2025-26: 88¢) | [ATO cents per kilometre](https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/deductions-you-can-claim/work-related-deductions/cars-transport-and-travel/motor-vehicle-and-car-expenses/expenses-for-a-car-you-own-or-lease/cents-per-kilometre-method) | 2026-11-06 |
| Cents per kilometre — maximum | 2026-27 | 5,000 business km per car per year (91¢ → **$4,550** max) | ATO | 2026-11-06 |
| Instant asset write-off | 2026-27 | **$20,000** per asset, small business entities with aggregated turnover < $10M | [ATO instant asset write-off](https://www.ato.gov.au/about-ato/new-legislation/in-detail/businesses/20000-dollars-instant-asset-write-off) | 2026-11-06 |
| Working from home — fixed rate | 2025-26 | **70¢ per hour**; actual hours must be recorded. Confirm the rate for 2026-27 before use | [ATO fixed rate method](https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/deductions-you-can-claim/work-related-deductions/working-from-home-expenses/fixed-rate-method) | 2026-11-06 |
| Super guarantee rate | 2026-27 | **12%** | [ATO super guarantee](https://www.ato.gov.au/tax-rates-and-codes/key-superannuation-rates-and-thresholds/super-guarantee) | 2026-11-06 |
| Concessional contributions cap | 2026-27 | $32,500 (from 1 Jul 2026) | ATO | 2026-11-06 |
| Company tax — base rate entity | 2026-27 | **25%** (aggregated turnover < $50M and ≤ 80% passive income) | [ATO company tax rates](https://www.ato.gov.au/tax-rates-and-codes/company-tax-rate-changes) | 2026-11-06 |
| Company tax — otherwise | 2026-27 | **30%** | ATO | 2026-11-06 |
| No-ABN withholding | 2026-27 | 47% (top marginal rate incl. Medicare levy) on payments to suppliers without a valid ABN | ATO | 2026-11-06 |
| Record retention | 2026-27 | **5 years** from when the record was prepared/obtained or the transaction completed; assets: ownership period + 5 years | [ATO record keeping](https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/record-keeping-for-business/overview-of-record-keeping-rules-for-business) | 2026-11-06 |

Not tabulated here because they change every year or depend on the taxpayer: individual marginal rates and the tax-free threshold, Medicare levy and surcharge thresholds, HELP/HECS repayment thresholds, Division 293, fuel tax credit rates, FBT rates and gross-up factors, and state payroll tax thresholds. Verify against ATO primary sources and state revenue offices before use.

## Chart-of-accounts implications

| Area | Australian bookkeeping implication |
|---|---|
| Revenue | Record GST-inclusive in the ledger by default; split GST to a **GST Collected** liability account. If the ledger is GST-exclusive, be consistent and document the convention. |
| GST on purchases | Split to **GST Paid** (input tax credit) account. Do not include GST paid in the expense amount when registered. |
| GST-free sales | Food, health, education, exports — no GST collected; still report on the BAS. |
| Input-taxed sales | Residential rent, some financial supplies — no GST collected and **no input tax credits** on related purchases. |
| Instant asset write-off | One account per pool or asset; track purchase date against the threshold that applied on that date. |
| Depreciation | Diminishing value or prime cost using effective life; simplified depreciation pools available to small business entities. |
| Motor vehicle | Separate **cents per kilometre** (no receipts needed beyond km log) vs **logbook** (12-week representative log, valid 5 years) vs actual cost. Never mix methods for the same car in one year. |
| WFH | Fixed rate (70¢/hr, records of hours) vs actual cost (needs a reasonable basis for business-use %). |
| Superannuation | **Superannuation Payable** liability, not an expense paid to the ATO. SG is deductible when paid. |
| PAYG withholding | **PAYG Withholding Payable** liability — money held on behalf of employees, never an expense. |
| PAYG instalments | Income tax paid in advance — an asset/clearing item, not an expense. |
| Owner drawings | Sole trader: drawings are not deductible and not wages. Company: director's loan account needs Division 7A attention if not repaid. |
| Trust distributions | Do not post; flag for accountant review. |

## BAS and lodgment calendar

Quarterly BAS due dates (when lodging through a tax agent, later dates often apply):

| Quarter | Period | Due |
|---|---|---|
| Q1 | 1 Jul – 30 Sep | 28 October |
| Q2 | 1 Oct – 31 Dec | 28 February |
| Q3 | 1 Jan – 31 Mar | 28 April |
| Q4 | 1 Apr – 30 Jun | 28 July |

Monthly BAS: due on the 21st of the following month.

Other obligations to check:

- **TPAR** (Taxable payments annual report) — due **28 August** for building and construction, cleaning, courier, road freight, IT and security services.
- **PAYG withholding** — due 21st of the following month (quarterly for small withholders).
- **Super guarantee** — quarterly due dates through 2025-26; from 1 July 2026 super must be paid on the same day as wages ("payday super"). Verify the transition rules before relying on this.
- **Single Touch Payroll (STP)** — report each pay event.

## Tax and compliance rules

| Topic | Rule | Source | Last verified |
|---|---|---|---|
| GST registration | Must register once GST turnover reaches $75,000 ($150,000 non-profit) in a rolling 12-month period or projected | ATO | 2026-11-06 |
| Tax invoices | Sales ≥ $82.50 incl. GST require a tax invoice; ≥ $1,000 requires the buyer's identity/ABN. Purchases need a valid tax invoice to claim a credit | ATO | 2026-11-06 |
| GST credits | Claimable only on purchases used in carrying on the enterprise, with a valid tax invoice, and not for input-taxed supplies | ATO | 2026-11-06 |
| Instant asset write-off | Assets under the threshold, first used or installed ready for use in the income year, used for a taxable purpose | ATO | 2026-11-06 |
| Car — cents per km | Covers all running costs; cannot also claim fuel, rego or insurance. 5,000 km cap applies per car | ATO | 2026-11-06 |
| Car — logbook | 12 continuous weeks, representative, valid 5 years; odometer readings at start and end of year | ATO | 2026-11-06 |
| Entertainment | Generally **not** deductible (FBT applies); client meals are not deductible in Australia the way they are in the US | ATO | 2026-11-06 |
| Contractor vs employee | Multi-factor test (control, integration, risk, tools, ability to delegate). "Sham contracting" is prohibited | ATO | 2026-11-06 |
| Contractors | No PAYG withholding when a valid ABN is quoted and the engagement is genuinely contracting; **TPAR** may still apply | ATO | 2026-11-06 |
| Record keeping | 5 years; records must be in English or readily translatable, and kept for the longest applicable period | ATO | 2026-11-06 |
| Digital records | Photographs of paper receipts are acceptable if legible and complete | ATO | 2026-11-06 |

## Agent boundaries

Safe to draft:

- GST-coded transaction registers
- BAS draft workings (GST on sales, GST on purchases, PAYG withholding, PAYG instalments)
- instant asset write-off and depreciation schedules
- cents-per-km and logbook worksheets
- WFH fixed-rate hours worksheets
- contractor payment summaries and TPAR drafts
- reconciliation reports and monthly close packages
- accountant/tax-agent ready packages

Requires user approval:

- posting entries to accounting software
- deleting, merging, or re-coding historical transactions
- lodging or paying a BAS, TPAR, PAYG or SG obligation
- changing GST registration or BAS cycle
- applying an override to amounts, dates, suppliers, or GST codes

Requires professional review:

- entity type or trust distribution questions
- GST treatment of mixed or input-taxed supplies
- property, residential rent, or financial supplies
- Division 7A loans and director loan accounts
- fringe benefits (FBT)
- contractor vs employee classification disputes
- multi-state payroll tax
- cross-border supplies and reverse-charged GST

## Related skills

- `bookkeeping-setup`
- `income-invoicing`
- `receipt-processing`
- `expense-categorization`
- `bank-reconciliation`
- `monthly-close`
- `tax-prep`
- `depreciation-assets`
- `vehicle-expenses`
- `home-office`
- `contractor-1099` (US-specific form; the *contractor tracking* pattern applies, the W-9/1099 mechanics do not)
