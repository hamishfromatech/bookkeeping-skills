# Changelog

All notable changes to this skill pack. Versions apply to the skill content, not
to the repository as a product.

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
