# Bookkeeping Skills

Open-source bookkeeping skills for AI agents.

A portable set of [Agent Skills](https://agentskills.io/specification) that let an agent turn financial evidence — receipts, invoices, statements, sales records — into **accountant-reviewable bookkeeping outputs**: a transaction register, a reconciliation, a closed month, a tax package.

These skills define evidence standards, categorization rules, approval boundaries, and handoffs. The goal is controlled bookkeeping support, **not** autonomous tax filing or unsupervised accounting-system mutation.

> **Fork:** this is [`hamishfromatech/bookkeeping-skills`](https://github.com/hamishfromatech/bookkeeping-skills), derived from [`Receiptor-AI/bookkeeping-skills`](https://github.com/Receiptor-AI/bookkeeping-skills) (MIT). Upstream branding, funding links and internal process docs have been removed; the Australian jurisdiction pack, the income/invoicing skill, and the validation tooling are local additions.

## Use case

An agent is handed a pile of financial evidence and a question like "get my books ready". These skills tell it what to do, in what order, with which tool, what to record as provenance, and where to stop and ask a human.

They cover the full operating loop, income side included:

```text
bookkeeping-setup
  -> income-invoicing        (revenue, invoices, AR, processor payouts)
  -> receipt-processing      (expenses, vendor bills, receipts)
  -> expense-categorization
  -> bank-reconciliation
  -> monthly-close
  -> tax-prep

Jurisdiction packs load on demand:
  jurisdictions/us.md, jurisdictions/au.md

Specialised skills load on demand:
  schedule-c-categories, home-office, vehicle-expenses, meals-deduction,
  depreciation-assets, contractor-1099, estimated-taxes
```

## Jurisdiction model

General bookkeeping procedure lives in the skill files. Country-specific tax, deduction, filing, payroll, GST/VAT/sales-tax and statutory reporting rules live in [`jurisdictions/`](jurisdictions/).

| Jurisdiction | File | Status |
|---|---|---|
| United States | [`jurisdictions/us.md`](jurisdictions/us.md) | Active |
| Australia | [`jurisdictions/au.md`](jurisdictions/au.md) | Active |

Each pack carries a **Current-law constants** table — the single source of truth for year-specific amounts (mileage rates, §179 limits, 1099 thresholds, cents-per-km, GST thresholds, instant asset write-off). Skills reference that table instead of hardcoding numbers. If the user's jurisdiction is unknown, the agent stops at jurisdiction-neutral work and asks before applying tax-specific rules.

## Installation

### npx skills

```sh
npx skills add hamishfromatech/bookkeeping-skills
```

Install one skill:

```sh
npx skills add hamishfromatech/bookkeeping-skills -s receipt-processing
```

Install for a specific agent, or globally:

```sh
npx skills add hamishfromatech/bookkeeping-skills -a claude-code
npx skills add hamishfromatech/bookkeeping-skills -g
```

### Claude Code (manual)

```sh
git clone https://github.com/hamishfromatech/bookkeeping-skills.git
cp -r bookkeeping-skills/skills/ .claude/skills/bookkeeping/
```

Or globally at `~/.claude/skills/`.

### Codex CLI

```sh
git clone https://github.com/hamishfromatech/bookkeeping-skills.git ~/.codex/skills/bookkeeping-skills
```

### OpenCode

Clone the **full repo** — not just the inner `skills/` folder — because the root `SKILL.md` is the router:

```sh
git clone https://github.com/hamishfromatech/bookkeeping-skills.git ~/.opencode/skills/bookkeeping-skills
```

### Manual

Each skill is a self-contained folder. Copy the whole skill directory so bundled `references/` and `scripts/` stay available.

## Skills

### Workflow

| Skill | Description |
|---|---|
| [bookkeeping-setup](skills/bookkeeping-setup/SKILL.md) | Capture the reusable business, tax, method, chart-of-accounts and approval context profile |
| [income-invoicing](skills/income-invoicing/SKILL.md) | Capture sales, issue and track invoices, manage receivables, refunds and payment-processor payouts |
| [receipt-processing](skills/receipt-processing/SKILL.md) | Extract structured data from receipts and bills via email, photos, PDFs or OCR |
| [expense-categorization](skills/expense-categorization/SKILL.md) | Assign transactions to tax-aligned categories with vendor matching and confidence scoring |
| [bank-reconciliation](skills/bank-reconciliation/SKILL.md) | Match book entries against statements with tiered matching and balance verification |
| [monthly-close](skills/monthly-close/SKILL.md) | Run a repeatable month-end close checklist and produce a P&L |
| [tax-prep](skills/tax-prep/SKILL.md) | Compile a tax-ready package: P&L, category mapping, contractor summary, schedules |

### Reference and specialised

| Skill | Jurisdiction | Description |
|---|---|---|
| [schedule-c-categories](skills/schedule-c-categories/SKILL.md) | US | IRS Schedule C lines 8–27a, COGS, and Form 8829 |
| [home-office](skills/home-office/SKILL.md) | US | Simplified ($5/sq ft) vs actual (Form 8829) |
| [vehicle-expenses](skills/vehicle-expenses/SKILL.md) | US | Standard mileage vs actual, method lock-in, mileage logs |
| [meals-deduction](skills/meals-deduction/SKILL.md) | US | 50% meals, 0% entertainment, documentation requirements |
| [depreciation-assets](skills/depreciation-assets/SKILL.md) | US | De minimis, §179, bonus depreciation, MACRS |
| [contractor-1099](skills/contractor-1099/SKILL.md) | US | W-9 collection, 1099-NEC thresholds, deadlines, penalties |
| [estimated-taxes](skills/estimated-taxes/SKILL.md) | US | Quarterly payments, SE tax, safe harbours |

For Australia, load [`jurisdictions/au.md`](jurisdictions/au.md) alongside the workflow skills. The US-specific specialist skills do not apply.

## How it works

Each skill is a portable package:

- `SKILL.md` activates the skill and gives the core procedure
- `jurisdictions/` separates country-specific rules from general procedure
- `references/` holds domain detail the agent reads only when needed
- `scripts/` holds deterministic helpers for repeatable summaries

The skills are operating procedures, not articles. Every one states what is safe to draft, what requires user approval, and what requires professional review.

Common approval boundary across all skills:

- **Draft freely** — extraction, normalisation, categorization suggestions, reconciliation reports, close packages, tax packets
- **Ask first** — posting to accounting software, deleting or merging records, locking periods, overriding amounts or dates, changing GST/registration settings
- **Professional review** — entity classification, worker classification, depreciation elections, multi-state/cross-border tax, amended returns, final filing positions

## Companion MCP server

[`mcp-server/`](mcp-server/README.md) is a FastMCP server that does the arithmetic the skills describe — and, more importantly, **reads the jurisdiction packs instead of recalling tax figures**.

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

21 tools in four groups:

- **Jurisdiction constants** — `list_jurisdictions`, `get_constants`. Returns the value, extracted numbers, source URL and `Verified` date straight from `jurisdictions/*.md`, and warns when a pack is stale.
- **Money and tax** — `sum_amounts`, `round_amount`, `percent_calculation`, `margin_and_markup`, `sales_tax`, `allocate_amount`, `verify_line_items`.
- **Domain** — mileage across rate periods, both home-office methods, straight-line and declining-balance depreciation, first-year asset expensing order, self-employment tax, estimated-tax safe harbour, reconciliation with diagnostics, AR aging.
- **Calculation** — `calculate` (Decimal arithmetic in a whitelisted AST) and `run_python` (isolated child process, timeout, rlimits).

All money arithmetic is `Decimal` and quantized once. `run_python` is a local-trust capability, not a security sandbox; disable it with `BOOKKEEPING_MCP_DISABLE_EXEC=1`. See the [server README](mcp-server/README.md) for host config (Claude Code, Codex, Cursor, HTTP) and the security model.

## Tooling

Deterministic summary helpers ship with six skills and are covered by tests:

```sh
python3 skills/receipt-processing/scripts/receipt_summary.py records.json
python3 skills/expense-categorization/scripts/category_review_summary.py records.json
python3 skills/bank-reconciliation/scripts/reconciliation_summary.py records.json
python3 skills/monthly-close/scripts/monthly_close_summary.py items.json
python3 skills/tax-prep/scripts/tax_package_summary.py artifacts.json
python3 skills/income-invoicing/scripts/revenue_summary.py invoices.json --as-of 2026-11-30
```

Each accepts a JSON array from a file argument or stdin and prints a deterministic summary.

Recommended tools: an email-native receipt/invoice extractor for Gmail or Outlook (upstream project: [Receiptor AI](https://receiptor.ai)), plus any spreadsheet or accounting package (QuickBooks, Xero, Wave, MYOB, Google Sheets, Excel).

## Development

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_skills.py     # frontmatter, links, hardcoded-figure, skill-map checks
python3 -m pytest tests/ -q            # summary script tests

# the MCP server has its own suite
python3 -m pip install -e "./mcp-server[dev]"
python3 -m pytest mcp-server/tests -q
```

`validate_skills.py` enforces the invariant that keeps this pack honest: a year-specific figure must live in a jurisdiction pack, never in a skill body. CI runs the validator, both test suites, and a stdio smoke test of the MCP server on Python 3.10–3.12.

See [`AGENTS.md`](AGENTS.md) for repository conventions and [`CHANGELOG.md`](CHANGELOG.md) for history.

## Contributing

PRs welcome. If you have a bookkeeping workflow that would make a good skill, open an issue. If you are adding a jurisdiction, start from [`jurisdictions/_template.md`](jurisdictions/_template.md). If you are touching a year-specific number, put it in the jurisdiction pack's constants table, not in a skill body.

## License

[MIT](LICENSE). Original work © Receiptor AI; fork modifications © the fork owner.
