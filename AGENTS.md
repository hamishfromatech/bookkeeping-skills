# bookkeeping-skills agent guide

## Repository context

This is the independent `bookkeeping-skills` Git repository (`hamishfromatech/bookkeeping-skills`), derived from `Receiptor-AI/bookkeeping-skills` under MIT. Paths and commands below are relative to this repository's root. Do not require a parent checkout or sibling repository.

Read runtime versions and commands from this checkout. There is no package manager, build step, or runtime dependency for the skills themselves. The only tooling is Python 3.9+ for the bundled helper scripts and validation, plus `pytest` for tests.

## What this repo owns

Portable bookkeeping skills plus their calculation companion:

- `SKILL.md` — the user-facing router and skill map
- `skills/` — one self-contained folder per task skill
- `jurisdictions/` — country-specific tax and compliance references; the **only** place year-specific figures may live
- `mcp-server/` — FastMCP server exposing jurisdiction constants, Decimal money maths and a sandboxed Python runner
- `scripts/` — repository tooling (validation), not skill scripts
- `tests/` — tests for the skill helper scripts

Repository development instructions are separate from the runtime skill instructions. Do not load `AGENTS.md` content into a bookkeeping task; do not treat a skill's approval boundaries as repo-editing rules.

## Invariants — do not break these

1. **Year-specific numbers live in `jurisdictions/<cc>.md` only.** Skills must not hardcode rates, thresholds, limits, or penalty amounts. If a skill needs one, it references the jurisdiction pack and names the tax year in its output.
2. **Every skill states its three boundaries**: safe to draft, requires user approval, requires professional review.
3. **No skill may authorise** filing taxes, moving money, locking periods, deleting records, or posting to a live accounting system without explicit user approval.
4. **Jurisdiction-neutral by default.** If the jurisdiction is unknown, only evidence capture, normalisation, deduplication, reconciliation structure, review queues and artifact formats apply.
5. **Never blend rules across countries.** A US concept (`Schedule C`, `§179`, `1099-NEC`, `de minimis safe harbor`, `entertainment deduction`) is not portable.
6. **Evidence beats plausibility.** A statement proves money moved; it is not a receipt. Do not fabricate missing fields, business purpose, or attendees.
7. **References stay relative to the packaged skill** (`references/…`, `scripts/…`) so a copied skill folder still resolves.
8. **The MCP server must not duplicate a figure either.** It parses `jurisdictions/*.md`; if a tool needs a tax number it calls the pack, and if the pack is stale it says so.

## Validation

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_skills.py     # frontmatter, links, hardcoded figures, skill map
python3 -m pytest tests/ -q

python3 -m pip install -e "./mcp-server[dev]"
python3 -m pytest mcp-server/tests -q
```

`scripts/validate_skills.py` checks:

- every `SKILL.md` has valid YAML frontmatter with `name` (kebab-case, matching its folder) and `description`
- `metadata.version` is consistent between frontmatter and the trailing agent-metadata block
- every relative markdown link resolves
- no skill body contains a bare year-specific constant that belongs in a jurisdiction pack (a curated list of patterns such as `67 cents`, `§1,220,000`, `$168,600`)
- every jurisdiction pack has a `Last reviewed` date, a `Current-law constants` section, and a `Verified` column
- `SKILL.md` skill map matches the folders present on disk

Run it before every commit. CI runs it on push and pull request.

## Editing rules

- Read the affected skill and its referenced resources before editing.
- Preserve evidence standards, jurisdiction boundaries, approval requirements and accountant-reviewable output.
- When adding a skill: create `skills/<kebab-name>/SKILL.md`, add it to the root `SKILL.md` map, the `README.md` table, and, if it has a helper script, to the tooling section.
- When adding a jurisdiction: copy `jurisdictions/_template.md`, include a constants table with per-row `Verified` dates and a `Last reviewed` date, and add it to `jurisdictions/README.md` and the root `SKILL.md`.
- When a tax figure changes: update only the jurisdiction pack, bump its `Last reviewed` date and the row's `Verified` date. Do not chase the number through skills, and do not add it to the MCP server.
- When adding an MCP tool: keep it a pure function in `mcp-server/src/bookkeeping_mcp/`, add a test, and keep the server layer a thin wrapper.
- Update `CHANGELOG.md` for anything a user would notice.

## Scope boundaries

Source changes to bookkeeping content do not authorise filing taxes, moving money, or changing a customer's accounting records. Those remain user-approval and professional-review actions described in the skills themselves.

## PRs

Commit directly or open a PR against `main`; there is no staging branch. Do not force-push `main`. Keep commits scoped and describe validation in the PR body.
