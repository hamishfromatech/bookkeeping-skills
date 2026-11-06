# Revenue and Invoice Schema

Use this file when producing JSON, CSV, or a revenue register artifact.

## Required fields

| Field | Type | Notes |
|---|---|---|
| `customer_name` | string | Legal or trading name of the buyer |
| `issue_date` | string | `YYYY-MM-DD` invoice or sale date |
| `total_amount` | number | Gross amount including tax/GST/VAT, in `currency` |
| `currency` | string | ISO 4217 currency code |
| `status` | string | `draft`, `open`, `paid`, `partially-paid`, `overdue`, `void`, `credited` |
| `source_type` | string | `invoicing-tool`, `processor-export`, `csv`, `bank`, `manual-review` |
| `source_reference` | string | Export row ID, invoice ID, payout ID, or file path |
| `confidence` | string | `high`, `medium`, `low` |

## Recommended fields

| Field | Type | Notes |
|---|---|---|
| `invoice_number` | string | Must be unique and sequential per entity; never reused |
| `due_date` | string | `YYYY-MM-DD`. Omit rather than invent terms |
| `service_period_start` | string | Needed for revenue-recognition timing |
| `service_period_end` | string | |
| `net_amount` | number | Excluding tax |
| `tax_amount` | number | Tax, GST, or VAT collected |
| `tax_rate` | number | Percentage, e.g. `10` or `8.875` |
| `tax_code` | string | Jurisdiction-specific code, e.g. `GST`, `GST-FREE`, `INPUT-TAXED`, `EXEMPT` |
| `amount_paid` | number | Sum of payments applied to this invoice |
| `amount_outstanding` | number | `total_amount − amount_paid` |
| `payment_method` | string | Card, ACH, bank transfer, cash, PayPal, etc. |
| `processor` | string | Stripe, Square, PayPal, Shopify, etc. |
| `processor_fee` | number | Fee charged for this sale — record as an expense, never net it off revenue |
| `payout_id` | string | Processor settlement ID that this sale was paid out in |
| `customer_tax_id` | string | ABN, VAT number, or state resale certificate as applicable |
| `business_purpose` | string | Rarely relevant for income; use for grant or reimbursement income |

## Line items

When available, include:

```json
[
  {
    "description": "Consulting — October retainer",
    "quantity": 1,
    "unit_price": 3000.00,
    "line_total": 3000.00,
    "tax_code": "GST"
  }
]
```

## JSON example

```json
{
  "customer_name": "Acme Corp",
  "invoice_number": "INV-2026-0142",
  "issue_date": "2026-10-03",
  "due_date": "2026-10-17",
  "service_period_start": "2026-10-01",
  "service_period_end": "2026-10-31",
  "net_amount": 3000.00,
  "tax_amount": 300.00,
  "tax_rate": 10,
  "tax_code": "GST",
  "total_amount": 3300.00,
  "amount_paid": 0,
  "amount_outstanding": 3300.00,
  "currency": "AUD",
  "status": "open",
  "payment_method": null,
  "processor": null,
  "processor_fee": 0,
  "source_type": "invoicing-tool",
  "source_reference": "xero:invoice:8f2c41a0",
  "confidence": "high"
}
```

## CSV columns

Use this column order when exporting CSV:

```text
invoice_number,customer_name,issue_date,due_date,service_period_start,service_period_end,net_amount,tax_amount,total_amount,amount_paid,amount_outstanding,currency,tax_code,status,payment_method,processor,processor_fee,payout_id,source_type,source_reference,confidence
```

## Gross-versus-net processor example

A payout covering two sales with different fees:

```json
{
  "payout_id": "po_1QxAbC",
  "period_start": "2026-10-01",
  "period_end": "2026-10-15",
  "gross_sales": 4300.00,
  "refunds": 0.00,
  "fees": 125.30,
  "net_settlement": 4174.70,
  "bank_account": "****4521",
  "sale_references": ["INV-2026-0142", "ch_3Pq7Yz"]
}
```

Book revenue at `gross_sales` and fees at `fees`. The bank deposit is `net_settlement` and is the only line the bank statement will show.

## AR aging extension

If producing an aging report, add:

| Field | Type | Notes |
|---|---|---|
| `days_overdue` | integer | Negative = not yet due; `null` if `due_date` is missing |
| `aging_bucket` | string | `not-yet-due`, `1-30`, `31-60`, `61-90`, `90-plus`, `unknown-due-date` |

## Status semantics

| Status | Means | Affects revenue? |
|---|---|---|
| `draft` | Not issued. No sequence number consumed | No |
| `open` | Issued, unpaid, within terms | Accrual basis only |
| `partially-paid` | Some payment received | Accrual basis only |
| `paid` | Fully settled | Yes |
| `overdue` | Issued, unpaid, past due date | Accrual basis only |
| `void` | Cancelled before settlement; credit note issued | No (original + credit net to zero) |
| `credited` | Reduced by a credit note | Reduced by the credit amount |
