#!/usr/bin/env python3
"""Deterministic revenue and AR-aging summary for invoice / sale records.

Usage:
    python3 revenue_summary.py records.json [--as-of 2026-11-30]
    cat records.json | python3 revenue_summary.py --as-of 2026-11-30

Input: a JSON array of records following references/INVOICE-SCHEMA.md.
Output: counts by status, gross revenue, cash received, outstanding AR and
aging buckets. No writes, no network, no interpretation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

VOID_STATUSES = {"void", "draft"}
OUTSTANDING_STATUSES = {"open", "overdue", "partially-paid"}

BUCKETS = (
    ("not-yet-due", None),
    ("1-30", 30),
    ("31-60", 60),
    ("61-90", 90),
    ("90-plus", None),
)


def load_records(path: str | None) -> list:
    if path:
        return json.loads(Path(path).read_text())
    return json.load(sys.stdin)


def money(value) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def parse_date(value) -> date | None:
    if not value:
        return None
    text = str(value)[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def bucket_for(due: date | None, as_of: date) -> str:
    if due is None:
        return "unknown-due-date"
    days = (as_of - due).days
    if days <= 0:
        return "not-yet-due"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90-plus"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", nargs="?", help="JSON file; stdin when omitted")
    parser.add_argument(
        "--as-of",
        dest="as_of",
        default=None,
        help="Aging reference date (YYYY-MM-DD). Defaults to today.",
    )
    args = parser.parse_args(argv)

    as_of = parse_date(args.as_of) or date.today()

    records = load_records(args.file)
    if not isinstance(records, list):
        raise SystemExit("Expected a JSON array of invoice or sale records")

    rows = [r for r in records if isinstance(r, dict)]

    status_counts = Counter()
    aging_counts = Counter()
    invoiced = Decimal("0")
    received = Decimal("0")
    outstanding = Decimal("0")
    tax_collected = Decimal("0")
    currencies = set()
    invoice_numbers: Counter = Counter()
    missing_due = 0
    missing_number = 0

    for row in rows:
        status = str(row.get("status", "unlabeled"))
        status_counts[status] += 1

        total = money(row.get("total_amount"))
        paid = money(row.get("amount_paid"))
        if status == "paid" and paid == 0:
            paid = total

        if row.get("currency"):
            currencies.add(str(row["currency"]).upper())

        if status in VOID_STATUSES:
            continue

        invoiced += total
        received += paid
        tax_collected += money(row.get("tax_amount"))

        number = str(row.get("invoice_number") or "").strip()
        if number:
            invoice_numbers[number] += 1
        else:
            missing_number += 1

        if status in OUTSTANDING_STATUSES:
            open_amount = money(row.get("amount_outstanding"))
            if open_amount == 0 and total > paid:
                open_amount = total - paid
            open_amount = max(open_amount, Decimal("0"))
            outstanding += open_amount
            due = parse_date(row.get("due_date"))
            if due is None:
                missing_due += 1
            if open_amount > 0:
                aging_counts[bucket_for(due, as_of)] += open_amount

    duplicates = sorted(number for number, count in invoice_numbers.items() if count > 1)

    print(f"Sales records: {len(rows)}")
    print("Status:")
    for status in (
        "paid",
        "open",
        "partially-paid",
        "overdue",
        "credited",
        "draft",
        "void",
        "unlabeled",
    ):
        if status_counts[status]:
            print(f"  {status}: {status_counts[status]}")
    for status, count in sorted(status_counts.items()):
        if status not in {
            "paid",
            "open",
            "partially-paid",
            "overdue",
            "credited",
            "draft",
            "void",
            "unlabeled",
        }:
            print(f"  {status}: {count}")

    print(f"Gross invoiced: {invoiced:,.2f}")
    print(f"Received: {received:,.2f}")
    print(f"Outstanding (AR): {outstanding:,.2f}")
    print(f"Tax collected: {tax_collected:,.2f}")
    if currencies:
        print(f"Currencies: {', '.join(sorted(currencies))}")

    print(f"AR aging as of {as_of.isoformat()}:")
    for name, _limit in BUCKETS:
        if aging_counts[name]:
            print(f"  {name}: {aging_counts[name]:,.2f}")
    if aging_counts["unknown-due-date"]:
        print(f"  unknown-due-date: {aging_counts['unknown-due-date']:,.2f}")

    if missing_due:
        print(f"Records missing due_date: {missing_due}")
    if missing_number:
        print(f"Records missing invoice_number: {missing_number}")
    if duplicates:
        print(f"Duplicate invoice numbers: {len(duplicates)}")
        for number in duplicates:
            print(f"  {number}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
