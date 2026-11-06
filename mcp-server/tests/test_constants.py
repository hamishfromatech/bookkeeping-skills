from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from bookkeeping_mcp.constants import (
    RepositoryError,
    find_repo_root,
    get_jurisdiction,
    load_jurisdictions,
    parse_jurisdiction,
    search_constants,
)


def test_find_repo_root_from_package(repo_root: Path):
    assert find_repo_root() == repo_root


def test_find_repo_root_honours_env(monkeypatch, repo_root: Path):
    monkeypatch.setenv("BOOKKEEPING_SKILLS_ROOT", str(repo_root))
    assert find_repo_root() == repo_root


def test_unknown_root_raises(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("BOOKKEEPING_SKILLS_ROOT", str(tmp_path))
    with pytest.raises(RepositoryError):
        find_repo_root(tmp_path)


def test_both_packs_load(repo_root: Path):
    packs = load_jurisdictions(repo_root)
    assert set(packs) == {"us", "au", "nz"}


def test_template_and_readme_are_skipped(repo_root: Path):
    packs = load_jurisdictions(repo_root)
    assert "_template" not in packs
    assert "readme" not in packs


def test_us_pack_parses_review_date_and_rows(repo_root: Path):
    pack = get_jurisdiction("us", repo_root)
    assert pack.last_reviewed is not None
    assert len(pack.rows) > 15
    topics = " | ".join(row.topic for row in pack.rows).lower()
    assert "mileage" in topics
    assert "section 179" in topics
    assert "1099" in topics


def test_us_mileage_row_has_numbers_and_source(repo_root: Path):
    pack = get_jurisdiction("us", repo_root)
    rows = [r for r in pack.rows if "mileage" in r.topic.lower() and "business" in r.topic.lower()]
    assert rows, "expected a business mileage row"
    row = rows[0]
    assert row.numbers, "expected numbers extracted from the value"
    assert any(70 <= n <= 90 for n in row.numbers), row.numbers
    assert row.source_url and row.source_url.startswith("http")
    assert row.verified is not None


def test_au_pack_parses(repo_root: Path):
    pack = get_jurisdiction("au", repo_root)
    assert pack.last_reviewed is not None
    topics = " | ".join(row.topic for row in pack.rows).lower()
    assert "gst" in topics
    assert "cents per kilometre" in topics
    assert "super" in topics


def test_nz_pack_parses(repo_root: Path):
    pack = get_jurisdiction("nz", repo_root)
    assert pack.last_reviewed is not None
    topics = " | ".join(row.topic for row in pack.rows).lower()
    assert "gst" in topics
    assert "kilometre" in topics
    assert "provisional tax" in topics
    assert "acc" in topics


def test_nz_constants_carry_sources_and_numbers(repo_root: Path):
    pack = get_jurisdiction("nz", repo_root)
    gst = [r for r in pack.rows if r.topic.lower().startswith("gst rate")][0]
    assert gst.numbers == [15.0]
    assert gst.source_url and gst.source_url.startswith("http")
    assert gst.verified == "2026-11-06"

    low_value = [r for r in pack.rows if "low-value asset" in r.topic.lower()][0]
    assert 1000.0 in low_value.numbers


def test_alias_lookup(repo_root: Path):
    assert get_jurisdiction("Australia", repo_root).code == "au"
    assert get_jurisdiction("USA", repo_root).code == "us"
    assert get_jurisdiction("New Zealand", repo_root).code == "nz"
    assert get_jurisdiction("aotearoa", repo_root).code == "nz"


def test_unknown_jurisdiction_lists_available(repo_root: Path):
    with pytest.raises(RepositoryError, match="us"):
        get_jurisdiction("zz", repo_root)


def test_search_matches_topic(repo_root: Path):
    pack = get_jurisdiction("us", repo_root)
    hits = search_constants(pack, "bonus depreciation")
    assert hits
    assert any("bonus" in r.topic.lower() for r in hits)
    assert all(
        any(term in f"{r.topic} {r.value}".lower() for term in ("bonus", "depreciation"))
        for r in hits
    )


def test_search_no_match_returns_empty(repo_root: Path):
    pack = get_jurisdiction("us", repo_root)
    assert search_constants(pack, "zzzzz-not-a-topic") == []


def test_staleness_threshold(repo_root: Path):
    pack = get_jurisdiction("us", repo_root)
    assert pack.is_stale(today=pack.last_reviewed) is False
    later = pack.last_reviewed + timedelta(days=400)
    assert pack.is_stale(today=later) is True
    assert pack.age_days(today=pack.last_reviewed) == 0


def test_missing_last_reviewed_is_stale(tmp_path: Path):
    path = tmp_path / "zz.md"
    path.write_text("# Zetland\n\n## Current-law constants\n\n| Topic | Year | Value | Source | Verified |\n|---|---|---|---|---|\n| GST | 2026 | 10% | ATO | 2026-01-01 |\n", encoding="utf-8")
    pack = parse_jurisdiction(path)
    assert pack.last_reviewed is None
    assert pack.is_stale() is True
    assert len(pack.rows) == 1
    assert pack.rows[0].numbers == [10.0]


def test_header_row_and_separator_are_not_rows(tmp_path: Path):
    path = tmp_path / "zz.md"
    path.write_text(
        "# Zetland\n\nLast reviewed: 2026-01-01\n\n## Current-law constants\n\n"
        "| Topic | Year | Value | Source | Verified |\n"
        "|---|---|---|---|---|\n"
        "| Rate | 2026 | 5% | [ATO](https://ato.gov.au) | 2026-01-01 |\n",
        encoding="utf-8",
    )
    pack = parse_jurisdiction(path)
    assert len(pack.rows) == 1
    assert pack.rows[0].source_url == "https://ato.gov.au"
    assert pack.last_reviewed == date(2026, 1, 1)


def test_search_ranks_distinctive_term_above_common_one(repo_root: Path):
    """'rate' appears in nearly every row; 'kilometre' should dominate."""
    pack = get_jurisdiction("nz", repo_root)
    hits = search_constants(pack, "kilometre rate petrol")
    assert hits
    assert "kilometre" in hits[0].topic.lower(), hits[0].topic


def test_search_prefers_topic_matches(repo_root: Path):
    pack = get_jurisdiction("nz", repo_root)
    hits = search_constants(pack, "provisional tax")
    assert "provisional tax" in hits[0].topic.lower(), hits[0].topic


def test_acc_work_levy_schedule_parses(repo_root: Path):
    from bookkeeping_mcp.constants import get_acc_levy_schedule

    schedule = get_acc_levy_schedule(repo_root)
    assert schedule.year == "2026/27"
    assert "excluding GST" in schedule.basis
    assert schedule.source_url and "legislation.govt.nz" in schedule.source_url
    assert len(schedule.rows) == 28


def test_acc_work_levy_known_rates(repo_root: Path):
    from bookkeeping_mcp.constants import get_acc_levy_schedule

    by_cu = {row.cu: row for row in get_acc_levy_schedule(repo_root).rows}
    assert by_cu["42420"].classification == "Carpentry services"
    assert by_cu["42420"].rate == 1.76
    assert by_cu["42230"].rate == 2.25          # roofing — highest construction rate
    assert by_cu["42320"].rate == 0.68          # electrical — low risk
    assert by_cu["42595"].rate == 0.40          # all trades subcontracted


def test_acc_work_levy_search_by_name_and_code(repo_root: Path):
    from bookkeeping_mcp.constants import get_acc_levy_schedule, search_levy_rows

    schedule = get_acc_levy_schedule(repo_root)
    assert [r.cu for r in search_levy_rows(schedule, "42420")] == ["42420"]
    assert search_levy_rows(schedule, "plumber")[0].cu == "42310"
    assert search_levy_rows(schedule, "zzzz") == []


def test_job_title_aliases_resolve(repo_root: Path):
    from bookkeeping_mcp.constants import get_acc_levy_schedule, search_levy_rows

    schedule = get_acc_levy_schedule(repo_root)
    assert [r.cu for r in search_levy_rows(schedule, "sparky")] == ["42320"]
    assert [r.cu for r in search_levy_rows(schedule, "roofer")] == ["42230"]
    assert [r.cu for r in search_levy_rows(schedule, "chippy")] == ["42420"]
    assert [r.cu for r in search_levy_rows(schedule, "brickie")] == ["42220"]


def test_ambiguous_job_title_returns_every_candidate(repo_root: Path):
    from bookkeeping_mcp.constants import get_acc_levy_schedule, search_levy_rows

    schedule = get_acc_levy_schedule(repo_root)
    cus = {r.cu for r in search_levy_rows(schedule, "builder")}
    assert cus == {"41110", "42420"}
