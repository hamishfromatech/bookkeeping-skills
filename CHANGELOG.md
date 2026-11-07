# Changelog

All notable changes to this skill pack. Versions apply to the skill content, not
to the repository as a product.

## 3.6 — 2026-11-06

### Added

- **`search_tools`**: a natural-language tool finder. Ask "how much tax do I owe this
  quarter" or "ACC levy for a roofer" and get the matching tool with its required
  parameters and a ready-to-run example, instead of reading every schema.
- **`BOOKKEEPING_MCP_TOOL_MODE=search`**: lists six tools instead of 24 and reaches
  the rest by name through **`run_tool`**. Tool payload drops from ~4,000 tokens to
  ~900, which is the point for small or cheap models.
- **Skills are searchable too**, tagged `kind: "skill"` with the resource URI to
  read. Without this, "is this expense deductible" resolved to the nearest
  calculator (`first_year_asset_expense`), which is the wrong answer.
- A registry-drift test: every live tool must have exactly one entry, every skill
  folder must have one, and no entry may reference something that does not exist.

### Fixed

- Tool matching was substring-based, so `"on"` matched inside `bonus`, `"new"`
  matched `New Zealand` and hijacked unrelated queries, and the amount `"110"`
  matched `100%/110%` in an estimated-tax description. Matching is now stemmed
  whole-word, with a stopword list and numeric tokens ignored unless they are a
  form or section number (`179`, `1099`, `1040`, …).
- Registry entries for `sales_tax` and `sum_amounts` gained the phrasing people
  actually use ("including tax", "add up invoices").

### Fixed after end-to-end testing

- "I run a roofing business, what will ACC cost on 120k" ranked the rate *lookup*
  above the *estimator*. Cost phrasing now favours `acc_levy_estimate`; rate phrasing
  still favours `acc_work_levy_rates`.
- "is a work laptop deductible" tied between `mileage_deduction` and
  `schedule-c-categories` and lost the tie alphabetically, sending a tax question to
  a mileage calculator. Ties now prefer the procedure when the query reads as a
  question, and the deductibility entry carries the asset words people type
  (laptop, computer, phone, tools, equipment).

### Changed

- 24 tools in `all` mode (23 + `search_tools`); 172 server tests.

## 3.5 — 2026-11-06

### Fixed

