---
name: depreciation-assets
title: Depreciation and asset tracking
description: Determine whether to expense or depreciate business assets using the de minimis safe harbor, Section 179, 100% bonus depreciation, or MACRS schedules. Track asset basis, useful life, and accumulated depreciation. Year-specific limits live in the US jurisdiction pack. Trigger on "depreciate", "Section 179", "bonus depreciation", "capitalize or expense", "asset tracking", "de minimis".
license: MIT
compatibility: Designed for skills-compatible agents with access to asset purchases, invoices, and the US jurisdiction pack.
metadata:
  version: "3.1"
  execution-mode: semi-automated
allowed-tools: Read Write Edit WebFetch
publishDate: 2026-03-24
updatedDate: 2026-11-06
tags:
  - tax
  - depreciation
  - assets
featured: false
---

# Depreciation and Asset Tracking

Determine the correct tax treatment for business assets: immediate expensing vs. capitalization and depreciation. Track each asset's basis, method, and accumulated depreciation.

## The core question: expense or capitalize?

When you buy something for your business, the tax treatment depends on two factors:

1. **Cost** — Is it above or below $2,500?
2. **Useful life** — Will it last more than one year?

If the answer to both is "above $2,500" and "more than one year," you generally must capitalize the asset and depreciate it over time. But there are several ways to accelerate or fully expense the cost in year one.

## Decision tree

```
Purchase amount ≤$2,500?
  └─ YES → Expense immediately (de minimis safe harbor)
  └─ NO → Useful life > 1 year?
       └─ NO → Expense immediately (ordinary business expense)
       └─ YES → Choose: Section 179, bonus depreciation, or regular MACRS
```

## Option 1: De minimis safe harbor (≤$2,500)

Items costing **$2,500 or less** per invoice (or per item if the invoice lists items separately) can be expensed immediately rather than depreciated.

**Requirements:**
- Must make an annual election by attaching a statement to your tax return
- The $2,500 threshold applies per invoice or per item — not per total purchase. If you buy 10 monitors at $400 each on one invoice for $4,000, each monitor is under $2,500 and qualifies
- Must have written accounting procedures in place (or follow IRS guidelines)

**For businesses with audited financial statements (AFS):** The threshold is $5,000 per item instead of $2,500. Most small businesses don't have AFS, so $2,500 applies.

**Common items that qualify:** Laptops under $2,500, monitors, keyboards/mice, basic printers, office chairs, desks, external hard drives, tablets, basic smartphones, small tools, basic software licenses.

**Common items that DON'T qualify (over $2,500):** MacBook Pro ($2,499+ configurations), high-end monitors ($2,500+), standing desk setups ($2,500+ total), photography equipment, specialized machinery, vehicles.

## Option 2: Section 179 (full first-year expensing)

Allows you to deduct the **full cost** of qualifying assets in the year they're placed in service, regardless of useful life.

**Limits: read them from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md).** Both the maximum deduction and the phase-out threshold are indexed annually. The OBBBA increased the limit substantially from 2025, so any figure quoted from memory before mid-2025 is wrong.

The phase-out is dollar-for-dollar: once total qualifying purchases exceed the phase-out threshold, the deduction limit falls by the same amount. Compute the current year's effective cap from the two figures in the jurisdiction pack — do not reuse last year's worked example.

**What qualifies:**
- Tangible personal property: computers, machinery, equipment, furniture, vehicles (with limitations)
- Off-the-shelf software (not custom-developed)
- Certain improvements to nonresidential real property: roofs, HVAC, fire protection, alarm/security systems
- Qualified improvement property (interior improvements to nonresidential buildings)

**What does NOT qualify:**
- Real property (buildings, structural components)
- Land
- Inventory
- Property used outside the US
- Property acquired from a related party
- Air conditioning or heating units (unless part of a building improvement)

**Vehicle limitations (Section 179):**
- SUVs over 6,000 lbs GVWR: Section 179 is capped at a separate, much lower annual figure for SUVs. Read it from the jurisdiction pack.
- Passenger automobiles: subject to annual luxury auto limits (see vehicle-expenses skill)
- Heavy vehicles over 6,000 lbs GVWR that are NOT SUVs (trucks, vans): no special Section 179 limit — full deduction allowed up to the general cap

**Key advantage:** You choose exactly how much to expense under Section 179 (up to the limit). This gives you control over your taxable income.

**Key limitation:** Section 179 cannot create or increase a net loss. The deduction is limited to your taxable income from all active trades or businesses. Any unused amount carries forward to future years.

## Option 3: Bonus depreciation (first-year percentage)

Allows a **percentage** of the asset's cost to be deducted in the first year, with the remainder depreciated normally.

**Current percentage: read it from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md).** The phase-down schedule written into TCJA was superseded by the OBBBA, which restored 100% bonus depreciation for qualified property. Bonus percentages have changed three times since 2022 — never quote them from memory, and never assume a phase-out is still running.

The important mechanic: the percentage applies to **qualified property placed in service in that year**. Property placed in service in an earlier year keeps the percentage that applied then.

**What qualifies:** Most tangible property with a MACRS recovery period of 20 years or less, computer software, qualified film/TV/live theatrical production, specified plants. Both **new and used** property qualify (since TCJA 2017 — previously only new property).

**Key advantages over Section 179:**
- No annual dollar limit
- Can create or increase a net loss (unlike Section 179)
- Applies automatically unless you elect out

