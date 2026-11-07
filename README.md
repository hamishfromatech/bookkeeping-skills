# Bookkeeping Skills

**Open-source bookkeeping skills for AI agents — built and maintained by [The A-Tech Corporation PTY LTD](https://atech.industries).**

A portable pack of [Agent Skills](https://agentskills.io/specification) plus a companion MCP server that let an agent turn financial evidence — receipts, invoices, statements, sales records — into **accountant-reviewable bookkeeping outputs**: a transaction register, a reconciliation, a closed month, a tax package.

The pack defines the evidence standards, categorisation rules, approval boundaries and handoffs. The server does the arithmetic. Neither one files your taxes.

> ### Want to learn how to build things like this?
>
> This repository is a working example of what we teach inside the **Open Source AI Builder's Club** — agent skills, MCP servers, and shipping AI tooling that a real business actually uses.
>
> **[Join the club →](https://www.skool.com/open-source-ai-builders-club/about)**

---

## Why this exists

Bookkeeping is the perfect test case for AI agents, and the worst place to let one improvise.

It is repetitive, evidence-heavy, rule-bound, and expensive when wrong. Generic AI assistance fails in three predictable ways: it invents tax figures, it rounds money incorrectly, and it treats a bank statement as a receipt. This pack is built to make those three failures structurally impossible.

- **One source of truth for every figure.** Mileage rates, Section 179 limits, 1099 thresholds, GST rates, penalty tiers and standard deductions live in `jurisdictions/<country>.md` with a source URL and a verified date. No skill — and no tool — hardcodes one.
- **Exact money.** Every calculation is `Decimal`, quantised once. Allocation uses largest-remainder so no cent is invented or lost.
- **Evidence over plausibility.** A statement proves money moved; it is not a receipt. Missing business purpose is left blank and flagged, never guessed.
- **Explicit stop points.** Every skill states what it may draft, what needs your approval, and what needs a professional. Nothing posts to your accounting system without a human.

## Who it's for

Operators who have to keep usable books but are not accounting specialists:

- Solo founders and freelancers doing their own books
- Small businesses with lean teams and no dedicated finance function
- Technical operators who would rather automate than hire

It is not built for enterprise finance departments or for tax professionals with mature processes — though both are welcome to fork it.

## The operating loop

```text
bookkeeping-setup
  -> income-invoicing        (revenue, invoices, AR, processor payouts)
  -> receipt-processing      (expenses, vendor bills, receipts)
  -> expense-categorization
  -> bank-reconciliation
  -> monthly-close
  -> tax-prep
```

Jurisdiction packs and specialised tax skills load on demand. Start with `bookkeeping-setup` if the agent does not already know the business.

## Jurisdictions

General bookkeeping procedure lives in the skills. Country-specific tax, deduction, filing, payroll, GST/VAT/sales-tax and record-retention rules live in [`jurisdictions/`](jurisdictions/).

| Jurisdiction | File | Covers |
|---|---|---|
| United States | [`jurisdictions/us.md`](jurisdictions/us.md) | Schedule C mapping, 1099-NEC, estimated taxes, Section 179 and bonus depreciation, meals, vehicle, home office |
| Australia | [`jurisdictions/au.md`](jurisdictions/au.md) | GST and BAS, tax invoices, instant asset write-off, cents-per-km and logbook, WFH fixed rate, PAYG, TPAR, superannuation |
| New Zealand | [`jurisdictions/nz.md`](jurisdictions/nz.md) | GST returns and taxable supply information, ACC earners' levy, provisional tax, kilometre rates, square metre rate, low-value assets, schedular payments, KiwiSaver |

Each pack carries a `Current-law constants` table with per-row `Source` and `Verified` dates, plus a `Last reviewed` date. If a pack is more than twelve months old the tooling says so and every figure must be treated as unverified.

If the jurisdiction is unknown, the agent stops at jurisdiction-neutral work — evidence capture, normalisation, deduplication, reconciliation structure and review queues — and asks.

## Install

### npx skills

```sh
npx skills add hamishfromatech/bookkeeping-skills
```

One skill, or one agent:

```sh
npx skills add hamishfromatech/bookkeeping-skills -s income-invoicing
npx skills add hamishfromatech/bookkeeping-skills -a claude-code
npx skills add hamishfromatech/bookkeeping-skills -g
```

### Claude Code (manual)

```sh
git clone https://github.com/hamishfromatech/bookkeeping-skills.git
cp -r bookkeeping-skills/skills/ .claude/skills/bookkeeping/
```

### Codex CLI

```sh
git clone https://github.com/hamishfromatech/bookkeeping-skills.git ~/.codex/skills/bookkeeping-skills
```

### OpenCode

Clone the **full repo**, not just `skills/` — the root `SKILL.md` is the router:

```sh
git clone https://github.com/hamishfromatech/bookkeeping-skills.git ~/.opencode/skills/bookkeeping-skills
```

### Manual

Each skill is self-contained. Copy the whole folder so its `references/` and `scripts/` travel with it.

## Skills

### Workflow

| Skill | What it does |
|---|---|
| [bookkeeping-setup](skills/bookkeeping-setup/SKILL.md) | Business, tax, method, chart-of-accounts and approval context profile |
| [income-invoicing](skills/income-invoicing/SKILL.md) | Sales capture, invoices, receivables and aging, refunds, processor payouts |
| [receipt-processing](skills/receipt-processing/SKILL.md) | Structured extraction from email, photos, PDFs and OCR |
| [expense-categorization](skills/expense-categorization/SKILL.md) | Tax-aligned categories with vendor matching and confidence scoring |
| [bank-reconciliation](skills/bank-reconciliation/SKILL.md) | Tiered matching and balance verification |
| [monthly-close](skills/monthly-close/SKILL.md) | Repeatable month-end checklist and P&L |
| [tax-prep](skills/tax-prep/SKILL.md) | Tax-ready package: P&L, mappings, contractor summary, schedules |

### Reference and specialised

| Skill | Jurisdiction | Covers |
|---|---|---|
| [schedule-c-categories](skills/schedule-c-categories/SKILL.md) | US | Schedule C lines 8–27a, COGS, Form 8829 |
| [home-office](skills/home-office/SKILL.md) | US | Simplified vs actual method |
| [vehicle-expenses](skills/vehicle-expenses/SKILL.md) | US | Standard mileage vs actual, method lock-in, logs |
| [meals-deduction](skills/meals-deduction/SKILL.md) | US | 50% meals, 0% entertainment, documentation |
| [depreciation-assets](skills/depreciation-assets/SKILL.md) | US | De minimis, Section 179, bonus, MACRS |
| [contractor-1099](skills/contractor-1099/SKILL.md) | US | W-9 collection, 1099-NEC, deadlines, penalties |
| [estimated-taxes](skills/estimated-taxes/SKILL.md) | US | Quarterly payments, SE tax, safe harbours |

For Australia and New Zealand, load the local pack alongside the workflow skills. The US specialist skills do not apply — in particular there is no 1099-NEC or Section 179 outside the US, and the $2,500 de minimis is replaced by New Zealand's $1,000 low-value threshold.

## Companion MCP server

[`mcp-server/`](mcp-server/README.md) is a FastMCP server that does the arithmetic the skills describe — and reads the jurisdiction packs instead of recalling tax figures.

```sh
pip install -e ./mcp-server
```

```json
{
  "mcpServers": {
    "bookkeeping": { "command": "bookkeeping-mcp" }
  }
}
```

24 tools in five groups:

- **Jurisdiction constants** — `list_jurisdictions`, `get_constants`. Returns the value, extracted numbers, source URL and verified date from `jurisdictions/*.md`, and warns when a pack is stale.
- **Money and tax** — `sum_amounts`, `round_amount`, `percent_calculation`, `margin_and_markup`, `sales_tax`, `allocate_amount`, `verify_line_items`.
- **Domain** — mileage across rate periods, both home-office methods, straight-line and declining-balance depreciation, first-year expensing order, self-employment tax, estimated-tax safe harbour, reconciliation with diagnostics, AR aging.
- **New Zealand ACC** — `acc_work_levy_rates` and `acc_levy_estimate`, including the 2026/27 tradie work-levy schedule, the Working Safer and earners' levies, and the liable-earnings cap.
- **Calculation** — `calculate` (Decimal arithmetic in a whitelisted AST) and `run_python` (isolated child process, timeout, rlimits).
- **Discovery** — `search_tools`, plus a `BOOKKEEPING_MCP_TOOL_MODE=search` mode that lists six tools instead of 24 (~900 tokens instead of ~4,000) and reaches the rest by name.

Resources expose pack summaries, raw packs and raw `SKILL.md` files, so an agent reads the procedure as a resource and does the maths with a tool.

Money is `Decimal` throughout and quantised once. `run_python` is a local-trust capability, not a security sandbox; disable it with `BOOKKEEPING_MCP_DISABLE_EXEC=1`. Host configuration for Claude Code, Codex, Cursor and HTTP is in the [server README](mcp-server/README.md).

## Design principles

These are enforced, not aspirational:

1. **Year-specific figures live only in jurisdiction packs.** A curated check in `scripts/validate_skills.py` fails the build if a stale constant reappears in a skill body.
2. **Every skill declares three boundaries** — safe to draft, requires your approval, requires professional review.
3. **No skill may authorise** filing taxes, moving money, locking periods, deleting records, or posting to a live accounting system without explicit approval.
4. **Jurisdiction-neutral by default.** No blending of countries, and no translating a US concept (`Schedule C`, `§179`, `1099-NEC`, de minimis) into another jurisdiction.
5. **Evidence beats plausibility.** Missing fields, business purpose and attendees are flagged, never fabricated.
6. **Skills are portable.** References resolve relative to the skill folder so a copied directory still works.

## Tooling

Deterministic summary helpers ship with six skills:

```sh
python3 skills/receipt-processing/scripts/receipt_summary.py records.json
python3 skills/expense-categorization/scripts/category_review_summary.py records.json
python3 skills/bank-reconciliation/scripts/reconciliation_summary.py records.json
python3 skills/monthly-close/scripts/monthly_close_summary.py items.json
python3 skills/tax-prep/scripts/tax_package_summary.py artifacts.json
python3 skills/income-invoicing/scripts/revenue_summary.py invoices.json --as-of 2026-11-30
```

Each accepts a JSON array from a file argument or stdin and prints a deterministic summary.

Recommended companions: an email-native receipt and invoice extractor for Gmail or Outlook, plus any spreadsheet or accounting package (QuickBooks, Xero, Wave, MYOB, Google Sheets, Excel).

## Development

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_skills.py     # frontmatter, links, hardcoded figures, skill map
python3 -m pytest tests/ -q            # summary script tests

python3 -m pip install -e "./mcp-server[dev]"
python3 -m pytest mcp-server/tests -q  # 114 server tests
```

`validate_skills.py` enforces the invariant that keeps the pack honest: a year-specific figure must live in a jurisdiction pack, never in a skill body.

Automatic CI is disabled for this repository. The workflow is kept at [`.github/workflows/validate.yml`](.github/workflows/validate.yml) and runs the validator, both test suites and a real stdio handshake on Python 3.10–3.12, but only when triggered by hand from the Actions tab.

See [`AGENTS.md`](AGENTS.md) for repository conventions and [`CHANGELOG.md`](CHANGELOG.md) for history.

## Contributing

PRs welcome.

- **New skill** — start from an existing folder, add it to `SKILL.md` and the tables here.
- **New jurisdiction** — copy [`jurisdictions/_template.md`](jurisdictions/_template.md); the constants table needs per-row `Source` and `Verified` dates.
- **A tax figure changed** — update only the jurisdiction pack. Do not chase the number through the skills, and do not add it to the server.
- **New MCP tool** — keep it a pure function in `mcp-server/src/bookkeeping_mcp/`, add a test, keep the server layer thin.

Run the validator before opening a PR. If it fails, the invariant broke.

## Community

The patterns in this repository — progressive-disclosure skills, jurisdiction packs, an MCP server as the deterministic layer, validation that catches drift — are what we teach in the **Open Source AI Builder's Club**.

**[Join the club and learn to build this →](https://www.skool.com/open-source-ai-builders-club/about)**

## License and attribution

MIT. See [LICENSE](LICENSE).

- Original work © 2026 [Receiptor AI](https://receiptor.ai) — this repository began as a fork of [`Receiptor-AI/bookkeeping-skills`](https://github.com/Receiptor-AI/bookkeeping-skills). Upstream branding, funding links and internal process notes have been removed.
- Fork additions and maintenance © 2026 **The A-Tech Corporation PTY LTD** — Australia, building open-source AI tooling.

Maintained by [The A-Tech Corporation PTY LTD](https://atech.industries). Questions, corrections and jurisdiction packs are welcome as issues or PRs.
