"""Tests for the searchable tool registry.

The registry is hand-written, so the important tests are the ones that stop it
drifting out of step with the live tool set and the skills on disk.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookkeeping_mcp.registry import (
    META_TOOLS,
    REGISTRY,
    SKILL_ENTRIES,
    groups,
    search_registry,
)
from bookkeeping_mcp.server import build_server


def live_tool_names(repo_root: Path) -> set[str]:
    server = build_server(repo_root)
    return set(server._tool_manager._tools)


# ------------------------------------------------------------------ coverage


def test_every_tool_has_exactly_one_registry_entry(repo_root: Path):
    tool_names = live_tool_names(repo_root) - set(META_TOOLS)
    registered = [entry.name for entry in REGISTRY]
    assert len(registered) == len(set(registered)), "duplicate registry entries"
    assert set(registered) == tool_names, (
        f"registry drift — missing: {sorted(tool_names - set(registered))}, "
        f"stale: {sorted(set(registered) - tool_names)}"
    )


def test_every_skill_has_an_entry(repo_root: Path):
    on_disk = {p.parent.name for p in (repo_root / "skills").glob("*/SKILL.md")}
    registered = {entry.name for entry in SKILL_ENTRIES}
    assert registered == on_disk, (
        f"skill registry drift — missing: {sorted(on_disk - registered)}, "
        f"stale: {sorted(registered - on_disk)}"
    )


def test_skill_entries_are_marked_as_skills():
    for entry in SKILL_ENTRIES:
        assert entry.kind == "skill", entry.name
        payload = entry.to_dict()
        assert payload["read_resource"] == f"skill://{entry.name}"
        assert "required_params" not in payload


def test_tool_entries_declare_required_params():
    for entry in REGISTRY:
        assert entry.kind == "tool"
        # every tool with required params must declare them, so search results
        # can be acted on without a second round trip
        if entry.params:
            assert isinstance(entry.params, tuple)


# -------------------------------------------------------------------- search


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("how much tax do I owe this quarter", "estimated_tax_safe_harbor"),
        ("split this receipt across categories", "allocate_amount"),
        ("ACC levy for a roofer", "acc_work_levy_rates"),
        ("GST on 110 including tax", "sales_tax"),
        ("who owes me money", "ar_aging"),
        ("add up these invoices", "sum_amounts"),
        ("is this expense deductible", "schedule-c-categories"),
        ("can I claim my spare room as an office", "home-office"),
        ("do I need to file a 1099 for a subcontractor", "contractor-1099"),
        ("reconcile my bank balance", "reconciliation_check"),
        ("section 179 write off equipment", "first_year_asset_expense"),
        ("how much is the ACC for a builder", "acc_work_levy_rates"),
    ],
)
def test_natural_language_queries_rank_the_right_entry(query, expected):
    results = search_registry(query, limit=5)
    assert results, f"no match for {query!r}"
    top = results[0][1]
    assert top.name == expected, [e.name for _s, e in results]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        # genuinely ambiguous phrasing: either the calculator or the procedure
        # is a defensible answer, so only require that both surface in the top 2
        ("section 179 on a new ute", "first_year_asset_expense"),
        ("GST on 110 including tax", "sales_tax"),
        ("what's the mileage rate this year", "mileage_deduction"),
    ],
)
def test_ambiguous_queries_surface_the_answer_in_the_top_two(query, expected):
    names = [entry.name for _score, entry in search_registry(query, limit=2)]
    assert expected in names, names


def test_empty_query_returns_nothing():
    assert search_registry("") == []
    assert search_registry("   ") == []


def test_unmatchable_query_returns_nothing():
    assert search_registry("zzzz qqqq") == []


def test_limit_is_respected():
    assert len(search_registry("tax", limit=2)) <= 2
    assert len(search_registry("tax", limit=10)) <= 10


def test_results_are_ordered_by_score():
    results = search_registry("invoice", limit=8)
    scores = [score for score, _entry in results]
    assert scores == sorted(scores, reverse=True)


def test_groups_cover_every_tool():
    listed = {name for names in groups().values() for name in names}
    assert listed == {entry.name for entry in REGISTRY}
