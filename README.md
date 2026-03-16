# Block FP&A — Financial Reporting Automation

Agent infrastructure for automating Block financial reporting deliverables using Claude Code.

---

## System Map

Three component types, each with a distinct role:

| Type | Component | Description |
|------|-----------|-------------|
| **Global Recipe** | [`skills/financial-reporting/`](skills/financial-reporting/SKILL.md) | Base standards applied to every report — metric formats, rounding, style rules. Must be loaded first. |
| **Sub-Skill** | [`skills/financial-reporting-weekly/`](skills/financial-reporting-weekly/SKILL.md) | Step-by-step instructions for populating the weekly performance digest. Depends on global recipe + gdrive. |
| **Sub-Skill** | [`skills/financial-reporting-mrp/`](skills/financial-reporting-mrp/SKILL.md) | Step-by-step instructions for populating the Monthly Reporting Pack. Two-phase: coverage check then population. Depends on global recipe + gdrive + Block Data MCP. |
| **Utility Skill** | [`skills/gdrive/`](skills/gdrive/SKILL.md) | Google Drive CLI wrapper — Docs, Sheets, Slides read/write. Required by reporting sub-skills. |
| **Agent** | [`agents/financial-reporting-weekly.md`](agents/financial-reporting-weekly.md) | Runs the weekly report end-to-end: reads master Sheet, creates dated Doc tab, populates fact lines and tables. |
| **Agent** | [`agents/financial-reporting-weekly-validator.md`](agents/financial-reporting-weekly-validator.md) | Validates weekly report accuracy after it's written. Field-by-field PASS/FAIL against the source Sheet. |
| **Agent** | [`agents/financial-reporting-mrp.md`](agents/financial-reporting-mrp.md) | Runs the MRP end-to-end: coverage check vs. Block Data MCP, creates new monthly Doc, populates full P&L, brand tables, and fact lines. |
| **Agent** | [`agents/financial-reporting-mrp-validator.md`](agents/financial-reporting-mrp-validator.md) | Validates MRP accuracy after it's written. Field-by-field PASS/FAIL across all tables, fact lines, and emojis. |

---

## Dependency Chain

```
[Global Recipe] financial-reporting
        ├── [Sub-Skill] financial-reporting-weekly
        │       ├── depends on: financial-reporting
        │       └── depends on: gdrive
        │               └── [Agent] financial-reporting-weekly.md
        │                           └── validated by: financial-reporting-weekly-validator.md
        │
        └── [Sub-Skill] financial-reporting-mrp
                ├── depends on: financial-reporting
                ├── depends on: gdrive
                └── data source: Block Data MCP
                        └── [Agent] financial-reporting-mrp.md
                                    └── validated by: financial-reporting-mrp-validator.md
```

---

## How to Use

**Weekly report:**
1. Load `financial-reporting` skill (global recipe — required first)
2. Load `financial-reporting-weekly` skill
3. Say: _"data is ready, run the weekly report"_

**Validate the weekly report:**
After the weekly agent completes, invoke the `financial-reporting-weekly-validator` agent.

**Monthly Reporting Pack (MRP):**
1. Load `financial-reporting` skill (global recipe — required first)
2. Load `financial-reporting-mrp` skill
3. Say: _"data is ready, run the MRP"_
4. Review the Phase A coverage report and confirm before Phase B population begins

**Validate the MRP:**
After the MRP agent completes Phase B, invoke the `financial-reporting-mrp-validator` agent with the new Doc ID.

---

## Roadmap

| Deliverable | Status |
|-------------|--------|
| Global reporting recipe | ✅ Complete |
| Weekly report agent | ✅ Complete |
| Weekly report validator | ✅ Complete |
| Monthly reporting pack (MRP) agent | ✅ Complete |
| MRP validator | ✅ Complete |
| Board report agent | Planned |

---

## Reference

| File | Description |
|------|-------------|
| [`decisions/log.md`](decisions/log.md) | Append-only architecture decision log |
| [`references/fpa-style-guide.md`](references/fpa-style-guide.md) | Block FP&A style & formatting standards |
