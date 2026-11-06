"""Read jurisdiction packs out of the bookkeeping-skills repository.

The skills are told never to hardcode a year-specific figure. This module is how
the server honours that: it parses the ``Current-law constants`` table out of
``jurisdictions/<code>.md`` so a tool call always returns the figure that is
written down in the repo, together with its source and verified date.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

CONSTANTS_HEADING = "current-law constants"
SKIP_FILES = {"readme.md", "_template.md"}
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
LAST_REVIEWED_RE = re.compile(r"last reviewed\**\s*:?\s*\**\s*" + DATE_RE.pattern, re.IGNORECASE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
NUMBER_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")


class RepositoryError(RuntimeError):
    """Raised when the skills repository cannot be located or parsed."""


@dataclass(frozen=True)
class ConstantRow:
    topic: str
    tax_year: str
    value: str
    source: str
    source_url: str | None
    verified: str | None
    numbers: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "tax_year": self.tax_year,
            "value": self.value,
            "numbers": self.numbers,
            "source": self.source,
            "source_url": self.source_url,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class Jurisdiction:
    code: str
    name: str
    path: Path
    last_reviewed: date | None
    note: str
    rows: tuple[ConstantRow, ...]

    def to_summary(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "stale": self.is_stale(),
            "constant_count": len(self.rows),
            "path": str(self.path),
        }

    def is_stale(self, today: date | None = None) -> bool:
        if self.last_reviewed is None:
            return True
        reference = today or date.today()
        return (reference - self.last_reviewed).days > 365

    def age_days(self, today: date | None = None) -> int | None:
        if self.last_reviewed is None:
            return None
        return ((today or date.today()) - self.last_reviewed).days


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the skills repo root: env var, then the package location, then cwd.

    An explicit ``BOOKKEEPING_SKILLS_ROOT`` is honoured strictly: if it is set
    but does not point at a valid repo, raise rather than silently falling back
    to a different checkout.
    """
    env = os.environ.get("BOOKKEEPING_SKILLS_ROOT")
    if env:
        root = Path(env).expanduser()
        if (root / "jurisdictions").is_dir() and (root / "SKILL.md").is_file():
            return root
        raise RepositoryError(
            f"BOOKKEEPING_SKILLS_ROOT={env!r} is not a bookkeeping-skills repo "
            "(expected jurisdictions/ and SKILL.md)."
        )

    candidates: list[Path] = []
    if start is not None:
        candidates.append(Path(start))
    candidates.append(Path(__file__).resolve())
    candidates.append(Path.cwd())

    for candidate in candidates:
        bases = [candidate, *candidate.parents] if candidate.is_dir() else list(candidate.parents)
        for base in bases:
            if (base / "jurisdictions").is_dir() and (base / "SKILL.md").is_file():
                return base

    raise RepositoryError(
        "Could not find the bookkeeping-skills repo root. Set BOOKKEEPING_SKILLS_ROOT "
        "to the directory containing jurisdictions/ and SKILL.md."
    )


def _strip_markup(text: str) -> str:
    text = text.replace("**", "").replace("`", "").replace("__", "")
    return re.sub(r"\s+", " ", text).strip()


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    body = stripped[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells)


def _extract_numbers(text: str) -> list[float]:
    out: list[float] = []
    for match in NUMBER_RE.findall(text):
        try:
            out.append(float(match.replace(",", "")))
        except ValueError:
            continue
    return out


def parse_jurisdiction(path: Path) -> Jurisdiction:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    name = _strip_markup(title_match.group(1)) if title_match else path.stem.upper()

    last_reviewed: date | None = None
    note = ""
    for line in lines:
        if "last reviewed" in line.lower():
            match = LAST_REVIEWED_RE.search(line)
            if match:
                try:
                    last_reviewed = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                except ValueError:
                    last_reviewed = None
                note = _strip_markup(line.split(":", 1)[-1] if ":" in line else line)
                break

    rows: list[ConstantRow] = []
    in_section = False
    for line in lines:
        heading = re.match(r"^(#{2,3})\s+(.*)$", line)
        if heading:
            level, title = heading.group(1), heading.group(2)
            if CONSTANTS_HEADING in title.lower():
                in_section = True
                continue
            if in_section and len(level) <= 2:
                in_section = False
            continue

        if not in_section:
            continue

        cells = _split_row(line)
        if len(cells) < 5 or _is_separator(cells):
            continue
        if _strip_markup(cells[0]).lower() == "topic":
            continue

        topic, tax_year, value, source, verified = cells[:5]
        link = LINK_RE.search(source)
        rows.append(
            ConstantRow(
                topic=_strip_markup(topic),
                tax_year=_strip_markup(tax_year),
                value=_strip_markup(value),
                source=_strip_markup(LINK_RE.sub(r"\1", source)),
                source_url=link.group(2) if link else None,
                verified=_strip_markup(verified) or None,
                numbers=_extract_numbers(value),
            )
        )

    return Jurisdiction(
        code=path.stem.lower(),
        name=name,
        path=path,
        last_reviewed=last_reviewed,
        note=note,
        rows=tuple(rows),
    )


def load_jurisdictions(root: Path | None = None) -> dict[str, Jurisdiction]:
    base = (root or find_repo_root()) / "jurisdictions"
    if not base.is_dir():
        raise RepositoryError(f"No jurisdictions/ directory at {base}")

    packs: dict[str, Jurisdiction] = {}
    for path in sorted(base.glob("*.md")):
        if path.name.lower() in SKIP_FILES:
            continue
        pack = parse_jurisdiction(path)
        if pack.rows:
            packs[pack.code] = pack
    if not packs:
        raise RepositoryError(f"No jurisdiction packs with a constants table found in {base}")
    return packs


def get_jurisdiction(code: str, root: Path | None = None) -> Jurisdiction:
    packs = load_jurisdictions(root)
    key = (code or "").strip().lower()
    aliases = {
        "usa": "us",
        "united states": "us",
        "america": "us",
        "australia": "au",
        "aus": "au",
        "new zealand": "nz",
        "aotearoa": "nz",
        "nzl": "nz",
    }
    key = aliases.get(key, key)
    if key not in packs:
        raise RepositoryError(
            f"Unknown jurisdiction {code!r}. Available: {', '.join(sorted(packs))}"
        )
    return packs[key]


def search_constants(jurisdiction: Jurisdiction, query: str | None = None) -> list[ConstantRow]:
    """Filter constants, best match first.

    Terms are weighted by inverse document frequency so that a distinctive word
    ("kilometre") outranks a word that appears in almost every row ("rate").
    """
    rows = list(jurisdiction.rows)
    if not query:
        return rows

    terms = [t for t in re.split(r"[\s,]+", query.lower()) if t]
    if not terms:
        return rows

    def haystack(row: ConstantRow) -> str:
        return f"{row.topic} {row.tax_year} {row.value}".lower()

    docs = max(len(rows), 1)
    frequency = {
        term: max(sum(1 for row in rows if term in haystack(row)), 1) for term in set(terms)
    }

    def score(row: ConstantRow) -> float:
        text = haystack(row)
        total = 0.0
        for term in terms:
            if term in text:
                total += 1.0 / frequency[term]
                if term in row.topic.lower():
                    total += 0.5 / frequency[term]
        return total

    scored = [(score(row), row) for row in rows]
    matched = [(s, row) for s, row in scored if s > 0]
    matched.sort(key=lambda pair: (-pair[0], pair[1].topic))
    return [row for _score, row in matched]
