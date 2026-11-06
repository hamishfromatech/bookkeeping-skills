---
name: estimated-taxes
title: Estimated tax payments
description: Calculate and schedule quarterly estimated tax payments (Form 1040-ES) for self-employed individuals. Covers self-employment tax calculation, income tax estimation, safe harbour rules, payment deadlines, and underpayment penalties. Year-specific rates live in the US jurisdiction pack. Trigger on "estimated taxes", "quarterly taxes", "1040-ES", "how much should I pay quarterly", "self-employment tax", "avoid tax penalty".
license: MIT
compatibility: Designed for skills-compatible agents with access to categorized books, prior-year return figures, and the US jurisdiction pack.
metadata:
  version: "3.1"
  execution-mode: semi-automated
allowed-tools: Read Write Edit WebFetch
publishDate: 2026-03-24
updatedDate: 2026-11-06
tags:
  - tax
  - quarterly
  - estimated-taxes
featured: false
---

# Estimated Tax Payments

Calculate and schedule quarterly estimated tax payments to avoid underpayment penalties. Essential for self-employed individuals, freelancers, and small business owners who don't have taxes withheld from a paycheck.

## Why you need to pay quarterly

Employees have taxes withheld every paycheck. Self-employed people don't. The IRS expects to receive tax payments throughout the year, not one lump sum in April. If you wait until filing to pay everything, you'll owe an underpayment penalty.

**You must make estimated payments if** you expect to owe **$1,000 or more** in tax for the year after subtracting withholding and credits.

**You're exempt if:** You had zero tax liability last year (100% of prior-year tax is $0), or your withholding from other sources (W-2 job, pension, etc.) covers your expected tax.

## Payment schedule

| Quarter | Covers income from | Payment due |
|---------|-------------------|-------------|
| Q1 | January 1 – March 31 | **April 15** |
| Q2 | April 1 – May 31 | **June 15** |
| Q3 | June 1 – August 31 | **September 15** |
| Q4 | September 1 – December 31 | **January 15** (next year) |

Note: Q2 covers only 2 months and Q3 covers 3 months — the periods are uneven. If a due date falls on a weekend or holiday, the deadline moves to the next business day.

**How to pay:** IRS Direct Pay (irs.gov/payments), EFTPS (Electronic Federal Tax Payment System), credit/debit card (processors charge a fee), or mail a check with a 1040-ES payment voucher. Direct Pay or EFTPS are free and instant-confirmation.

## The two things you're paying

### 1. Self-employment tax (Social Security + Medicare)

This is the self-employed equivalent of FICA. Employees pay 7.65% and their employer pays 7.65%. As a self-employed person, you pay both halves.

**Calculation:**

```
Net Schedule C profit                               $100,000
× 92.35% (adjustment factor)                        × 0.9235
= Self-employment tax base                          $92,350
× 15.3% (12.4% Social Security + 2.9% Medicare)     × 0.153
= Self-employment tax                               $14,130
```

**Social Security cap:** The 12.4% Social Security portion applies only up to the annual Social Security wage base. Read it from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md) — it is re-indexed every year. Income above the cap is taxed only at the 2.9% Medicare rate.

Also note the cap is applied to **combined** wages plus self-employment income. If the user also has a W-2 job, employer withholding may already have consumed part or all of the cap.

**Additional Medicare tax:** If net self-employment income exceeds **$200,000** ($250,000 married filing jointly), an additional **0.9% Medicare surtax** applies on the excess.

**Half is deductible:** 50% of your self-employment tax is an above-the-line deduction on Form 1040 — you get it even if you don't itemize. It reduces income tax but not self-employment tax. Refer to the deduction by name rather than by line number; the form is renumbered periodically.

### 2. Income tax (federal)

Your Schedule C net profit (minus the above-the-line SE tax deduction, plus any other income, minus other deductions) is taxed at your marginal income tax rate.

**Do not use a memorised bracket table.** Brackets are re-indexed every year, and a stale table silently produces a wrong payment. Read the current-year brackets from the IRS (or use the Form 1040-ES worksheet), state the tax year used in the output, and cite the source.

Brackets: <https://www.irs.gov/filing/federal-income-tax-rates-and-brackets>

That also applies to the **standard deduction**, which is tabulated in [jurisdictions/us.md](../../jurisdictions/us.md) and changes annually.

Don't forget: self-employed health insurance, retirement contributions, and the 50% SE tax deduction are all above-the-line and reduce taxable income **before** applying the brackets.

## Quick estimation method

For a back-of-the-envelope quarterly payment:

```
Estimated annual net profit          $100,000
Self-employment tax:                  $14,130
Deductible half of SE tax:           −$7,065
Adjusted profit for income tax:       $92,935
Federal income tax (approx):          $15,000  (depends on filing status, other income, deductions)
Total estimated tax:                  $29,130
÷ 4 quarters:                         $7,283 per quarter
```

