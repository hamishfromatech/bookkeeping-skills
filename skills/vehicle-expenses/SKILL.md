---
name: vehicle-expenses
title: Vehicle expense deduction
description: Choose between standard mileage rate and actual expenses for business vehicle deductions. Covers the current IRS mileage rate, method lock-in rules, mileage log requirements, commuting rules, luxury auto limits, and heavy vehicle exceptions. Year-specific rates live in the US jurisdiction pack. Trigger on "mileage deduction", "standard mileage rate", "vehicle expenses", "car deduction", "business miles", "mileage tracking".
license: MIT
compatibility: Designed for skills-compatible agents with access to mileage logs, vehicle costs, and the US jurisdiction pack.
metadata:
  version: "3.1"
  execution-mode: semi-automated
allowed-tools: Read Write Edit WebFetch
publishDate: 2026-03-24
updatedDate: 2026-11-06
tags:
  - tax
  - vehicle
  - deduction
  - mileage
featured: false
---

# Vehicle Expense Deduction

Choose and apply the right method for deducting business vehicle expenses: standard mileage rate or actual expenses.

## Two methods — pick one per vehicle

### Standard mileage rate

Multiply your business miles by the IRS standard rate. Simple.

**Current rate: read it from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md).** The rate is set annually and the IRS has revised the business rate mid-year, so for a full year you may need two rates (for example a different rate for each half of 2026). Never quote a mileage rate from memory.

Business miles × the applicable rate = deduction. If the rate changed mid-year, split the miles across the two rate periods and add the results. State the rate and the period used in the output.

What the rate includes: gas, oil, repairs, tires, insurance, registration, depreciation. You do NOT deduct these separately when using the standard mileage rate — they are baked into the per-mile rate.

What you CAN add on top: parking fees and tolls for business trips (deducted on Schedule C Line 24a Travel), and interest on a car loan (Line 16b).

**When you can use it:**
- You must use it in the first year the vehicle is available for business use. If you don't elect it in year 1, you're locked into actual expenses for that vehicle.
- You must own or lease the vehicle (not available for fleet vehicles of 5+ cars)
- You can't have claimed Section 179 or bonus depreciation on the vehicle
- You can't have used MACRS depreciation in a prior year (unless you switch from standard mileage, which then limits you to straight-line)

### Actual expense method

Track every dollar spent on the vehicle, then multiply by your business-use percentage.

**Deductible actual expenses:**
- Gas and oil
- Repairs and maintenance
- Tires
- Insurance
- Registration and license fees
- Lease payments (if leasing)
- Depreciation (if you own — subject to luxury auto limits)
- Garage rent
- Car washes (yes, really)

**Business-use percentage:** Total business miles ÷ total miles driven during the year. If you drove 15,000 miles total and 10,000 were for business, your business-use % is 66.7%. Apply this to all actual expenses.

## The method lock-in rule

This is the most important rule and the one most people get wrong:

| First-year choice | Can switch to standard mileage later? | Can switch to actual later? |
|---|---|---|
| **Standard mileage** | N/A | **Yes**, but depreciation limited to straight-line |
| **Actual expenses** | **No** — locked out of standard mileage for this vehicle permanently | N/A |
| **Section 179 or bonus depreciation claimed** | **No** — locked out permanently | N/A |

**Best practice:** Start every new vehicle on the standard mileage rate. This preserves your option to switch to actual later if circumstances change (e.g., repair costs spike). Going the other direction — actual to standard — is not allowed.

## What counts as a deductible business mile?

**Deductible:**
- Home to client site (if you have a home office that qualifies as your principal place of business)
- Office to client site
- Client site to client site
- Office to temporary work location
- Between two different work locations
- To the bank, post office, supply store for business errands

**NOT deductible — ever:**
- **Commuting** — driving from home to your regular office and back. This is personal, period. Even if you make business calls in the car. Even if you carry tools in the trunk.
- **Personal errands** — grocery store, gym, school pickup during a business trip

**The home office exception:** If your home office qualifies as your principal place of business (passes the exclusive-use test), then trips from home to any business destination are deductible — not commuting. This is a significant benefit that effectively makes your first and last trip of the day deductible.

## Mileage log requirements

The IRS requires "adequate records" or "sufficient evidence" to support your vehicle deduction. In practice, this means a contemporaneous log:

**What to record for each trip:**
| Field | Example |
|-------|---------|
| Date | 2026-03-15 |
| Destination | Acme Corp office, 123 Main St |
| Business purpose | Client meeting to review Q1 financials |
| Miles driven | 28.4 |

**"Contemporaneous" means:** Recorded at or near the time of the trip. An IRS auditor will reject a mileage log created at year-end from memory. Apps like MileIQ, Everlance, or TripLog record trips automatically via GPS.

