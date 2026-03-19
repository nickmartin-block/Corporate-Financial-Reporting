# Block FP&A Reporting — Automation

Automated financial reporting for Block FP&A using Claude Code. Single slash commands that generate, publish, and validate management reports from governed spreadsheet data.

---

## Reports

### Weekly Performance Digest (`/weekly-summary`)

Generates the weekly Block Performance Digest with emoji-coded narrative, detailed overview sections, and formatted performance tables. Pulls from the master pacing sheet and Slack digests, publishes to a dated Google Doc tab, and validates every table cell against the source.

See [`skills/weekly-reporting/`](skills/weekly-reporting/) for full details.

### Monthly Topline Flash (`/monthly-flash`)

Generates the monthly topline flash email with preliminary close results. Covers 21 metrics across gross profit, volume, and profitability — all validated against the MRP Charts & Tables sheet (106 values checked).

See [`skills/monthly-flash/`](skills/monthly-flash/) for full details.

---

## Architecture

```
skills/
  ├── weekly-reporting/              Weekly Performance Digest
  │   ├── commands/                    /weekly-summary, /weekly-tables, /weekly-validate
  │   ├── skills/                      Formatting recipe, table specs, validation logic
  │   └── gdrive/                      Google Drive CLI (shared tool)
  │
  └── monthly-flash/                 Monthly Topline Flash
      ├── commands/                    /monthly-flash
      └── skills/                      Formatting recipe (inherited)
```

Both reporting systems share:
- **`financial-reporting.md`** — global formatting recipe (rounding, signs, comparison framework, deviation handling)
- **`gdrive-cli.py`** — CLI tool for Google Sheets, Docs, and Slides operations
- **Validation pattern** — independent re-read of source data, normalize + compare with rounding tolerance, PASS/FAIL report

---

## Quick Start

1. Open Claude Code in the project directory
2. Run a command:

```
/weekly-summary     # Full weekly digest pipeline
/monthly-flash      # Full monthly flash pipeline
```

Both commands handle auth, data extraction, narrative generation, Google Doc publishing, and validation end-to-end.