This is a rough estimate. For precision, use IRS Form 1040-ES worksheet or tax software.

## Safe harbor rules — how to avoid penalties

Even if your estimate is wrong, you avoid the underpayment penalty if you meet either safe harbor:

### Safe harbor 1: 90% of current-year tax

Pay at least 90% of what you'll actually owe for the current year. This requires accurately predicting your income — hard if your income fluctuates.

### Safe harbor 2: 100% of prior-year tax (the easy one)

Pay at least **100% of last year's total tax liability**, divided into four equal quarterly payments. If your prior-year AGI exceeded **$150,000** ($75,000 married filing separately), the threshold is **110%** of prior-year tax.

**This is the safe harbor most self-employed people use** because it's predictable. You know exactly what last year's tax was. It doesn't matter if you earn more this year — as long as your quarterly payments total 100% (or 110%) of last year's tax, no penalty.

**Where to find prior-year tax:** Form 1040 Line 24 (total tax) minus Line 33 (total payments and credits from withholding, etc.). Or your tax software will calculate it.

### Which safe harbor to use?

| Situation | Best safe harbor |
|---|---|
| Income is stable year to year | Either works, but prior-year is simpler |
| Income is growing | Prior-year — pay based on last year, even if this year is higher |
| Income is dropping | Current-year 90% — why overpay based on a higher prior year? |
| First year of self-employment | Current-year 90% — there's no prior-year SE tax to use |
| Prior-year AGI >$150K | 110% of prior-year tax |

## Annualized income installment method

If your income is highly seasonal (e.g., 70% of revenue in Q4), you can use the **annualized income installment method** (Form 2210 Schedule AI). This calculates each quarter's required payment based on income actually earned through that quarter, rather than dividing the annual estimate by 4.

This is more work but avoids overpaying early in the year when income hasn't arrived yet. Useful for: holiday-season businesses, accountants/CPAs (busy Jan–Apr), real estate agents (spring/summer heavy), consultants with uneven project timing.

## State estimated taxes

Most states with income tax also require quarterly estimated payments, often on the same schedule. Common states with self-employment-relevant taxes:

- **California:** Franchise Tax Board, same quarterly dates. Uses 30/40/0/30% allocation instead of equal quarters.
- **New York:** Same quarterly dates. NYC residents also owe city estimated tax.
- **Texas, Florida, Nevada, Wyoming, Washington, South Dakota, Alaska, New Hampshire (wages only):** No state income tax — no state estimated payments needed.

Check your state's requirements separately. Some states have different safe harbor rules.

## What happens if you underpay

The penalty is essentially interest on the underpayment. The IRS charges the federal short-term rate + 3% (currently around 8% annually, but it fluctuates). The penalty is calculated per quarter, so paying late for Q1 accumulates more penalty than paying late for Q4.

**The penalty is NOT a flat fee** — it's computed as interest. If you underpaid by $5,000 for one quarter, the penalty might be $100–$150 for that quarter. Annoying but not catastrophic.

**When the penalty is waived:** If you owe less than $1,000 at filing. If your withholding + estimated payments cover at least 90% or the 100%/110% safe harbor. If you had a casualty, disaster, or other unusual circumstance. If you retired or became disabled during the year.

## Adjusting payments mid-year

If your income changes significantly during the year, adjust your remaining quarterly payments. The IRS doesn't require equal payments — you can pay $2,000 in Q1 and $10,000 in Q3 if that reflects your income pattern. Just ensure the total meets the safe harbor by year-end.

**If you realize you've underpaid:** Make a larger Q4 payment by January 15 to reduce the penalty. You can also increase Q4 to cover earlier shortfalls.

**If your income spiked late in the year:** Consider making an extra payment before December 31 to cover the spike. This doesn't have a special form — just make an additional estimated payment via Direct Pay or EFTPS marked for the current tax year.

## Integration with bookkeeping

During the monthly close, calculate year-to-date net profit. Before each quarterly deadline, estimate the quarter's tax liability and compare against your safe harbor target. This prevents the "surprise" of a large underpayment at filing.

Your monthly P&L from the monthly-close skill gives you the numbers you need. Multiply YTD net profit by your combined tax rate (SE tax + income tax marginal rate) and compare to payments made.

## Agent metadata

```yaml
skill: estimated-taxes
version: 3.1
input: year-to-date net profit, prior-year return figures, payments made
output: quarterly payment worksheet + safe harbour comparison
jurisdiction: us
automation_boundary: draft-and-flag
approval_required_for:
  - applying a treatment to a specific transaction
  - filing or finalising a position
next_steps:
  - monthly-close
```
