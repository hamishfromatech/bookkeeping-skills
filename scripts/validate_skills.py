#!/usr/bin/env python3
"""Validate the bookkeeping-skills repository.

Checks, in order:

1. Every ``SKILL.md`` has YAML frontmatter with a kebab-case ``name`` that
   matches its folder (the root router is exempt), and a ``description``.
2. Frontmatter is complete: ``license``, ``compatibility``, ``allowed-tools``
   and ``metadata.version`` are present.
3. ``metadata.version`` agrees with the trailing agent-metadata block.
4. Every relative markdown link resolves.
5. No year-specific tax constant is hardcoded in a skill body — those belong in
   a jurisdiction pack.
6. Every jurisdiction pack is structurally valid: a ``Last reviewed`` date, a
   ``Current-law constants`` section, and a ``Verified`` column.
7. The root ``SKILL.md`` skill map matches the folders on disk.

Exit code 0 on success, 1 on any failure. Run from anywhere.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
JURISDICTIONS_DIR = ROOT / "jurisdictions"

REQUIRED_FRONTMATTER = ("name", "description", "license", "compatibility", "allowed-tools")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
AGENT_VERSION_RE = re.compile(r"^version:\s*\"?([0-9][^\s\"]*)\"?\s*$", re.MULTILINE)

# Tokens that were once hardcoded in a skill and are now maintained only in the
# jurisdiction packs. If one reappears here, the figure has drifted back in.
FORBIDDEN_IN_SKILLS = {
    "67¢": "2024 US mileage rate",
    "67 cents": "2024 US mileage rate",
    "$1,220,000": "2024 Section 179 limit",
    "$168,600": "2024 Social Security wage base",
    "$20,400": "2024 luxury auto cap",
    "$232,500": "2024 information-return penalty maximum",
    "$11,600": "2024 10% tax bracket ceiling",
    "$47,150": "2024 12% tax bracket ceiling",
    "$191,950": "2024 24% tax bracket ceiling",
}

# Files under skills/ that are allowed to mention a forbidden token because they
# are explaining history rather than quoting a current figure.
FORBIDDEN_ALLOWLIST = {
    "skills/meals-deduction/SKILL.md",  # historical deductibility table
}


@dataclass
class Finding:
    level: str  # "error" | "warning"
    where: str
    message: str

    def render(self) -> str:
        return f"{self.level.upper():7} {self.where}: {self.message}"


def load_frontmatter(text: str) -> tuple[dict | None, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return {"__error__": str(exc)}, text[match.end() :]
    if not isinstance(data, dict):
        return {"__error__": "frontmatter is not a mapping"}, text[match.end() :]
    return data, text[match.end() :]


def relative_links(text: str) -> list[str]:
    links = []
    for target in LINK_RE.findall(text):
        target = target.split("#", 1)[0].strip()
        target = target.split(" ", 1)[0]
        if not target:
            continue
        if target.startswith(("http://", "https://", "mailto:", "#", "tel:")):
            continue
        links.append(target)
    return links


def check_skill(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    front, body = load_frontmatter(text)

    if front is None:
        findings.append(Finding("error", rel, "missing YAML frontmatter"))
        return findings
    if "__error__" in front:
        findings.append(Finding("error", rel, f"invalid YAML frontmatter: {front['__error__']}"))
        return findings

    for field in REQUIRED_FRONTMATTER:
        if not front.get(field):
            findings.append(Finding("error", rel, f"frontmatter missing '{field}'"))

    name = str(front.get("name", "")).strip()
    if not name:
        findings.append(Finding("error", rel, "frontmatter missing 'name'"))
    elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        findings.append(Finding("error", rel, f"name '{name}' is not kebab-case"))

    is_root = path.parent == ROOT
    if not is_root and name and name != path.parent.name:
        findings.append(
            Finding("error", rel, f"name '{name}' does not match folder '{path.parent.name}'")
        )

    description = str(front.get("description", ""))
    if description and len(description) > 1024:
        findings.append(
            Finding("error", rel, f"description is {len(description)} chars (max 1024)")
        )

    metadata = front.get("metadata") or {}
    version = None
    if isinstance(metadata, dict):
        version = metadata.get("version")
        version = str(version) if version is not None else None
    if not version:
        findings.append(Finding("error", rel, "frontmatter missing metadata.version"))

    agent_version_match = AGENT_VERSION_RE.search(body)
    if version and agent_version_match:
        agent_version = agent_version_match.group(1)
        if agent_version != version:
            findings.append(
                Finding(
                    "error",
                    rel,
                    f"version drift: metadata.version={version!r} but agent metadata says {agent_version!r}",
                )
            )
    if version and not agent_version_match:
        findings.append(
            Finding("warning", rel, "no agent-metadata block, so the version cannot be cross-checked")
        )

    for target in relative_links(text):
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            findings.append(Finding("error", rel, f"broken relative link: {target}"))

    for token, reason in FORBIDDEN_IN_SKILLS.items():
        if token in body and rel not in FORBIDDEN_ALLOWLIST:
            findings.append(
                Finding(
                    "error",
                    rel,
                    f"hardcoded year-specific figure {token!r} ({reason}); "
                    "move it to jurisdictions/ and reference the pack",
                )
            )

    return findings


def check_jurisdiction(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")

    if path.name.lower() in {"readme.md", "_template.md"}:
        return findings

    if not re.search(r"^#\s+", text, re.MULTILINE):
        findings.append(Finding("error", rel, "missing top-level heading"))

    reviewed = re.search(r"last reviewed\**\s*:?\s*\**\s*(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if not reviewed:
        findings.append(Finding("error", rel, "missing 'Last reviewed: YYYY-MM-DD'"))
    else:
        try:
            when = datetime.strptime(reviewed.group(1), "%Y-%m-%d").date()
            if (date.today() - when).days > 365:
                findings.append(
                    Finding(
                        "warning",
                        rel,
                        f"last reviewed {when.isoformat()} — more than 12 months ago",
                    )
                )
        except ValueError:
            findings.append(Finding("error", rel, "unparseable 'Last reviewed' date"))

    if "## Current-law constants" not in text:
        findings.append(Finding("error", rel, "missing '## Current-law constants' section"))
    else:
        section = text.split("## Current-law constants", 1)[1].split("\n## ", 1)[0]
        if "Verified" not in section:
            findings.append(Finding("error", rel, "constants table has no 'Verified' column"))
        if "Source" not in section:
            findings.append(Finding("error", rel, "constants table has no 'Source' column"))
        data_rows = [
            line
            for line in section.splitlines()
            if line.strip().startswith("|")
            and not re.fullmatch(r"\|[\s:|-]+\|?", line.strip())
        ]
        if len(data_rows) < 3:
            findings.append(Finding("error", rel, "constants table has fewer than 2 data rows"))

    findings.extend(_check_acc_levy_table(path, rel, text))

    for target in relative_links(text):
        if not (path.parent / target).resolve().exists():
            findings.append(Finding("error", rel, f"broken relative link: {target}"))

    return findings


def _check_acc_levy_table(path: Path, rel: str, text: str) -> list[Finding]:
    """The ACC work-levy table is hand-maintained; guard it against rot."""
    findings: list[Finding] = []
    if "## ACC work levy" not in text:
        return findings

    section = text.split("## ACC work levy", 1)[1]
    next_heading = re.search(r"^## ", section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]

    rows: list[tuple[str, float]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        cu, rate = cells[0], cells[2]
        if re.fullmatch(r"\d{4,5}", cu) and re.fullmatch(r"\d+(?:\.\d+)?", rate):
            rows.append((cu, float(rate)))

    if len(rows) < 20:
        findings.append(
            Finding("error", rel, f"ACC work levy table has only {len(rows)} rows; expected 20+")
        )
        return findings

    counts = Counter(cu for cu, _rate in rows)
    duplicates = sorted(cu for cu, n in counts.items() if n > 1)
    if duplicates:
        findings.append(
            Finding("error", rel, f"duplicate classification units: {', '.join(duplicates)}")
        )

    for cu, rate in rows:
        if not 0 < rate <= 10:
            findings.append(
                Finding("error", rel, f"CU {cu} has an implausible work levy rate: {rate}")
            )

    return findings


def check_skill_map() -> list[Finding]:
    findings: list[Finding] = []
    root_skill = ROOT / "SKILL.md"
    if not root_skill.is_file():
        return [Finding("error", "SKILL.md", "missing root router")]
    text = root_skill.read_text(encoding="utf-8")

    on_disk = {p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md")}
    linked = set(re.findall(r"\]\(skills/([a-z0-9-]+)/SKILL\.md\)", text))

    for missing in sorted(on_disk - linked):
        findings.append(
            Finding("error", "SKILL.md", f"skill '{missing}' exists on disk but is not in the map")
        )
    for extra in sorted(linked - on_disk):
        findings.append(
            Finding("error", "SKILL.md", f"skill map links '{extra}' but no such folder exists")
        )
    return findings


def check_readme_map() -> list[Finding]:
    findings: list[Finding] = []
    readme = ROOT / "README.md"
    if not readme.is_file():
        return findings
    text = readme.read_text(encoding="utf-8")
    on_disk = {p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md")}
    linked = set(re.findall(r"\]\(skills/([a-z0-9-]+)/SKILL\.md\)", text))
    for missing in sorted(on_disk - linked):
        findings.append(
            Finding("warning", "README.md", f"skill '{missing}' is not listed in the README")
        )
    return findings


def check_docs() -> list[Finding]:
    findings: list[Finding] = []
    for name in ("README.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG.md", "mcp-server/README.md"):
        path = ROOT / name
        if not path.is_file():
            findings.append(Finding("error", name, "documented file is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for target in relative_links(text):
            if not (path.parent / target).resolve().exists():
                findings.append(Finding("error", name, f"broken relative link: {target}"))
    return findings


def main() -> int:
    findings: list[Finding] = []

    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        print("error: no skills found", file=sys.stderr)
        return 1

    findings.extend(check_skill(ROOT / "SKILL.md"))
    for path in skill_files:
        findings.extend(check_skill(path))

    for path in sorted(JURISDICTIONS_DIR.glob("*.md")):
        findings.extend(check_jurisdiction(path))

    findings.extend(check_skill_map())
    findings.extend(check_readme_map())
    findings.extend(check_docs())

    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]

    for finding in findings:
        print(finding.render())

    print()
    print(f"Skills: {len(skill_files)}")
    print(f"Jurisdiction packs: {len(list(JURISDICTIONS_DIR.glob('*.md'))) - 2}")
    print(f"Errors: {len(errors)}  Warnings: {len(warnings)}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
