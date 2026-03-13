# Block FP&A — Financial Reporting Automation

Agent infrastructure for automating Block financial reporting deliverables.

## What's in here

| File / Folder | Description |
|---------------|-------------|
| `SKILL.md` | Global reporting recipe — data rules, metric formats, style standards, sub-agent inheritance |
| `docs/weekly-report-plan.md` | Weekly report sub-agent architecture + Mac Day 1 kickoff prompt |
| `decisions/log.md` | Append-only log of key architecture and process decisions |
| `references/fpa-style-guide.md` | Block FP&A Style & Formatting Guide |

## How to use

**Starting a new reporting agent:**
1. Load `SKILL.md` first — these standards apply to all agents and may not be overridden
2. Apply deliverable-specific logic on top

**Building the weekly report sub-agent (Mac Day 1):**
See `docs/weekly-report-plan.md` for the full architecture and kickoff prompt.
Requires Google Workspace MCP connected to Google Drive, Sheets, and Docs.

## Roadmap

| Deliverable | Status |
|-------------|--------|
| Global reporting recipe | Complete |
| Weekly report sub-agent | Architecture planned — pending Mac + MCP |
| Monthly reporting pack (MRP) sub-agent | Future |
| Board report sub-agent | Future |
