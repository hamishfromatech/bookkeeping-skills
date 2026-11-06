# New Zealand Jurisdiction Pack

## Scope

- Country or tax system: New Zealand (Inland Revenue / IRD administered)
- Applies to: sole traders, partnerships, look-through companies, companies and trusts operating a small business in New Zealand
- Does not cover: the brightline property rules, residential rental ring-fencing, FIF/CFC rules, Division 7A equivalent (shareholder current accounts are mentioned only as an accounting item), FBT calculations in detail, or KiwiSaver scheme administration
- Last reviewed: 2026-11-06 (income year 2026-27, 1 Apr 2026 – 31 Mar 2027)

> This pack does not replace a chartered accountant, a registered tax agent, a bookkeeper, or a lawyer. It guides draft bookkeeping outputs, exception queues and accountant-ready packages.

## When to load

Load this file before applying New Zealand-specific rules such as:

- GST treatment, GST-return preparation and taxable supply information
- income tax rates and the ACC earners' levy
- provisional tax and terminal tax
- kilometre rates, logbook claims and vehicle depreciation
- home office (square metre rate or actual proportion)
- depreciation and the low-value asset threshold
- schedular payments and contractor withholding
- KiwiSaver employer contributions

## Core bookkeeping context

Capture these in `bookkeeping-setup`:

| Field | Options / notes |
|---|---|
| Entity type | Sole trader, partnership, look-through company (LTC), company, trust, or unknown |
| NZBN | Yes / no — the New Zealand Business Number |
| IRD number | Required for PAYE, GST and withholding obligations |
| GST registration | Registered / not registered / unknown |
| GST accounting basis | **Payments**, **invoice** or **hybrid** — this is the GST basis, independent of the income tax accounting method |
| GST filing frequency | Monthly, two-monthly (default), or six-monthly |
| Balance date | 31 March (default) or an approved alternative |
| PAYE registration | Employer? Withholding from schedular payments? |
| KiwiSaver | Employer obligations, contribution rate, ESCT |
| ACC | Self-employed work levy, earners' levy |
| Income year | 1 April – 31 March (default) |
| Home currency | NZD |

If entity type is unknown, draft records only and flag entity-specific treatment for review. Do not apply company or trust treatment by default.

**Balance date matters for every due date in this pack.** Everything below assumes the standard 31 March balance date.

## Current-law constants

**This table is the single source of truth for year-specific amounts.** Skills must reference this file instead of hardcoding numbers.

