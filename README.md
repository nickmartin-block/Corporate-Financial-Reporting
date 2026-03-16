# Block FP&A — Financial Reporting Automation

Agent infrastructure for automating Block financial reporting deliverables using Claude Code.

---

## System Map

Three component types, each with a distinct role:

| Type | Component | Description |
|------|-----------|-------------|
| **Global Recipe** | [`skills/financial-reporting/`](skills/financial-reporting/SKILL.md) | Base standards applied to every report — metric formats, rounding, style rules. Must be loaded first. |
| **Sub-Skill** | [`skills/financial-reporting-weekly/`](skills/financial-reporting-weekly/SKILL.md) | Step-by-step instructions for populating the weekly performance digest. Depends on global recipe + gdrive. |
| **Utility Skill** | [`skills/gdrive/`](skills/gdrive/SKILL.md) | Google Drive CLI wrapper — Docs, Sheets, Slides read/write. Required by the weekly skill. |
| **Agent** | [`agents/financial-reporting-weekly.md`](agents/financial-reporting-weekly.md) | Runs the weekly report end-to-end: reads master Sheet, creates dated Doc tab, populates fact lines and tables. |
| **Agent** | [`agents/financial-reporting-weekly-validator.md`](agents/financial-reporting-weekly-validator.md) | Validates weekly report accuracy after it's written. Field-by-field PASS/FAIL against the source Sheet. |

---

## Dependency Chain

```
[Global Recipe] financial-reporting
        └── [Sub-Skill] financial-reporting-weekly
                ├── depends on: financial-reporting
                └── depends on: gdrive
                        └── [Agent] financial-reporting-weekly.md
                                    └── validated by: financial-reporting-weekly-validator.md
```

---

## How to Use

**Weekly report:**
1. Load `financial-reporting` skill (global recipe — required first)
2. Load `financial-reporting-weekly` skill
3. Say: _"data is ready, run the weekly report"_

**Validate the weekly report:**
After the weekly agent completes, invoke the `financial-reporting-weekly-validator` agent.

---

## Roadmap

| Deliverable | Status |
|-------------|--------|
| Global reporting recipe | ✅ Complete |
| Weekly report agent | ✅ Complete |
| Weekly report validator | ✅ Complete |
| Monthly reporting pack (MRP) agent | Planned |
| Board report agent | Planned |

---

## Reference

| File | Description |
|------|-------------|
| [`decisions/log.md`](decisions/log.md) | Append-only architecture decision log |
| [`references/fpa-style-guide.md`](references/fpa-style-guide.md) | Block FP&A style & formatting standards |
