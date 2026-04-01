#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
from __future__ import annotations
"""
populate_tables.py

Generate Google Docs API batch-update JSON to populate all 5 template tables
in the Block Performance Digest. Replaces LLM-based table population with
pure Python -- runs in seconds instead of minutes.

Usage:
    python3 populate_tables.py SHEET_JSON DOC_JSON TAB_ID [--colors]

Output:
    Prints JSON to stdout: {"requests": [...]} ready to pipe to
    `gdrive docs batch-update`. If --colors is set, prints a second JSON
    object on a separate line (colors require a Doc re-read after values
    are applied, so the color batch is a placeholder structure).

Examples:
    # Value population only:
    python3 populate_tables.py /tmp/pacing_sheet_2026-03-31.json /tmp/doc.json t.abc123

    # Pipe directly to gdrive:
    python3 populate_tables.py /tmp/sheet.json /tmp/doc.json t.abc123 | \\
        cd ~/skills/gdrive && uv run gdrive-cli.py docs batch-update DOC_ID
"""
import json
import sys
import re
import argparse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Section labels to scan for in column B (index 1) of the sheet
SECTION_LABELS = {
    "gp":       "1a) Block gross profit",
    "aoi":      "1b) Block adjusted OI",
    "cashapp":  "2) Cash App",       # starts-with match
    "commerce": "3) Commerce",       # starts-with match
    "gpv":      "4) Square GPV",
}

# Doc table identification: scan first-column text in row index >= 3
TABLE_IDENTIFIERS = {
    "Block gross profit": "gp",
    "Gross profit":       "aoi",
    "Actives":            "cashapp",
    "Inflows":            "commerce",
    "Global GPV":         "gpv",
}

# Sheet column indices (0-based) for each doc column
# Doc col -> sheet col
SHEET_COL_MAP = {
    1: 11,   # Jan Actual
    2: 12,   # Feb Actual
    3: 13,   # Mar Pacing
    # 4 is separator -- skip
    5: 17,   # Q1 Pacing
    6: 18,   # Q1 AP
    7: 20,   # Guidance / Consensus
    8: 21,   # Consensus (1a/1b only)
}

# Number of doc columns per table (determines which cols are present)
TABLE_COL_COUNTS = {
    "gp":       9,   # cols 0-8 (has 7 + 8)
    "aoi":      9,   # cols 0-8 (has 7 + 8)
    "cashapp":  8,   # cols 0-7 (has 7, no 8)
    "commerce": 7,   # cols 0-6 (no 7 or 8)
    "gpv":      8,   # cols 0-7 (has 7, no 8)
}

# Row offsets from section header for each table's data rows.
# Each entry: (doc_row_index, sheet_row_offset_from_section_start)
# doc_row_index is 0-based row within the doc table (rows 0-2 are headers).
TABLE_ROW_OFFSETS = {
    # Sheet offset = doc_row + 1 because the sheet has an extra section-header
    # row (e.g. "1a) Block gross profit") before the year/type/month headers,
    # while doc tables start directly at the year header (row 0).
    "gp": [
        (3,  4),   # Block gross profit
        (4,  5),   # YoY Growth (%)
        (5,  6),   # Delta vs. AP (%)
        # 6 = blank
        (7,  8),   # Cash App gross profit
        (8,  9),   # YoY
        (9,  10),  # Delta
        # 10 = blank
        (11, 12),  # Square GP
        (12, 13),  # YoY
        (13, 14),  # Delta
        # 14 = blank
        (15, 16),  # Proto GP
        (16, 17),  # YoY
        (17, 18),  # Delta
        # 18 = blank
        (19, 20),  # TIDAL GP
        (20, 21),  # YoY
        (21, 22),  # Delta
    ],
    "aoi": [
        (3,  4),   # Gross profit
        (4,  5),   # YoY
        (5,  6),   # Delta
        # 6 = blank
        (7,  8),   # AOI
        (8,  9),   # Margin
        (9,  10),  # Delta
        # 10 = blank
        (11, 12),  # Rule of 40
        (12, 13),  # Delta pts
    ],
    "cashapp": [
        (3,  4),   # Actives
        (4,  5),   # YoY
        (5,  6),   # Delta
        # 6 = blank
        (7,  8),   # IPA
        (8,  9),   # YoY
        (9,  10),  # Delta
        # 10 = blank
        (11, 12),  # Mon Rate
        (12, 13),  # YoY
        (13, 14),  # Delta
    ],
    "commerce": "special",  # handled separately -- keyed off "Inflows" row
    "gpv": [
        (3,  4),   # Global GPV
        (4,  5),   # YoY
        (5,  6),   # Delta
        # 6 = blank
        (7,  8),   # US GPV
        (8,  9),   # YoY
        (9,  10),  # Delta
        # 10 = blank
        (11, 12),  # Intl GPV
        (12, 13),  # YoY
        (13, 14),  # Delta
    ],
}

