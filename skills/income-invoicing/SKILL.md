---
name: income-invoicing
title: Income and invoicing
description: Capture sales and revenue, issue and track invoices, manage receivables and aging, handle refunds, credits and chargebacks, and reconcile payment-processor payouts on a gross-versus-net basis. Produces a revenue register and AR summary that feed reconciliation, monthly close and tax prep. Trigger on "invoice my clients", "record a sale", "who owes me money", "accounts receivable", "unpaid invoices", "Stripe payout", "revenue report", "sales register".
license: MIT
compatibility: Designed for skills-compatible agents with access to invoices, sales records, payment-processor exports, bank statements, or accounting exports.
metadata:
  version: "3.3"
  execution-mode: semi-automated
  artifact-types: table,csv,json,revenue-register,ar-summary
allowed-tools: Read Write Edit WebFetch
publishDate: 2026-11-06
updatedDate: 2026-11-06
tags:
  - income
  - invoicing
  - receivables
  - revenue
  - skill
featured: true
---

# Income and Invoicing

Capture the revenue side of the books. Without it there is no P&L — only a list of expenses.

This skill covers sales capture, invoice issuance and tracking, receivables, refunds and credits, and payment-processor payouts. It ends where `bank-reconciliation` begins: every revenue figure produced here should be matchable to a bank deposit.

## Read these when needed

- Read [references/INVOICE-SCHEMA.md](references/INVOICE-SCHEMA.md) when producing JSON, CSV, or a revenue register artifact.
- Run `scripts/revenue_summary.py` when you already have invoice or sale records and need a deterministic revenue and AR-aging summary.

## Why this matters

Three problems show up in almost every small-business set of books, and all three are revenue-side:

1. **Revenue recorded net of processor fees.** Stripe pays $970 on a $1,000 sale. If the only entry is "$970 deposit", revenue is understated, expenses are understated, and the P&L is wrong in two places at once.
2. **Invoices treated as revenue when issued, or never recorded until paid.** On a cash basis, an unpaid invoice is not income yet. On an accrual basis, it is. Recording the wrong one changes profit, tax, and the AR balance.
3. **A bank deposit that cannot be tied to anything.** A $4,320 ACH credit with the reference "STRIPE" is not revenue evidence. It is a settlement of one or more sales, minus fees, possibly spanning two months.

## Tool priority

1. Accounting-system or invoicing-tool export (invoice list, customer list, payment list) — highest provenance
2. Payment-processor export (Stripe, Square, PayPal, Shopify, Gumroad, Xero/QuickBooks payments)
3. Bank deposits and merchant settlements
4. Manual reconstruction from client correspondence — last resort, flag every record

Do not infer revenue from bank deposits alone. A deposit is a settlement, not a sale.

## Procedure

### 1. Establish scope and basis

Before recording anything, confirm:

- **Period** — the date range being captured, and whether sales are recognised on invoice date, service date, or payment date
- **Basis** — cash or accrual, taken from the `bookkeeping_context_profile`. This decision changes whether an unpaid invoice is revenue.
- **Jurisdiction** — needed before applying sales tax, GST, or VAT. Load `jurisdictions/us.md` or `jurisdictions/au.md`.
- **Tax treatment** — is the business registered for sales tax / GST / VAT? Are any sales tax-exempt, GST-free, or input-taxed?
- **Currency** — home currency and any foreign-currency sales

If basis is unknown, record sales on invoice date but mark the register `basis: unknown` and flag that revenue timing is unconfirmed.

### 2. Normalise every sale and invoice

For each record, capture at minimum:

- `customer_name`
- `issue_date`
- `total_amount` (gross, tax-inclusive)
- `currency`
- `status` (`draft`, `open`, `paid`, `partially-paid`, `overdue`, `void`, `credited`)

Capture when available: `invoice_number`, `due_date`, `service_period_start`/`end`, `tax_amount`, `tax_rate`, `tax_code`, `amount_paid`, `payment_method`, `processor`, `processor_fee`, `source_reference`, `confidence`, `line_items`.