- **The ACC estimate was understating the invoice.** The [ACC Levy Guidebook 2026/27](https://www.acc.co.nz/assets/business/Levy-Guidebook-2026-2027.pdf)
  (p.10) states the **Working Safer levy** is a flat **$0.08 per $100** of liable
  earnings collected *in addition to* the work levy. `acc_levy_estimate` omitted
  it, so every estimate was low by $80 per $100,000 of liable earnings.
- **The liable-earnings cap now applies to the whole calculation.** MBIE's
  levy-setting page confirms maximum liable earnings of **$156,641** for the
  2026/27 levy period ($160,244 for 2027/28), and the guidebook describes a single
  cap for the levy calculation. Previously only the earners' levy was capped.

### Added

- `ACC minimum liable earnings` constant: **$50,501** for 2026/27. Surfaced, not
  applied — whether it bites depends on the taxpayer.

### Changed

- `acc_levy_estimate` now returns `liable_base`, `capped`, and a
  `working_safer_levy` component, and charges all three levies on the same base.
- At $120,000 a roofer's estimate moves from $5,202.60 to **$5,313.00**; a sparky
  from $3,036.00 to **$3,146.40**.

## 3.4 — 2026-11-06

### Added

- **ACC work levy schedule for trades** in `jurisdictions/nz.md`. All 26
  construction classification units (CU 41110–42595) for 2026/27, plus two
  adjacent trades, transcribed from Schedule 2 of the
  [Accident Compensation (Work Account Levies) Regulations 2025](https://www.legislation.govt.nz/regulation/public/2025/0017/12.0/whole.html).
  Rates range from $0.40 (property developers, all trades subcontracted) to
  $2.25 (bricklaying, roofing, structural steel erection).
- `acc_work_levy_rates` and `acc_levy_estimate` MCP tools. Lookup accepts a CU
  number, a trade name, or a job title (`sparky`, `roofer`, `brickie`,
  `digger driver`); a title that spans two CUs (`builder`) returns both rather
  than guessing. The estimate combines the trade work levy with the flat
  earners' levy, applies the earners' cap, and adds GST.
- Guidance on which CU applies to common situations (house builder vs
  carpentry contractor, renovation, earthmoving, developers).

### Changed

- The ACC earners' levy is now two constants, excluding and including GST,
  because ACC publishes the rate ex-GST ($1.52) while IRD quotes it inc-GST
  ($1.75). The estimate tool reads the ex-GST rate and adds GST.

### Validation

- The validator now guards the ACC table: at least 20 rows, no duplicate CUs,
  and every rate within a plausible $0–$10 per $100.

## 3.3 — 2026-11-06

### Added

- **New Zealand jurisdiction pack** (`jurisdictions/nz.md`): GST at 15% and the
  $60,000 registration threshold, GST return calendar and frequencies, the
  taxable-supply-information rules that replaced tax invoices on 1 April 2023,
  individual rates from 1 April 2025, company tax at 28%, ACC earners' levy and
  maximum liable earnings, provisional tax threshold and 105%/110% uplift,
  kilometre rates by vehicle type with the 14,000 km tier split, the home office
  square metre rate, the $1,000 low-value asset threshold, KiwiSaver at 3.5%,
  schedular-payment withholding, and 7-year record retention.
- The pack documents one deliberate wrinkle: IRD publishes the kilometre rates
  and square metre rate *after* an income year ends, so the 2026-27 pack carries
  the latest published (2025-26) sets and requires claims to be marked
  provisional rather than extrapolated.

### Changed

- `expense-categorization` and `income-invoicing` now cover New Zealand GST and
  taxable supply information alongside the Australian and US rules.
- `bookkeeping-mcp` recognises `nz` and the aliases `new zealand`, `aotearoa` and
  `nzl`; the constants parser and tool tests cover all three packs.

## 3.2 — 2026-11-06

### Added

- **`income-invoicing` skill.** Closes the revenue-side gap: sales capture,
  invoice numbering rules, receivables and aging, refunds and credits,
  prepayments as liabilities, and gross-versus-net processor payouts. Ships
  `references/INVOICE-SCHEMA.md` and `scripts/revenue_summary.py`.
- **Australia jurisdiction pack** (`jurisdictions/au.md`): GST and BAS, tax
  invoice requirements, instant asset write-off, cents-per-kilometre and
  logbook, working-from-home fixed rate, PAYG, TPAR, superannuation, record
  retention.
- **`mcp-server/`** — a FastMCP companion server. `get_constants` reads the
  jurisdiction packs so figures are never recalled from memory; the rest of the
  surface is exact Decimal money arithmetic, domain calculators (mileage, home
  office, depreciation, self-employment tax, safe harbour, reconciliation, AR
  aging), a whitelisted-AST `calculate`, and a sandboxed `run_python`.
- **Validation**: `scripts/validate_skills.py` checks frontmatter, version
  consistency, relative links, hardcoded tax figures, jurisdiction-pack
  structure and the skill map. `tests/` covers the summary scripts. CI runs both,
  plus the MCP server tests across Python 3.10–3.12.

### Changed

- **Year-specific figures moved out of skills.** Mileage rates, Section 179 and
  bonus limits, 1099 thresholds and penalties, Social Security wage base, luxury
  auto caps, standard deductions and penalty tiers now live only in the
  jurisdiction packs, in a `Current-law constants` table with per-row source and
  `Verified` date. Skills reference the table and state the tax year.
- Individual income tax bracket tables removed from `estimated-taxes` — they are
  re-indexed annually and a stale copy silently corrupts guidance. The skill now
  points at the IRS page and requires the tax year to be stated.
- `home-office` and `contractor-1099` promotional sections replaced with neutral
  sourcing guidance.
- `bookkeeping-setup` now separates the tax accounting method from the sales-tax
  / GST accounting basis, and hands off to `income-invoicing` first.
- `receipt_summary.py`: a `$0.00` receipt is no longer classified as missing a
  total (falsy-zero bug).
- All skills normalised to version 3.1/3.2 with a consistent frontmatter block
  (`license`, `compatibility`, `allowed-tools`, `metadata.version`) and an
  agent-metadata trailer.

### Fixed

- Version drift: `bank-reconciliation` and `monthly-close` declared `3.0` in
  frontmatter and `2.0` in their agent-metadata block.
- Stale figures corrected: 2024 mileage (67¢), Section 179 ($1,220,000), bonus
  phase-out table (superseded by 100% under OBBBA), Social Security wage base
  ($168,600), 1099 penalties ($60/$130/$330/$660), 1099 threshold ($600).
- Fork identity: install commands, badges and funding links no longer point at
  the upstream repository; upstream internal process docs removed from
  `AGENTS.md`.

## 3.0 — 2026-03-24

- Restructured into focused skills with `references/` and `scripts/`.
- Added the jurisdiction model, with the United States as the baseline pack.
- Added approval boundaries and accountant-review routing to every skill.

## 2.0 and earlier

- Monolithic bookkeeping skill set. See git history.
