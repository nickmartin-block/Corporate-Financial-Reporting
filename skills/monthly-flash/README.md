# Block Monthly Topline Flash — Automation

A single command (`/monthly-flash`) that generates, publishes, and validates the Block Monthly Topline Flash using Claude Code.

---

## What It Does

Each month after close, Block FP&A publishes a topline flash email with preliminary results for senior management. This system automates the entire pipeline:

1. **Reads the MRP Charts & Tables sheet** — pulls every in-scope metric from a single range (`L11:Y90`): gross profit by brand and sub-product, volume metrics (GPV, GMV, Actives, Inflows), Variable Profit, Adjusted OpEx breakdown (V/A/F), Adjusted Operating Income, and Rule of 40.

2. **Generates the narrative** — writes a structured flash report with:
   - **Title block**: "Block Topline Flash: [Month] [Year]" with a disclaimer noting preliminary figures and a `[MRP DATE]` placeholder for the Monthly Management Reporting Pack date.
   - **Summary section**: Block GP headline with brand bridge, followed by Cash App (6 sub-products + ex-Commerce detail + Actives + Inflows + Monetization Rate + Commerce GMV), Square (5 sub-products + Global/US/INTL GPV with constant-currency), TIDAL, Proto, Variable Profit, Adjusted OpEx with V/A/F breakdown, Adjusted OI, and Rule of 40.
   - Every metric includes: Actual, vs. AP delta ($ and %), YoY %, and prior month YoY % where available.

3. **Publishes to Google Docs** — clears the target tab, inserts the markdown with rich formatting (headings, bold metric labels, nested bullet lists), and applies post-insertion fixes for bullet nesting and italic/bold disclaimer text.

4. **Validates the data** — compares every metric value in the published Doc against the source spreadsheet. Checks Actuals, vs. AP deltas, YoY rates, sub-product deltas, and brand bridge contributions. Reports PASS/FAIL with details on any mismatches.

The output is a management-ready Google Doc tab, a local markdown file, and a validation report. One `[MRP DATE]` placeholder is left for the Monthly Management Reporting Pack date, which varies each month.

---

## How To Run

Open Claude Code in the project directory and type:

```
/monthly-flash
```

That's it. The command handles everything end-to-end:
- Step 1: Auth check (Google Drive)
- Step 2: Read MRP Charts & Tables sheet
- Step 3: Generate the flash narrative
- Step 4: Save markdown file
- Step 5: Publish to Google Doc (with formatting fixes)
- Step 6: Validate every metric against the source sheet
- Step 7: Report results

Output files:
- `~/Desktop/Nick's Cursor/Monthly Reporting/monthly_flash_YYYY_MM.md`
- `~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md`

---

## What's In This Directory

```
skills/monthly-flash/
  ├── commands/                    Slash commands (what you type)
  │   └── monthly-flash.md          Full pipeline: generate + publish + validate
  │
  └── skills/                      Reference docs (loaded as context)
      └── financial-reporting.md     Global formatting recipe (rounding, signs, etc.)
```

The monthly flash reuses the same `gdrive-cli.py` tool from `skills/weekly-reporting/gdrive/` for all Google Sheets and Docs operations.

---

## Key Data Sources

| Source | What It Provides |
|--------|-----------------|
| MRP Charts & Tables sheet (`L11:Y90`) | All metric values — actuals, vs. AP, vs. Q1OL, YoY %, Jan YoY % |

### Metrics Covered (21 metrics, 106 validated values)

| Section | Metrics |
|---------|---------|
| Gross Profit | Block GP, Cash App GP (+ 6 sub-products), Square GP (+ 5 sub-products), TIDAL GP, Proto GP |
| Cash App Detail | ex-Commerce GP, Actives, Inflows per Active, Monetization Rate, Commerce GMV |
| Volume | Square GPV (Global, US, INTL, INTL CC) |
| Profitability | Variable Profit, Adjusted OpEx (+ V/A/F breakdown), Adjusted OI, Rule of 40 |

---

## Comparison Framework

The flash compares to **Annual Plan (AP)** for Q1. For subsequent quarters, the comparison point shifts per the financial-reporting recipe:

| Quarter | Comparison Point |
|---------|-----------------|
| Q1 | AP |
| Q2 | Q2OL |
| Q3 | Q3OL |
| Q4 | Q4OL |

---

## What's Automated vs. Manual

| Automated | Manual |
|-----------|--------|
| All metric extraction from the sheet | `[MRP DATE]` — Monthly Reporting Pack date |
| Narrative generation with formatting rules | Final review before distribution |
| Brand bridge calculation (Cash App + Square + Other Brands) | Qualitative commentary (future enhancement) |
| Sub-product outperformance sorting | |
| Google Doc publishing with bullet nesting + italic/bold | |
| Cell-by-cell data validation (106 values) | |

---

## Doc Publishing Notes

The Google Docs markdown converter requires two post-insertion fixes that the command handles automatically:

1. **Bullet nesting** — The converter renders parent bullets (Cash App, Square) as paragraphs instead of list items. The command deletes bullets, inserts tab characters at sub-item starts, then recreates bullets to achieve proper nesting (level 0 parents, level 1 children).

2. **Italic/bold disclaimer** — The converter doesn't render `*italic **bold** italic*` correctly. The command removes literal asterisks and applies italic/bold formatting via the Docs API.
