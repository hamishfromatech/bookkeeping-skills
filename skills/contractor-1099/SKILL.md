---
name: contractor-1099
title: 1099 contractor management
description: Track independent contractor payments, collect W-9s, determine 1099-NEC filing requirements, and avoid penalties. Covers the $2,000 threshold from tax year 2026 ($600 through 2025), the 31 January deadline, corporate exceptions, backup withholding, and the penalty schedule ($60/$130/$340/$680 per form). Trigger on "1099", "contractor payment", "do I need to file a 1099", "W-9", "independent contractor".
license: MIT
compatibility: Designed for skills-compatible agents with access to payment records, contractor lists, and the US jurisdiction pack.
metadata:
  version: "3.1"
  execution-mode: semi-automated
allowed-tools: Read Write Edit WebFetch
publishDate: 2026-03-24
updatedDate: 2026-11-06
tags:
  - tax
  - 1099
  - contractors
featured: false
---

# 1099 Contractor Management

Track payments to independent contractors, determine who needs a 1099-NEC, collect W-9s, and file on time to avoid penalties.

## When do you need to file a 1099-NEC?

File a 1099-NEC for each person or non-corporate entity to whom you paid at least the reporting threshold during the calendar year for services performed in the course of your trade or business.

**The threshold is not static.** It was $600 for many years and increased to **$2,000 for payments made on or after 1 January 2026**. Read the current figure from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md) and use the threshold that applied to the payment date, not the filing date. If a payment spans the change (services in 2025, paid in 2026), flag it rather than guessing.

Keep tracking **all** contractor payments regardless of threshold. The total is the evidence, and the threshold has changed once already.

**If you are not in the US, this skill's form mechanics do not apply.** Australia, for example, has no 1099-NEC; contractor reporting runs through an ABN and, for certain industries, the Taxable payments annual report. See [jurisdictions/au.md](../../jurisdictions/au.md).

## Who needs a 1099-NEC?

| Payee type | 1099-NEC required? | Notes |
|-----------|-------------------|-------|
| Individual (sole proprietor, freelancer) | **Yes** at or above the threshold | Most common scenario |
| Single-member LLC (disregarded entity) | **Yes** at or above the threshold | Treated as individual for tax purposes |
| Partnership / Multi-member LLC | **Yes** at or above the threshold | |
| S-Corporation | **Generally no** | **Exception:** payments for legal services and medical/health care services always require a 1099 regardless of entity type |
| C-Corporation | **Generally no** | Same exceptions as S-Corp: legal and medical services |
| Payments via credit/debit card or third-party networks | **No** | The payment processor (Stripe, PayPal, Venmo, Square) reports these on **1099-K** instead. You don't double-report. |
| Employees | **No** | They get a W-2, not a 1099 |
| Rent paid to real estate agents | **No (1099-NEC)** | Gets 1099-MISC instead |
| Payments for merchandise/inventory | **No** | 1099-NEC is for services, not goods |

## The W-9: Get it before you pay

**Form W-9** (Request for Taxpayer Identification Number) collects the information you need to file a 1099. Collect it from every contractor **before making the first payment.** This is critical — chasing down W-9s in January when you're trying to file is miserable.

**What the W-9 provides:** Legal name, business name (if different), federal tax classification (individual, LLC, corporation, etc.), address, and TIN (Taxpayer Identification Number — either SSN or EIN).

**If a contractor refuses to provide a W-9:** You are required to begin **backup withholding** at **24%** of all future payments to that contractor. You must remit the withheld amount to the IRS using Form 945. This is not optional — failing to withhold when required makes you liable for the tax.

**Best practice:** Make W-9 collection part of your contractor onboarding process. No W-9, no first payment. Store W-9s securely — they contain SSNs.

## Tracking payments throughout the year

Don't wait until January to figure out who needs a 1099. Track continuously:

| Contractor | Entity type | TIN on file? | Payment method | Q1 | Q2 | Q3 | Q4 | YTD total | 1099 required? |
|-----------|------------|-------------|---------------|-----|-----|-----|-----|-----------|---------------|
| Jane Smith Design | Individual | SSN ✓ | ACH | $2,100 | $2,100 | $2,100 | $2,100 | $8,400 | Yes |
| Acme Dev LLC | LLC (single-member) | EIN ✓ | Check | $6,000 | $6,000 | $6,000 | $6,000 | $24,000 | Yes |
| CloudFlare Inc | C-Corp | EIN ✓ | Credit card | $300 | $300 | $300 | $300 | $1,200 | No (corp + card) |
| Bob's Plumbing | Individual | None ❌ | Check | $0 | $0 | $800 | $0 | $800 | Yes (get W-9!) |
| Legal Eagle LLP | Partnership | EIN ✓ | ACH | $0 | $5,000 | $0 | $0 | $5,000 | Yes |