**Annual totals needed:** Total miles driven for the year, total business miles, total commuting miles, total other personal miles. These go on Form 4562 Part V.

**Sampling method:** The IRS allows you to keep a detailed log for a representative period (e.g., 3 months) and extrapolate, provided your driving patterns are consistent. But a full-year log is always stronger evidence.

## Luxury auto depreciation limits

If you own a passenger automobile (under 6,000 lbs GVWR) and use the actual expense method, annual depreciation is capped by §280F. The caps are indexed each year and are published in an annual revenue procedure.

Read the current-year caps from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md). Do not quote them from memory — the first-year cap in particular moves most years.

Mechanics that matter more than the numbers:

- there is a **higher first-year cap** if §168(k) bonus depreciation is applied, and a lower one if it is not
- the caps apply **after** the business-use percentage is applied
- an expensive vehicle therefore takes many years to depreciate, well beyond the 5-year MACRS recovery period

## Heavy vehicle exception (>6,000 lbs GVWR)

Vehicles with a gross vehicle weight rating over 6,000 lbs are NOT subject to the luxury auto limits. This includes many full-size SUVs, trucks, and vans.

**Common qualifying vehicles:** Ford F-150, Chevy Silverado, Toyota Tundra, Ford Expedition, Chevy Tahoe, GMC Yukon, Jeep Grand Cherokee L, Mercedes GLS, BMW X5, Land Rover Defender, Tesla Model X.

**Section 179 limit for SUVs:** Even though heavy SUVs escape luxury auto limits, there is a separate, much lower Section 179 cap specifically for SUVs over 6,000 lbs. It is indexed annually — read the current figure from the constants table in [jurisdictions/us.md](../../jurisdictions/us.md). The remainder can use bonus depreciation.

**Heavy non-SUV vehicles** (trucks, vans built on a truck chassis): No special Section 179 limit. You can Section 179 the full cost up to the general annual limit, which is also read from the jurisdiction pack.

**Important:** The vehicle must be used >50% for business. If business use drops to 50% or below, you must recapture excess depreciation from prior years.

## Standard mileage vs. actual: which saves more?

**Standard mileage tends to win when:** Your car is fuel-efficient, has low maintenance costs, is relatively new (fewer repairs), and you drive a lot of business miles. The rate includes a depreciation component that gives you a "phantom" deduction even on a paid-off car.

**Actual expenses tend to win when:** You have an expensive vehicle (high insurance, high depreciation), your car needs a lot of repairs, your business-use percentage is very high (80%+), or you can claim significant Section 179 or bonus depreciation in year 1.

**Quick comparison (arithmetic shown with a placeholder rate so it cannot go stale):**

A freelancer driving 12,000 business miles in a Honda Civic, at rate `R`:
- Standard mileage: 12,000 × `R`
- Actual: ~$7,200 in total car costs × 80% business use = **$5,760** (plus maybe $2,000 depreciation = $7,760)

At any rate above about 48¢ the standard method wins on these assumptions.

A consultant driving 20,000 business miles in a BMW X5 (new, $65,000):
- Standard mileage: 20,000 × `R`
- Actual: ~$12,000 in costs × 90% business use = $10,800, plus Section 179 capped at the SUV limit in the jurisdiction pack

Actual expenses can win dramatically in year 1 because of Section 179. But you are locked in for the life of the vehicle.

## Multiple vehicles

Each vehicle is tracked independently. You can use standard mileage for one and actual for another. But you can't use standard mileage for a fleet of 5 or more vehicles used simultaneously.

## Leased vehicles

If you lease: you can use either the standard mileage rate OR actual expenses. If you choose actual, you deduct the business portion of lease payments (instead of depreciation). However, you may need to add back an "inclusion amount" from IRS tables if the vehicle's fair market value exceeds a certain threshold — this prevents using leasing to circumvent the luxury auto limits.

If you start with the standard mileage rate on a leased vehicle, you must use it for the entire lease period.

## Documentation checklist

- [ ] Mileage log (contemporaneous, with date/destination/purpose/miles for each trip)
- [ ] Annual totals: business miles, commuting miles, personal miles, total miles
- [ ] If actual method: all receipts for gas, repairs, insurance, registration
- [ ] If actual method: depreciation calculation and Form 4562
- [ ] For heavy vehicles: documentation of GVWR (from door sticker or registration)
- [ ] Business-use percentage calculation

## Agent metadata

```yaml
skill: vehicle-expenses
version: 3.1
input: mileage log, vehicle costs, method already elected
output: method comparison + deduction + log gap list
jurisdiction: us
automation_boundary: draft-and-flag
approval_required_for:
  - applying a treatment to a specific transaction
  - filing or finalising a position
next_steps:
  - tax-prep
```
