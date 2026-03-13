# Weekly Report Automation — Architecture & Kickoff Prompt

## Context
Nick manually compiles and validates weekly financial data in a single master Google Sheet. Everything after that is the automation target: reading the finalized data, populating an existing Google Doc report template with tables and formatted fact lines, and leaving narrative placeholders for Nick to fill in drivers and context. The agent must inherit Block's global reporting recipe (formatting standards, metric formats, comparison framework) before applying any weekly-specific logic.

---

## Architecture

**Three-layer stack:**
| Layer | What | Status |
|-------|------|--------|
| Global Recipe | Formatting, metric standards, comparison framework | Exists — `SKILL.md` |
| Weekly Report Sub-Agent | Inherits global recipe; report-specific logic | To build |
| Google Workspace MCP | Connects Claude to Sheets and Docs APIs | Pending Mac |

**Trigger:** Manual — Nick tells Claude "data is ready, run the weekly report."

**Agent workflow:**
1. Load and internalize global recipe (`SKILL.md`)
2. Read master Google Sheet — all metrics (Block GP, brand GPs, Square GPV, Cash App Inflows/Actives/monetization rate, Commerce Inflows/monetization rate, AOI, pacing vs. AP / consensus / guidance)
3. Read the weekly report Google Doc — prior weeks live as separate tabs (e.g., '3/3', '2/24'); reference them to understand the expected structure and detail level
4. Create a new tab labeled with the current Tuesday's date (e.g., '3/10')
5. Copy/paste updated tables from Sheet into the new tab
6. Write a quantitative fact line for each metric per global recipe format
7. Insert `[DRI to include context]` after any line needing driver/narrative
8. Insert `[DATA MISSING: {metric} | {period}]` for any gaps
9. Report back: which sections are populated, which have missing data

**What the agent does NOT do:**
- Fill in reasons, drivers, or narrative (that's Nick's job)
- Estimate or infer missing data
- Override global recipe standards

---

## Mac Day 1 Kickoff Prompt

Use this prompt to kick off the first build session once Google Workspace MCP is connected.
Fill in `[SHEET_FILE_ID]` and `[DOC_FILE_ID]` from the Google Drive URLs before running.

```
Context: I am a Finance Manager at Block (NYSE: XYZ). I own the weekly financial
reporting deliverable for Block executive leadership (innercore). My goal is to
automate the population of this report from a governed Google Sheet master table.

You are the Weekly Report Sub-Agent.

Step 1 — Load the global recipe:
Read and internalize the global reporting recipe at:
SKILL.md
These standards govern ALL reporting output and may not be overridden.

Step 2 — Understand the data source:
Read the master Google Sheet at: [SHEET_FILE_ID]
- Structure: rows = metrics, columns = time periods
- Identify all available metrics and time periods
- Note the current quarter's actuals (closed periods) and pacing (open periods)
- Benchmark comparisons needed: internal forecast (AP or applicable Outlook),
  consensus (from consensus tab), and guidance

Step 3 — Review prior examples and understand report structure:
Read the weekly report Google Doc at: [DOC_FILE_ID]
Prior weeks each have their own tab (e.g., '3/3', '2/24', '2/17').
Review the most recent 2–3 tabs to understand:
- The structure of each section
- Level of detail expected in fact lines
- Where tables appear vs. narrative text

Step 4 — Create a new tab for this week:
Create a new tab in the same Google Doc labeled with this Tuesday's date (e.g., '3/10').
Use the prior week's tab as the structural template.

Step 5 — Populate the report:
- Copy updated data tables from the Sheet into the Doc (exact values, no rounding
  or reformatting beyond global recipe rules)
- For each metric, write a fact line:
    Pacing format: "[Metric] is pacing to [Value] in [Period] ([+/-]% YoY),
    [+/-]% ([+/-$]) [above/below] [Forecast]"
    Actuals format: "[Metric] landed at [Value] ([+/-]% YoY), [+/-]% ([+/-$])
    [above/below] [Forecast]"
- After each fact line where context/drivers are needed, insert on a new line:
    [DRI to include context]
- For any missing data, insert:
    [DATA MISSING: {metric} | {period}]

Step 6 — Report back:
List which sections were populated successfully and which have missing data flags.
Do NOT fill in drivers, narrative, or explanations — those are for me to complete.
```

---

## Pre-Mac Prep Checklist

- [ ] Master Sheet file ID (from the URL: `docs.google.com/spreadsheets/d/[FILE_ID]/`)
- [ ] Weekly report Doc file ID (same pattern — prior weeks are tabs in the same Doc)
- [ ] Confirm which Sheet tab(s) are the clean summary data (vs. build-up/model tabs)
- [ ] Complete Google Cloud project setup (OAuth credentials) for Google Workspace MCP

---

## Verification (End-to-End Test)

1. Confirm MCP is connected: Claude can read the master Sheet and weekly report Doc
2. Run manual trigger: "data is ready, run the weekly report"
3. Check tables in the Doc match Sheet values exactly
4. Check fact lines follow global recipe format (pacing vs. actuals, correct units/rounding/signs)
5. Check `[DRI to include context]` placeholders appear where expected
6. Check `[DATA MISSING]` tags appear for any gaps
7. Confirm no narrative or driver text was generated by the agent