**Monthly check:** During your monthly close, review contractor YTD totals. Flag anyone who has crossed or is approaching the threshold. Verify W-9s are on file for everyone above threshold.

An email-native extractor can pull contractor invoices automatically, making it easy to maintain accurate year-to-date totals throughout the year instead of scrambling in January. If there is no extractor, keep a running payments register updated at each monthly close.

## Filing deadline and forms

**Deadline:** **January 31** of the year following payment. Both the contractor's copy AND the IRS filing are due on January 31. There is **no extension** for 1099-NEC (unlike 1099-MISC, which has a March deadline for the IRS copy).

**What you file:**
- **Copy A** — to the IRS (electronically via FIRE system, or paper with Form 1096 transmittal)
- **Copy B** — to the contractor
- **Copy C** — for your records

**Electronic filing requirement:** If you are filing 10 or more information returns in aggregate (any combination of 1099s, W-2s, etc.), you must file electronically. That threshold dropped from 250 to 10 for filings from 2024 onward.

**How to file:** Use the IRS FIRE (Filing Information Returns Electronically) system, or use a service like Tax1099.com, Track1099, QuickBooks, or Gusto that handles the filing for you. Paper filing with Form 1096 is still allowed if filing fewer than 10 total information returns.

## Penalties for late or incorrect filing

Penalty amounts are indexed annually. Read the current per-form amounts from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md). The structure is:

| When you file | Penalty tier |
|---|---|
| Within 30 days of the deadline | lowest tier |
| 31 days late through 1 August | middle tier |
| After 1 August, or not filed at all | highest tier |
| **Intentional disregard** (you knew and didn't file) | roughly double the highest tier, **no maximum cap** |

Annual maximums also apply for small businesses and are indexed too. Intentional disregard has no maximum.

These penalties apply **per form** — if you have 20 contractors and miss all of them, multiply accordingly. The penalties also apply to incorrect forms (wrong TIN, wrong amount, wrong name).

## Correcting 1099s

If you discover an error after filing, file a corrected 1099-NEC:

**Type 1 correction:** Wrong amount, wrong code, or wrong checkbox. File a new 1099-NEC with the "CORRECTED" box checked and the correct information.

**Type 2 correction:** Wrong payee name or TIN. This requires two forms: one to zero out the incorrect payee, and one with the correct payee information.

File corrections as soon as you discover the error. If you correct before the IRS notices, you generally avoid penalties.

## Worker classification: Employee vs. contractor

This is the most dangerous area of 1099 compliance. If you classify a worker as a contractor when they should be an employee, you face:

- Back employment taxes (employer's share of FICA: 7.65% of all payments)
- Penalties for failure to withhold income tax
- Penalties for failure to file W-2s
- Interest on all of the above
- Potential state-level penalties (many states are even more aggressive than the IRS)

**Key factors the IRS considers (common law test):**

**Behavioral control:** Do you control how the work is done, or just the result? Contractors control their own methods. If you dictate hours, tools, processes, and work location, that looks like an employee.

**Financial control:** Does the worker have unreimbursed business expenses? Do they invest in their own tools/equipment? Can they profit or lose money? Do they offer services to the general public? Contractors typically say yes to all of these.

**Relationship:** Is there a written contract? Are there employee-type benefits (insurance, retirement, PTO)? Is the relationship permanent or project-based? Is the work a key part of your regular business? Employee indicators: ongoing relationship, benefits, work is core to the business.

**When in doubt:** File Form SS-8 with the IRS to request a worker classification determination. Or consult an employment attorney. The cost of getting it wrong vastly exceeds the cost of getting professional advice.

## Year-end checklist

By December 15:
- [ ] Review all contractor YTD totals
- [ ] Verify W-9 is on file for every contractor above threshold
- [ ] Request W-9s from any contractor without one
- [ ] Verify TINs match contractor names (consider TIN matching via IRS e-Services)

By January 31:
- [ ] Generate 1099-NEC forms for all qualifying contractors
- [ ] Mail or electronically deliver Copy B to each contractor
- [ ] File Copy A with the IRS (electronically if ≥10 forms)
- [ ] Retain Copy C for your records

After filing:
- [ ] Monitor for any IRS notices about mismatches
- [ ] File corrections promptly if errors are discovered

## Agent metadata

```yaml
skill: contractor-1099
version: 3.1
input: contractor payment records, W-9 status, payment dates and methods
output: 1099-NEC exposure summary + W-9 gap list + filing checklist
jurisdiction: us
automation_boundary: draft-and-flag
approval_required_for:
  - applying a treatment to a specific transaction
  - filing or finalising a position
next_steps:
  - tax-prep
```
