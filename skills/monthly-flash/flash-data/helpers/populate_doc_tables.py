#!/usr/bin/env python3
"""DEPRECATED — use populate_flash_table.py instead.

This script used `sq agent-tools google-drive docs-edit update_table_cell`,
which silently ignores `table_start_position` / `table_index` and always
writes to the first table in a tab. The replacement (populate_flash_table.py)
goes through the Docs API batchUpdate path via gdrive-cli.py, which targets
cells by their absolute startIndex and therefore works regardless of how
many tables sit in the tab.

Kept on disk briefly as a reference for the failure mode. Safe to delete
once the new populator has been in use for a cycle.

Original docstring follows.

---

Populate the two Google Docs tables in the Claude tab.

Two modes:

  --mode shell-init
    Populates ONLY the static header row + label column. Run once when first
    creating the shell template (or to re-initialize after manual structural
    edits). Period header is left as `[PERIOD]` placeholder.

  --mode values
    Populates the value cells using the JSON packet from /flash-data.
    Also replaces `[PERIOD]` and other text placeholders via find-replace
    (handled by a separate caller).

Usage:
  python3 populate_doc_tables.py --mode shell-init \
      --doc 1faTUvm5CYK-W4J7JeKezbi1aEvRbSJ95vkjMtzc_sJA \
      --tab t.6lmbmhs5p561

  python3 populate_doc_tables.py --mode values \
      --doc 1faTUvm5CYK-W4J7JeKezbi1aEvRbSJ95vkjMtzc_sJA \
      --tab t.6lmbmhs5p561 \
      --packet /tmp/apr26_out.json
"""

from __future__ import annotations
import argparse
import json
import subprocess
import sys
from typing import Any


# Static structure for the two tables.
# Each entry: (row, col, text)

# Table 1 (Flash summary, 28 rows × 8 cols)
FLASH_HEADER_CELLS = [
    (0, 1, "[PERIOD]"),
    (1, 0, "Metric"),
    (1, 1, "Actual"),
    (1, 2, "vs. OL $"),
    (1, 3, "vs. OL %"),
    (1, 4, "vs. AP $"),
    (1, 5, "vs. AP %"),
    (1, 6, "YoY %"),
    (1, 7, "Prior-mo YoY %"),
]

# NBSP (U+00A0) used for indent — Docs cell API rejects leading regular whitespace.
_N = " "  # non-breaking space; 4 = one indent level
FLASH_ROW_LABELS = [
    "Cash App Actives",
    "Cash App Inflows per Active",
    "Commerce GMV",
    "Square GPV",
    _N*4 + "Square US GPV",
    _N*4 + "Square INTL GPV",
    _N*8 + "Square INTL GPV (CC)",
    "Gross Profit",
    _N*4 + "Block",
    _N*8 + "Cash App",
    _N*12 + "Commerce",
    _N*12 + "Borrow",
    _N*12 + "Cash App Card",
    _N*12 + "Instant Deposit",
    _N*12 + "Post-Purchase BNPL",
    _N*8 + "Square",
    _N*12 + "US Payments",
    _N*12 + "INTL Payments",
    _N*12 + "Banking",
    _N*12 + "SaaS",
    _N*12 + "Hardware",
    _N*8 + "TIDAL",
    _N*8 + "Proto",
    "Adjusted Opex",
    "Adjusted OI",
    "Rule of 40",
]

# Table 2 (Stnd P&L, 37 rows × 7 cols)
PNL_HEADER_CELLS = [
    (0, 0, "Metric"),
    (0, 1, "Actual"),
    (0, 2, "vs. OL $"),
    (0, 3, "vs. OL %"),
    (0, 4, "vs. AP $"),
    (0, 5, "vs. AP %"),
    (0, 6, "YoY %"),
]

PNL_ROW_LABELS = [
    "Variable Operational Costs",
    "P2P",
    "Risk Loss",
    "Card Issuance",
    "Warehouse Financing",
    "Other",
    _N*3 + "Hardware Logistics",
    _N*3 + "Bad Debt Expense",
    _N*3 + "Customer Reimbursements",
    "Total Variable Operational Costs",
    "Acquisition Costs",
    "Marketing (Non-People)",
    _N*3 + "Marketing",
    _N*3 + "Onboarding Costs",
    _N*3 + "Partnership Fees",
    _N*3 + "Reader Expense",
    "Sales & Marketing (People)",
    "Total Acquisition Costs",
    "Fixed Costs",
    "Product Development People",
    "G&A People",
    _N*3 + "G&A People (ex. CS)",
    _N*3 + "Customer Support People",
    "Software & Cloud",
    _N*3 + "Software",
    _N*3 + "Cloud fees",
    "Taxes, Insurance & Other Corp",
    "Litigation & Professional Services",
    _N*3 + "Legal fees",
    _N*3 + "Other Professional Services",
    "Rent, Facilities, Equipment",
    "Travel & Entertainment",
    "Hardware Production Costs",
    "Non-Cash expenses (ex. SBC)",
    "Total Fixed Costs",
    "Total Block GAAP OpEx",
]


def find_tables(doc: str, tab: str) -> list[dict]:
    """Read the doc and return list of table blocks (sorted by start_position)."""
    r = subprocess.run([
        "sq", "agent-tools", "google-drive", "docs-v2-read", "--json",
        json.dumps({"document_id_or_url": doc, "tab_id": tab})
    ], capture_output=True, text=True, timeout=120)
    data = json.loads(json.loads(r.stdout)["result"])
    tables = []
    for b in data["blocks"]:
        if b["type"] == "table":
            tables.append({
                "start_position": b["start_position"],
                "end_position": b["end_position"],
                "rows": b["metadata"].get("rows"),
                "cols": b["metadata"].get("cols"),
            })
    tables.sort(key=lambda t: t["start_position"])
    return tables