| Topic | Tax year | Value | Source | Verified |
|---|---|---|---|---|
| Individual income tax — lowest rate | 2026-27 | **10.5%** on $0 – $15,600 | [IRD tax rates for individuals](https://www.ird.govt.nz/income-tax/income-tax-for-individuals/tax-codes-and-tax-rates-for-individuals/tax-rates-for-individuals) | 2026-11-06 |
| Individual income tax — 17.5% band | 2026-27 | **17.5%** on $15,601 – $53,500 | [IRD tax rates](https://www.ird.govt.nz/income-tax/income-tax-for-individuals/tax-codes-and-tax-rates-for-individuals/tax-rates-for-individuals) | 2026-11-06 |
| Individual income tax — 30% band | 2026-27 | **30%** on $53,501 – $78,100 | [IRD tax rates](https://www.ird.govt.nz/income-tax/income-tax-for-individuals/tax-codes-and-tax-rates-for-individuals/tax-rates-for-individuals) | 2026-11-06 |
| Individual income tax — 33% band | 2026-27 | **33%** on $78,101 – $180,000 | [IRD tax rates](https://www.ird.govt.nz/income-tax/income-tax-for-individuals/tax-codes-and-tax-rates-for-individuals/tax-rates-for-individuals) | 2026-11-06 |
| Individual income tax — top rate | 2026-27 | **39%** above $180,000 | [IRD tax rates](https://www.ird.govt.nz/income-tax/income-tax-for-individuals/tax-codes-and-tax-rates-for-individuals/tax-rates-for-individuals) | 2026-11-06 |
| Company tax rate | 2026-27 | **28%** | [IRD tax rates for businesses](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/tax-rates-for-businesses) | 2026-11-06 |
| Trustee tax rate | 2026-27 | 39% | [IRD business rates](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/tax-rates-for-businesses) | 2026-11-06 |
| Māori authority tax rate | 2026-27 | 17.5% | [IRD business rates](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/tax-rates-for-businesses) | 2026-11-06 |
| GST rate | 2026-27 | **15%** | [IRD GST](https://www.ird.govt.nz/gst) | 2026-11-06 |
| GST registration threshold | 2026-27 | **$60,000** taxable supplies in any 12-month period, or expected to exceed it | [IRD registering for GST](https://www.ird.govt.nz/gst/registering-for-gst) | 2026-11-06 |
| Taxable supply information required | 2026-27 | Not required at or below **$200** (GST inclusive); required above $200; additional detail above $1,000 | [IRD taxable supply information](https://www.ird.govt.nz/gst/tax-invoices-for-gst) | 2026-11-06 |
| ACC earners' levy rate | 2026-27 | **1.75%** of liable earnings | [IRD ACC earners' levy rates](https://www.ird.govt.nz/income-tax/income-tax-for-individuals/acc-clients-and-carers/acc-earners-levy-rates) | 2026-11-06 |
| ACC maximum liable earnings | 2026-27 | **$156,641** (maximum earners' levy $2,741.22) | [IRD ACC rates](https://www.ird.govt.nz/income-tax/income-tax-for-individuals/acc-clients-and-carers/acc-earners-levy-rates) | 2026-11-06 |
| Provisional tax threshold | 2026-27 | Required when residual income tax exceeds **$5,000** | [IRD provisional tax](https://www.ird.govt.nz/income-tax/provisional-tax) | 2026-11-06 |
| Provisional tax — standard uplift | 2026-27 | **105%** of the prior year's residual income tax, or **110%** of the year before that once filed | [IRD provisional tax](https://www.ird.govt.nz/income-tax/provisional-tax) | 2026-11-06 |
| Kilometre rate — petrol | 2025-26 | Tier 1 **$1.20/km** (first 14,000 km of total travel); Tier 2 **37c/km** | [IRD kilometre rates 2025-2026](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/types-of-business-expenses/claiming-vehicle-expenses/kilometre-rates-2025-2026) | 2026-11-06 |
| Kilometre rate — diesel | 2025-26 | Tier 1 $1.30/km; Tier 2 38c/km | [IRD kilometre rates](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/types-of-business-expenses/claiming-vehicle-expenses/kilometre-rates-2025-2026) | 2026-11-06 |
| Kilometre rate — petrol hybrid | 2025-26 | Tier 1 90c/km; Tier 2 24c/km | [IRD kilometre rates](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/types-of-business-expenses/claiming-vehicle-expenses/kilometre-rates-2025-2026) | 2026-11-06 |
| Kilometre rate — electric | 2025-26 | Tier 1 $1.22/km; Tier 2 23c/km | [IRD kilometre rates](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/types-of-business-expenses/claiming-vehicle-expenses/kilometre-rates-2025-2026) | 2026-11-06 |
| Home office square metre rate | 2025-26 | **$57.30 per square metre** per year | [IRD home office expenses](https://www.ird.govt.nz/home-office-expenses) | 2026-11-06 |
| Low-value asset threshold | 2026-27 | **$1,000** per asset — immediate deduction | [IRD claiming depreciation](https://www.ird.govt.nz/income-tax/income-tax-for-businesses-and-organisations/types-of-business-expenses/depreciation/claiming-depreciation) | 2026-11-06 |
| KiwiSaver minimum contribution | 2026-27 | **3.5%** employer and employee, from 1 April 2026 | [IRD KiwiSaver changes](https://www.ird.govt.nz/updates/news-folder/2025/kiwisaver-changes) | 2026-11-06 |
| Schedular payment withholding | 2026-27 | Standard **20%**; a contractor may elect a rate of at least 10% (15% for non-residents on a temporary visa) | [IRD schedular payments](https://www.ird.govt.nz/income-tax/withholding-taxes/schedular-payments) | 2026-11-06 |
| Record retention | 2026-27 | **7 years**, in English or Māori | [IRD record keeping](https://www.ird.govt.nz/managing-my-tax/record-keeping) | 2026-11-06 |

### Deliberately not tabulated here

**Two rows above are one year behind the tax year, on purpose.** IRD publishes the kilometre rates and the square metre rate *after* an income year ends. The latest published sets are for 2025-26. For 2026-27 activity, use the latest published set and mark the claim as provisional until IRD publishes the 2026-27 rates — do not extrapolate them.

Also not tabulated, because they depend on the taxpayer or move independently:

- ACC **work levy** rates (industry-classified, invoiced by ACC directly, not through IRD)
- ESCT rates on employer KiwiSaver contributions (banded on the employee's income)
- FBT rates, the FBT de minimis and the motor vehicle valuation methods
- Imputation credit ratios and RWT rates on dividends and interest
- Student loan repayment thresholds
- Working for Families and independent-earner tax credit thresholds
- Any rate applying to a non-standard balance date

## Chart-of-accounts implications

| Area | New Zealand bookkeeping implication |
|---|---|
| Revenue | Record GST-inclusive by default unless the ledger is explicitly GST-exclusive **and** that convention is documented. GST collected is a liability, never income. |
| GST on purchases | Split to a **GST Paid** (input tax) account. Not an expense. |
| Zero-rated supplies | Exports and land transactions — GST at 0%; still reported in the GST return. |
| Exempt supplies | Financial services, residential rent, donated goods — no GST and no input credits on related costs. |
| Provisional tax | A tax payment in advance, not an expense. Post to an income-tax clearing account. |
| Terminal tax | Same clearing account; reconcile to the IRD statement after the return is assessed. |
| ACC levies | Self-employed: a business expense. Employees: withheld through PAYE. Do not mix the two. |
| PAYE / ESCT withholding | Liabilities held for IRD. Never an expense. |
| KiwiSaver employer contribution | An expense (subject to ESCT); the employee's own contribution is a payroll deduction, not an expense. |
| Shareholder current account | Company drawings by shareholders are a loan/current account balance. Track it separately and flag it — overdrawn current accounts have tax consequences. |
| Depreciation | DV or SL at IRD rates. Low-value assets ($1,000 or less) are expensed directly. |
| Motor vehicle | One method per vehicle: kilometre rate, logbook (actual cost × business %), or actual cost for high-use vehicles. Do not mix. |
| Entertainment | Generally 50% deductible; entertainment provided to employees is subject to FBT. Flag, do not decide. |

## GST and filing calendar

Standard 31 March balance date.

| Obligation | Period | Due |
|---|---|---|
| GST return and payment | Each taxable period | 28th of the following month |
| GST — period ending 30 November | Oct–Nov (two-monthly) | **15 January** |
| GST — period ending 31 March | Feb–Mar (two-monthly) | **7 May** |
| Provisional tax instalment 1 | 2026-27 | 28 August 2026 |
| Provisional tax instalment 2 | 2026-27 | 15 January 2027 |
| Provisional tax instalment 3 | 2026-27 | 7 May 2027 |
| PAYE | Each payday, due 20th of the following month (twice-monthly for larger employers) | 20th |
| KiwiSaver | With PAYE | 20th of the following month |
| Terminal tax | Prior income year | 7 April following balance date |
| ACC | Annual invoice for self-employed | Per the ACC invoice |

Verify every date against IRD's key dates before relying on it: <https://www.ird.govt.nz/index/key-dates>

## Tax and compliance rules

| Topic | Rule | Source | Last verified |
|---|---|---|---|
| GST registration | Compulsory once taxable supplies exceed $60,000 in any 12-month period, or are expected to | IRD | 2026-11-06 |
| GST — taxable supply information | From 1 April 2023 the "tax invoice" concept was replaced by **taxable supply information**. Not required at or below $200 (incl GST); required above $200 | IRD | 2026-11-06 |
| GST — claiming input tax | Requires a valid GST record; buyers need taxable supply information for supplies over $200 | IRD | 2026-11-06 |
| GST accounting basis | Payments, invoice or hybrid. The basis determines when GST is recognised and can differ from the income tax method | IRD | 2026-11-06 |
| Provisional tax | Required where residual income tax exceeds $5,000; standard uplift 105%/110%, or the estimation option | IRD | 2026-11-06 |
| Kilometre rate method | Covers all running costs; no separate claim for fuel, registration or insurance. Tier 1 applies to the first 14,000 km of **total** travel, then Tier 2 | IRD | 2026-11-06 |
| Logbook method | A representative logbook is valid for **3 years**; odometer readings at the start and end of each year | IRD | 2026-11-06 |
| Home office — square metre rate | A flat rate per square metre for the year; an alternative to apportioning actual household costs | IRD | 2026-11-06 |
| Low-value assets | Assets costing $1,000 or less can be expensed in the year of purchase | IRD | 2026-11-06 |
| Entertainment | Generally 50% deductible; entertainment for employees is subject to FBT | IRD | 2026-11-06 |
| Contractor withholding | Payments for listed activities are **schedular payments** and attract withholding at the contractor's WT rate (standard 20%) | IRD | 2026-11-06 |
| Contractor vs employee | Test is control, integration, and whether the person is genuinely in business on their own account. Misclassification carries PAYE and penalty exposure | IRD | 2026-11-06 |
| Record keeping | 7 years, in English or Māori; electronic records acceptable | IRD | 2026-11-06 |
| No US-style information returns | New Zealand has no 1099-NEC or W-9 equivalent. Contractor reporting runs through schedular-payment withholding, not an annual form | IRD | 2026-11-06 |

## Agent boundaries

Safe to draft:

- GST-coded transaction registers
- GST return workings (output tax, input tax, adjustments)
- provisional tax workings and uplift comparisons
- kilometre-rate and logbook worksheets
- home office square metre calculations
- depreciation schedules using IRD rates
- low-value asset write-off lists
- schedular-payment and withholding summaries
- reconciliation reports and monthly close packages
- accountant/tax-agent ready packages

Requires user approval:

- posting entries to accounting software
- deleting, merging, or re-coding historical transactions
- filing or paying a GST return, provisional tax, PAYE or KiwiSaver obligation
- changing GST registration, basis or filing frequency
- applying an override to amounts, dates, suppliers or GST codes
- writing off a shareholder current account balance

Requires professional review:

- entity type, LTC elections, or trust distributions
- GST treatment of mixed, exempt or zero-rated supplies
- residential property transactions and the brightline rules
- shareholder current accounts and overdrawn balances
- FBT positions and motor vehicle valuation
- contractor vs employee classification disputes
- non-resident contractors and cross-border supplies
- any final tax filing position or amended assessment

## Related skills

- `bookkeeping-setup`
- `income-invoicing`
- `receipt-processing`
- `expense-categorization`
- `bank-reconciliation`
- `monthly-close`
- `tax-prep`
- `depreciation-assets` (the *concept* applies; the $2,500 de minimis and Section 179 do not — use the $1,000 low-value threshold in this pack)
- `contractor-1099` (the *contractor tracking* pattern applies; W-9 and 1099-NEC do not)
