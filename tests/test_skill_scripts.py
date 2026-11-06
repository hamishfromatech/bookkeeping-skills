"""Tests for the deterministic summary helpers that ship inside skills.

Each script is exercised through its real command line with fixture JSON, so the
tests cover the contract an agent actually relies on: a file argument (or stdin)
in, a stable text summary out.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills"


def run(script: str, payload, *args: str) -> subprocess.CompletedProcess:
    path = SCRIPTS / script
    assert path.is_file(), f"missing script {path}"
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture = Path(tmpdir) / "fixture.json"
        fixture.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(path), str(fixture), *args],
            capture_output=True,
            text=True,
            timeout=30,
        )


def run_stdin(script: str, payload) -> subprocess.CompletedProcess:
    path = SCRIPTS / script
    return subprocess.run(
        [sys.executable, str(path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
    )


# --------------------------------------------------------------- receipts


def test_receipt_summary_counts_statuses():
    result = run(
        "receipt-processing/scripts/receipt_summary.py",
        [
            {
                "vendor_name": "Blue Bottle",
                "date": "2026-03-18",
                "total_amount": 12.75,
                "currency": "USD",
                "source_type": "receiptor",
            },
            {"vendor_name": "Unknown", "date": "2026-03-18", "currency": "USD"},
        ],
    )
    assert result.returncode == 0, result.stderr
    assert "Receipts processed: 2" in result.stdout
    assert "ready: 1" in result.stdout
    assert "needs-review: 1" in result.stdout


def test_receipt_summary_treats_zero_total_as_present():
    """Regression: a $0.00 receipt was classed as missing because 0 is falsy."""
    result = run(
        "receipt-processing/scripts/receipt_summary.py",
        [
            {
                "vendor_name": "Free sample",
                "date": "2026-03-18",
                "total_amount": 0,
                "currency": "USD",
            }
        ],
    )
    assert result.returncode == 0, result.stderr
    assert "ready: 1" in result.stdout
    assert "needs-review" not in result.stdout


def test_receipt_summary_reports_sources():
    result = run(
        "receipt-processing/scripts/receipt_summary.py",
        [
            {"vendor_name": "A", "date": "2026-01-01", "total_amount": 1, "currency": "USD", "source_type": "pdf"},
            {"vendor_name": "B", "date": "2026-01-01", "total_amount": 1, "currency": "USD", "source_type": "pdf"},
            {"vendor_name": "C", "date": "2026-01-01", "total_amount": 1, "currency": "USD", "source_type": "photo"},
        ],
    )
    assert "pdf: 2" in result.stdout
    assert "photo: 1" in result.stdout


def test_receipt_summary_rejects_non_array():
    result = run("receipt-processing/scripts/receipt_summary.py", {"not": "an array"})
    assert result.returncode != 0
    assert "JSON array" in result.stderr


# -------------------------------------------------------------- categories


def test_category_review_summary_groups_confidence_and_category():
    result = run(
        "expense-categorization/scripts/category_review_summary.py",
        [
            {"category": "Advertising", "confidence": "high", "review_status": "ready"},
            {"category": "Advertising", "confidence": "low", "review_status": "needs-review"},
            {"category": "Office", "confidence": "high", "review_status": "ready"},
        ],
    )
    assert result.returncode == 0, result.stderr
    assert "Transactions categorized: 3" in result.stdout
    assert "high: 2" in result.stdout
    assert "Advertising: 2" in result.stdout


def test_category_summary_defaults_unlabelled():
    result = run("expense-categorization/scripts/category_review_summary.py", [{}])
    assert "uncategorized: 1" in result.stdout
    assert "unknown: 1" in result.stdout


# ----------------------------------------------------------- reconciliation


def test_reconciliation_summary_counts_tiers():
    result = run(
        "bank-reconciliation/scripts/reconciliation_summary.py",
        [
            {"status": "matched"},
            {"status": "matched"},
            {"status": "bank-only"},
            {"status": "needs-review"},
        ],
    )
    assert result.returncode == 0, result.stderr
    assert "Reconciliation records: 4" in result.stdout
    assert "matched: 2" in result.stdout
    assert "bank-only: 1" in result.stdout


# ------------------------------------------------------------ monthly close


def test_monthly_close_summary_counts_checklist():
    result = run(
        "monthly-close/scripts/monthly_close_summary.py",
        [
            {"status": "done"},
            {"status": "done"},
            {"status": "blocked"},
        ],
    )
    assert result.returncode == 0, result.stderr
    assert "Checklist items: 3" in result.stdout
    assert "done: 2" in result.stdout
    assert "blocked: 1" in result.stdout


# --------------------------------------------------------------- tax package


def test_tax_package_summary_counts_artifacts():
    result = run(
        "tax-prep/scripts/tax_package_summary.py",
        [{"status": "ready"}, {"status": "missing"}, {"status": "draft"}],
    )
    assert result.returncode == 0, result.stderr
    assert "Artifacts tracked: 3" in result.stdout
    assert "missing: 1" in result.stdout


# ------------------------------------------------------------------ revenue


def test_revenue_summary_totals_and_aging():
    result = run(
        "income-invoicing/scripts/revenue_summary.py",
        [
            {"status": "open", "total_amount": 1000, "due_date": "2026-12-15", "invoice_number": "A1"},
            {"status": "overdue", "total_amount": 500, "due_date": "2026-11-01", "invoice_number": "A2"},
            {"status": "paid", "total_amount": 700, "amount_paid": 700, "invoice_number": "A3"},
            {"status": "void", "total_amount": 900, "invoice_number": "A4"},
        ],
        "--as-of",
        "2026-11-30",
    )
    assert result.returncode == 0, result.stderr
    assert "Sales records: 4" in result.stdout
    assert "Gross invoiced: 2,200.00" in result.stdout
    assert "Received: 700.00" in result.stdout
    assert "Outstanding (AR): 1,500.00" in result.stdout
    assert "not-yet-due: 1,000.00" in result.stdout
    assert "1-30: 500.00" in result.stdout


def test_revenue_summary_flags_duplicate_invoice_numbers():
    result = run(
        "income-invoicing/scripts/revenue_summary.py",
        [
            {"status": "open", "total_amount": 10, "invoice_number": "DUP"},
            {"status": "open", "total_amount": 20, "invoice_number": "DUP"},
        ],
    )
    assert "Duplicate invoice numbers: 1" in result.stdout
    assert "DUP" in result.stdout


def test_revenue_summary_reads_stdin():
    result = run_stdin(
        "income-invoicing/scripts/revenue_summary.py",
        [{"status": "open", "total_amount": 100}],
    )
    assert result.returncode == 0, result.stderr
    assert "Gross invoiced: 100.00" in result.stdout