def update_cell(doc: str, tab: str, table_pos: int, row: int, col: int, text: str) -> bool:
    r = subprocess.run([
        "sq", "agent-tools", "google-drive", "docs-edit", "--json",
        json.dumps({
            "document_id_or_url": doc,
            "operation": "update_table_cell",
            "tab_id": tab,
            "text": text,
            "table_params": {
                "table_start_position": table_pos,
                "row_index": row,
                "column_index": col,
            },
        })
    ], capture_output=True, text=True, timeout=60)
    ok = "Updated cell" in r.stdout
    if not ok:
        print(f"  FAIL cell ({row},{col}): {r.stdout[:200]} {r.stderr[:200]}", file=sys.stderr)
    return ok


def write_cells_with_refresh(doc: str, tab: str, table_index: int, cells: list[tuple]):
    """Write each cell, re-reading the table's current start_position before each call."""
    print(f"  [write_cells_with_refresh] table_index={table_index}, cells[:3]={cells[:3]}, last={cells[-1] if cells else None}")
    for row, col, text in cells:
        tables = find_tables(doc, tab)
        if table_index >= len(tables):
            print(f"  FAIL ({row},{col}): table_index {table_index} not found", file=sys.stderr)
            continue
        pos = tables[table_index]["start_position"]
        update_cell(doc, tab, pos, row, col, text)


def shell_init(doc: str, tab: str):
    """Populate static headers + label column for both tables."""
    tables = find_tables(doc, tab)
    if len(tables) < 2:
        print(f"ERROR: expected 2 tables, found {len(tables)}", file=sys.stderr)
        sys.exit(1)
    t1, t2 = tables[0], tables[1]
    print(f"Table 1 (Flash) at pos {t1['start_position']}, {t1['rows']}x{t1['cols']}")
    print(f"Table 2 (P&L) at pos {t2['start_position']}, {t2['rows']}x{t2['cols']}")

    # Build full cell lists
    flash_cells = list(FLASH_HEADER_CELLS) + [(i + 2, 0, label) for i, label in enumerate(FLASH_ROW_LABELS)]
    pnl_cells = list(PNL_HEADER_CELLS) + [(i + 1, 0, label) for i, label in enumerate(PNL_ROW_LABELS)]

    print(f"\nPopulating Table 1 (Flash summary, {len(flash_cells)} cells)...")
    write_cells_with_refresh(doc, tab, 0, flash_cells)

    # Re-check tables before second pass
    refreshed = find_tables(doc, tab)
    print(f"\nAfter Table 1 fill — tables found:")
    for i, t in enumerate(refreshed):
        print(f"  tables[{i}] pos={t['start_position']} {t['rows']}x{t['cols']}")

    print(f"\nPopulating Table 2 (Standardized P&L, {len(pnl_cells)} cells)...")
    write_cells_with_refresh(doc, tab, 1, pnl_cells)

    print("\nShell-init done.")


def populate_values(doc: str, tab: str, packet_path: str):
    """Populate value cells from a /flash-data JSON packet."""
    with open(packet_path) as f:
        packet = json.load(f)

    tables = find_tables(doc, tab)
    if len(tables) < 2:
        print(f"ERROR: expected 2 tables, found {len(tables)}", file=sys.stderr)
        sys.exit(1)
    t1, t2 = tables[0], tables[1]

    # Table 1: flash_table_formatted is 28 rows × 8 cols.
    # Our doc table layout: row 0 = period header, row 1 = col headers, rows 2-27 = data.
    # Helper output: row 0 = period (label col blank), row 1 = col headers, rows 2-27 = data labels in col 0 + values in cols 1-7.
    flash = packet["flash_table_formatted"]
    print(f"Populating Table 1 values (Flash, {len(flash)} rows from packet)...")
    # Period header → row 0, col 1
    period_val = flash[0][1] if flash[0] and len(flash[0]) > 1 else ""
    update_cell(doc, tab, t1["start_position"], 0, 1, str(period_val))
    # Data rows: rows 2-27 of helper = rows 2-27 of doc table
    for r_idx in range(2, len(flash)):
        helper_row = flash[r_idx]
        # Helper col 0 is label (already in doc as static), cols 1-7 are values
        for c_idx in range(1, len(helper_row)):
            val = helper_row[c_idx]
            if val in (None, ""):
                continue
            update_cell(doc, tab, t1["start_position"], r_idx, c_idx, str(val))

    pnl = packet["pnl_table_formatted"]
    print(f"\nPopulating Table 2 values (P&L, {len(pnl)} rows from packet)...")
    # Helper P&L: row 0 = col headers, rows 1-36 = data rows
    # Doc P&L: same — row 0 = col headers (static), rows 1-36 = data
    for r_idx in range(1, len(pnl)):
        helper_row = pnl[r_idx]
        for c_idx in range(1, len(helper_row)):
            val = helper_row[c_idx]
            if val in (None, ""):
                continue
            update_cell(doc, tab, t2["start_position"], r_idx, c_idx, str(val))

    print("\nValue population done.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["shell-init", "values"], required=True)
    ap.add_argument("--doc", required=True)
    ap.add_argument("--tab", required=True)
    ap.add_argument("--packet", help="Required for --mode values")
    args = ap.parse_args()

    if args.mode == "shell-init":
        shell_init(args.doc, args.tab)
    else:
        if not args.packet:
            print("--packet required for --mode values", file=sys.stderr)
            sys.exit(1)
        populate_values(args.doc, args.tab, args.packet)


if __name__ == "__main__":
    main()