# Commerce row offsets relative to the "Inflows" label row in the sheet
COMMERCE_ROW_OFFSETS = [
    (3, 0),    # Inflows
    (4, 1),    # YoY
    (5, 2),    # Delta
    # 6 = blank
    (7, 4),    # Mon Rate
    (8, 5),    # YoY
    (9, 6),    # Delta
]

# Regex for detecting raw decimal values that should be replaced with "--"
RAW_DECIMAL_RE = re.compile(
    r"^[\d\.\s\-]+\s*$"  # all digits, dots, spaces, optional trailing space
)

# Characters that indicate a formatted (display) value, not a raw decimal
FORMATTED_INDICATORS = ("$", "%", "bps", "pts", "M", "B", "K", "nm", "x", "pp")


# ---------------------------------------------------------------------------
# Sheet parsing
# ---------------------------------------------------------------------------

def load_sheet(path: str) -> list[list[str]]:
    """Load sheet JSON and return 2D array of string values."""
    with open(path) as f:
        data = json.load(f)

    values = data.get("values")
    if values is None:
        # Some formats nest it differently
        if isinstance(data, list):
            values = data
        elif "sheets" in data:
            values = data["sheets"][0].get("data", [{}])[0].get("rowData", [])
        else:
            raise ValueError(f"Cannot find 'values' key in sheet JSON. Top-level keys: {list(data.keys())}")

    # Normalize: ensure every cell is a string
    result = []
    for row in values:
        if isinstance(row, list):
            result.append([str(cell) if cell is not None else "" for cell in row])
        else:
            result.append([])
    return result


def find_section_starts(sheet: list[list[str]]) -> dict[str, int]:
    """Scan column B for section labels. Returns {table_key: row_index}."""
    sections = {}
    for row_idx, row in enumerate(sheet):
        if len(row) < 2:
            continue
        cell_b = row[1].strip()
        if not cell_b:
            continue

        # Exact matches
        if cell_b == SECTION_LABELS["gp"]:
            sections["gp"] = row_idx
        elif cell_b == SECTION_LABELS["aoi"]:
            sections["aoi"] = row_idx
        elif cell_b == SECTION_LABELS["gpv"]:
            sections["gpv"] = row_idx
        # Starts-with matches
        elif cell_b.startswith("2) Cash App") or cell_b.startswith("2) Cash App (Ex Commerce)"):
            sections["cashapp"] = row_idx
        elif cell_b.startswith("3) Commerce"):
            sections["commerce"] = row_idx

    return sections


def find_commerce_inflows_row(sheet: list[list[str]], section_start: int) -> int:
    """Find the row with label 'Inflows' in the Commerce section, skipping #N/A rows."""
    for offset in range(3, 30):  # search up to 30 rows past section header
        row_idx = section_start + offset
        if row_idx >= len(sheet):
            break
        row = sheet[row_idx]
        if len(row) < 2:
            continue
        label = row[1].strip()
        if label == "Inflows":
            return row_idx
    raise ValueError(
        f"Could not find 'Inflows' row in Commerce section starting at row {section_start}. "
        f"Scanned rows {section_start + 3} through {min(section_start + 32, len(sheet) - 1)}."
    )


def get_sheet_value(sheet: list[list[str]], row: int, col: int) -> str:
    """Get a display value from the sheet, returning '--' for missing/raw/NA values."""
    if row < 0 or row >= len(sheet):
        return "--"
    row_data = sheet[row]
    if col < 0 or col >= len(row_data):
        return "--"

    val = row_data[col].strip()

    # Empty or error
    if not val or val == "#N/A" or val == "#REF!" or val == "#VALUE!" or val == "#DIV/0!":
        return "--"

    # Check for raw decimal: no formatted indicators and matches raw pattern
    if not any(indicator in val for indicator in FORMATTED_INDICATORS):
        if RAW_DECIMAL_RE.match(val):
            return "--"

    return val


# ---------------------------------------------------------------------------
# Doc parsing
# ---------------------------------------------------------------------------

def load_doc(path: str) -> dict:
    """Load Doc structure JSON."""
    with open(path) as f:
        return json.load(f)


