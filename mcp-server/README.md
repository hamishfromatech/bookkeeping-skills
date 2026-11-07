# bookkeeping-mcp

A calculation companion for the [bookkeeping skills](../skills). It is an MCP
server, so any MCP-capable agent can use it: Claude Code, Codex, Cursor,
Copilot, Windsurf, or your own client.

Three jobs, in order of importance:

1. **Stop tax figures being recalled from memory.** `get_constants` reads the
   `Current-law constants` table straight out of [`jurisdictions/`](../jurisdictions)
   — US, Australia and New Zealand — and returns the value, its source URL, and
   the date it was verified. When a
   pack is more than 12 months old the response says so.
2. **Do money arithmetic exactly.** Every calculation is `Decimal`-based,
   quantized once, at the boundary. No float drift, no silent rounding, no
   invented cents.
3. **Be the calculator.** `calculate` evaluates arithmetic in a locked-down AST;
   `run_python` runs anything else in an isolated child process with a timeout.

It does not decide tax treatment, and it cannot post to an accounting system.
Every result is a draft for review.

## Install

Requires Python 3.10+.

```sh
# from the repo root
pip install -e ./mcp-server

# or, isolated
pipx install ./mcp-server
```

Check it starts:

```sh
bookkeeping-mcp --help
```

The server finds the repo by walking up from its own location, so an editable
install inside the repo needs no configuration. If you install it somewhere
else, point it at the repo:

```sh
export BOOKKEEPING_SKILLS_ROOT=/path/to/bookkeeping-skills
```

## Connect it to a host

### Claude Code — `.mcp.json` in the project

```json
{
  "mcpServers": {
    "bookkeeping": {
      "command": "bookkeeping-mcp",
      "args": [],
      "env": {
        "BOOKKEEPING_SKILLS_ROOT": "/absolute/path/to/bookkeeping-skills"
      }
    }
  }
}
```

### Codex — `~/.codex/config.toml`

```toml
[mcp_servers.bookkeeping]
command = "bookkeeping-mcp"
args = []
env = { BOOKKEEPING_SKILLS_ROOT = "/absolute/path/to/bookkeeping-skills" }
```

### Cursor — `.cursor/mcp.json`

Same shape as the Claude Code file.

### HTTP instead of stdio

For a long-running server, or when the client cannot spawn a subprocess:

```sh
bookkeeping-mcp --transport http --host 127.0.0.1 --port 8765
```

Then point the client at `http://127.0.0.1:8765/mcp`. Do not expose it publicly:
`run_python` is a code-execution capability.

## Tools

### Jurisdiction constants

| Tool | What it does |
|---|---|
| `list_jurisdictions` | Packs available, review dates, staleness |
| `get_constants` | Filtered constants with value, numbers, source URL, verified date |

`get_constants("us", "mileage")` returns the split 2026 business rate, because
the IRS changed it mid-year:

```json
{
  "topic": "Standard mileage — business",
  "tax_year": "2026",
  "value": "72.5¢/mile (1 Jan – 30 Jun 2026); 76¢/mile (1 Jul – 31 Dec 2026)",
  "numbers": [72.5, 1, 30, 2026, 76, 1, 31, 2026],
  "source_url": "https://www.irs.gov/tax-professionals/standard-mileage-rates",
  "verified": "2026-11-06"
}
```

### Money and tax

| Tool | What it does |
|---|---|
| `sum_amounts` | Exact addition, rounded once |
| `round_amount` | Round with an explicit mode, report the adjustment |
| `percent_calculation` | `of`, `add`, `subtract`, `reverse` |
| `margin_and_markup` | Gross profit, margin %, markup % |
| `sales_tax` | Split net/tax/gross, inclusive or exclusive |
| `allocate_amount` | Largest-remainder split that sums exactly |
| `verify_line_items` | Reconcile lines to a total, with causes and per-category rollup |

### Domain

| Tool | What it does |
|---|---|
| `mileage_deduction` | Sum mileage across multiple rate periods |
| `home_office_simplified` | Per-sq-ft method with the area cap |
| `home_office_actual` | Direct 100% + indirect × business-use % |
| `straight_line_depreciation` | Annual and monthly, at business use % |
| `declining_balance_depreciation` | Declining balance for a year, with schedule |
| `first_year_asset_expense` | Business use → Section 179 → bonus → remainder |
| `self_employment_tax` | 92.35% base, 12.4% capped, 2.9%, 0.9% surtax |
| `estimated_tax_safe_harbor` | Prior-year 100/110% and current-year 90% routes |
| `reconciliation_check` | Adjusted bank vs adjusted book, with diagnostics |
| `ar_aging` | Receivables buckets from invoice records |

### New Zealand ACC

| Tool | What it does |
|---|---|
| `acc_work_levy_rates` | Work levy rates by classification unit, searched by trade name, job title (`sparky`, `roofer`, `brickie`) or CU number |
| `acc_levy_estimate` | Work levy + Working Safer + earners' levy, on the capped base, plus GST |

Rates come from the `ACC work levy` table in [`jurisdictions/nz.md`](../jurisdictions/nz.md), which mirrors Schedule 2 of the Work Account Levies Regulations 2025 for 2026/27. A job title that spans two CUs (`builder`) returns both and refuses to guess.

The estimate charges all three levies on one base, capped at the maximum liable earnings ($156,641 for 2026/27): the trade work levy, the flat Working Safer levy ($0.08 per $100), and the flat earners' levy ($1.52 per $100). The statutory minimum ($50,501) is surfaced as a constant but not applied.

### Calculation

| Tool | What it does |
|---|---|
| `calculate` | Decimal arithmetic in a whitelisted AST |
| `run_python` | Isolated child process, timeout, captured output |

## Resources

| URI | Content |
|---|---|
| `bookkeeping://jurisdictions` | Pack summaries and staleness |
| `jurisdiction://{code}` | Raw markdown of a pack, e.g. `jurisdiction://au` |
| `skill://{name}` | Raw `SKILL.md`, e.g. `skill://income-invoicing` |

Resources are how an agent reads the *procedure*; the tools are how it does the
*arithmetic*.

## Examples

```text
get_constants("au", "cents per kilometre")     → 91¢/km for 2026-27
mileage_deduction([{miles: 4000, rate_per_mile: 0.725},
                   {miles: 6000, rate_per_mile: 0.76}])   → 7,460.00
sales_tax(110, 10, inclusive=True)             → net 100.00, tax 10.00
allocate_amount(100, [1, 1, 1])                → [33.34, 33.33, 33.33]
verify_line_items(347.82, [...6 lines...])     → reconciles: true
reconciliation_check(bank, book, ...)          → difference 0.00
calculate("(1234.56 - 200) * 0.7")             → 724.192
```

## Security model

- `calculate` cannot reach names, attributes, imports, comprehensions or
  strings. It is safe to expose.
- `run_python` runs in a child process with `-I` (isolated interpreter), a
  scratch working directory, a minimal environment, a wall-clock timeout, and
  CPU / address-space / file-size rlimits. That protects against runaway loops
  and stray file writes. **It is not a sandbox against hostile code** — there is
  no network isolation and no filesystem jail. Treat it as equivalent to giving
  the agent a local Python prompt.
- Disable execution entirely with `BOOKKEEPING_MCP_DISABLE_EXEC=1`; `calculate`
  keeps working.

## Development

```sh
cd mcp-server
pip install -e ".[dev]"
pytest -q
```

Tests cover the Decimal helpers, every calculation, the jurisdiction parser, the
AST whitelist, the subprocess runner, and the full tool surface through an
in-memory MCP client.