**Key disadvantage:** You don't control the amount — it's all or nothing for each asset. To partially use bonus depreciation, you'd use Section 179 for the controlled portion.

**Electing out:** You can elect out of bonus depreciation on a class-by-class basis (e.g., elect out for all 5-year property but keep it for 7-year property). Do this if you want to spread the deduction over multiple years — useful if you expect higher income in future years.

## Option 4: Regular MACRS depreciation

If you don't use Section 179 or bonus depreciation (or for the portion not covered by them), assets are depreciated under MACRS (Modified Accelerated Cost Recovery System).

### Common MACRS class lives

| Asset type | Recovery period | Examples |
|-----------|----------------|---------|
| **3-year** | 3 years | Tractor units, racehorses, some manufacturing tools |
| **5-year** | 5 years | Computers, peripherals, copiers, typewriters, automobiles, light trucks, research equipment, certain manufacturing equipment |
| **7-year** | 7 years | Office furniture (desks, chairs, filing cabinets), fixtures, agricultural machinery, any asset without a designated class life |
| **10-year** | 10 years | Water transportation equipment, some fruit/nut trees |
| **15-year** | 15 years | Land improvements (fences, roads, sidewalks, landscaping, parking lots), qualified improvement property |
| **27.5-year** | 27.5 years | Residential rental property |
| **39-year** | 39 years | Nonresidential real property (office buildings, retail stores, warehouses) |

### Depreciation methods

**GDS (General Depreciation System)** — Default. Uses 200% declining balance for 3-, 5-, 7-, 10-year property; 150% declining balance for 15-, 20-year property; straight-line for 27.5- and 39-year property.

**ADS (Alternative Depreciation System)** — Required for certain situations (listed property used ≤50% for business, tax-exempt use property, farming with elected straight-line). Uses straight-line depreciation with longer recovery periods.

### Half-year and mid-quarter conventions

**Half-year convention (default):** Regardless of when during the year you bought the asset, you get half a year's depreciation in year 1 and half a year in the final year. This is the standard.

**Mid-quarter convention (triggered):** If more than 40% of your total asset purchases for the year are placed in service in Q4, ALL assets for the year use the mid-quarter convention instead. This generally results in less depreciation for Q4 purchases (1.5 months instead of 6 months). Watch for this if you're buying a lot of equipment late in the year.

## Asset tracking register

Maintain a register of all capitalized assets:

| Asset | Date placed in service | Cost basis | Business use % | Method | Prior depreciation | Current year | Remaining basis |
|-------|----------------------|-----------|---------------|--------|-------------------|-------------|----------------|
| MacBook Pro 16" | 2024-03-15 | $3,499 | 100% | Sec 179 | $3,499 | $0 | $0 |
| Herman Miller desk | 2024-06-01 | $2,800 | 100% | Bonus | $1,680 | $160 | $960 |
| Honda CR-V (business) | 2023-09-01 | $32,000 | 75% | MACRS 5yr | $7,200 | $3,840 | $12,960 |
| Office renovation | 2024-01-15 | $18,000 | 100% | MACRS 15yr | $600 | $1,200 | $16,200 |

The figures above illustrate **structure, not current law** — they are placeholder values. Compute real depreciation from the method, class life and the year-specific limit in the jurisdiction pack.

Update this register annually when preparing tax returns. Your accountant needs this to complete Form 4562.

## Disposition of assets

When you sell, trade in, donate, or discard a depreciated asset:

**Gain calculation:** Sale price − remaining basis = gain. If the sale price exceeds original cost, you have a gain. If it's between remaining basis and original cost, you have depreciation recapture (taxed as ordinary income, up to 25% for real property). If it's below remaining basis, you have a loss.

**Section 179 recapture:** If business use of a Section 179 asset drops to 50% or below before the end of the MACRS recovery period, you must recapture (add back to income) the excess Section 179 benefit.

**Fully depreciated assets still in use:** No more depreciation expense, but keep them on the register until disposed of. If you sell a fully depreciated asset, the entire sale price is gain.

## Common mistakes

**Expensing assets over $2,500 without Section 179 election.** A $3,000 laptop put in "Office Supplies" is wrong unless you've made a Section 179 election on Form 4562.

**Forgetting the de minimis election.** The $2,500 safe harbor requires an annual election statement. Without it, even a $500 chair technically should be depreciated (though in practice the IRS rarely enforces this for very small amounts).

**Depreciating land.** Land is never depreciable. When you buy property, allocate between building (depreciable) and land (not depreciable) based on appraisal or tax assessment ratios.

**Using the wrong class life.** A computer is 5-year property, not 7-year. Office furniture is 7-year, not 5-year. Using the wrong class life changes the annual deduction amount and can trigger issues on audit.

**Not tracking business-use percentage.** If business use of an asset drops below 50% in any year, you must switch from MACRS to ADS (slower depreciation) and may need to recapture previously claimed Section 179 or bonus depreciation. Track business-use percentages annually.

## Agent metadata

```yaml
skill: depreciation-assets
version: 3.1
input: asset purchases, placed-in-service dates, business-use percentages
output: asset register + depreciation schedule + Form 4562 inputs
jurisdiction: us
automation_boundary: draft-and-flag
approval_required_for:
  - applying a treatment to a specific transaction
  - filing or finalising a position
next_steps:
  - tax-prep
```