def get_tab_content(doc: dict, tab_id: str) -> list[dict] | None:
    """Recursively search tabs for the given tab_id, return body content elements."""
    tabs = doc.get("tabs", [])
    return _search_tabs(tabs, tab_id)


def _search_tabs(tabs: list[dict], tab_id: str) -> list[dict] | None:
    for tab in tabs:
        tid = tab.get("tabProperties", {}).get("tabId", "")
        if tid == tab_id:
            return tab.get("documentTab", {}).get("body", {}).get("content", [])
        child_result = _search_tabs(tab.get("childTabs", []), tab_id)
        if child_result is not None:
            return child_result
    return None


def find_doc_tables(content: list[dict]) -> list[dict]:
    """Extract all table elements from the doc content."""
    tables = []
    for elem in content:
        if "table" in elem:
            tables.append(elem)
    return tables


def identify_table(table_elem: dict) -> str | None:
    """Identify which table this is by scanning first-column text in data rows (row >= 3)."""
    table = table_elem["table"]
    table_rows = table.get("tableRows", [])

    for row_idx in range(3, min(len(table_rows), 15)):
        row = table_rows[row_idx]
        cells = row.get("tableCells", [])
        if not cells:
            continue
        # Get text from first cell (col 0)
        cell_text = _get_cell_text(cells[0])
        cell_text_stripped = cell_text.strip()

        for identifier, table_key in TABLE_IDENTIFIERS.items():
            if cell_text_stripped == identifier:
                return table_key

    return None


def _get_cell_text(cell: dict) -> str:
    """Extract full text from a table cell."""
    texts = []
    for content_elem in cell.get("content", []):
        para = content_elem.get("paragraph")
        if not para:
            continue
        for pe in para.get("elements", []):
            tr = pe.get("textRun")
            if tr:
                texts.append(tr.get("content", ""))
    return "".join(texts)


def _get_cell_first_text_run(cell: dict) -> dict | None:
    """Get the first textRun element from a table cell."""
    for content_elem in cell.get("content", []):
        para = content_elem.get("paragraph")
        if not para:
            continue
        for pe in para.get("elements", []):
            if "textRun" in pe:
                return pe
    return None


def _get_cell_start_index(cell: dict) -> int | None:
    """Get the startIndex of the first text run in a cell."""
    te = _get_cell_first_text_run(cell)
    if te is not None:
        return te.get("startIndex")
    return None


def _cell_has_existing_text(cell: dict) -> tuple[bool, int, int]:
    """
    Check if a cell has text content beyond just a newline.
    Returns (has_text, start_index, end_index_before_newline).
    """
    for content_elem in cell.get("content", []):
        para = content_elem.get("paragraph")
        if not para:
            continue
        elements = para.get("elements", [])
        if not elements:
            continue

        # Collect all text runs in this paragraph
        all_text = ""
        first_start = None
        last_end = None

        for pe in elements:
            tr = pe.get("textRun")
            if tr:
                si = pe.get("startIndex", pe.get("startIndex"))
                ei = pe.get("endIndex", pe.get("endIndex"))
                if first_start is None:
                    first_start = si
                last_end = ei
                all_text += tr.get("content", "")

        # If the text is just "\n", the cell is empty
        stripped = all_text.replace("\n", "").strip()
        if stripped and first_start is not None and last_end is not None:
            # end index is before the trailing \n
            return (True, first_start, last_end - 1 if all_text.endswith("\n") else last_end)
        elif first_start is not None:
            return (False, first_start, first_start)

    return (False, 0, 0)


# ---------------------------------------------------------------------------
# Request building
# ---------------------------------------------------------------------------

