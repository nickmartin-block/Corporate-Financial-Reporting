# Block Weekly Performance Digest — Automation

A single command (`/weekly-summary`) that generates, publishes, and validates the weekly Block Performance Digest using Claude Code.

---

## What It Does

Every week, Block FP&A publishes a performance digest for senior management. This system automates the entire pipeline:

1. **Reads the master pacing spreadsheet** — pulls every in-scope metric (gross profit by brand, AOI, Rule of 40, Cash App inflows, Commerce inflows, Square GPV) with monthly actuals, quarterly pacing, annual plan, guidance, and consensus comparisons.

2. **Reads Slack for context** — finds the latest Cash App and Square weekly digests in the reporting group DM and synthesizes WoW driver commentary (no names or attribution in the output).

3. **Generates the narrative** — writes a two-layer report:
   - **Summary**: emoji-coded executive overview covering every major metric with YoY, vs. AP, vs. guidance/consensus context, and WoW change drivers.
   - **Overview sections**: detailed plain-text commentary + formatted performance tables for each area (Gross Profit, AOI & Rule of 40, Inflows, Commerce, Square GPV).

4. **Publishes to Google Docs** — creates a dated tab in the weekly digest Doc, converts the markdown to rich formatting (headings, bold, bullets, tables with black headers, pacing column shading), and applies Inter font throughout.

5. **Validates the data** — compares every number in the published Doc tables cell-by-cell against the source spreadsheet. Reports PASS/FAIL with details on any mismatches.

The output is a management-ready Google Doc tab and a local validation report. A few `[MANUAL]` placeholders are left for context that requires human judgment (e.g., Square WoW drivers, Proto qualitative context).

---

## How To Run

Open Claude Code in the project directory and type:

```
/weekly-summary
```

That's it. The command handles everything end-to-end:
- Step 1: Auth check (Google Drive + Slack)
- Step 2: Read master pacing sheet
- Step 3: Read Slack digests
- Step 4: Generate the narrative + tables
- Step 5: Save markdown file + publish to Google Doc
- Step 6: Validate published tables against source data
- Step 7: Report results

Output files:
- `~/Desktop/Nick's Cursor/Weekly Reporting/weekly_summary_YYYY-MM-DD.md`
- `~/Desktop/Nick's Cursor/Weekly Reporting/validation_YYYY-MM-DD.md`

### Standalone commands

You can also run individual pieces:
- `/weekly-tables` — generate just the performance tables (useful for testing)
- `/weekly-validate` — re-run validation on an already-published tab

---

## What's In This Repo

```
skills/weekly-reporting/
  ├── commands/                    Slash commands (what you type)
  │   ├── weekly-summary.md          Full pipeline: generate + publish + validate
  │   ├── weekly-tables.md           Standalone table generation
  │   └── weekly-validate.md         Standalone validation
  │
  ├── skills/                      Reference docs (loaded as context)
  │   ├── financial-reporting.md     Global formatting recipe (rounding, signs, etc.)
  │   ├── weekly-summary.md          Skill definition for the summary generator
  │   ├── weekly-tables.md           Table column mapping + cell formatting rules
  │   └── weekly-validate.md         Validation procedure + normalization rules
  │
  └── gdrive/                      Google Drive CLI tool
      ├── gdrive-cli.py              CLI for Docs, Sheets, Slides operations
      └── scripts/
          ├── markdown_converter.py   Converts markdown → Google Docs API requests
          ├── auth.py                 OAuth handling
          └── services.py             Google API service builders
```

---

## Key Data Sources

| Source | What It Provides |
|--------|-----------------|
| Master pacing sheet (Google Sheets) | All metric values — actuals, pacing, AP, guidance, consensus |
| Slack group DM (C07LV8RS05A) | Cash App weekly digest + Square weekly update for WoW driver context |

---

## What's Automated vs. Manual

| Automated | Manual |
|-----------|--------|
| All metric extraction from the sheet | Square WoW driver context (if not posted to Slack) |
| YoY, vs. AP, vs. guidance/consensus calculations | Proto qualitative context (deal timing, etc.) |
| Emoji assignment (green/yellow/red) | Final review before distribution |
| Narrative generation | |
| Table construction + formatting | |
| Google Doc publishing with rich formatting | |
| Cell-by-cell data validation | |