The full field list, JSON example and CSV column order live in [references/INVOICE-SCHEMA.md](references/INVOICE-SCHEMA.md).

### 3. Issue and number invoices correctly

Invoice numbering must be **sequential and never reused**, because tax authorities treat a gap in the sequence as a missing sale.

| Rule | Why |
|---|---|
| One sequence per entity, per jurisdiction | Auditors and tax authorities expect an unbroken series |
| Void by issuing a credit note, not by deleting | Deleting an invoice leaves a gap and destroys the audit trail |
| Never renumber to "tidy up" | Same reason |
| Keep original issue date when re-sending | Changing dates across periods is a red flag |
| State tax/GST/VAT separately | Required for a valid tax invoice in most jurisdictions |
| Include the legal entity name and tax registration number | Required for the customer to claim an input credit |

**Jurisdiction-specific invoice requirements:**

- **Australia** — a tax invoice is required for sales of $82.50 or more (incl. GST). It must show the seller's identity and ABN, the date, a description of what was sold, the GST amount (or that the total includes GST), and for sales of $1,000 or more, the buyer's identity or ABN. Sales that are GST-free must say so.
- **New Zealand** — since 1 April 2023 the "tax invoice" concept was replaced by **taxable supply information**. It is not required at or below $200 (GST inclusive), is required above $200, and needs additional detail above $1,000. GST is 15% and must be shown or stated as included. See [jurisdictions/nz.md](../../jurisdictions/nz.md).
- **US** — no federal invoice format, but state sales-tax rules require the tax to be separately stated where sales tax applies, and nexus rules determine whether it applies at all.

### 4. Handle receivables and aging

Produce an AR aging summary from the open invoices:

| Bucket | Meaning |
|---|---|
| Not yet due | Due date in the future |
| 1–30 days overdue | Standard follow-up window |
| 31–60 days overdue | Second reminder, confirm the invoice was received |
| 61–90 days overdue | Escalate; consider withholding further work |
| 90+ days overdue | Collection decision, or write-off review |
| Unknown due date | Missing `due_date` — flag, do not guess terms |

Do not silently write off old receivables. A write-off is an accounting decision with tax consequences (bad-debt treatment differs by jurisdiction and by basis); route it to review.

Cash-basis businesses still need this report. The invoice is not income until paid, but the receivable is the only record of what is owed, and chasing it is the point.

### 5. Reconcile payment-processor payouts on a gross basis

This is the most common revenue error. Record **gross sales** and **fees as a separate expense**, not a net deposit.

```text
Gross sales for the period         $1,000.00
Processor fee (2.9% + 30c)        −   $29.30
Net settlement to bank             $  970.70
```

Book:

```text
Debit   Bank                       970.70
Debit   Merchant fees (expense)     29.30
Credit  Sales revenue            1,000.00
```

Recording only the $970.70 deposit understates revenue by $29.30 and understates deductible fees by the same amount. Net profit is unchanged, but revenue, expense ratios, and any revenue-based threshold (GST registration, sales-tax nexus, 1099-K, small-business concessions) are all wrong.

Payouts typically lag sales by 2–7 days and can straddle month ends. Match on the **processor's settlement report**, not the bank date. Items to expect in a payout reconciliation:

- gross sales, refunds, chargebacks, and fee lines for the settlement period
- reserve or rolling-reserve holds
- currency-conversion lines and FX gains/losses
- payouts to a different bank account than expected

### 6. Refunds, credits, chargebacks and bad debts