def build_cell_requests(
    start_index: int,
    value: str,
    tab_id: str,
    has_existing_text: bool,
    existing_start: int,
    existing_end: int,
) -> list[dict]:
    """
    Build the batch-update requests for a single cell:
    1. deleteContentRange (if cell has existing text)
    2. insertText
    3. updateTextStyle (Roboto 10pt)
    4. updateParagraphStyle (CENTER)
    """
    requests = []

    # If cell has existing text, delete it first
    if has_existing_text and existing_end > existing_start:
        requests.append({
            "deleteContentRange": {
                "range": {
                    "startIndex": existing_start,
                    "endIndex": existing_end,
                    "tabId": tab_id,
                }
            }
        })
        # After deletion, insert at existing_start
        insert_at = existing_start
    else:
        insert_at = start_index

    # Insert the value text
    requests.append({
        "insertText": {
            "location": {
                "index": insert_at,
                "tabId": tab_id,
            },
            "text": value,
        }
    })

    # Style the inserted text: Roboto 10pt
    text_end = insert_at + len(value)
    requests.append({
        "updateTextStyle": {
            "range": {
                "startIndex": insert_at,
                "endIndex": text_end,
                "tabId": tab_id,
            },
            "textStyle": {
                "fontSize": {"magnitude": 10, "unit": "PT"},
                "weightedFontFamily": {"fontFamily": "Roboto"},
            },
            "fields": "fontSize,weightedFontFamily",
        }
    })

    # Center alignment (range includes trailing \n)
    requests.append({
        "updateParagraphStyle": {
            "range": {
                "startIndex": insert_at,
                "endIndex": text_end + 1,  # include the \n
                "tabId": tab_id,
            },
            "paragraphStyle": {
                "alignment": "CENTER",
            },
            "fields": "alignment",
        }
    })

    return requests


def get_sort_key(request: dict) -> int:
    """Extract the startIndex from a request for sorting."""
    for key in ("deleteContentRange", "insertText", "updateTextStyle", "updateParagraphStyle"):
        if key in request:
            inner = request[key]
            if "range" in inner:
                return inner["range"].get("startIndex", 0)
            if "location" in inner:
                return inner["location"].get("index", 0)
    return 0


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def build_all_requests(
    sheet: list[list[str]],
    doc_tables: dict[str, dict],
    section_starts: dict[str, int],
    tab_id: str,
) -> tuple[list[dict], dict[str, int], list[str]]:
    """
    Build all batch-update requests for all 5 tables.
    Returns (requests, cell_counts, warnings).
    """
    all_requests = []
    cell_counts = {}
    warnings = []

    for table_key in ("gp", "aoi", "cashapp", "commerce", "gpv"):
        if table_key not in doc_tables:
            warnings.append(f"Doc table not found for: {table_key}")
            continue
        if table_key not in section_starts:
            warnings.append(f"Sheet section not found for: {table_key}")
            continue

        table_elem = doc_tables[table_key]
        section_start = section_starts[table_key]
        table = table_elem["table"]
        table_rows = table.get("tableRows", [])
        col_count = TABLE_COL_COUNTS[table_key]
        count = 0

        # Determine row mapping
        if table_key == "commerce":
            try:
                inflows_row = find_commerce_inflows_row(sheet, section_start)
            except ValueError as e:
                warnings.append(str(e))
                continue
            row_offsets = [(doc_row, inflows_row + sheet_offset) for doc_row, sheet_offset in COMMERCE_ROW_OFFSETS]
        else:
            offsets_def = TABLE_ROW_OFFSETS[table_key]
            row_offsets = [(doc_row, section_start + sheet_offset) for doc_row, sheet_offset in offsets_def]

        # Determine which doc columns to populate
        data_cols = []
        for doc_col in range(1, col_count):
            if doc_col == 4:  # separator column
                continue
            if doc_col in SHEET_COL_MAP:
                data_cols.append(doc_col)

        for doc_row, sheet_row in row_offsets:
            if doc_row >= len(table_rows):
                warnings.append(
                    f"Table {table_key}: doc row {doc_row} out of range "
                    f"(table has {len(table_rows)} rows)"
                )
                continue

            cells = table_rows[doc_row].get("tableCells", [])

            for doc_col in data_cols:
                # Check column is within this table
                if doc_col >= col_count:
                    continue
                if doc_col >= len(cells):
                    warnings.append(
                        f"Table {table_key}: doc col {doc_col} out of range at row {doc_row} "
                        f"(row has {len(cells)} cells)"
                    )
                    continue

                sheet_col = SHEET_COL_MAP[doc_col]
                value = get_sheet_value(sheet, sheet_row, sheet_col)

                cell = cells[doc_col]
                has_text, existing_start, existing_end = _cell_has_existing_text(cell)
                cell_start = _get_cell_start_index(cell)

                if cell_start is None:
                    warnings.append(
                        f"Table {table_key}: no startIndex for cell ({doc_row}, {doc_col})"
                    )
                    continue

                reqs = build_cell_requests(
                    start_index=cell_start,
                    value=value,
                    tab_id=tab_id,
                    has_existing_text=has_text,
                    existing_start=existing_start,
                    existing_end=existing_end,
                )
                all_requests.extend(reqs)
                count += 1

        cell_counts[table_key] = count

    return all_requests, cell_counts, warnings


def main():
    parser = argparse.ArgumentParser(
        description="Generate Docs API batch-update JSON to populate Block Performance Digest tables."
    )
    parser.add_argument("sheet_json", help="Path to cached pacing sheet JSON")
    parser.add_argument("doc_json", help="Path to Doc structure JSON")
    parser.add_argument("tab_id", help="Tab ID (e.g., t.c1h7yqcqcq60)")
    parser.add_argument(
        "--colors", action="store_true",
        help="Output a placeholder note about conditional color requests (requires Doc re-read)"
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    try:
        sheet = load_sheet(args.sheet_json)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading sheet JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        doc = load_doc(args.doc_json)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading doc JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Parse sheet sections
    # ------------------------------------------------------------------
    section_starts = find_section_starts(sheet)
    if not section_starts:
        print("Error: no section labels found in sheet column B.", file=sys.stderr)
        print(
            "Expected labels like '1a) Block gross profit', '1b) Block adjusted OI', etc.",
            file=sys.stderr,
        )
        sys.exit(1)

    found = ", ".join(f"{k} (row {v})" for k, v in sorted(section_starts.items(), key=lambda x: x[1]))
    print(f"Sheet sections found: {found}", file=sys.stderr)

    missing_sections = set(TABLE_COL_COUNTS.keys()) - set(section_starts.keys())
    if missing_sections:
        print(f"Warning: missing sheet sections: {missing_sections}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Parse doc tables
    # ------------------------------------------------------------------
    tab_content = get_tab_content(doc, args.tab_id)
    if tab_content is None:
        print(f"Error: tab '{args.tab_id}' not found in doc JSON.", file=sys.stderr)
        print("Available tabs:", file=sys.stderr)
        for tab in doc.get("tabs", []):
            tp = tab.get("tabProperties", {})
            print(f"  {tp.get('tabId', '?')} - {tp.get('title', '?')}", file=sys.stderr)
        sys.exit(1)

    raw_tables = find_doc_tables(tab_content)
    print(f"Found {len(raw_tables)} tables in doc tab.", file=sys.stderr)

    doc_tables: dict[str, dict] = {}
    for table_elem in raw_tables:
        table_key = identify_table(table_elem)
        if table_key:
            doc_tables[table_key] = table_elem
            row_count = table_elem["table"].get("rows", 0)
            col_count = table_elem["table"].get("columns", 0)
            print(f"  Identified: {table_key} ({row_count} rows x {col_count} cols)", file=sys.stderr)
        else:
            row_count = table_elem["table"].get("rows", 0)
            col_count = table_elem["table"].get("columns", 0)
            print(f"  Unidentified table ({row_count} rows x {col_count} cols)", file=sys.stderr)

    if not doc_tables:
        print("Error: no tables could be identified in the doc.", file=sys.stderr)
        sys.exit(1)

    missing_tables = set(TABLE_COL_COUNTS.keys()) - set(doc_tables.keys())
    if missing_tables:
        print(f"Warning: missing doc tables: {missing_tables}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Build requests
    # ------------------------------------------------------------------
    all_requests, cell_counts, warnings = build_all_requests(
        sheet, doc_tables, section_starts, args.tab_id,
    )

    for w in warnings:
        print(f"Warning: {w}", file=sys.stderr)

    # Sort ALL requests by startIndex DESCENDING
    all_requests.sort(key=get_sort_key, reverse=True)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    total_cells = sum(cell_counts.values())
    table_summary = ", ".join(f"{k}={v}" for k, v in sorted(cell_counts.items()))
    print(f"Total cells to populate: {total_cells} ({table_summary})", file=sys.stderr)
    print(f"Total requests: {len(all_requests)}", file=sys.stderr)

    json.dump({"requests": all_requests}, sys.stdout, indent=2)
    print(file=sys.stdout)  # trailing newline

    if args.colors:
        # Colors require a Doc re-read after values are inserted, because
        # all startIndex values shift. Output a note instead of stale indices.
        print(file=sys.stdout)  # blank separator line
        color_note = {
            "_comment": (
                "Conditional colors for Delta rows require a Doc re-read after "
                "the value batch is applied. Re-run with the updated Doc JSON, or "
                "use the weekly-tables skill Step 7 to apply colors in a second pass."
            ),
            "requests": [],
        }
        json.dump(color_note, sys.stdout, indent=2)
        print(file=sys.stdout)
        print(
            "Note: color batch is empty -- re-read the Doc after applying values, "
            "then use the color pass.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