| Item | Treatment | Review needed |
|---|---|---|
| Refund of a current-period sale | Reduce revenue (or record as a negative sale) in the same period | No |
| Refund of a prior-period sale | Reduce revenue in the current period, or restate — depends on materiality | Yes |
| Credit note for a voided invoice | Reduce revenue; keep the original invoice and the credit note linked | No |
| Chargeback | Reduce revenue; the chargeback fee is a separate expense | No |
| Chargeback later reversed | Reverse both entries | No |
| Uncollectible receivable | Write-off or bad-debt deduction — jurisdiction and basis dependent | Yes |
| Customer overpayment / prepayment | **Liability** (unearned revenue), not revenue, until the service is delivered | Yes |
| Deposit held for future work | **Liability**, not revenue | No |

Prepayments and deposits are the second-most-common revenue error: money received is not the same as revenue earned.

### 7. Jurisdiction notes

- **US** — sales tax is state and local, driven by nexus (economic or physical). Do not assume a sale is taxable or exempt. If the business sells into multiple states, flag it for review. 1099-K reports from processors are informational and do not replace the sales register. Revenue recognition follows the accounting method chosen in setup.
- **Australia** — GST is 10% on taxable supplies. Report total sales, GST-free sales, and input-taxed sales separately on the BAS; they are not interchangeable. Sales are reported for the period in which the invoice is issued (accrual) or payment is received (cash), matching the GST accounting basis chosen at registration.

### 8. Produce artifacts

Deliver one or more of:

- revenue register (table, CSV, or JSON per the schema)
- AR aging summary
- unmatched deposits / unexplained settlements list
- processor payout reconciliation
- exception queue: missing invoice numbers, gaps in sequence, duplicate invoices, sales with no matching deposit, deposits with no matching sale, currency mismatches

Always include a summary:

```text
Sales recorded: N
  Paid: N        Open: N        Overdue: N        Void/credited: N
Period: ...
Gross revenue: ...
Tax/GST collected: ...
Outstanding (AR): ...
Overdue: ...
Unmatched deposits: N
Processor fees recorded: ...
Sources: invoicing tool / processor export / bank / manual
Basis: cash | accrual | unknown
Jurisdiction: us | au | other | unknown
```

### 9. Hand off

- send the revenue register and AR summary to `bank-reconciliation` so deposits can be matched against sales
- include processor fees in `expense-categorization` rather than netting them against revenue
- `monthly-close` uses the revenue register for the P&L and the AR aging for the balance sheet
- `tax-prep` uses gross revenue, tax collected, and any unearned revenue split

## Automation boundary

Safe to automate without asking first:

- extracting sales and invoice records from a tool export
- normalising fields
- building the revenue register, CSV, or JSON
- computing AR aging
- flagging sequence gaps, duplicates, unmatched settlements, and fee-netting
- drafting invoice records for review

Require explicit user confirmation before:

- issuing or sending an invoice to a customer
- changing an invoice number, date, amount, or customer
- writing off a receivable
- reclassifying a prior-period sale or refund
- altering a sales-tax or GST code on a historical transaction
- posting revenue into live accounting software

Require professional review when:

- revenue recognition timing is unclear (milestones, retainers, subscriptions, long projects)
- the business has multi-state or cross-border sales-tax exposure
- GST-free, input-taxed, or export supplies are involved
- unearned revenue or prepayments are material
- an amended return or prior-year restatement would follow

## Related skills

- **bookkeeping-setup** — entity, basis, jurisdiction, chart of accounts
- **receipt-processing** — the expense-side counterpart
- **expense-categorization** — where processor fees belong
- **bank-reconciliation** — matches deposits to the revenue register
- **monthly-close** — consumes the register and AR aging
- **tax-prep** — consumes gross revenue and tax collected

## Agent metadata

```yaml
skill: income-invoicing
version: 3.3
input: invoice records, sales exports, processor settlements, bank deposits
output: revenue register + AR aging + exception queue
automation_boundary: extract-draft-and-summarise
approval_required_for:
  - issuing invoices
  - write-offs
  - prior-period reclassification
  - tax code changes
dependencies:
  - bookkeeping-setup (basis and jurisdiction)
  - jurisdictions/*
next_steps:
  - bank-reconciliation
  - monthly-close
```
